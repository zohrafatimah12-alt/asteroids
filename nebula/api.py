"""FastAPI layer: validation and presentation only. Rules live in nebula.core."""

import copy
import json
import os
import subprocess
import sys
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from nebula.analytics.pipeline import metrics
from nebula.core import agreements, commander, conflict, db, diplomacy, endings, hangar, intel, missions, stages, world
from nebula.core.state import HOME, RuleError, home, new_state, relation, stats
from nebula.data.aircraft import ABILITIES, AIRCRAFT, UPGRADES
from nebula.data.characters import AIR_CHIEFS, CHARACTERS, LEADERS, public as public_character
from nebula.data.countries import COUNTRIES
from nebula.data.treaty import DEFAULT, DEFENSIVE_TYPES, TERMS
from nebula.data.geography import map_payload, neighbours

WEB = Path(__file__).parent / "web"
ROOT = WEB.parents[1]

app = FastAPI(title="NEBULA", version="0.1.0")
# Local game: reject other Host headers (blocks DNS-rebinding from web pages).
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])
_lock = threading.Lock()  # one writer at a time: read-modify-write on the state blob
_processes: dict[str, subprocess.Popen] = {}


@app.exception_handler(RuleError)
def rule_error(_: Request, exc: RuleError):
    return JSONResponse({"detail": str(exc)}, status_code=409)


@app.exception_handler(KeyError)
def missing(_: Request, exc: KeyError):
    return JSONResponse({"detail": "Not found"}, status_code=404)


class NewCampaign(BaseModel):
    player: str = Field(min_length=1, max_length=40)
    seed: int | None = None
    nation: str = HOME


class Action(BaseModel):
    type: str
    terms: dict[str, str] = Field(default_factory=dict, max_length=20)
    stage: int = Field(default=0, ge=0, le=9)
    country: str = ""
    kind: str = ""
    subject: str = ""
    uid: int = 0
    level: int = Field(default=0, ge=0, le=110)
    offer: int = Field(default=0, ge=0, le=1000)


class Label(BaseModel):
    label: str = Field(min_length=1, max_length=40)


class SortieRequest(BaseModel):
    level: int = Field(ge=1, le=110)
    uid: int


def country_profile(state, cid: str) -> dict:
    c = dict(COUNTRIES[cid])
    c["borders"] = neighbours(cid)
    stances = {o: relation(state, cid, o) for o in COUNTRIES if o != cid}
    c["allies"] = [o for o, v in stances.items() if v >= 40]
    c["enemies"] = [o for o, v in stances.items() if v <= -35]
    c["neutral"] = [o for o, v in stances.items() if -35 < v < 40]
    c["fleet"] = None
    if cid == home(state):
        c["intel"] = None
    else:
        c["intel"] = intel.report(state, cid)
        # Never leak exact figures the player has not confirmed.
        c["military"] = c["intel"]["strength"]["value"]
        c["weaknesses"] = c["intel"]["weaknesses"]["value"]
        c["relation"] = relation(state, cid)
        c["trust"] = state["trust"][cid]
        c["treaties"] = state["treaties"][cid]
        c["ally"] = agreements.is_ally(state, cid)
        c["outlook"] = {k: diplomacy.outlook(state, cid, k) for k in diplomacy.TREATIES}
    return c


def _ending_story(state):
    if not state["ending"]:
        return None
    title, lines = endings.ENDINGS[state["ending"]]
    mine = COUNTRIES[home(state)]
    return title, [x.replace("Lumeris", mine["name"]).replace("Elowen", mine["capital"]) for x in lines]


def view(campaign_id: int, state: dict) -> dict:
    fleet = [{**p, "stats": stats(p), "grounded": stages.grounded(state, p), "service": hangar.service_cost(p),
              "upgrade_costs": {k: hangar.upgrade_cost(p["upgrades"].get(k, 0)) for k in UPGRADES}}
             for p in state["fleet"]]
    public = {k: v for k, v in state.items() if k not in ("_records", "intel", "seed")}
    return {
        "id": campaign_id, **public, "fleet": fleet,
        "countries": {c: country_profile(state, c) for c in COUNTRIES},
        "tracks": intel.tracks(state), "income": world.daily_income(state),
        "research_tree": [{"id": k, "name": v[0], "description": v[1], "requires": v[3],
                           "cost": hangar.research_cost(state, k)} for k, v in hangar.RESEARCH.items()
                          if k != "airframe" or home(state) == HOME],
        "market": [{**a, "locked": hangar.availability(state, k), "price": hangar.build_cost(k)}
                   for k, a in AIRCRAFT.items()],
        "ending_requirements": endings.requirements(state),
        "ending_story": _ending_story(state),
        "inbox": commander.inbox(state), "advice": commander.advice(state),
        "ranking": commander.national_ranking(), "air_power": commander.air_power(state),
        "history": state.get("history", []), "tactics": state.get("tactics", []),
        "philosophy": state.get("philosophy"),
        "air_ranking": stages.air_ranking(state), "joint": state.get("joint", {}),
        "talks": state.get("talks", {}), "stage_reports": stages.reports(state),
        "joint_strength": stages.air_ratings(state)[home(state)], "signed_stages": stages.signed_stages(state),
        "stages": [{"stage": n, "country": c, "complete": stages.stage_complete(state, n),
                    "done": sum(str(x) in state["completed"] for x in range(n * 10 - 9, n * 10 + 1)),
                    }
                   for n, c in enumerate(stages.opponents(home(state)), 1)],
        "rival": stages.current_rival(state),
        "home": home(state), "start_rank": stages.start_rank(state), "joint_rank": stages.joint_rank(state),
        "next_objective": commander.next_objective(state), **conflict.view(state),
    }


