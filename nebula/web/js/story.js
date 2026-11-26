// Cinematic introduction, command centre, conversations and mission debrief.
import { S, go } from "./app.js";
import { voiceBar, bindVoice } from "./voice.js";
import { esc, cap, flag } from "./ui.js";
import { airChart } from "./stages.js";
import { portrait, commandRoom } from "./art.js";

const G = () => S.game, nation = id => G().countries[id];
const person = id => S.world.characters[id];
const rankOf = id => G().ranking.indexOf(id) + 1;
export const face = (id, size) => portrait(person(id), nation(person(id).country).colors, size);
const home = () => G().home;
const chief = () => S.world.air_chiefs[home()];
const officer = () => home() === "lumeris" ? "lu_officer" : chief();
const speech = (id, text) => `<div class="speech">${face(id, 104)}<div><div class="gold small">${esc(nation(person(id).country).name.toUpperCase())} · ${esc(person(id).role.toUpperCase())}</div><b>${esc(person(id).name)}</b><p class="type" data-text="${esc(text)}">${esc(text)}</p></div></div>`;

export const rankChart = () => `<div class="ranks">${G().ranking.map((c, i) => `<div class="rank ${c === home() ? "mine" : c === G().stages[0].country ? "foe" : ""}" style="animation-delay:${i * .09}s"><b>${i + 1}</b>${flag(nation(c))}<span>${esc(nation(c).name)}</span><span class="small dim">${c === home() ? "your command" : c === G().stages[0].country ? "first opponent" : ""}</span></div>`).join("")}</div>`;

const store = key => localStorage.getItem(`nebula.${key}.${G().id}`);
export const mark = key => localStorage.setItem(`nebula.${key}.${G().id}`, "1");
const TRAINING = () => [
  ["Study Veyra and its ten nations on the world map", !!store("seen.map"), "map"],
  ["Answer a message", Object.keys(G().replies ?? {}).length > 0, "inbox"],
  [`Learn something about ${nation(G().stages[0].country).name}`, Object.values(nation(G().stages[0].country).intel).some(v => v.confidence > 0), "intel"],
  ["Inspect your aircraft, fuel and ammunition", !!store("seen.hangar"), "hangar"],
  ["Complete the first mission", !!G().completed[1], "briefing"],
];

export function hq(el) {
  const steps = TRAINING(), done = steps.filter(s => s[1]).length, next = steps.find(s => !s[1]);
  const unread = G().inbox.filter(m => !m.answer).length;
  el.innerHTML = `${commandRoom(S.world, G().countries, home())}<div class="panel objective"><span class="small dim">NEXT OBJECTIVE</span><b>${esc(G().next_objective)}</b>
  <button class="primary" data-go="${G().incidents.some(i => i.status === "open") || G().wars.length ? "crisis" : G().next_objective.startsWith("Negotiate") ? "joint" : "briefing"}">Go ▸</button></div><div class="grid" style="margin-top:14px">
  <div class="panel"><h3>Your adviser</h3>${speech(officer(), G().advice[0])}${G().advice.slice(1).map(a => `<p class="dim">${esc(a)}</p>`).join("")}</div>
  <div class="panel"><h3>Commander ${esc(G().player)}</h3><p>National military rank <b class="gold">${rankOf(home())} of 10</b><br>Joint air-force rank <b class="gold">${G().joint_rank} of 10</b></p><p>Reputation <b>${G().reputation}</b> · Air command rating <b>${G().air_power}</b> <span class="small dim">(your own airframes, weighted by condition)</span></p>
  <p>${G().philosophy ? esc(S.world.philosophies[G().philosophy].name) : "No philosophy declared"} · ${Object.keys(G().completed).length}/100 levels</p>
  <div class="row"><button class="primary" data-go="briefing">Mission briefing ▸</button><button data-go="inbox">Inbox (${unread})</button>${G().last_debrief ? `<button data-go="debrief">Last debrief</button>` : ""}</div></div>
  ${store("training.off") ? `<div class="panel"><h3>Training</h3><button data-training="">Replay training</button></div>` : `<div class="panel"><h3>Commander training ${done}/${steps.length}</h3>${steps.map(([t, ok, where]) => `<div class="row between"><span class="${ok ? "good" : ""}">${ok ? "✔" : "○"} ${esc(t)}</span>${next && next[0] === t ? `<button class="on" data-go="${where}">Go</button>` : ""}</div>`).join("")}<button data-training="1">Skip training</button></div>`}
  <div class="panel"><h3>National military ranking</h3>${rankChart()}</div>
  <div class="panel"><h3>Joint air-force ranking</h3>${airChart()}<button data-go="joint">Joint Command</button></div>
  <div class="panel"><h3>Historical record</h3>${G().history.slice(-8).reverse().map(h => `<p class="small"><span class="gold">Day ${h.day}</span> ${esc(h.text)}</p>`).join("") || `<p class="dim">Nothing recorded yet.</p>`}</div></div>`;
  return () => el.querySelectorAll("[data-training]").forEach(b => b.onclick = () => {
    const key = `nebula.training.off.${G().id}`;
    b.dataset.training ? localStorage.setItem(key, "1") : localStorage.removeItem(key);
    go("hq");
  });
}

