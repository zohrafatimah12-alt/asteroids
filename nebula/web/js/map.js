// Interactive SVG world map. Geometry comes from the server's shared-vertex mesh.
import { esc, cap } from "./ui.js";

export const MODES = ["political", "diplomatic", "military", "intelligence", "resource", "airbase"];
const RESOURCE_COLORS = { lumeris: "#4c8f7c", aerovant: "#7f9fd0", varkhen: "#8a4a3a", elyndra: "#7667b0", zorvania: "#4c5578", thalmora: "#2f7f98", kryvos: "#a87f3d", frostara: "#8fb4cc", drakoria: "#6a6a70", ostraven: "#58803f" };
const view = { x: 0, y: 0, w: 1600, h: 900 };

const ramp = (t, hue) => `hsl(${hue} 55% ${14 + t * 40}%)`;
export function fillFor(mode, id, game, home) {
  const c = game.countries[id];
  if (mode === "diplomatic") {
    if (id === home) return "#c9a24f";
    const r = c.relation;
    return r >= 0 ? `hsl(165 ${20 + r * .6}% ${26 + r * .14}%)` : `hsl(350 ${20 - r * .6}% ${26 - r * .12}%)`;
  }
  if (mode === "military") {
    if (id === home) return ramp(.2, 12);
    // Unknown strength stays grey: the map never reveals what intelligence has not.
    const value = c.military;
    if (!value) return "#2a3050";
    const [lo, hi = lo] = value.split("–").map(Number);
    return ramp((lo + hi) / 200, 12);
  }
  if (mode === "intelligence") {
    if (id === home) return ramp(1, 190);
    const known = Object.values(c.intel).reduce((s, v) => s + v.confidence, 0) / 4;
    return ramp(known, 190);
  }
  if (mode === "resource") return RESOURCE_COLORS[id];
  if (mode === "airbase") return "#17264a";
  return c.colors[["zorvania", "aerovant", "frostara"].includes(id) ? 1 : 0] + "b0";
}

const GLYPHS = {
  mountain: "M-26 8L-14-12L-4 6L6-16L22 8M14-2L24-10L34 8",
  forest: "M-22 8l7-18 7 18ZM-4 12l7-20 7 20ZM14 6l7-17 7 17Z",
  desert: "M-34 4q14-14 28 0t28 0M-20 14q12-10 24 0t24 0",
  polar: "M0-14V14M-12-7L12 7M12-7L-12 7",
};

