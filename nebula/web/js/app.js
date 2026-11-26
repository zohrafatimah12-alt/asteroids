// Router, API client and action dispatch. Gameplay rules live on the server.
import { esc, toast } from "./ui.js";
import { cue, starfield } from "./audio.js";
import { SCREENS } from "./screens.js";

export const S = { world: null, levels: null, game: null, ui: { mode: "political", country: "lumeris", level: 0 } };
const NAV = [["map", "World"], ["campaign", "Campaign"], ["diplomacy", "Diplomacy"], ["intel", "Intelligence"], ["command", "Air Force"], ["hangar", "Hangar"], ["events", "Events"], ["analytics", "Analytics"], ["settings", "Settings"]];

export async function api(path, body) {
  const res = await fetch("/api" + path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : "Request failed");
  return json;
}
export function setGame(game) {
  S.game = game;
  localStorage.setItem("nebula.campaign", game.id);
}
export async function act(type, extra = {}) {
  try {
    const { message, state } = await api(`/campaigns/${S.game.id}/actions`, { type, ...extra });
    setGame(state);
    toast(message); cue("good");
    if (type === "ending") location.hash = "ending"; else await render(false);
    return true;
  } catch (e) { toast(e.message, true); cue("bad"); return false; }
}
export const go = name => { if (location.hash === "#" + name) render(); else location.hash = name; };

let token = 0;
export async function render(animate = true) {
  const mine = ++token;
  let name = location.hash.slice(1) || "menu";
  if (!SCREENS[name] || (!S.game && !["menu", "new"].includes(name))) name = "menu";
  const main = document.getElementById("screen");
  const g = S.game;
  document.getElementById("top").innerHTML = !g || ["menu", "new", "ending"].includes(name) ? "" :
    `<h1 class="brand" data-go="menu">NEBULA</h1><nav>${NAV.map(([k, t]) => `<a href="#${k}" class="${k === name ? "on" : ""}">${t}</a>`).join("")}</nav>
     <div class="res" title="${esc(g.player)}"><span>Day <b>${g.day}</b></span>${Object.entries(g.resources).map(([k, v]) => `<span>${k} <b>${v}</b></span>`).join("")}<span>rep <b>${g.reputation}</b></span></div>`;
  if (animate) { main.style.animation = "none"; void main.offsetWidth; main.style.animation = ""; scrollTo(0, 0); }
  try {
    const bind = await SCREENS[name](main, () => mine === token);
    if (mine === token) bind?.();
  } catch (e) { toast(e.message, true); }
}

document.addEventListener("click", e => {
  const el = e.target.closest("[data-go],[data-act]");
  if (!el || el.disabled) return;
  cue("click");
  if (el.dataset.go) go(el.dataset.go);
  else {
    const { act: type, ...rest } = el.dataset;
    for (const key of ["uid", "level", "offer"]) if (key in rest) rest[key] = Number(rest[key]);
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
    render();
  } catch (e) { toast("Cannot reach the NEBULA server: " + e.message, true); }
})();