const NETWORKS = ["all", "diplomatic", "military", "intelligence", "personal"];
export function inbox(el) {
  S.ui.network ??= "all";
  const list = G().inbox.filter(m => S.ui.network === "all" || m.network === S.ui.network);
  const open = list.find(m => m.id === S.ui.message) ?? list.find(m => !m.answer) ?? list[0];
  el.innerHTML = `<h2>Communications</h2><div class="row">${NETWORKS.map(n => `<button data-network="${n}" class="${n === S.ui.network ? "on" : ""}">${cap(n)}</button>`).join("")}</div>
  <div class="mail"><div class="panel">${list.map(m => `<button class="envelope ${open?.id === m.id ? "on" : ""}" data-message="${m.id}">${face(m.sender.id, 46)}<span><b>${esc(m.sender.name)}</b><br>${esc(m.subject)}<br><span class="small ${m.answer ? "dim" : "gold"}">${m.answer ? "answered" : esc(m.priority)} · day ${m.day}</span></span></button>`).join("") || `<p class="dim">No messages on this network.</p>`}</div>
  <div class="panel">${open ? `<div class="row">${flag(nation(open.sender.country))}<div><h2 style="margin:0">${esc(open.subject)}</h2><span class="small dim">From ${esc(open.sender.name)} to Commander ${esc(G().player)} · ${esc(open.network)} · ${esc(open.priority)} · day ${open.day}</span></div></div>
  <p class="small dim">${esc(open.sender.personality)}. Publicly wants to: ${esc(open.sender.goal)}.</p>${speech(open.sender.id, open.body)}
  ${open.answer ? `<div class="mine-line"><span class="small gold">YOU</span><p>${esc(open.answer.text)}</p></div>${speech(open.sender.id, open.answer.response)}` : `<h3>Your reply</h3>${open.replies.map(r => `<div class="row"><button data-act="reply" data-subject="${open.id}" data-kind="${r.id}">${esc(r.text)}${Object.keys(r.cost).length ? ` (costs ${Object.entries(r.cost).map(([k, v]) => `${v} ${k}`).join(", ")})` : ""}</button></div>`).join("")}`}` : ""}</div></div>`;
  return () => {
    if (open) S.ui.message = open.id;
    el.querySelectorAll("[data-network]").forEach(b => b.onclick = () => { S.ui.network = b.dataset.network; go("inbox"); });
    el.querySelectorAll("[data-message]").forEach(b => b.onclick = () => { S.ui.message = b.dataset.message; go("inbox"); });
  };
}

export function nations(el) {
  el.innerHTML = `<h2>The Ten Nations</h2><div class="grid">${G().ranking.map(c => { const n = nation(c), id = S.world.leaders[c], p = person(id); return `<div class="panel"><div class="row">${flag(n)}<div><h3 style="margin:0">${esc(n.name)}</h3><span class="small dim">Rank ${rankOf(c)} · ${esc(n.capital)}</span></div></div><div class="speech">${face(id, 88)}<div><b>${esc(p.name)}</b><div class="small gold">${esc(p.role)}</div><div class="small dim">${esc(p.personality)}</div></div></div><p>${esc(n.government)}. ${esc(n.history)}</p><button data-profile="${c}">Open atlas profile</button></div>`; }).join("")}</div>`;
  return () => el.querySelectorAll("[data-profile]").forEach(b => b.onclick = () => { S.ui.country = b.dataset.profile; go("map"); });
}