export function renderMap(el, data, game, mode, selected, onPick) {
  const m = data.map, home = data.home;
  const pos = Object.fromEntries(m.airbases.map(b => [b[0], b]));
  const path = pts => "M" + pts.map(p => p.join(" ")).join("L");
  const land = Object.entries(m.shapes).map(([id, polys]) =>
    `<path class="land ${id === selected ? "sel" : ""}" data-country="${id}" fill="${fillFor(mode, id, game, home)}" d="${polys.map(p => path(p) + "Z").join("")}"><title>${esc(game.countries[id].name)}</title></path>`).join("");
  const borders = m.borders.flatMap(b => b.lines.map(l => `<path class="border" d="${path(l)}"/>`)).join("");
  const features = m.features.map(([kind, name, x, y]) => `<g transform="translate(${x} ${y})" opacity=".5" pointer-events="none"><path d="${GLYPHS[kind]}" fill="none" stroke="#e8eeff" stroke-width="1.5"/><text y="24" text-anchor="middle">${esc(name)}</text></g>`).join("");
  const oceans = m.oceans.map(([n, x, y]) => `<text class="sea" x="${x}" y="${y}" text-anchor="middle">${esc(n)}</text>`).join("");
  const places = Object.entries(m.capitals).map(([id, [x, y]]) => {
    const c = game.countries[id];
    const cities = m.cities[id].map(([cx, cy], i) => `<circle cx="${cx}" cy="${cy}" r="2.5" fill="#dbe6ff"/><text x="${cx + 5}" y="${cy + 3}">${esc(c.cities[i + 1])}</text>`).join("");
    const label = mode === "resource" ? `<text x="${x}" y="${y + 20}" text-anchor="middle" style="fill:#f0c870">${esc(c.resources.join(" · "))}</text>`
      : mode === "military" ? `<text x="${x}" y="${y + 20}" text-anchor="middle">${esc(id === home ? "Home " + c.military : c.military ? "Strength " + c.military : "Strength unknown")}</text>` : "";
    return `<g pointer-events="none">${mode === "political" ? cities : ""}<path d="M${x} ${y - 7}l2 5h5l-4 3 2 6-5-4-5 4 2-6-4-3h5Z" fill="#f0c870"/><text x="${x + 10}" y="${y + 4}">${esc(c.capital)}</text><text class="name" x="${x}" y="${y - 16}" text-anchor="middle">${esc(c.name.toUpperCase())}</text>${label}</g>`;
  }).join("");
  const routes = ["political", "resource", "diplomatic"].includes(mode) ? m.trade_routes.map(([a, b]) => {
    const [ax, ay] = m.capitals[a], [bx, by] = m.capitals[b];
    return `<path class="route" d="M${ax} ${ay}Q${(ax + bx) / 2} ${(ay + by) / 2 - 55} ${bx} ${by}"/>`;
  }).join("") : "";
  const bases = ["airbase", "military", "intelligence"].includes(mode) ? m.airbases.map(([id, name, owner, x, y, role]) =>
    `<g class="hit" data-base="${id}"><circle cx="${x}" cy="${y}" r="9" fill="#06122a" stroke="${owner === home ? "#f0c870" : "#52dcf0"}" stroke-width="1.5"/><path d="M${x - 5} ${y}h10M${x} ${y - 5}v10" stroke="#e8eeff"/>${mode === "airbase" ? `<text x="${x}" y="${y + 21}" text-anchor="middle">${esc(name)} · ${esc(role)}</text>` : ""}</g>`).join("") : "";
  const disputes = ["political", "diplomatic", "military"].includes(mode) ? m.disputes.map(([id, name, , , x, y]) => {
    const open = game.disputes[id] === "open", color = open ? "#ff6b7a" : "#5fd9a0";
    return `<g class="hit" data-dispute="${id}"><circle class="${open ? "ping" : ""}" cx="${x}" cy="${y}" r="11" stroke="${color}"/><circle cx="${x}" cy="${y}" r="6" fill="${color}" fill-opacity=".6"/><title>${esc(name)}: ${open ? "disputed" : "settled"}</title></g>`;
  }).join("") : "";
  const strategic = ["military", "intelligence", "political"].includes(mode) ? m.strategic.map(([, name, x, y, why]) =>
    `<g class="hit" data-note="${esc(name + ": " + why)}"><path d="M${x} ${y - 8}l8 8-8 8-8-8Z" fill="none" stroke="#9a7dff" stroke-width="2"/><title>${esc(name)}</title></g>`).join("") : "";
  const tracks = ["military", "intelligence", "airbase"].includes(mode) ? game.tracks.map(t => {
    const a = pos[t.from], b = pos[t.to];
    const d = `M${a[3]} ${a[4]}Q${(a[3] + b[3]) / 2} ${(a[4] + b[4]) / 2 - 80} ${b[3]} ${b[4]}`;
    return `<g pointer-events="none" opacity="${.35 + t.confidence * .65}"><path d="${d}" fill="none" stroke="#9a7dff" stroke-dasharray="${t.level === "confirmed" ? "none" : "4 5"}"/><path d="M9 0L-7-6L-3 0L-7 6Z" fill="#fff"><animateMotion dur="14s" repeatCount="indefinite" rotate="auto" path="${d}"/></path><text x="${a[3]}" y="${a[4] - 14}">${esc(cap(t.country))} flight · ${t.level}</text></g>`;
  }).join("") : "";
  const events = game.events.filter(e => e.day >= game.day - 2).map(e => {
    const [x, y] = m.capitals[e.countries[0]];
    return `<g pointer-events="none"><circle class="ping" cx="${x - 30}" cy="${y - 38}" r="12" stroke="#f0c870" stroke-width="2"/><text x="${x - 30}" y="${y - 34}" text-anchor="middle">!</text></g>`;
  }).join("");
  const [ix, iy] = m.capitals[home];
  const sweep = mode === "intelligence" ? `<g transform="translate(${ix} ${iy})"><g class="sweep"><path d="M0 0L330 0A330 330 0 0 1 286 165Z" fill="#52dcf0" opacity=".12"/></g><circle r="330" fill="none" stroke="#52dcf0" stroke-opacity=".25"/><circle r="170" fill="none" stroke="#52dcf0" stroke-opacity=".2"/></g>` : "";
  el.innerHTML = `<svg id="map" viewBox="${view.x} ${view.y} ${view.w} ${view.h}" role="img" aria-label="Map of Veyra">${oceans}${land}${borders}${features}${routes}${sweep}${disputes}${strategic}${places}${bases}${tracks}${events}</svg>`;
  interact(el.firstChild, onPick);
}

function apply(svg) {
  view.w = Math.min(1600, Math.max(320, view.w)); view.h = view.w * 9 / 16;
  view.x = Math.min(1600 - view.w, Math.max(0, view.x)); view.y = Math.min(900 - view.h, Math.max(0, view.y));
  svg.setAttribute("viewBox", `${view.x} ${view.y} ${view.w} ${view.h}`);
}
export function zoom(svg, factor, fx = .5, fy = .5) {
  const w = Math.min(1600, Math.max(320, view.w * factor));
  view.x += (view.w - w) * fx; view.y += (view.w - w) * 9 / 16 * fy; view.w = w;
  apply(svg);
}
function interact(svg, onPick) {
  let drag = null, moved = false;
  svg.addEventListener("wheel", e => {
    e.preventDefault();
    const r = svg.getBoundingClientRect();
    zoom(svg, e.deltaY > 0 ? 1.15 : 0.87, (e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height);
  }, { passive: false });
  svg.addEventListener("pointerdown", e => { drag = [e.clientX, e.clientY]; moved = false; });
  addEventListener("pointerup", () => drag = null);
  svg.addEventListener("pointermove", e => {
    if (!drag) return;
    const dx = e.clientX - drag[0], dy = e.clientY - drag[1];
    if (!moved && Math.hypot(dx, dy) < 4) return;
    moved = true;
    const scale = view.w / svg.clientWidth;
    view.x -= dx * scale; view.y -= dy * scale; drag = [e.clientX, e.clientY];
    apply(svg);
  });
  svg.addEventListener("click", e => {
    if (moved) return;
    const hit = e.target.closest("[data-country],[data-base],[data-dispute],[data-note]");
    if (hit) onPick({ ...hit.dataset });
  });
}
