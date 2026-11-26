"""Ranked stages, joint air-command treaties and rankings.

Defeated nations stay sovereign: only the aircraft and support named in a signed
treaty come under joint command, and they can be grounded or withdrawn.
"""

from nebula.core.intel import add_intel
from nebula.core.state import (RuleError, add_aircraft, home, change_relation, change_reputation,
                               change_trust, clamp, gain, log, record, relation, stats)
from nebula.data.aircraft import AIRCRAFT
from nebula.data.campaign import CHAPTERS
from nebula.data.characters import LEADERS, AIR_CHIEFS
from nebula.data.countries import COUNTRIES
from nebula.data.treaty import AIR_TERMS, DEFENSIVE_TYPES, OBJECTIONS, PRIORITY, TERMS

STAGE_OPPONENTS = [c for c, _, _ in CHAPTERS[:9]]  # the authored Lumeris ladder


def national_order() -> list[str]:
    return sorted(COUNTRIES, key=lambda c: -COUNTRIES[c]["military"])


def opponents(nation: str) -> list[str]:
    """The other nine nations, weakest first. For Lumeris this is the authored ladder."""
    return [c for c in reversed(national_order()) if c != nation]


def start_rank(state) -> int:
    return national_order().index(home(state)) + 1
SUPPLIES = {"none": (0, 0), "modest": (100, 60), "large": (200, 120)}  # fuel, materials at signing
DAILY = {"none": (0, 0), "modest": (8, 4), "large": (16, 8)}
BASE_RANGE_RELIEF = {"none": 0, "selected": 2, "wide": 5}


def remember(state, text):
    state.setdefault("history", []).append({"day": state["day"], "text": text})


def joint(state) -> dict:
    return state.setdefault("joint", {})


def rating(spec: dict) -> float:
    return sum(spec[k] for k in ("speed", "agility", "armour", "radar")) / 4


def grounded(state, plane) -> bool:
    owner = plane.get("owner")
    return bool(owner) and joint(state)[owner]["status"] == "restricted"


def air_ratings(state) -> dict:
    """Combat-aircraft capability of every command, from actual inventories."""
    from nebula.data.forces import INVENTORY

    result = {home(state): sum(rating(stats(p)) for p in state["fleet"] if not grounded(state, p))}
    for country, counts in INVENTORY.items():
        if country == home(state):
            continue
        lent = sum(rating(AIRCRAFT[p["type"]]) for p in state["fleet"]
                   if p.get("owner") == country and not grounded(state, p))
        result[country] = sum(rating(AIRCRAFT[k]) * n for k, n in counts.items()) - lent
    return {c: round(v) for c, v in result.items()}


def signed_stages(state) -> int:
    """Stages whose ten missions are done and whose treaty was signed (each counts once)."""
    return sum(bool(r["signed"]) for r in state.get("stage_reports", {}).values())


def joint_rank(state) -> int:
    """Competitive position: one place per stage treaty. It never alters strength."""
    return max(1, start_rank(state) - signed_stages(state))


def air_ranking(state) -> list[dict]:
    """The competitive ladder, each entry carrying its actual calculated strength."""
    ratings = air_ratings(state)
    order = [c for c in national_order() if c != home(state)]
    order.insert(joint_rank(state) - 1, home(state))
    return [{"country": c, "rating": ratings[c]} for c in order]


def reports(state) -> dict:
    """Saved stage reports, with ranks shown as one step per signed treaty.

    Reports written by the earlier strength-based ranking are recalculated for
    display only; the saved records are left as they were.
    """
    saved = state.get("stage_reports", {})
    shown, signed = {}, 0
    for key, r in sorted(saved.items(), key=lambda item: (item[1]["day"], item[1]["stage"])):
        previous = 10 - signed
        signed += bool(r["signed"])
        shown[key] = r if r.get("stepped") else {**r, "previous_rank": previous, "new_rank": 10 - signed}
    return shown


