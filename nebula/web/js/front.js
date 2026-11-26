// Home page, nation selection, local log-in/out, settings and the crisis room.
import { S, api, act, go, render, setGame } from "./app.js";
import { esc, cap, flag, toast } from "./ui.js";
import { startIntro } from "./cinema.js";
import { face } from "./story.js";
import { prefs, setPref, voices, voiceAvailable, say, stopSpeech, stopMusic, voiceBar, bindVoice } from "./voice.js";

const $ = (el, q) => el.querySelector(q);
const loggedOut = () => localStorage.getItem("nebula.loggedOut") === "1";
const enter = game => { localStorage.removeItem("nebula.loggedOut"); setGame(game); };
const ICON = {
  trust: '<path d="M6 22l9-9 7 4 7-4 13 10-8 9-5-4-6 6-6-6-4 3Z"/>', alliance: '<circle cx="17" cy="24" r="11"/><circle cx="31" cy="24" r="11"/>',
  conflict: '<path d="M10 10l28 28M38 10L10 38M8 34l6 6M40 34l-6 6"/>', protect: '<path d="M24 6l15 6v11q-2 13-15 19Q11 36 9 23V12Z"/><circle cx="24" cy="23" r="5"/>',
};
const how = () => `<div class="how"><h3>How to play</h3><div class="steps">${[["trust", "Build trust", "Answer messages"], ["alliance", "Make alliances", "Negotiate treaties"], ["conflict", "Handle conflicts", "Talk or fly"], ["protect", "Protect Veyra", "Reach level 100"]].map(([k, t, s], i) => `<div style="animation-delay:${i * .15}s"><svg viewBox="0 0 48 48" width="48" height="48" fill="none" stroke="#52dcf0" stroke-width="2">${ICON[k]}</svg><b>${i + 1}. ${t}</b><span class="small dim">${s}</span></div>`).join("")}</div>
<p class="small dim">Follow the <b class="gold">Next objective</b>. Press HINT if you are stuck.</p></div>`;

export function menu(el) {
  const g = loggedOut() ? null : S.game;
  const save = g ? `<div class="panel savecard"><div class="row">${flag(g.countries[g.home])}<div><b>${esc(g.countries[g.home].name)}</b><div class="small dim">Commander ${esc(g.player)} · day ${g.day}</div></div></div>
    <div class="row between"><span>National rank <b class="gold">${g.ranking.indexOf(g.home) + 1}</b></span><span>Joint air rank <b class="gold">${g.joint_rank}</b></span></div>
    <p><span class="small dim">NEXT OBJECTIVE</span><br>${esc(g.next_objective)}</p><button class="primary" data-go="hq">CONTINUE CAMPAIGN</button></div>` : "";
  el.innerHTML = `<div class="menu"><div class="star"></div><h1>NEBULA</h1>${save}
  <button class="primary big" data-m="start">START CAMPAIGN</button>
  ${loggedOut() ? `<button data-go="login">LOG IN</button>` : ""}${how()}
  <div class="row" style="justify-content:center"><button data-m="intro">▶ REPLAY INTRO</button><button data-go="settings">⚙ SETTINGS</button>${g ? [["map", "WORLD ATLAS"], ["nations", "TEN NATIONS"], ["command", "MILITARY DATABASE"], ["intel", "INTELLIGENCE"], ["analytics", "ANALYTICS"]].map(([k, t]) => `<button data-go="${k}">${t}</button>`).join("") : loggedOut() ? "" : `<button data-go="login">SAVED CAMPAIGNS</button>`}</div></div>`;
  return () => {
    $(el, '[data-m="start"]').onclick = () => startIntro("select");
    $(el, '[data-m="intro"]').onclick = () => startIntro("menu");
  };
}

export function select(el) {
  S.ui.nation ??= "lumeris";
  const list = Object.values(S.world.nations).sort((a, b) => b.rank - a.rank);
  el.innerHTML = `<h2>Choose your nation</h2><div class="nationgrid">${list.map(n => `<button data-nation="${n.id}" class="${n.id === S.ui.nation ? "on" : ""}">${flag(n)}<b>${esc(n.name)}</b><span class="small">Military rank ${n.rank}</span><span class="small dim">${esc(n.strengths[0])}</span>${n.id === "lumeris" ? `<span class="tag confirmed">Best first game · full story</span>` : ""}</button>`).join("")}</div>
  <form class="panel" style="margin-top:14px"><div class="row"><input name="player" maxlength="40" placeholder="Your commander name" required autocomplete="off">
  <label>Style <select name="philosophy">${Object.entries(S.world.philosophies).map(([k, p]) => `<option value="${k}">${esc(p.name)}</option>`).join("")}</select></label>
  <button class="primary">BEGIN AS ${esc(S.world.nations[S.ui.nation].name.toUpperCase())}</button></div>
  ${S.ui.nation === "lumeris" ? "" : `<p class="small dim">Other nations use the same game with shorter mission briefings and fewer messages than Lumeris.</p>`}</form>`;
  return () => {
    el.querySelectorAll("[data-nation]").forEach(b => b.onclick = () => { S.ui.nation = b.dataset.nation; render(false); });
    $(el, "form").onsubmit = async e => {
      e.preventDefault();
      const form = new FormData(e.target);
      try {
        let game = await api("/campaigns", { player: form.get("player"), nation: S.ui.nation });
        game = (await api(`/campaigns/${game.id}/actions`, { type: "philosophy", kind: form.get("philosophy") })).state;
        S.ui = { mode: "political", country: game.home, level: 0 };
        enter(game); go("hq");
      } catch (err) { toast(err.message, true); }
    };
  };
}

