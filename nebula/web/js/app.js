// Router, API client and action dispatch. Gameplay rules live on the server.
import { esc, toast } from "./ui.js";
import { cue, starfield } from "./audio.js";
import { SCREENS } from "./screens.js";
import { stopSpeech, stopMusic } from "./voice.js";

export const S = { world: null, levels: null, game: null, ui: { mode: "political", country: "lumeris", level: 0 } };
const NAV = [["menu", "Home"], ["hq", "Command"], ["crisis", "Crisis"], ["inbox", "Inbox"], ["map", "World"], ["nations", "Nations"], ["campaign", "Campaign"], ["joint", "Joint Command"], ["diplomacy", "Diplomacy"], ["intel", "Intelligence"], ["command", "Air Force"], ["hangar", "Hangar"], ["events", "Events"], ["analytics", "Analytics"], ["settings", "⚙ Settings"]];
const OPEN_SCREENS = ["menu", "new", "select", "login", "intro", "settings"];

export async function api(path, body) {
  const base = window.NEBULA_API || "";  // set in config.js when the API is on another host
  let res;
  try {
    res = await fetch(base + "/api" + path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  } catch (err) {
    // Name the request so a failing connection can be traced in the browser's network log.
    throw new Error(`no response from ${base || location.origin}/api${path} (${err.message})`);
  }
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `request failed with status ${res.status} for ${path}`);
  return json;
}
export function setGame(game) {
  S.game = game;
  localStorage.setItem("nebula.campaign", game.id);
}
export async function act(type, extra = {}) {
  try {
    const crises = S.game.incidents.length + S.game.wars.length;
    const { message, state } = await api(`/campaigns/${S.game.id}/actions`, { type, ...extra });
    setGame(state);
    toast(message); cue("good");
    if (type === "ending") location.hash = "ending";
    else if (["decide", "delegate", "peaceful"].includes(type)) go("debrief");
    else if (state.incidents.length + state.wars.length > crises && type !== "incident") go("crisis");
    else await render(false);
    return true;
  } catch (e) { toast(e.message, true); cue("bad"); return false; }
}
export const go = name => { if (location.hash === "#" + name) render(); else location.hash = name; };

let token = 0;
export async function render(animate = true) {
  const mine = ++token;
  let name = location.hash.slice(1) || "menu";
  if (!SCREENS[name] || (!S.game && !OPEN_SCREENS.includes(name))) name = "menu";
  stopSpeech();
  if (name !== "intro") stopMusic();
  const main = document.getElementById("screen");
  const g = S.game;
  document.getElementById("top").innerHTML = !g || ["menu", "new", "select", "login", "ending", "intro"].includes(name) ? "" :
    `<h1 class="brand" data-go="menu">NEBULA</h1><nav>${NAV.filter(([k]) => g.completed[1] || !["command", "events", "analytics"].includes(k)).map(([k, t]) => `<a href="#${k}" class="${k === name ? "on" : ""}">${t}${k === "crisis" && (g.incidents.some(i => i.status === "open") || g.wars.length) ? ' <b class="bad">●</b>' : ""}</a>`).join("")}</nav>
     <div class="res" title="${esc(g.player)}"><span>Day <b>${g.day}</b></span>${Object.entries(g.resources).map(([k, v]) => `<span>${k} <b>${v}</b></span>`).join("")}<span>rep <b>${g.reputation}</b></span><button data-hint>HINT</button></div>`;
  if (["map", "hangar"].includes(name)) localStorage.setItem(`nebula.seen.${name}.${g.id}`, "1");
  if (animate) { main.style.animation = "none"; void main.offsetWidth; main.style.animation = ""; scrollTo(0, 0); }
  try {
    const bind = await SCREENS[name](main, () => mine === token);
    if (mine === token) bind?.();
  } catch (e) { toast(e.message, true); }
}

document.addEventListener("click", e => {
  if (e.target.closest("[data-hint]")) { toast(S.game.advice[0]); return; }
  const el = e.target.closest("[data-go],[data-act]");
  if (!el || el.disabled) return;
  cue("click");
  if (el.dataset.go) go(el.dataset.go);
  else {
    const { act: type, ...rest } = el.dataset;
    for (const key of ["uid", "level", "offer", "stage"]) if (key in rest) rest[key] = Number(rest[key]);
    el.disabled = true;
    act(type, rest).then(ok => { if (!ok) el.disabled = false; });
  }
});
addEventListener("hashchange", () => render());

(async () => {
  document.body.classList.toggle("calm", localStorage.getItem("nebula.calm") === "on");
  starfield(document.getElementById("sky"));
  try {
    [S.world, S.levels] = await Promise.all([api("/world"), api("/levels")]);
    const saved = localStorage.getItem("nebula.campaign");
    if (saved) S.game = await api(`/campaigns/${Number(saved)}`).catch(() => null);
    // First visit on this browser: play the introduction, then go to nation selection.
    if (!S.game && !location.hash && !localStorage.getItem("nebula.introSeen") && !localStorage.getItem("nebula.loggedOut") && !(await api("/campaigns")).length) {
      S.ui.introNext = "select";
      history.replaceState(null, "", "#intro");
    }
    render();
  } catch (e) { toast("Cannot reach the NEBULA server: " + e.message, true); }
})();
