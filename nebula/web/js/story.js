// Cinematic introduction, command centre, conversations and mission debrief.
import { S, act, go } from "./app.js";
import { esc, cap, flag } from "./ui.js";
import { airChart } from "./stages.js";
import { portrait, star, planet, commandRoom, ambience } from "./art.js";

const G = () => S.game, nation = id => G().countries[id];
const person = id => S.world.characters[id];
const rankOf = id => G().ranking.indexOf(id) + 1;
export const face = (id, size) => portrait(person(id), nation(person(id).country).colors, size);
const speech = (id, text) => `<div class="speech">${face(id, 104)}<div><div class="gold small">${esc(nation(person(id).country).name.toUpperCase())} · ${esc(person(id).role.toUpperCase())}</div><b>${esc(person(id).name)}</b><p class="type" data-text="${esc(text)}">${esc(text)}</p></div></div>`;

export const rankChart = () => `<div class="ranks">${G().ranking.map((c, i) => `<div class="rank ${c === "lumeris" ? "mine" : i === 8 ? "foe" : ""}" style="animation-delay:${i * .09}s"><b>${i + 1}</b>${flag(nation(c))}<span>${esc(nation(c).name)}</span><span class="small dim">${c === "lumeris" ? "your command" : i === 8 ? "first opponent" : ""}</span></div>`).join("")}</div>`;

const talk = (id, text) => ({ id, text });
const SCENES = [
  () => `${star()}<h2>NEBULA</h2><p class="caption">A star far beyond the Milky Way. For ten thousand years it has been the one certain thing in every sky.</p>`,
  () => `${planet(S.world, G().countries)}<h2>VEYRA</h2><p class="caption">Its one living world. Pale oceans, a single great continent, a chain of isles, and ten nations that do not agree.</p>`,
  ...["lumeris", "aerovant", "varkhen", "elyndra", "zorvania", "thalmora", "kryvos", "frostara", "drakoria", "ostraven"].map((c, i) => () => {
    const n = nation(c), lead = S.world.leaders[c];
    return `<div class="reveal">${planet(S.world, G().countries, c)}<div>${flag(n)}<h2>${esc(n.name.toUpperCase())}</h2><p class="small gold">Nation ${i + 1} of 10 · Capital ${esc(n.capital)}</p><div class="speech">${face(lead, 96)}<div><b>${esc(person(lead).name)}</b><div class="dim">${esc(person(lead).role)}</div></div></div><p>${esc(n.geography)}.</p><p class="dim">Known for ${esc(n.strengths.join(" and "))}. Cities: ${esc(n.cities.join(", "))}.</p></div></div>`;
  }),
  ...[talk("lu_pres", "Something is changing along our south-eastern border. Our intelligence reports are incomplete."),
    talk("lu_air", "Our aircraft are not prepared for a large-scale confrontation. We need more time."),
    talk("lu_intel", "We intercepted a communication suggesting that the ninth-ranked nation is preparing a military operation. One source. I would not stake lives on it yet."),
    talk("ae_head", "We advise restraint. A military confrontation could destabilise the entire region."),
    talk("vk_head", "Lumeris should understand that military weakness has consequences."),
    talk("zv_head", "Our survey flights are lawful research. It would be unfortunate if anyone treated them otherwise.")].map(t => () => speech(t.id, t.text)),
  () => `<div class="letter"><div class="small gold">OFFICE OF THE PRESIDENT · ELOWEN</div><h2>Letter of Appointment</h2><p>To <b>${esc(G().player)}</b>:</p><p>By decision of the Civic Council you are appointed Commander of the Lumeris Skywatch, effective today. You inherit few aircraft, a thin treasury, and our complete need of you.</p><p><i>Isaveth Orrin, President</i></p></div>`,
  "choice",
  () => `<h2>The Balance of Power</h2>${rankChart()}<p class="caption">Order of national military strength. Lumeris is tenth. Zorvania, ninth, is the first opponent.</p>`,
  () => speech("lu_air", "That gap is real, Commander. Two serviceable airframes against a service built on seeing us first. We win by choosing when, and whether, to fight."),
  () => `${commandRoom(S.world, G().countries)}<h2>Your Command Centre</h2><p class="caption">Elowen. The map table is live, your advisers are waiting, and the first briefing is on your desk.</p>`,
];
const CHOICE = SCENES.indexOf("choice");
let scene = 0, timer;

export function startIntro() { scene = 0; go("intro"); }