function opener(m) {
  const c = m.opponent, n = nation(c), head = S.world.leaders[c];
  const air = Object.values(S.world.characters).find(p => p.country === c && p.role === "Air Force Commander");
  const show = r => r.value == null ? `<span class="tag unknown">unknown</span>` : `${esc([].concat(r.value).join(", "))} <span class="tag ${r.level}">${r.level}</span>`;
  return `<div class="panel" style="margin-top:12px"><h3>Stage ${m.stage} opponent dossier</h3><div class="row">${flag(n)}<b>${esc(n.name)} · national rank ${rankOf(c)}</b></div><p>${esc(n.history)}</p>
  <table>${["strength", "aircraft", "bases", "weaknesses"].map(k => `<tr><th>${cap(k)}</th><td>${show(n.intel[k])}</td></tr>`).join("")}</table>
  <div class="grid">${speech(head, `Commander, ${n.name} will judge you by what your aircraft do here.`)}${speech(air.id, "My crews know their own sky. Consider that before you enter it.")}</div></div>`;
}

// Level 1 dossier and the beginner's guide to every option.
export function dossier(m) {
  if (m.ally) return "";  // no opponent dossier on a partner
  if (m.level > 100) return "";  // war sorties have no stage dossier
  if (m.level !== 1 || home() !== "lumeris") return m.level % 10 === 1 && m.opponent ? opener(m) : "";
  const z = nation("zorvania"), known = z.intel;
  const show = r => r.value == null ? `<span class="tag unknown">unknown</span>` : `${esc([].concat(r.value).join(", "))} <span class="tag ${r.level}">${r.level}</span>`;
  return `<div class="panel" style="margin-top:12px"><h3>Opponent dossier</h3><div class="row">${flag(z)}<b>Zorvania · national rank ${rankOf("zorvania")}</b></div>
  <p><b>Why:</b> Zorvanian drones keep crossing toward Calix Reach. Zorvek calls it research. <b>Threatened:</b> the Calix Reach corridor. <b>Their stated aim:</b> secure their south-eastern frontier. <b>Contacts reported for this sortie:</b> ${m.params.n}.</p>
  <table><tr><th>Military strength</th><td>${show(known.strength)}</td></tr><tr><th>Aircraft types</th><td>${show(known.aircraft)}</td></tr><tr><th>Defences and bases</th><td>${show(known.bases)}</td></tr><tr><th>Weaknesses</th><td>${show(known.weaknesses)}</td></tr><tr><th>Fleet numbers</th><td><span class="tag unknown">unknown</span></td></tr>
  <tr><th>Your forces</th><td>${esc(G().fleet.map(p => p.stats.name).join(", "))}</td></tr><tr><th>Your weaknesses</th><td>${esc(nation("lumeris").weaknesses.join(", "))}</td></tr></table>
  <div class="grid">${speech("zv_head", "Commander, a research drone carries no weapons. Please remember that when you decide.")}${speech("zv_def", "Lumeris keeps old sky records. We would all be safer if knowledge were shared.")}${speech("zv_air", "If my escorts are fired on, they will answer. I would prefer they never had to.")}</div></div>`;
}

