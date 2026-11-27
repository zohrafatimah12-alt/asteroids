// One function per screen. Each writes markup and may return a binder for events.
import { S, api, act, go, render, setGame } from "./app.js";
import { esc, cap, flag, craft, meter, bars, line, toast } from "./ui.js";
import { MODES, renderMap, zoom } from "./map.js";
import { jointScreen } from "./stages.js";
import { cue } from "./audio.js";
import { menu, select, login, settings, crisis } from "./front.js";
import { intro } from "./cinema.js";
import { voiceBar, bindVoice } from "./voice.js";
import { hq, inbox, nations, debrief, dossier, options } from "./story.js";

const G = () => S.game, nation = id => G().countries[id];
const foreign = () => Object.keys(G().countries).filter(c => c !== G().home);
const cost = c => Object.entries(c).filter(([, v]) => v).map(([k, v]) => `${v} ${k}`).join(", ") || "free";
const $ = (el, q) => el.querySelector(q);
const names = ids => ids.map(i => nation(i).name).join(", ") || "none";
const picker = (id = "pick") => `<div class="row">${foreign().map(c => `<button data-${id}="${c}" class="${c === S.ui.target ? "on" : ""}">${flag(nation(c))} ${esc(nation(c).name)}</button>`).join("")}</div>`;
function bindPicker(el) {
  el.querySelectorAll("[data-pick]").forEach(b => b.onclick = () => { S.ui.target = b.dataset.pick; render(false); });
}
const actionButton = (label, type, attrs = {}, disabled = false) =>
  `<button data-act="${type}" ${Object.entries(attrs).map(([k, v]) => `data-${k}="${esc(v)}"`).join(" ")} ${disabled ? "disabled" : ""}>${esc(label)}</button>`;

function profile(id) {
  const c = nation(id), home = id === G().home;
  const intel = (key, text) => home ? esc([].concat(c[key] ?? []).join(", ")) : text == null ? `<span class="tag unknown">unknown</span>` : `${esc([].concat(text).join(", "))} <span class="tag ${c.intel[key === "military" ? "strength" : key].level}">${c.intel[key === "military" ? "strength" : key].level}</span>`;
  const bases = S.world.map.airbases.filter(b => b[2] === id).map(b => b[1]);
  return `<div class="row">${flag(c)}<div><h2 style="margin:0">${esc(c.name)}</h2><span class="dim">Capital ${esc(c.capital)} · ${c.population}M people</span></div></div>
  <div class="row">${c.colors.map(x => `<span style="width:30px;height:10px;background:${x}"></span>`).join("")}</div>
  <p>${esc(c.history)}</p><p class="dim">${esc(c.culture)}</p>
  <table><tr><th>Government</th><td>${esc(c.government)}</td></tr><tr><th>Geography</th><td>${esc(c.geography)}</td></tr>
  <tr><th>Cities</th><td>${esc(c.cities.join(", "))}</td></tr><tr><th>Resources</th><td>${esc(c.resources.join(", "))}</td></tr>
  <tr><th>Air force</th><td>${esc(c.airforce)}</td></tr><tr><th>Military</th><td>${intel("military", c.military)}</td></tr>
  <tr><th>Aircraft</th><td>${home ? esc(G().fleet.map(p => p.stats.name).join(", ")) : intel("aircraft", c.intel.aircraft.value)}</td></tr>
  <tr><th>Airbases</th><td>${esc(bases.join(", ") || "none charted")}</td></tr>
  <tr><th>Strengths</th><td>${esc(c.strengths.join(", "))}</td></tr><tr><th>Weaknesses</th><td>${intel("weaknesses", c.weaknesses)}</td></tr>
  <tr><th>Land borders</th><td>${esc(names(c.borders)) === "none" ? "Island nation" : esc(names(c.borders))}</td></tr>
  <tr><th>Allies</th><td class="good">${esc(names(c.allies))}</td></tr><tr><th>Enemies</th><td class="bad">${esc(names(c.enemies))}</td></tr><tr><th>Neutral</th><td class="dim">${esc(names(c.neutral))}</td></tr></table>
  <div style="margin-top:8px">${meter("Economy", c.economy)}${meter("Technology", c.technology)}</div>
  ${home ? "" : `<div class="row"><button data-open="diplomacy">Diplomacy</button><button data-open="intel">Intelligence</button></div>`}`;
}