@app.get("/api/world")
def get_world():
    return {"map": map_payload(), "abilities": ABILITIES,
            "upgrades": UPGRADES, "treaties": diplomacy.TREATIES,
            "approaches": diplomacy.APPROACHES, "home": HOME,
            "leaders": LEADERS, "air_chiefs": AIR_CHIEFS,
            "nations": {c: {"id": c, "name": v["name"], "capital": v["capital"], "colors": v["colors"],
                            "emblem": v["emblem"], "strengths": v["strengths"], "weaknesses": v["weaknesses"],
                            "rank": stages.national_order().index(c) + 1} for c, v in COUNTRIES.items()},
            "characters": {k: public_character(k) for k in CHARACTERS}, "leaders": LEADERS,
            "philosophies": commander.PHILOSOPHIES, "tactics": missions.TACTICS,
            "terms": TERMS, "default_terms": DEFAULT, "defensive_types": DEFENSIVE_TYPES}


@app.get("/api/levels")
def get_levels(home: str = HOME):
    if home not in COUNTRIES:
        raise KeyError(home)
    return [missions.definition(n, home) for n in range(1, 101)]


@app.get("/api/campaigns")
def get_campaigns():
    with db.connect() as con:
        return db.list_campaigns(con)


@app.post("/api/campaigns", status_code=201)
def post_campaign(body: NewCampaign):
    state = new_state(body.player.strip() or "Commander", body.seed, body.nation)
    with _lock, db.connect() as con:
        cid = db.create_campaign(con, state)
        return view(cid, state)


@app.get("/api/campaigns/{cid}")
def get_campaign(cid: int):
    with db.connect() as con:
        return view(cid, db.load(con, cid))


@app.get("/api/campaigns/{cid}/levels")
def get_campaign_levels(cid: int):
    with db.connect() as con:
        return missions.campaign_for(db.load(con, cid))


@app.get("/api/campaigns/{cid}/missions/{level}")
def get_mission(cid: int, level: int):
    with db.connect() as con:
        state = db.load(con, cid)
    mission = missions.mission_for(state, level)
    mission["peaceful"] = missions.peaceful_option(state, mission)
    mission["odds"] = {p["uid"]: missions.success_chance(state, mission, p)
                       for p in state["fleet"]} if mission["combat"] else {}
    return mission


ACTIONS = {
    "treaty": lambda s, a: diplomacy.propose(s, a.country, a.kind, a.offer)[1],
    "end_alliance": lambda s, a: diplomacy.end_alliance(s, a.country),
    "aid": lambda s, a: diplomacy.send_aid(s, a.country),
    "pressure": lambda s, a: diplomacy.pressure(s, a.country)[1],
    "dispute": lambda s, a: diplomacy.negotiate_dispute(s, a.subject, a.kind)[1],
    "intel": lambda s, a: intel.operate(s, a.country, a.subject, a.kind),
    "service": lambda s, a: hangar.service(s, a.uid, a.kind),
    "upgrade": lambda s, a: hangar.upgrade(s, a.uid, a.kind),
    "manufacture": lambda s, a: hangar.manufacture(s, a.kind),
    "research": lambda s, a: hangar.do_research(s, a.kind),
    "decide": lambda s, a: missions.decide(s, a.level, a.kind)[1],
    "delegate": lambda s, a: missions.delegate(s, a.level, a.uid),
    "peaceful": lambda s, a: missions.resolve_peacefully(s, a.level),
    "wait": lambda s, a: f"A day passes. {len(world.advance_day(s))} new report(s).",
    "philosophy": lambda s, a: commander.choose_philosophy(s, a.kind),
    "reply": lambda s, a: commander.reply(s, a.subject, a.kind),
    "prepare": lambda s, a: missions.prepare(s, a.kind),
    "joint_propose": lambda s, a: stages.propose(s, a.stage, a.terms),
    "joint_counter": lambda s, a: stages.accept_counter(s, a.stage),
    "joint_postpone": lambda s, a: stages.postpone(s, a.stage),
    "incident": lambda s, a: conflict.respond(s, a.kind),
    "ceasefire": lambda s, a: conflict.ceasefire(s, a.country),
    "ending": lambda s, a: f"Ending reached: {endings.ENDINGS[endings.conclude(s, a.kind)][0]}",
}
DAY_ACTIONS = {"end_alliance", "incident", "ceasefire", "joint_propose", "treaty", "aid", "pressure", "dispute", "intel"}  # each takes a day