def track_rank(state):
    rank = joint_rank(state)
    old = state.get("joint_rank", start_rank(state))
    if rank != old:
        state["joint_rank"] = rank
        remember(state, f"Joint air-command ranking moved from {old} to {rank}")
        log(state, "rank_change", previous=old, new=rank, rating=air_ratings(state)[home(state)])


def stage_complete(state, stage: int) -> bool:
    return all(str(n) in state["completed"] for n in range(stage * 10 - 9, stage * 10 + 1))


def check_unlocked(state, level: int):
    previous = (level - 1) // 10
    if previous and str(level) not in state["completed"] and str(previous) not in state.get("stage_reports", {}):
        raise RuleError(f"Conclude Stage {previous} first: negotiate with its nation or postpone the treaty")


def _check_stage(state, stage: int) -> str:
    if not 1 <= stage <= 9:
        raise RuleError("That stage has no treaty")
    if not stage_complete(state, stage):
        raise RuleError("Complete all ten missions of this stage first")
    country = opponents(home(state))[stage - 1]
    if joint(state).get(country, {}).get("status") in ("active", "restricted"):
        raise RuleError("A joint command treaty is already in force")
    return country


def clean_terms(terms: dict) -> dict:
    if set(terms) != set(TERMS) or any(terms[k] not in [o[0] for o in TERMS[k][1]] for k in TERMS):
        raise RuleError("Every treaty term needs a valid choice")
    return dict(terms)


def _cost(country, key, option) -> int:
    base = next(o[2] for o in TERMS[key][1] if o[0] == option)
    if PRIORITY[country] != key:
        return base
    # A priority doubles what hurts; for exchanges they value, their absence hurts.
    if key == "technology":
        return -8 if option == "shared" else 10
    return base * 2 if base > 0 else base


def burden(country, terms) -> int:
    return sum(_cost(country, k, v) for k, v in terms.items())


def willingness(state, country) -> float:
    return round(20 + (state["trust"][country] - 40) * 0.6 + relation(state, country) * 0.35
                 + (state["reputation"] - 50) * 0.3 + 6 * ("peace" in state["treaties"][country]), 1)


def _counter(country, terms, limit):
    """Soften the costliest term one step at a time until the partner could sign."""
    offer = dict(terms)
    goodwill = {"technology": "shared", "training": "shared", "defence": "mutual", "withdrawal": "notice"}
    while burden(country, offer) > limit:
        steps = []
        for key, (_, options) in TERMS.items():
            ids = [o[0] for o in options]
            if key in goodwill:
                target = goodwill[key]
            else:
                target = ids[max(0, ids.index(offer[key]) - 1)]
            saving = _cost(country, key, offer[key]) - _cost(country, key, target)
            if saving > 0:
                # Aircraft are the point of the talks, so they are conceded last.
                steps.append((key != "aircraft", saving, key, target))
        if not steps:
            return None
        _, _, key, target = max(steps)
        offer[key] = target
    return offer


def _voices(country, before, after=None):
    """Leader and air chief each speak about the term in their remit that matters most."""
    lines = []
    for speaker, mine in ((LEADERS[country], False), (AIR_CHIEFS[country], True)):
        keys = [k for k in TERMS if (k in AIR_TERMS) == mine and
                (before[k] != after[k] if after else _cost(country, k, before[k]) > 0)]
        if keys:
            worst = max(keys, key=lambda k: _cost(country, k, before[k]))
            lines.append({"speaker": speaker, "text": OBJECTIONS[worst]})
        else:
            lines.append({"speaker": speaker, "text": "My part of this I can accept."})
    return lines