function map(el) {
  el.innerHTML = `<div class="split"><div><div class="row">${MODES.map(m => `<button data-mode="${m}" class="${m === S.ui.mode ? "on" : ""}">${cap(m)}</button>`).join("")}
  <span style="flex:1"></span><button data-zoom="0.75">＋</button><button data-zoom="1.33">－</button><button data-zoom="9">Reset</button>${actionButton("Advance day ▸", "wait")}</div>
  <div id="mapbox"></div><p class="dim small">Scroll to zoom · drag to pan · click a nation, airbase or marker. Gold pulses are fresh events; red pulses are open disputes.</p>
  <div class="panel"><h3>Latest from Veyra</h3>${G().events.slice(-3).reverse().map(e => `<div>Day ${e.day} · <b>${esc(e.title)}</b> <span class="dim">${esc(e.text)}</span></div>`).join("") || `<span class="dim">The world is quiet.</span>`}
  <div class="row"><span class="gold">Threat awareness</span><span class="meter"><i style="width:${G().threat}%;background:var(--red)"></i></span>${G().threat}%</div></div></div>
  <aside class="panel" id="side"></aside></div>`;
  return () => {
    const side = $(el, "#side");
    const showProfile = () => {
      side.innerHTML = profile(S.ui.country);
      side.querySelectorAll("[data-open]").forEach(b => b.onclick = () => { S.ui.target = S.ui.country; go(b.dataset.open); });
    };
    const draw = () => renderMap($(el, "#mapbox"), S.world, G(), S.ui.mode, S.ui.country, hit => {
      cue("open");
      if (hit.country) { S.ui.country = hit.country; draw(); showProfile(); }
      else if (hit.base) {
        const [, name, owner, , , role] = S.world.map.airbases.find(b => b[0] === hit.base);
        const air = owner === G().home ? G().fleet.map(p => p.stats.name) : nation(owner).intel.aircraft.value;
        side.innerHTML = `<h2>${esc(name)}</h2><p>${esc(nation(owner).name)} · ${esc(role)} base</p><p>Aircraft: ${air ? esc(air.join(", ")) : `<span class="tag unknown">unknown</span>`}</p>`;
      } else if (hit.dispute) { go("diplomacy"); }
      else toast(hit.note);
    });
    el.querySelectorAll("[data-mode]").forEach(b => b.onclick = () => { S.ui.mode = b.dataset.mode; render(false); });
    el.querySelectorAll("[data-zoom]").forEach(b => b.onclick = () => zoom($(el, "#map"), Number(b.dataset.zoom)));
    draw(); showProfile();
  };
}