export function options(m) {
  const rows = [["Reconnaissance", "Learn Zorvania's aircraft and bases first.", "Takes a day. Recon flights cost fuel and annoy them; signals analysis costs credits.", `<button data-go="intel">Open intelligence</button>`],
    ["Diplomacy", "Their Chancellor has written to you. Goodwill can end this without a shot.", m.peaceful?.requirement ?? "Not decisive for this mission.", `<button data-go="inbox">Inbox</button> <button data-go="diplomacy">Diplomacy</button>`],
    ...Object.entries(S.world.tactics).map(([k, [label, cost, good, risk]]) => [label, good, `${risk} Cost: ${Object.entries(cost).map(([r, v]) => `${v} ${r}`).join(", ")}.`, G().tactics.includes(k) ? `<span class="good">Arranged</span>` : `<button data-act="prepare" data-kind="${k}">Arrange</button>`]),
    ["Direct combat / interception", "Fly the sortie yourself, or send a wing at the listed odds.", "Aircraft can be damaged; fuel and ammunition are spent. A defeat costs trust and can be retried.", `<span class="small">Choose an aircraft below</span>`]];
  return `<details class="panel guide" style="margin-top:12px"><summary>WHAT SHOULD I DO?</summary><table><tr><th>Option</th><th>Benefit</th><th>Risk</th><th></th></tr>${rows.map(r => `<tr><td><b>${esc(r[0])}</b></td><td>${esc(r[1])}</td><td class="dim">${esc(r[2])}</td><td>${r[3]}</td></tr>`).join("")}</table></details>`;
}

export function debrief(el) {
  const d = G().last_debrief;
  if (!d) { el.innerHTML = `<p class="dim">No mission has been flown yet.</p>`; return; }
  const na = v => v == null ? `<span class="dim">not tracked in this mode</span>` : v;
  const changes = o => Object.entries(o).map(([k, v]) => `${esc(cap(k))} ${v > 0 ? "+" : ""}${v}`).join(", ") || "no change";
  el.innerHTML = `<div class="panel"><span class="dim">Level ${d.level} · ${esc(d.title)} · resolved: ${esc(d.mode)}</span><h2 class="${d.success ? "good" : "bad"}">${d.success ? "MISSION ACCOMPLISHED" : "MISSION FAILED"}</h2>
  <table><tr><th>Objective</th><td>${d.success ? "✔" : "✘"} ${esc(d.objectives.join("; "))}</td></tr><tr><th>Enemy aircraft destroyed by you</th><td>${na(d.enemy_lost)}</td></tr><tr><th>Friendly wingmen lost</th><td>${na(d.wingman_lost)}</td></tr><tr><th>Hull damage %</th><td>${na(d.damage)}</td></tr><tr><th>Ammunition used</th><td>${na(d.ammo_used)}</td></tr><tr><th>Fuel used by aircraft</th><td>${na(d.fuel_used)}</td></tr>
  <tr><th>National resources (net, including daily income)</th><td>${changes(d.resources)}</td></tr><tr><th>Trust</th><td>${changes(d.trust)}</td></tr><tr><th>Reputation</th><td>${d.reputation > 0 ? "+" : ""}${d.reputation}</td></tr><tr><th>Intelligence gained</th><td>${esc(d.intel.join(", ")) || "none"}</td></tr><tr><th>Unlocked</th><td>${d.unlocked ? "Level " + d.unlocked : "nothing new"}</td></tr></table></div>
  ${voiceBar()}${speech(chief(), d.success ? "Everyone I am responsible for is accounted for. Well commanded." : "We recover, we repair, we go again. Look at what failed before you relaunch.")}
  ${G().incidents.some(i => i.status === "open") ? `<div class="panel alert"><b>A misunderstanding needs your answer.</b> <button class="primary" data-go="crisis">Open Crisis Room</button></div>` : ""}
  ${d.level % 10 === 0 && d.level < 100 && G().stages[d.level / 10 - 1].complete ? `<div class="panel"><h3>Stage ${d.level / 10} complete</h3><p>${esc(nation(G().stages[d.level / 10 - 1].country).name)} keeps its independence. Its leaders are ready to discuss a joint air command.</p><button class="primary" data-go="joint">Open the negotiating table ▸</button></div>` : ""}
  <div class="row"><button class="primary" data-go="hq">Return to command centre</button><button data-go="briefing">Next briefing</button><button data-go="analytics">Analytics</button></div>`;
  S.ui.level = 0;
  const line = el.querySelector(".speech p")?.textContent ?? "";
  return () => bindVoice(el, [{ name: "Narrator", text: d.success ? "Mission accomplished." : "Mission failed." }, { id: chief(), name: person(chief()).name, text: line }]);
}
