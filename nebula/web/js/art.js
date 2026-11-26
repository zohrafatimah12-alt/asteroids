// Original vector art: portraits, the star, the planet, the command centre.
import { esc } from "./ui.js";

const seeded = text => { let h = 2166136261; for (const ch of text) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return n => { h = Math.imul(h ^ (h >>> 13), 1274126177); return (h >>> 0) % n; }; };

export function portrait(person, colors, size = 96) {
  const pick = seeded(person.id);
  const skin = ["#f1c9a5", "#d9a47c", "#b57d57", "#8a5a3b", "#62402c", "#e6b891"][pick(6)];
  const hair = ["#17131a", "#3a2418", "#7a4a24", "#b9b4c4", "#5d2f2a", "#d8b36a"][pick(6)];
  const style = [
    "M30 48Q28 18 50 18T70 48Q64 30 50 31T30 48Z",
    "M27 66Q22 16 50 16T73 66L66 66Q70 34 50 29Q32 33 35 66Z",
    "M31 42Q33 20 56 21Q73 25 69 46Q62 31 31 42Z",
    "M32 40Q36 24 50 24T68 40Q50 31 32 40Z",
    "M30 46Q24 22 44 20Q46 10 58 18Q76 22 70 46Q60 28 30 46Z"][pick(5)];
  const id = "p" + person.id;
  return `<svg class="portrait" width="${size}" height="${size}" viewBox="0 0 100 100" role="img" aria-label="Portrait of ${esc(person.name)}">
  <defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${colors[0]}" stop-opacity=".75"/><stop offset="1" stop-color="#060a1c"/></linearGradient></defs>
  <rect width="100" height="100" fill="url(#${id})"/><path d="M0 24H100M0 76H100" stroke="#fff" stroke-opacity=".07"/>
  <path d="M10 100Q14 74 38 70L50 78L62 70Q86 74 90 100Z" fill="${colors[1]}" stroke="${colors[2]}" stroke-width="1.2"/>
  <path d="M43 60h14v14l-7 6-7-6Z" fill="${skin}"/><ellipse cx="50" cy="45" rx="${17 + pick(4)}" ry="${22 + pick(3)}" fill="${skin}"/>
  <path d="M50 23Q70 24 68 48Q66 64 50 68Z" fill="#000" opacity=".16"/><path d="${style}" fill="${hair}"/>
  <path d="M39 ${42 + pick(2)}l7-1M54 41l7 1" stroke="${hair}" stroke-width="2"/><circle cx="43" cy="47" r="1.7" fill="#14101a"/><circle cx="57" cy="47" r="1.7" fill="#14101a"/>
  <path d="M50 48l-2 8h4M44 ${60 + pick(2)}q6 ${pick(4) - 1} 12 0" fill="none" stroke="#3b1f1c" stroke-width="1.2"/>
  ${pick(4) === 0 ? '<path d="M37 47h12v-4H37ZM51 47h12v-4H51ZM49 45h2" fill="none" stroke="#dfe8ff"/>' : ""}
  <path d="M22 88h12M22 92h12" stroke="${colors[2]}" stroke-width="2"/></svg>`;
}

export const star = () => `<div class="space"><div class="corona"></div><div class="sun"></div></div>`;

export function planet(world, countries, highlight) {
  const land = Object.entries(world.map.shapes).map(([id, polys]) => polys.map(p =>
    `<path d="M${p.map(q => q.join(" ")).join("L")}Z" fill="${countries[id].colors[0]}" opacity="${!highlight || id === highlight ? .92 : .22}" stroke="#dfeaff" stroke-width="${id === highlight ? 7 : 2}"/>`).join("")).join("");
  return `<svg class="planet" viewBox="0 0 600 600" role="img" aria-label="The planet Veyra">
  <defs><clipPath id="globe"><circle cx="300" cy="300" r="250"/></clipPath>
  <radialGradient id="shade" cx=".34" cy=".3" r=".78"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000209" stop-opacity=".92"/></radialGradient>
  <radialGradient id="air"><stop offset=".8" stop-color="#52dcf0" stop-opacity="0"/><stop offset=".84" stop-color="#52dcf0" stop-opacity=".55"/><stop offset="1" stop-color="#6a5cff" stop-opacity="0"/></radialGradient></defs>
  <circle cx="300" cy="300" r="298" fill="url(#air)"/>
  <g clip-path="url(#globe)"><rect width="600" height="600" fill="#0a2c55"/><g transform="translate(14 112) scale(.355 .43)">${land}</g>
  <g class="cloudband" fill="#fff" opacity=".13"><ellipse cx="190" cy="170" rx="150" ry="16"/><ellipse cx="430" cy="280" rx="170" ry="12"/><ellipse cx="240" cy="430" rx="190" ry="18"/></g></g>
  <circle cx="300" cy="300" r="250" fill="url(#shade)"/></svg>`;
}

export function commandRoom(world, countries, home = "lumeris") {
  const pick = seeded("elowen");
  const city = Array.from({ length: 44 }, (_, i) => { const h = 30 + pick(105), x = 20 + i * 26; return `<path d="M${x} 205v-${h}l9-8 9 8v${h}Z" fill="#0c1740"/>${Array.from({ length: 4 }, () => `<rect x="${x + 3 + pick(11)}" y="${205 - pick(h)}" width="2" height="3" fill="${pick(4) ? "#52dcf0" : "#f0c870"}" opacity=".8"/>`).join("")}`; }).join("");
  const holo = Object.entries(world.map.shapes).map(([id, polys]) => polys.map(p => `<path d="M${p.map(q => q.join(" ")).join("L")}Z" fill="${countries[id].colors[0]}" fill-opacity="${id === home ? .8 : .16}" stroke="#52dcf0" stroke-width="3"/>`).join("")).join("");
  return `<svg class="room" viewBox="0 0 1160 380" role="img" aria-label="Command centre">
  <defs><linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#070b26"/><stop offset="1" stop-color="#33296b"/></linearGradient></defs>
  <rect width="1160" height="380" fill="#050814"/><rect x="14" y="12" width="1132" height="194" fill="url(#dusk)"/><circle cx="930" cy="58" r="14" fill="#ffe9bd"/><circle cx="930" cy="58" r="36" fill="#ffe9bd" opacity=".14"/>${city}
  ${[14, 297, 580, 863, 1146].map(x => `<rect x="${x - 5}" y="8" width="10" height="204" fill="#151d3d"/>`).join("")}<path d="M0 212H1160" stroke="#3a4a86" stroke-width="6"/>
  <ellipse cx="580" cy="318" rx="370" ry="55" fill="#0b1535" stroke="#52dcf0" stroke-opacity=".6"/>
  <path d="M290 305L350 232H810L870 305Z" fill="#52dcf0" opacity=".05"/><g class="holo" transform="translate(340 205) scale(.3 .15)">${holo}</g>
  ${[90, 190, 970, 1070].map((x, i) => `<g transform="translate(${x} 262)"><rect x="-40" y="-26" width="80" height="48" rx="3" fill="#0a1c3a" stroke="#52dcf0" stroke-opacity=".5"/><path d="M-30 ${8 - i * 3}l14-12 12 7 15-18 19 14" fill="none" stroke="#9a7dff" stroke-width="2"/><path d="M-14 62q2-34 14-34t14 34Z" fill="#02040c"/><circle cy="22" r="9" fill="#02040c"/></g>`).join("")}</svg>`;
}