def propose(state, stage: int, terms: dict) -> str:
    country = _check_stage(state, stage)
    if country in state.get("wars", {}):
        raise RuleError("You are at war with this nation. Agree a ceasefire first, or postpone.")
    terms = clean_terms(terms)
    margin = willingness(state, country) - burden(country, terms)
    counter = None if margin >= 0 or margin < -22 else _counter(country, terms, willingness(state, country))
    outcome = "accept" if margin >= 0 else "counter" if counter else "reject"
    talks = {"stage": stage, "day": state["day"], "outcome": outcome, "terms": terms, "counter": counter}
    record(state, "negotiations", country=country, kind=f"joint:{outcome}",
           success=int(outcome == "accept"), offer=0)
    log(state, "joint_treaty", country=country, outcome=outcome, burden=burden(country, terms))
    name = COUNTRIES[country]["name"]
    if outcome == "accept":
        talks["lines"] = [{"speaker": LEADERS[country], "text": "We remain our own nation. On these terms, our wings may fly beside yours."},
                          {"speaker": AIR_CHIEFS[country], "text": "The aircraft will be ready. Treat their crews as you treat your own."}]
        state.setdefault("talks", {})[country] = talks
        _sign(state, stage, country, terms, margin)
        return f"{name} accepted the treaty."
    talks["lines"] = _voices(country, terms, counter)
    state.setdefault("talks", {})[country] = talks
    if outcome == "reject":
        change_trust(state, country, -6)
        change_relation(state, country, -4, reason="unfair_proposal")
        remember(state, f"{name} rejected your proposed terms")
        return f"{name} rejected those terms. Distrust has grown."
    return f"{name} sent a counteroffer."


def accept_counter(state, stage: int) -> str:
    country = _check_stage(state, stage)
    talks = state.get("talks", {}).get(country)
    if not talks or not talks.get("counter"):
        raise RuleError("There is no counteroffer to accept")
    record(state, "negotiations", country=country, kind="joint:accept_counter", success=1, offer=0)
    log(state, "joint_treaty", country=country, outcome="accept_counter", burden=burden(country, talks["counter"]))
    _sign(state, stage, country, talks["counter"], max(0, willingness(state, country) - burden(country, talks["counter"])))
    state["talks"].pop(country)
    return f"Treaty signed on {COUNTRIES[country]['name']}'s terms."


def _contribution(country, share: str) -> list[str]:
    from nebula.data.forces import INVENTORY

    stock = dict(INVENTORY[country])
    count = max(1, int(sum(stock.values()) * int(share) / 100 + 0.5))
    picked = []
    while len(picked) < count:
        kind = max(stock, key=lambda k: stock[k])  # take from the deepest squadron
        stock[kind] -= 1
        picked.append(kind)
    return picked


def _report(state, stage, country, previous, **extra):
    report = {"stage": stage, "country": country, "day": state["day"], "previous_rank": previous,
              "stepped": True, "unlocked": f"Stage {stage + 1}: levels {stage * 10 + 1}–{stage * 10 + 10}",
              **extra}
    state.setdefault("stage_reports", {})[str(stage)] = report
    report["new_rank"] = joint_rank(state)  # counted once the report is on record
    state["unlocked"] = max(state["unlocked"], stage * 10 + 1)
    state["last_report"] = stage


def _sign(state, stage, country, terms, margin):
    previous = joint_rank(state)
    uids = []
    for kind in _contribution(country, terms["aircraft"]):
        plane = add_aircraft(state, kind)
        plane["owner"] = country
        plane["condition"] = 100 if terms["training"] == "shared" else 85
        uids.append(plane["uid"])
    days = None if terms["duration"] == "open" else int(terms["duration"])
    joint(state)[country] = {
        "terms": terms, "status": "active", "signed_day": state["day"], "aircraft": uids,
        "expires": state["day"] + days if days else None,
        "stability": int(clamp(50 + margin * 2, 35, 95)), "log": ["Treaty signed"]}
    fuel, materials = SUPPLIES[terms["supplies"]]
    research = 60 if terms["technology"] == "shared" else 0
    gain(state, "treaty:signing", fuel=fuel, materials=materials, research=research)
    amount = {"none": 0, "limited": 0.4, "full": 0.75}[terms["intelligence"]]
    if amount:
        for subject in ("strength", "weaknesses", "aircraft", "bases"):
            add_intel(state, country, subject, amount, "joint_treaty")
    change_relation(state, country, 10, reason="joint_treaty")
    change_trust(state, country, 5)
    change_reputation(state, 3)
    remember(state, f"Joint air command agreed with {COUNTRIES[country]['name']}, which remains sovereign")
    _report(state, stage, country, previous, signed=True, terms=terms,
            aircraft=[AIRCRAFT[state_plane["type"]]["name"] for state_plane in state["fleet"] if state_plane["uid"] in uids],
            resources={"fuel": fuel, "materials": materials, "research": research})
    track_rank(state)