function diplomacy(el) {
  if (!foreign().includes(S.ui.target)) S.ui.target = foreign().includes("aerovant") ? "aerovant" : foreign()[0];
  const id = S.ui.target, c = nation(id);
  const disputes = S.world.map.disputes.map(([d, name, a, b]) => {
    const status = G().disputes[d];
    return `<tr><td>${esc(name)}</td><td>${esc(nation(a).name)} / ${esc(nation(b).name)}</td><td>${status === "open" ? Object.entries(S.world.approaches).map(([k, v]) => actionButton(`${v[0]} (${v[2]}c)`, "dispute", { subject: d, kind: k }, k === "concede" && ![a, b].includes(G().home))).join(" ") : `<span class="good">Settled: ${esc(S.world.approaches[status][0])}</span>`}</td></tr>`;
  }).join("");
  el.innerHTML = `<h2>Diplomacy Centre</h2>${picker()}<div class="grid"><div class="panel">${flag(c)} <h3>${esc(c.name)}</h3>
  ${meter("Relations", c.relation + 100, 200)}<div class="small dim">${c.relation} on a −100…100 scale</div>${meter("Trust", c.trust)}${meter("Your reputation", G().reputation)}
  <p>In force: ${c.treaties.map(t => `<span class="tag confirmed">${esc(S.world.treaties[t][0])}</span>`).join(" ") || `<span class="dim">nothing</span>`}</p></div>
  <div class="panel"><h3>Negotiate (takes one day)</h3>${id === G().rival ? `<p class="bad">${esc(c.name)} is your current opponent. No treaties until you finish all ten missions of this stage. Messages and aid can still build trust.</p>` : ""}${Object.entries(S.world.treaties).map(([k, [label, , need]]) => {
    const signed = c.treaties.includes(k), rival = id === G().rival, blocked = rival || (need && !c.treaties.includes(need));
    return `<div class="row between"><span>${esc(label)} <span class="small dim">${signed ? "signed" : rival ? "current opponent" : blocked ? "needs " + need + " first" : c.outlook[k]}</span></span><span>${actionButton("Propose", "treaty", { country: id, kind: k }, signed || blocked)} ${actionButton("+100c offer", "treaty", { country: id, kind: k, offer: 100 }, signed || blocked)}</span></div>`;
  }).join("")}<hr style="border-color:var(--line)">${c.ally ? `<details><summary>End alliance…</summary><p class="small">War with ${esc(c.name)} is impossible while you are allies. Ending it takes a day, costs 15 relations, 15 trust and 3 reputation, ends any joint defence agreement and returns its aircraft.</p>${actionButton("Confirm: end alliance", "end_alliance", { country: id })}</details>` : ""}
  <div class="row">${actionButton("Send aid (80c, 20m)", "aid", { country: id })}${actionButton("Apply pressure", "pressure", { country: id })}</div>
  <p class="small dim">Peace unlocks peaceful mission outcomes. Trade raises daily income. Intelligence allows exchanges. Alliances unlock their aircraft, add a wingman and count toward the Great Union.</p></div></div>
  <div class="panel" style="margin-top:14px"><h3>Territorial disputes</h3><table>${disputes}</table></div>`;
  return () => bindPicker(el);
}

