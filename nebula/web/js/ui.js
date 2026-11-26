// Shared presentation helpers: escaping, flags, aircraft art and charts.
export const esc = v => String(v ?? "").replace(/[&<>"']/g, c => `&#${c.charCodeAt(0)};`);
export const cap = s => s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, " ");

const EMBLEMS = {
  sunburst: '<circle cx="30" cy="20" r="6"/><path d="M30 6v6M30 28v6M16 20h6M38 20h6M20 10l5 5M35 25l5 5M20 30l5-5M35 15l5-5" fill="none" stroke-width="2"/>',
  wing: '<path d="M12 26Q30 4 50 14Q36 16 32 22Q40 20 44 22Q30 34 12 26Z"/>',
  talon: '<path d="M18 8l8 16 4-18 4 18 8-16-5 26H23Z"/>',
  peaks: '<path d="M10 32l13-22 7 11 6-8 14 19Z"/>',
  eye: '<path d="M12 20Q30 4 48 20Q30 36 12 20Z" fill="none" stroke-width="2.5"/><circle cx="30" cy="20" r="5"/>',
  wave: '<path d="M8 18q7-9 14 0t15 0t15 0M8 28q7-9 14 0t15 0t15 0" fill="none" stroke-width="3"/>',
  dune: '<circle cx="40" cy="12" r="5"/><path d="M6 34Q20 12 34 28Q44 20 54 34Z"/>',
  snow: '<path d="M30 6v28M18 13l24 14M42 13L18 27" fill="none" stroke-width="3"/>',
  gear: '<circle cx="30" cy="20" r="9" fill="none" stroke-width="5"/><circle cx="30" cy="20" r="13" fill="none" stroke-width="3" stroke-dasharray="4 5"/>',
  coin: '<circle cx="30" cy="20" r="12" fill="none" stroke-width="3"/><path d="M30 12l5 8-5 8-5-8Z"/>',
};
const LAYOUT = {
  lumeris: c => `<path d="M0 30h60v10H0Z" fill="${c}"/>`, aerovant: c => `<path d="M0 0l22 20L0 40Z" fill="${c}"/>`,
  varkhen: c => `<path d="M0 0h60L0 40Z" fill="${c}"/>`, elyndra: c => `<path d="M0 27h60v13H0Z" fill="${c}"/>`,
  zorvania: c => `<path d="M0 17h60v6H0Z" fill="${c}"/>`, thalmora: c => `<path d="M0 0h12v40H0Z" fill="${c}"/>`,
  kryvos: c => `<path d="M0 24h60v16H0Z" fill="${c}"/>`, frostara: c => `<path d="M12 0h8v40h-8ZM0 16h60v8H0Z" fill="${c}"/>`,
  drakoria: c => `<path d="M0 0h15v40H0ZM45 0h15v40H45Z" fill="${c}"/>`, ostraven: c => `<path d="M0 0h60v9H0ZM0 31h60v9H0Z" fill="${c}"/>`,
};
export function flag(c) {
  const [a, b, e] = c.colors;
  return `<svg class="flag" viewBox="0 0 60 40" role="img" aria-label="Flag of ${esc(c.name)}"><rect width="60" height="40" fill="${a}"/>${LAYOUT[c.id](b)}<g fill="${e}" stroke="${e}" stroke-width="0">${EMBLEMS[c.emblem]}</g></svg>`;
}

const HULLS = {
  delta: "0,-13 9.5,9 2.5,5.5 -2.5,5.5 -9.5,9",
  arrow: "0,-15 2,-3 11,5 2.5,4.5 5,11 -5,11 -2.5,4.5 -11,5 -2,-3",
  needle: "0,-17 2,-1 7.5,9.5 0,6.5 -7.5,9.5 -2,-1",
  glider: "0,-11 2,-2 16,1 15,3.5 1.5,3 4.5,11 -4.5,11 -1.5,3 -15,3.5 -16,1 -2,-2",
  heavy: "0,-12 3.5,-5 14,0 13.5,4 3.5,3 3.5,9 7.5,12 -7.5,12 -3.5,9 -3.5,3 -13.5,4 -14,0 -3.5,-5",
};
export function craft(plane, colors) {
  return `<svg viewBox="-22 -20 44 40" width="100%" height="110" role="img" aria-label="${esc(plane.name)}">
  <circle r="17" fill="none" stroke="#52dcf0" stroke-opacity=".18" stroke-dasharray="1 2"/>
  <polygon points="${HULLS[plane.silhouette]}" fill="${colors[0]}" fill-opacity=".55" stroke="${colors[2]}" stroke-width=".7"/>
  <path d="M0 -8V8" stroke="${colors[1]}" stroke-width="1.6"/></svg>`;
}
export const meter = (label, value, max = 100) =>
  `<div class="stat"><span class="dim">${esc(label)}</span><span class="meter"><i style="width:${Math.min(100, value / max * 100)}%"></i></span><span>${Math.round(value)}</span></div>`;

// Charts: single-hue bars with direct labels, and a small multiple line chart.
export function bars(rows, { max, unit = "" } = {}) {
  if (!rows.length) return `<p class="dim">No recorded data yet.</p>`;
  const top = max ?? Math.max(1, ...rows.map(r => r[1]));
  return rows.map(([name, v, note]) => `<div class="stat" style="grid-template-columns:130px 1fr 90px" title="${esc(name)}: ${v}${unit}"><span class="dim">${esc(name)}</span><span class="meter"><i style="width:${v / top * 100}%;background:var(--cyan)"></i></span><span>${v}${unit} <span class="dim small">${esc(note ?? "")}</span></span></div>`).join("");
}
export function line(points) {
  const days = points.map(p => p.day), lo = Math.min(...days), hi = Math.max(...days, lo + 1);
  const xy = points.map(p => `${((p.day - lo) / (hi - lo) * 196 + 2).toFixed(1)},${(30 - p.value * 0.28).toFixed(1)}`).join(" ");
  const [ex, ey] = xy.split(" ").at(-1).split(",");
  return `<svg viewBox="0 0 200 60" width="100%"><circle cx="${ex}" cy="${ey}" r="2.5" fill="#52dcf0"/><path d="M0 30H200" stroke="#8d9cc4" stroke-opacity=".35"/><polyline points="${xy}" fill="none" stroke="#52dcf0" stroke-width="2"/></svg>`;
}

export function toast(message, error = false) {
  const el = Object.assign(document.createElement("div"), { textContent: message, className: error ? "error" : "" });
  document.getElementById("toast").append(el);
  setTimeout(() => el.remove(), 5000);
}
