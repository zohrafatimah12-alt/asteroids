// Browser combat rules: every mission ends, the world freezes at the end, arrows move
// the ship in the matching screen direction, and Space fires.
// Run: node tests/js/flight_test.mjs   (copies the module so Node can load it without a package.json)
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const dir = mkdtempSync(join(tmpdir(), "nebula-flight-"));
const copy = join(dir, "flight.mjs");
writeFileSync(copy, readFileSync(join(here, "../../nebula/web/js/flight.js"), "utf8"));
const { Sim, autopilot, NO_INPUT } = await import(pathToFileURL(copy).href);

const plane = { speed: 60, agility: 60, armour: 50, radar: 60, range: 60, ammo_now: 200, fuel_now: 300,
  condition: 100, silhouette: "delta", category: "fighter", ability: "surge" };
const ticket = (type, d, n) => ({ mission: { type, difficulty: d, params: { n, m: 3, s: 50 }, objectives: ["x"], title: type, level: 1, type_label: "" },
  plane, weather: "clear", wingman: false, radar_boost: 1, seed: 11 });

let failures = 0;
const check = (ok, label) => { console.log(`${ok ? "ok  " : "FAIL"} ${label}`); if (!ok) failures++; };

// One case per mission type; n is the mission's own count, so the objective is reachable.
const cases = { interception: [5, 4], reconnaissance: [3, 2], escort: [4, 1], investigation: [3, 2], airbase: [5, 1],
  rescue: [3, 1], battle: [8, 8], defence: [5, 1], emergency: [4, 2], strike: [4, 4] };
for (const [type, [d, n]] of Object.entries(cases)) {
  const sim = new Sim(ticket(type, d, n));
  let steps = 0;
  while (sim.outcome === null && steps++ < 30 * 260) sim.step(autopilot(sim), 1 / 30);
  check(sim.outcome !== null, `${type}: the mission reaches a result`);
  const t = sim.time, msg = sim.message;
  for (let i = 0; i < 60; i++) sim.step(autopilot(sim), 1 / 30);
  check(sim.time === t && sim.message === msg, `${type}: the world stops after the result`);
}

const dirs = { right: [1, 0], left: [-1, 0], down: [0, 1], up: [0, -1] };
for (const [name, [dx, dy]] of Object.entries(dirs)) {
  const sim = new Sim(ticket("defence", 1, 1));
  const start = sim.player.position.clone();
  for (let i = 0; i < 30; i++) sim.step({ ...NO_INPUT, move: { x: dx, y: dy } }, 1 / 30);
  const ex = sim.player.position.x - start.x, ey = sim.player.position.y - start.y;
  const along = dx ? Math.sign(ex) === dx && Math.abs(ex) > 50 : Math.sign(ey) === dy && Math.abs(ey) > 50;
  const across = dx ? Math.abs(ey) < 5 : Math.abs(ex) < 5;
  check(along && across, `arrow ${name} moves the ship ${name}`);
}

const thrusting = new Sim(ticket("defence", 1, 1));
const t0 = thrusting.player.position.clone();
for (let i = 0; i < 30; i++) thrusting.step({ ...NO_INPUT, thrust: true }, 1 / 30);
const moved = thrusting.player.position.sub(t0);
check(moved.x > 50 && Math.abs(moved.y) < 5, "Shift thrust moves the ship along its nose (facing right at start)");

const shooter = new Sim(ticket("defence", 1, 1));
for (let i = 0; i < 30; i++) shooter.step({ ...NO_INPUT, fire: true }, 1 / 30);
check(shooter.shots > 0, "Space fires");

// 360-degree joystick: the ship moves and faces every direction, and fires along its nose.
const unit = a => ({ x: Math.cos(a * Math.PI / 180), y: Math.sin(a * Math.PI / 180) });
const headingOf = r => ({ x: -Math.sin(r * Math.PI / 180), y: Math.cos(r * Math.PI / 180) });
for (let deg = 0; deg < 360; deg += 30) {
  const sim = new Sim(ticket("defence", 1, 1));
  const dir = unit(deg);
  for (let i = 0; i < 120; i++) sim.step({ ...NO_INPUT, move: { x: dir.x * 0.9, y: dir.y * 0.9 } }, 1 / 30);
  const v = sim.player.velocity, speed = Math.hypot(v.x, v.y);
  const alongMove = (v.x * dir.x + v.y * dir.y) / (speed || 1);
  const h = headingOf(sim.player.rotation);
  const noseDot = h.x * dir.x + h.y * dir.y;
  check(speed > 100 && alongMove > 0.98, `joystick ${deg}deg: ship moves that way`);
  check(noseDot > 0.98, `joystick ${deg}deg: nose faces the movement`);
  // Capture the shell at the moment it leaves the ship; enemies may remove it later in the frame.
  let shot = null;
  const fireNow = sim.fire.bind(sim);
  sim.fire = (plane, ...rest) => { fireNow(plane, ...rest); if (plane.role === "player" && !shot) shot = sim.rounds[sim.rounds.length - 1]; };
  sim.step({ ...NO_INPUT, fire: true }, 1 / 30);
  const sd = shot ? (shot.velocity.x * h.x + shot.velocity.y * h.y) / shot.velocity.len() : 0;
  check(shot && sd > 0.98, `joystick ${deg}deg: shots leave along the nose`);
}
{
  const sim = new Sim(ticket("defence", 1, 1));
  for (let i = 0; i < 60; i++) sim.step({ ...NO_INPUT, move: { x: 0, y: -1 } }, 1 / 30);
  const r0 = sim.player.rotation;
  for (let i = 0; i < 60; i++) sim.step({ ...NO_INPUT, fire: true }, 1 / 30);
  check(Math.abs(sim.player.rotation - r0) < 0.5 && sim.player.velocity.len() < 60, "released stick: ship keeps its heading and slows gently");
  const turnStart = new Sim(ticket("defence", 1, 1));
  turnStart.step({ ...NO_INPUT, move: { x: -1, y: 0 } }, 1 / 30);
  check(Math.abs(turnStart.player.rotation - (-90)) < 60, "turning is limited per frame (no snap)");
}

console.log(failures ? `${failures} check(s) failed` : "all browser flight checks passed");
process.exit(failures ? 1 : 0);