function intelScreen(el) {
  if (!foreign().includes(S.ui.target)) S.ui.target = foreign().includes("varkhen") ? "varkhen" : foreign()[0];
  const id = S.ui.target, c = nation(id), pact = c.treaties.includes("intelligence");
  el.innerHTML = `<h2>Intelligence Centre</h2>${picker()}<div class="grid">${Object.entries(c.intel).map(([subject, r]) => `<div class="panel"><h3>${cap(subject)}</h3>
  <span class="tag ${r.level}">${r.level} · ${Math.round(r.confidence * 100)}% confidence</span>
  <p style="min-height:44px">${r.value == null ? `<span class="dim">No reliable information.</span>` : esc([].concat(r.value).join(", "))}${r.level === "rumour" ? ` <span class="small gold">(unverified)</span>` : ""}</p>
  <div class="row">${[["signals", "Analyse signals (45c)"], ["reconnaissance", "Recon flight (60f, 20c)"], ["exchange", "Exchange (10r)"]].map(([k, t]) => actionButton(t, "intel", { country: id, subject, kind: k }, r.confidence >= 1 || (k === "exchange" && !pact))).join("")}</div></div>`).join("")}</div>
  <div class="panel" style="margin-top:14px"><h3>Tracked aircraft movements today</h3>${G().tracks.map(t => { const base = i => S.world.map.airbases.find(b => b[0] === i)[1]; return `<div>${esc(nation(t.country).name)}: ${esc(base(t.from))} → ${esc(base(t.to))} <span class="tag ${t.level}">${t.level}</span></div>`; }).join("") || `<span class="dim">Nothing tracked. Learn about a nation's aircraft or bases first.</span>`}
  <p class="small dim">Recon flights without an intelligence agreement damage relations. Strategic advantage: confirmed information is exact; anything less is an estimate.</p></div>`;
  return () => bindPicker(el);
}

function command(el) {
  const g = G();
  el.innerHTML = `<h2>Air Force Command</h2><div class="panel"><h3>Research</h3><div class="grid">${g.research_tree.map(r => `<div><b>${esc(r.name)}</b><div class="dim small">${esc(r.description)}<br>${esc(cost(r.cost))}</div>${g.research.includes(r.id) ? `<span class="good">Complete</span>` : actionButton("Research", "research", { kind: r.id }, r.requires && !g.research.includes(r.requires))}</div>`).join("")}</div>
  <p class="small dim">Alliances with Aerovant and Drakoria each cut project costs by 15%.</p></div>
  <h2 style="margin-top:18px">Manufacturing</h2>${g.builds.map(b => `<span class="tag">${esc(b.type)} ready day ${b.ready_day}</span>`).join(" ")}
  <div class="grid">${g.market.map(a => `<div class="panel">${craft(a, nation(a.country).colors)}<b>${esc(a.name)}</b> <span class="dim small">${esc(nation(a.country).name)} · ${a.category}</span>
  ${["speed", "agility", "armour", "radar", "range"].map(k => meter(cap(k), a[k])).join("")}<div class="small">Weapons ${a.ammo} · ${esc(S.world.abilities[a.ability])}</div>
  <div class="row">${actionButton(`Build (${cost(a.price)})`, "manufacture", { kind: a.id }, !!a.locked)}</div>${a.locked ? `<div class="small dim">${esc(a.locked)}</div>` : ""}</div>`).join("")}</div>`;
}

function hangar(el) {
  el.innerHTML = `<h2>Aircraft Hangar</h2><p class="dim">Daily income: ${esc(cost(G().income))}</p><div class="grid">${G().fleet.map(p => {
    const s = p.stats, total = {};
    for (const part of Object.values(p.service)) for (const [k, v] of Object.entries(part)) total[k] = (total[k] || 0) + v;
    return `<div class="panel">${craft(s, nation(s.country).colors)}<b>${esc(s.name)}</b> <span class="dim small">#${p.uid}${p.owner ? " · on loan from " + esc(nation(p.owner).name) : ""} · ${s.category} · ${p.sorties} sorties · ${p.kills} kills</span>
    ${meter("Condition", p.condition)}${meter("Fuel", p.fuel)}${meter("Ammo", p.ammo, s.ammo)}${["speed", "agility", "armour", "radar", "range"].map(k => meter(cap(k), s[k])).join("")}
    <div class="small">${esc(S.world.abilities[s.ability])}</div>
    <div class="row">${["refuel", "rearm", "repair"].map(a => actionButton(cap(a), "service", { uid: p.uid, kind: a })).join("")}${actionButton(`Full service (${cost(total)})`, "service", { uid: p.uid, kind: "all" })}</div>
    <h3>Upgrades</h3>${p.owner ? `<span class="small dim">Partner-owned aircraft cannot be modified.</span>` : ""}${(p.owner ? [] : Object.entries(S.world.upgrades)).map(([k, [label, , , max]]) => { const tier = p.upgrades[k] || 0; return `<div class="row between"><span class="small">${esc(label)} ${"◆".repeat(tier)}${"◇".repeat(max - tier)}</span>${actionButton(tier >= max ? "Max" : cost(p.upgrade_costs[k]), "upgrade", { uid: p.uid, kind: k }, tier >= max)}</div>`; }).join("")}</div>`;
  }).join("")}</div>`;
}

async function campaign(el, current) {
  S.levels = await api(`/campaigns/${G().id}/levels`);
  if (!current()) return;
  const g = G(), chapters = [...new Set(S.levels.map(l => l.chapter))];
  el.innerHTML = `<h2>Campaign · ${Object.keys(g.completed).length}/100</h2>${"100" in g.completed && !g.ending ? `<div class="panel"><button class="primary" data-go="ending">The final decision ▸</button></div>` : ""}${chapters.map(n => {
    const levels = S.levels.filter(l => l.chapter === n);
    return `<div class="panel" style="margin-bottom:10px"><h3>Stage ${n} · ${esc(levels[0].chapter_title)} · ${levels[0].ally ? `<span class="good">partner: ${esc(nation(levels[0].ally).name)} · ${esc(levels[0].ally_reason)}</span>` : levels[0].opponent ? "opponent: " + esc(nation(levels[0].opponent).name) : "all nations"}</h3><div class="levels">${levels.map(l => `<button data-level="${l.level}" title="${esc(l.title)} (${l.type_label})" class="${g.completed[l.level] ? "done" : l.level === g.unlocked ? "next" : ""}" ${l.level > g.unlocked || (l.chapter > 1 && !g.stage_reports[l.chapter - 1] && !g.completed[l.level]) ? "disabled" : ""}>${l.level}</button>`).join("")}</div></div>`;
  }).join("")}`;
  return () => el.querySelectorAll("[data-level]").forEach(b => b.onclick = () => { S.ui.level = Number(b.dataset.level); go("briefing"); });
}

const g_rules = p => G().joint[p.owner]?.terms.rules === "defensive";

async function briefing(el, current) {
  const level = S.ui.level || G().unlocked;
  const m = await api(`/campaigns/${G().id}/missions/${level}`);
  if (!current()) return;
  const req = m.requirements, planes = G().fleet;
  el.innerHTML = `<div class="panel"><span class="dim">Chapter ${m.chapter} · Level ${m.level} · ${esc(m.type_label)} · Difficulty ${m.difficulty}</span><h2>${esc(m.title)}</h2>
  <p style="font:19px/1.7 Georgia,serif">${esc(m.story)}</p>
  <table><tr><th>Country</th><td>${esc(nation(m.country).name)} · ${esc(m.location)}</td></tr><tr><th>Objective</th><td>${esc(m.objectives.join("; "))}</td></tr>
  <tr><th>Completion</th><td>${esc(m.completion)}</td></tr><tr><th>Rewards</th><td>${esc(cost(m.rewards))}</td></tr>
  <tr><th>Aircraft</th><td>${m.combat ? `Range ${req.min_range}+, condition ${req.min_condition}+, fuel ${req.fuel}+. Recommended: ${esc(req.recommended.join(", "))}` : "None needed"}</td></tr>
  <tr><th>Diplomacy</th><td>${esc(m.diplomatic_consequence)}</td></tr><tr><th>Intelligence</th><td>${esc(m.intel_consequence)}</td></tr></table></div>
  ${dossier(m)}${m.combat ? options(m) : ""}
  ${m.peaceful ? `<div class="panel" style="margin-top:12px"><h3>A way without fighting</h3><p>${esc(m.peaceful.requirement)}</p>${actionButton("Resolve peacefully", "peaceful", { level }, !m.peaceful.available)}</div>` : ""}
  <div class="grid" style="margin-top:12px">${m.combat ? planes.map(p => `<div class="panel">${craft(p.stats, nation(p.stats.country).colors)}<b>${esc(p.stats.name)}</b>
  ${p.owner ? `<div class="small ${m.requirements.recommended && !S.world.defensive_types.includes(m.type) && g_rules(p) ? "bad" : "dim"}">Owned by ${esc(nation(p.owner).name)}${p.grounded ? " · GROUNDED by treaty restriction" : g_rules(p) && !S.world.defensive_types.includes(m.type) ? " · WARNING: this mission breaks the agreed operational rules" : ""}</div>` : ""}
  <div class="small dim">condition ${p.condition} · fuel ${p.fuel} · ammo ${p.ammo} · range ${p.stats.range}</div>
  <div class="row"><button class="primary" data-fly="${p.uid}">LAUNCH MISSION</button>${actionButton(`Command a wing (${Math.round(m.odds[p.uid] * 100)}% odds)`, "delegate", { level, uid: p.uid })}${actionButton("Service", "service", { uid: p.uid, kind: "all" })}</div></div>`).join("")
    : m.choices.map(c => `<div class="panel"><h3>${esc(c.label)}</h3><p>${esc(c.text)}</p><div class="small dim">Cost: ${esc(cost(c.cost))}</div><div class="row">${actionButton("Choose", "decide", { level, kind: c.id })}</div></div>`).join("")}</div>`;
  el.insertAdjacentHTML("beforeend", `<details class="panel controls-help"><summary>Flight controls (desktop combat window)</summary>
  <p><kbd>↑</kbd><kbd>↓</kbd> throttle · <kbd>←</kbd><kbd>→</kbd> turn · <kbd>W</kbd><kbd>S</kbd> and <kbd>A</kbd><kbd>D</kbd> also work</p>
  <p><kbd>Space</kbd> guns · <kbd>F</kbd> missile · <kbd>Q</kbd> aircraft ability · <kbd>P</kbd> pause · <kbd>Esc</kbd> abort · <kbd>Enter</kbd> take off</p>
  <p class="small dim">Flying happens in a separate window on the computer running NEBULA. Phones and tablets can use <b>Command a wing</b>.</p></details>`);
  return () => el.querySelectorAll("[data-fly]").forEach(b => b.onclick = async () => {
    b.disabled = true;
    try {
      const sortie = await api(`/campaigns/${G().id}/sorties`, { level, uid: Number(b.dataset.fly) });
      S.ui.sortie = sortie.id; go("combat");
    } catch (e) { toast(e.message, true); b.disabled = false; }
  });
}

async function combat(el, current) {
  el.innerHTML = `<div class="cinema"><div class="star"></div><h2>SORTIE IN PROGRESS</h2><p>The combat window has opened on this computer. Fly the mission there.</p>
  <div class="panel small">W/S throttle · A/D turn · SPACE guns · F missile · Q ability · P pause · ESC abort</div><div id="status" class="dim">Awaiting flight report…</div><button data-go="map">Back to command</button></div>`;
  if (!S.ui.sortie) { $(el, "#status").textContent = "No active sortie."; return; }
  const poll = async () => {
    if (!current()) return;
    try {
      const r = await api(`/sorties/${S.ui.sortie}`);
      if (r.status !== "flying") {
        S.ui.sortie = null; setGame(await api(`/campaigns/${G().id}`)); toast(r.message, r.status !== "complete"); go(r.status === "complete" ? "debrief" : "briefing");
        return;
      }
    } catch (e) { toast(e.message, true); }
    setTimeout(poll, 1500);
  };
  poll();
}

function events(el) {
  el.innerHTML = `<h2>World Events</h2><div class="panel"><table><tr><th>Day</th><th>Kind</th><th>Event</th></tr>${G().events.slice().reverse().map(e => `<tr><td>${e.day}</td><td><span class="tag">${esc(e.category)}</span></td><td><b>${esc(e.title)}</b><br><span class="dim">${esc(e.text)}</span></td></tr>`).join("") || `<tr><td colspan="3" class="dim">Nothing yet. Time moves when you act.</td></tr>`}</table></div>`;
}

async function analytics(el, current) {
  const a = await api(`/campaigns/${G().id}/analytics`);
  if (!current()) return;
  const tile = (label, v, unit = "") => `<div class="panel"><div class="dim small">${label}</div><div style="font-size:30px">${v ?? "—"}${v == null ? "" : unit}</div></div>`;
  const panel = (title, body) => `<div class="panel"><h3>${title}</h3>${body}</div>`;
  const trend = {};
  for (const p of a.relationship_trend) (trend[p.country] ??= []).push(p);
  const strength = foreign().map(c => [c, nation(c).military]).filter(([, v]) => v).map(([c, v]) => { const [lo, hi = lo] = v.split("–").map(Number); return [nation(c).name, Math.round((lo + hi) / 2), v.includes("–") ? "estimate " + v : "confirmed"]; });
  strength.push([nation(G().home).name, nation(G().home).military, "home"]);
  el.innerHTML = `<h2>Analytics</h2><p class="dim">Computed with SQL and Pandas from this campaign's recorded play. Dashes mean there is no data yet.</p>
  <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(180px,1fr))">${tile("Mission success rate", a.mission_success_rate, "%")}${tile("Flown sortie success", a.flown_success_rate, "%")}${tile("Diplomacy success", a.diplomacy_success_rate, "%")}${tile("Conflicts avoided", a.conflicts_avoided)}${tile("Credits per success", a.credits_per_success)}${tile("Campaign progress", a.campaign.completed, "/100")}</div>
  <div class="grid" style="margin-top:14px">
  ${panel("Success by mission type", bars(a.by_type.map(r => [cap(r.mission_type), r.rate, `n=${r.attempts}`]), { max: 100, unit: "%" }))}
  ${panel("Aircraft performance", a.aircraft.length ? `<table><tr><th>Airframe</th><th>Sorties</th><th>Win %</th><th>Kills</th><th>Accuracy</th><th>Avg damage</th></tr>${a.aircraft.map(r => `<tr><td>${esc(G().market.find(m => m.id === r.aircraft)?.name)}</td><td>${r.sorties}</td><td>${r.success_rate}</td><td>${r.kills}</td><td>${r.accuracy ?? "—"}</td><td>${r.avg_damage}</td></tr>`).join("")}</table>` : bars([]))}
  ${panel("Country strength (as your intelligence knows it)", bars(strength, { max: 100 }))}
  ${panel("Resources spent by category", bars(a.spending.map(r => [cap(r.category), r.total])))}
  ${panel("Resource flow", a.resources.length ? `<table><tr><th>Resource</th><th>Earned</th><th>Spent</th></tr>${a.resources.map(r => `<tr><td>${r.resource}</td><td>${r.earned}</td><td>${r.spent}</td></tr>`).join("")}</table>` : bars([]))}
  ${panel("Player decision patterns", bars(a.decisions.map(d => [`${cap(d.type)}: ${d.choice}`, d.count])))}
  ${panel("Joint treaty talks", bars(Object.entries(a.joint_outcomes).map(([k, v]) => [cap(k), v])))}
  ${panel("Treaty stability", bars(a.treaties.map(t => [nation(t.country).name, t.stability, `${t.status}, ${t.aircraft} aircraft`]), { max: 100 }))}
  ${panel("Joint air rank changes", a.rank_history.map(r => `<div>Day ${r.day}: rank ${r.previous} → ${r.new} (actual strength ${r.rating})</div>`).join("") || bars([]))}
  ${panel("How missions were resolved", bars(Object.entries(a.by_mode).map(([k, v]) => [cap(k), v])))}</div>
  <div class="panel" style="margin-top:14px"><h3>Your relationships over time (−100 to 100)</h3><div class="grid">${Object.entries(trend).map(([c, pts]) => `<div>${esc(nation(c).name)} <span class="dim">now ${pts.at(-1).value}</span>${line(pts)}</div>`).join("") || bars([])}</div></div>`;
}

function ending(el) {
  const g = G();
  if (g.ending) {
    const [title, lines] = g.ending_story;
    el.innerHTML = `<div class="cinema"><div class="star"></div><h2>${esc(title.toUpperCase())}</h2>${voiceBar()}${lines.map((l, i) => `<p style="animation-delay:${1 + i * 2.6}s">${esc(l)}</p>`).join("")}<p style="animation-delay:${2 + lines.length * 2.6}s"><button data-go="analytics">See what your choices did</button> <button data-go="menu">Main menu</button></p></div>`;
    return () => bindVoice(el, lines.map(text => ({ name: "Narrator", text })));
  }
  const done = "100" in g.completed;
  el.innerHTML = `<div class="cinema"><h2>THE FINAL DECISION</h2><div class="grid" style="width:min(900px,100%);text-align:left">${[["union", "Raise the shield together"], ["evacuation", "Launch the arks"]].map(([k, t]) => `<div class="panel"><h3>${t}</h3>${g.ending_requirements[k].map(([text, ok]) => `<div class="${ok ? "good" : "bad"}">${ok ? "✔" : "✘"} ${esc(text)}</div>`).join("")}<div class="row">${actionButton("Commit", "ending", { kind: k }, !done)}</div></div>`).join("")}</div>
  <div class="dim">A plan whose conditions are unmet falls back to whatever Veyra can still achieve.</div><button data-go="campaign">Not yet</button></div>`;
}

export const SCREENS = { joint: jointScreen, menu, new: select, select, login, crisis, intro, hq, inbox, nations, debrief, map, diplomacy, intel: intelScreen, command, hangar, campaign, briefing, combat, events, analytics, settings, ending };