export function intro(el) {
  const volume = Number(localStorage.getItem("nebula.volume") ?? 0.5), muted = localStorage.getItem("nebula.sound") === "off";
  const choosing = SCENES[scene] === "choice";
  const body = !choosing ? SCENES[scene]() : G().philosophy
    ? `<h2>On Record</h2><p class="caption">You chose ${esc(S.world.philosophies[G().philosophy].name)}.</p><div class="reactions">${Object.entries(S.world.philosophies[G().philosophy].reactions).map(([id, t]) => speech(id, t)).join("")}</div>`
    : `<h2>WHAT KIND OF COMMANDER WILL YOU BE?</h2><p class="dim">This is recorded permanently. It does not change your rank or your first opponent.</p><div class="grid choices">${Object.entries(S.world.philosophies).map(([k, p]) => `<button data-philosophy="${k}"><b>${esc(p.name)}</b><span>${esc(p.text)}</span><span class="small gold">Reputation ${p.reputation >= 0 ? "+" : ""}${p.reputation} · trust ${p.trust >= 0 ? "+" : ""}${p.trust}${Object.entries(p.resources).map(([r, v]) => ` · ${r} +${v}`).join("")}</span></button>`).join("")}</div>`;
  el.innerHTML = `<section class="film"><div class="shot">${body}</div><div class="controls"><button data-step="-1" ${scene ? "" : "disabled"}>◂ Back</button><span class="dim small">${scene + 1} / ${SCENES.length}</span>
  <button class="primary" data-step="1" ${choosing && !G().philosophy ? "disabled" : ""}>${scene === SCENES.length - 1 ? "Enter command ▸" : "Continue ▸"}</button><button data-skip>Skip intro</button><button data-replay>Replay</button>
  <label class="small"><input type="checkbox" data-mute ${muted ? "checked" : ""}> Mute</label><label class="small">Music <input type="range" min="0" max="1" step="0.05" value="${volume}" data-volume></label></div></section>`;
  return () => {
    clearInterval(timer);
    const line = el.querySelector(".type");
    if (line && !document.body.classList.contains("calm") && el.querySelectorAll(".type").length === 1) {
      const full = line.dataset.text; let n = 0;
      line.textContent = "";
      timer = setInterval(() => { line.textContent = full.slice(0, n += 2); if (n >= full.length) clearInterval(timer); }, 28);
      line.onclick = () => { clearInterval(timer); line.textContent = full; };
    }
    const sound = () => ambience(el.querySelector("[data-mute]").checked ? 0 : Number(el.querySelector("[data-volume]").value));
    el.querySelector("[data-mute]").onchange = e => { localStorage.setItem("nebula.sound", e.target.checked ? "off" : "on"); sound(); };
    el.querySelector("[data-volume]").oninput = e => { localStorage.setItem("nebula.volume", e.target.value); sound(); };
    const move = to => {
      clearInterval(timer);
      if (to >= SCENES.length) { ambience(0); go("hq"); return; }
      scene = to; sound(); go("intro");
    };
    el.querySelectorAll("[data-step]").forEach(b => b.onclick = () => move(scene + Number(b.dataset.step)));
    // Skipping still stops at the one decision the campaign needs.
    el.querySelector("[data-skip]").onclick = () => move(G().philosophy ? SCENES.length : CHOICE);
    el.querySelector("[data-replay]").onclick = () => move(0);
    el.querySelectorAll("[data-philosophy]").forEach(b => b.onclick = () => act("philosophy", { kind: b.dataset.philosophy }));
  };
}

const store = key => localStorage.getItem(`nebula.${key}.${G().id}`);
export const mark = key => localStorage.setItem(`nebula.${key}.${G().id}`, "1");
const TRAINING = () => [
  ["Declare your command philosophy", !!G().philosophy, "intro"],
  ["Study Veyra and its ten nations on the world map", !!store("seen.map"), "map"],
  ["Answer a message", Object.keys(G().replies ?? {}).length > 0, "inbox"],
  ["Learn something about Zorvania", Object.values(nation("zorvania").intel).some(v => v.confidence > 0), "intel"],
  ["Inspect your aircraft, fuel and ammunition", !!store("seen.hangar"), "hangar"],
  ["Complete the first mission", !!G().completed[1], "briefing"],
];

export function hq(el) {
  const steps = TRAINING(), done = steps.filter(s => s[1]).length, next = steps.find(s => !s[1]);
  const unread = G().inbox.filter(m => !m.answer).length;
  el.innerHTML = `${commandRoom(S.world, G().countries)}<div class="grid" style="margin-top:14px">
  <div class="panel"><h3>Your adviser</h3>${speech("lu_officer", G().advice[0])}${G().advice.slice(1).map(a => `<p class="dim">${esc(a)}</p>`).join("")}</div>
  <div class="panel"><h3>Commander ${esc(G().player)}</h3><p>National military rank <b class="gold">${rankOf("lumeris")} of 10</b><br>Joint air-force rank <b class="gold">${G().air_ranking.findIndex(r => r.country === "lumeris") + 1} of 10</b></p><p>Reputation <b>${G().reputation}</b> · Air command rating <b>${G().air_power}</b> <span class="small dim">(your own airframes, weighted by condition)</span></p>
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
  if (m.level !== 1) return m.level % 10 === 1 && m.opponent ? opener(m) : "";
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
  ${speech("lu_air", d.success ? "Everyone I am responsible for is accounted for. Well commanded." : "We recover, we repair, we go again. Look at what failed before you relaunch.")}
  ${d.level % 10 === 0 && d.level < 100 && G().stages[d.level / 10 - 1].complete ? `<div class="panel"><h3>Stage ${d.level / 10} complete</h3><p>${esc(nation(G().stages[d.level / 10 - 1].country).name)} keeps its independence. Its leaders are ready to discuss a joint air command.</p><button class="primary" data-go="joint">Open the negotiating table ▸</button></div>` : ""}
  <div class="row"><button class="primary" data-go="hq">Return to command centre</button><button data-go="briefing">Next briefing</button><button data-go="analytics">Analytics</button></div>`;
}