def postpone(state, stage: int) -> str:
    country = _check_stage(state, stage)
    if str(stage) in state.get("stage_reports", {}):
        raise RuleError("This stage has already been concluded")
    _report(state, stage, country, joint_rank(state), signed=False, terms=None, aircraft=[], resources={})
    remember(state, f"Postponed a joint command treaty with {COUNTRIES[country]['name']}")
    log(state, "joint_treaty", country=country, outcome="postponed", burden=0)
    return "Treaty postponed. You can return to the table later."


def _remove_aircraft(state, country):
    state["fleet"] = [p for p in state["fleet"] if p.get("owner") != country]
    joint(state)[country]["aircraft"] = []


def strain(state, country: str, amount: int, reason: str):
    """Positive amounts damage a treaty; negative amounts repair it."""
    treaty = joint(state).get(country)
    if not treaty or treaty["status"] not in ("active", "restricted"):
        return
    treaty["stability"] = clamp(treaty["stability"] - amount, 0, 100)
    treaty["log"] = (treaty["log"] + [f"Day {state['day']}: {reason} ({-amount:+d})"])[-8:]
    name = COUNTRIES[country]["name"]
    if treaty["stability"] <= 0 and treaty["terms"]["withdrawal"] == "notice":
        treaty["status"] = "withdrawn"
        _remove_aircraft(state, country)
        remember(state, f"{name} withdrew its aircraft from joint command: {reason}")
        log(state, "treaty_status", country=country, status="withdrawn", reason=reason)
        return
    status = "restricted" if treaty["stability"] < 25 else "active"
    if status != treaty["status"]:
        treaty["status"] = status
        remember(state, f"{name} {'restricted' if status == 'restricted' else 'restored'} cooperation: {reason}")
        log(state, "treaty_status", country=country, status=status, reason=reason)


def breaks_rules(state, plane, mission) -> bool:
    owner = plane.get("owner")
    return bool(owner) and joint(state)[owner]["terms"]["rules"] == "defensive" \
        and mission["type"] not in DEFENSIVE_TYPES


def after_sortie(state, plane, mission, success: bool):
    owner = plane.get("owner")
    if not owner:
        return
    if breaks_rules(state, plane, mission):
        strain(state, owner, 30, "their aircraft flew outside the agreed rules")
    elif success:
        strain(state, owner, -3, "a joint sortie succeeded")
    if plane in state["fleet"] and plane["condition"] < 40:
        strain(state, owner, 12, "their aircraft came home badly damaged")


def daily(state):
    for country, treaty in list(joint(state).items()):
        if treaty["status"] not in ("active", "restricted"):
            continue
        if treaty["expires"] and state["day"] >= treaty["expires"]:
            treaty["status"] = "expired"
            _remove_aircraft(state, country)
            remember(state, f"The treaty with {COUNTRIES[country]['name']} expired; its aircraft went home")
            log(state, "treaty_status", country=country, status="expired", reason="duration")
        elif treaty["status"] == "active":
            fuel, materials = DAILY[treaty["terms"]["supplies"]]
            gain(state, "treaty:daily", fuel=fuel, materials=materials,
                 research=4 if treaty["terms"]["technology"] == "shared" else 0)


def active(state, key: str | None = None, value: str | None = None) -> list[str]:
    return [c for c, t in joint(state).items() if t["status"] == "active"
            and (key is None or t["terms"][key] == value)]


def range_relief(state) -> int:
    return max((BASE_RANGE_RELIEF[joint(state)[c]["terms"]["bases"]] for c in active(state)), default=0)