@app.post("/api/campaigns/{cid}/actions")
def post_action(cid: int, action: Action):
    if action.type not in ACTIONS:
        raise HTTPException(422, "Unknown action")
    with _lock, db.connect() as con:
        state = db.load(con, cid)
        state["_records"] = []
        if state["ending"]:
            raise RuleError("This campaign has ended")
        before = copy.deepcopy(state)
        message = ACTIONS[action.type](state, action)
        if action.type in ("decide", "delegate", "peaceful"):
            state["last_debrief"] = missions.debrief(before, state, action.level)
        if action.type in DAY_ACTIONS:
            world.advance_day(state)
        commander.deliver(state)
        stages.track_rank(state)
        db.save(con, cid, state)
        return {"message": message, "state": view(cid, state)}


@app.get("/api/campaigns/{cid}/analytics")
def get_analytics(cid: int):
    with db.connect() as con:
        return metrics(con, cid)


@app.get("/api/campaigns/{cid}/snapshots")
def get_snapshots(cid: int):
    with db.connect() as con:
        return db.list_snapshots(con, cid)


@app.post("/api/campaigns/{cid}/snapshots", status_code=201)
def post_snapshot(cid: int, body: Label):
    with _lock, db.connect() as con:
        return {"id": db.snapshot(con, cid, body.label)}


@app.post("/api/snapshots/{sid}/restore")
def post_restore(sid: int):
    with _lock, db.connect() as con:
        new_id = db.restore(con, sid)
        return view(new_id, db.load(con, new_id))


# --- Pygame bridge -----------------------------------------------------------
def sortie_dir() -> Path:
    path = db.db_path().parent / "sorties"
    path.mkdir(parents=True, exist_ok=True)
    return path


def launch_combat(ticket: Path) -> subprocess.Popen:
    # Fixed argv, no shell; the only variable is a path we generated ourselves.
    return subprocess.Popen([sys.executable, "-m", "nebula.combat", "--ticket", str(ticket)],
                            cwd=ROOT, env=os.environ.copy())


@app.post("/api/campaigns/{cid}/sorties", status_code=201)
def post_sortie(cid: int, body: SortieRequest):
    from nebula.combat.ticket import build_ticket

    with _lock, db.connect() as con:
        state = db.load(con, cid)
        mission = missions.mission_for(state, body.level)
        missions.check_level(state, body.level)
        if not mission["combat"]:
            raise RuleError("This is a strategic mission")
        plane = missions.check_aircraft(state, mission, body.uid)
        if any(p.poll() is None for p in _processes.values()):
            raise RuleError("A sortie is already in progress. Finish or close the combat window.")
        sid = uuid.uuid4().hex
        ticket = sortie_dir() / f"{sid}.json"
        ticket.write_text(json.dumps(build_ticket(state, mission, plane)))
        con.execute("INSERT INTO sorties VALUES (?,?,?,?,?,?,datetime('now'))",
                    (sid, cid, body.level, body.uid, "flying", ""))
    _processes[sid] = launch_combat(ticket)
    return {"id": sid, "status": "flying"}


@app.get("/api/sorties/{sid}")
def get_sortie(sid: str):
    """Poll a sortie. A finished result is applied exactly once."""
    with _lock, db.connect() as con:
        row = con.execute("SELECT * FROM sorties WHERE id=?", (sid,)).fetchone()
        if not row:
            raise KeyError(sid)
        if row["status"] != "flying":
            return {"id": sid, "status": row["status"], "message": row["message"]}
        result_file = sortie_dir() / f"{row['id']}.result.json"
        process = _processes.get(sid)
        # Check the process first, so a result written just before exit is not missed.
        exited = process is None or process.poll() is not None
        if result_file.exists():
            result = json.loads(result_file.read_text())
            state = db.load(con, row["campaign_id"])
            state["_records"] = []
            try:
                before = copy.deepcopy(state)
                message = missions.apply_combat(state, row["level"], row["uid"], result)
                state["last_debrief"] = missions.debrief(before, state, row["level"], result)
                status = "complete"
                commander.deliver(state)
                stages.track_rank(state)
                db.save(con, row["campaign_id"], state)
            except RuleError as exc:
                message, status = str(exc), "void"
        elif exited:
            message, status = "The combat window closed without a result. Nothing changed.", "aborted"
        else:
            return {"id": sid, "status": "flying", "message": ""}
        con.execute("UPDATE sorties SET status=?, message=? WHERE id=?", (status, message, sid))
        _processes.pop(sid, None)
        return {"id": sid, "status": status, "message": message}


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