export async function login(el, current) {
  const list = await api("/campaigns");
  if (!current()) return;
  el.innerHTML = `<div class="menu"><h2>Log in</h2><p class="small dim">Pick your saved commander. This is a local game: profiles have no password.</p>
  ${list.map(c => `<button data-load="${c.id}">${esc(c.player)} · day ${c.day} · ${c.completed}/100</button>`).join("") || `<p>No saved campaigns yet.</p>`}<button data-go="menu">Back</button></div>`;
  return () => el.querySelectorAll("[data-load]").forEach(b => b.onclick = async () => { enter(await api(`/campaigns/${b.dataset.load}`)); go("menu"); });
}

function logout() {
  stopSpeech(); stopMusic();
  localStorage.removeItem("nebula.campaign");
  localStorage.setItem("nebula.loggedOut", "1");
  S.game = null;
  S.ui = { mode: "political", country: "lumeris", level: 0 };
  toast("Logged out. Your campaign is saved.");
  go("menu");
}

export async function settings(el, current) {
  const saves = S.game ? await api(`/campaigns/${S.game.id}/snapshots`) : [];
  if (!current()) return;
  const p = prefs();
  const check = (key, text) => `<label class="row"><input type="checkbox" data-bool="${key}" ${p[key] ? "checked" : ""}> ${text}</label>`;
  const slider = (key, text, min, max) => `<label class="row between">${text}<input type="range" min="${min}" max="${max}" step="0.05" value="${p[key]}" data-num="${key}"></label>`;
  el.innerHTML = `<h2>Settings</h2><div class="grid"><div class="panel"><h3>Audio and display</h3>${check("muted", "Mute all sound")}${check("narration", "Voice narration and dialogue")}${check("subtitles", "Subtitles")}
  ${slider("voice", "Voice volume", 0, 1)}${slider("music", "Music volume", 0, 1)}${slider("rate", "Speech speed", 0.7, 1.4)}
  <label class="row between">Narrator voice<select data-voice-name><option value="">Default</option>${voices().map(v => `<option ${v.name === p.voiceName ? "selected" : ""}>${esc(v.name)}</option>`).join("")}</select></label>
  <div class="row"><button data-s="test">Test voice</button></div><p class="small dim">${voiceAvailable() ? "Voices come from your browser and computer." : "No speech voice found. Lines are shown as timed subtitles."}</p>
  <label class="row"><input type="checkbox" data-calm ${localStorage.getItem("nebula.calm") === "on" ? "checked" : ""}> Reduce motion</label><button data-go="menu">Home</button></div>
  ${S.game ? `<div class="panel"><h3>Save game</h3><p class="small dim">Progress saves automatically.</p><form class="row"><input name="label" maxlength="40" placeholder="Snapshot name" required><button>Save snapshot</button></form>
  ${saves.map(s => `<div class="row between"><span>${esc(s.label)}</span><button data-restore="${s.id}">Load</button></div>`).join("")}</div>
  <div class="panel"><h3>Session</h3><p>Logged in as <b>${esc(S.game.player)}</b></p><button data-s="logout">LOG OUT</button>
  <div class="confirm" hidden><p>Log out now? Your saved campaign will be kept.</p><div class="row"><button class="primary" data-s="yes">Yes, log out</button><button data-s="no">Stay</button></div></div></div>`
    : `<div class="panel"><h3>Session</h3><p>Not logged in.</p><button data-go="login">LOG IN</button></div>`}</div>`;
  return () => {
    el.querySelectorAll("[data-bool]").forEach(b => b.onchange = () => setPref(b.dataset.bool, b.checked));
    el.querySelectorAll("[data-num]").forEach(b => b.onchange = () => setPref(b.dataset.num, Number(b.value)));
    $(el, "[data-voice-name]").onchange = e => setPref("voiceName", e.target.value);
    $(el, '[data-s="test"]').onclick = () => say([{ name: "Narrator", text: "Command centre online." }], line => toast(line.text));
    $(el, "[data-calm]").onchange = e => { localStorage.setItem("nebula.calm", e.target.checked ? "on" : "off"); document.body.classList.toggle("calm", e.target.checked); };
    if (!S.game) return;
    $(el, '[data-s="logout"]').onclick = () => $(el, ".confirm").hidden = false;
    $(el, '[data-s="no"]').onclick = () => $(el, ".confirm").hidden = true;
    $(el, '[data-s="yes"]').onclick = logout;
    $(el, "form").onsubmit = async e => { e.preventDefault(); await api(`/campaigns/${S.game.id}/snapshots`, { label: new FormData(e.target).get("label") }); render(false); };
    el.querySelectorAll("[data-restore]").forEach(b => b.onclick = async () => { setGame(await api(`/snapshots/${b.dataset.restore}/restore`, {})); toast("Snapshot loaded as a new branch."); go("hq"); });
  };
}

export function crisis(el) {
  const g = S.game, nation = id => g.countries[id];
  const open = g.incidents.find(i => i.status === "open");
  const past = g.incidents.filter(i => i.status !== "open").reverse(), last = past[0];
  const price = c => Object.entries(c).map(([k, v]) => `${v} ${k}`).join(", ") || "free";
  const lines = open ? [{ name: "Narrator", text: open.text }, ...open.reactions.map(r => ({ id: r.speaker, name: S.world.characters[r.speaker].name, text: r.text }))]
    : last ? [{ name: "Narrator", text: last.summary }] : [];
  el.innerHTML = `<h2>Crisis Room</h2>${lines.length ? voiceBar() : ""}
  ${open ? `<div class="panel alert"><div class="row">${flag(nation(open.country))}<div><b>${esc(open.title)}</b><div class="small dim">${esc(nation(open.country).name)} · answer by day ${open.deadline} (today ${g.day})</div></div></div><p>${esc(open.text)}</p>
  <div class="reactions-grid">${open.reactions.map(r => { const p = S.world.characters[r.speaker]; return `<div class="speech">${face(r.speaker, 72)}<div><span class="gold small">${esc(nation(p.country).name)} · ${esc(p.role)}</span><br><b>${esc(p.name)}</b><div>${esc(r.text)}</div></div></div>`; }).join("")}</div>
  ${open.evidence ? `<p class="gold">Evidence (${esc(open.evidence.confidence)}): ${esc(open.evidence.finding)}</p>` : ""}
  <div class="grid">${open.choices.map(c => `<button class="option" data-act="incident" data-kind="${c.id}" ${c.blocked ? "disabled" : ""}><b>${esc(c.label)}</b><span class="small">${esc(price(c.cost))}</span><span class="small dim">${esc(c.blocked ?? c.hint)}</span></button>`).join("")}</div></div>`
    : last ? `<div class="panel"><h3>Latest outcome</h3><p>${esc(nation(last.country).name)}: ${esc(last.summary)}</p></div>` : `<p class="dim">No crisis. Misunderstandings appear as the campaign advances.</p>`}
  ${g.wars.map(w => `<div class="panel alert" style="margin-top:12px"><div class="row">${flag(nation(w.country))}<h3>War with ${esc(nation(w.country).name)}</h3></div><p>Day ${g.day - w.since + 1} · <b class="bad">${w.military} military and ${w.civilian} civilian dead</b> · victories ${w.victories}/2 · defeats ${w.defeats}/3 · supplies drain daily</p>
  <div class="row"><button class="primary" data-fight="${w.level}">War mission ▸</button><button data-act="ceasefire" data-country="${w.country}">Offer ceasefire (up to 100 credits)</button></div></div>`).join("")}
  ${past.length || g.war_record.length ? `<div class="panel" style="margin-top:12px"><h3>Remembered</h3>${g.promises.map(p => `<div class="${p.broken ? "bad" : ""}">Promise to ${esc(nation(p.country).name)}: ${esc(p.text)} ${p.broken ? "(BROKEN)" : g.day > p.until ? "(kept)" : `(until day ${p.until})`}</div>`).join("")}
  ${past.map(i => `<div class="small">Day ${i.day} · ${esc(nation(i.country).name)} · ${esc(i.title)} · you chose ${esc(i.choice)} · <b>${esc(cap(i.outcome))}</b></div>`).join("")}${g.war_record.map(w => `<div class="small">War with ${esc(nation(w.country).name)}: ${esc(w.how)}; ${w.military + w.civilian} dead</div>`).join("")}</div>` : ""}`;
  return () => {
    bindVoice(el, lines);
    el.querySelectorAll("[data-fight]").forEach(b => b.onclick = () => { S.ui.level = Number(b.dataset.fight); go("briefing"); });
  };
}
