// Browser port of nebula/combat/sim.py: the same flight model, enemies, weapons,
// abilities and mission objectives. Pure logic, no drawing, so it can be tested.

export const W = 1280, H = 720, TIME_LIMIT = 240, ABILITY_COOLDOWN = 14;
const VISION = { clear: 1, cloud: 0.85, wind: 0.95, storm: 0.65 };
const TAU = Math.PI * 2;

export function rng(seed) { // mulberry32: small, seedable, repeatable per mission
  let a = seed >>> 0;
  const next = () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  return { next, uniform: (lo, hi) => lo + (hi - lo) * next(), int: (lo, hi) => lo + Math.floor(next() * (hi - lo + 1)), choice: a => a[Math.floor(next() * a.length)] };
}

export class V {
  constructor(x = 0, y = 0) { this.x = x; this.y = y; }
  add(o) { return new V(this.x + o.x, this.y + o.y); }
  sub(o) { return new V(this.x - o.x, this.y - o.y); }
  mul(k) { return new V(this.x * k, this.y * k); }
  len() { return Math.hypot(this.x, this.y); }
  dist(o) { return Math.hypot(this.x - o.x, this.y - o.y); }
  rotate(deg) { const r = deg * Math.PI / 180, c = Math.cos(r), s = Math.sin(r); return new V(this.x * c - this.y * s, this.x * s + this.y * c); }
  clone() { return new V(this.x, this.y); }
}
const heading = rot => new V(0, 1).rotate(rot);
export const bearing = (from, to) => { const d = to.sub(from); return Math.atan2(-d.x, d.y) * 180 / Math.PI; };
export const angleDiff = (a, b) => ((b - a + 180) % 360 + 360) % 360 - 180;
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

class Aircraft {
  constructor(x, y, o) {
    Object.assign(this, { position: new V(x, y), velocity: new V(), radius: 16, rotation: 0, throttle: 0.7, gunTimer: 0, stun: 0, boost: 0, trail: [], alive: true, state: "patrol", stateTimer: 0, lane: y, role: "enemy", shape: "delta" }, o);
    this.hp = o.hp; this.maxHp = o.maxHp ?? o.hp;
  }
  steer(amount, dt) { this.rotation += clamp(amount, -1, 1) * this.turn * dt; }
  turnToward(target, dt) { this.steer(angleDiff(this.rotation, bearing(this.position, target)) / Math.max(1, this.turn * dt), dt); }
  fly(dt) {
    let speed = this.speed * (0.35 + 0.65 * this.throttle) * (this.boost > 0 ? 1.8 : 1);
    if (this.stun > 0) speed *= 0.3;
    const wanted = heading(this.rotation).mul(speed), k = Math.min(1, this.grip * dt);
    this.velocity = this.velocity.add(wanted.sub(this.velocity).mul(k));
    this.position = this.position.add(this.velocity.mul(dt));
    this.gunTimer -= dt; this.stun -= dt; this.boost -= dt;
    this.trail.push(this.position.sub(heading(this.rotation).mul(this.radius)));
    if (this.trail.length > 14) this.trail.shift();
  }
}

class Round {
  constructor(position, velocity, side, damage, target = null, life = 1.2) {
    Object.assign(this, { position, velocity, side, damage, target, life, radius: target ? 5 : 3, alive: true });
  }
  update(dt) {
    if (this.target && this.target.hp > 0) {
      const diff = angleDiff(bearing(new V(), this.velocity), bearing(this.position, this.target.position));
      this.velocity = this.velocity.rotate(clamp(diff, -200 * dt, 200 * dt));
    }
    this.life -= dt;
    this.position = this.position.add(this.velocity.mul(dt));
    if (this.position.x < 0 || this.position.x > W || this.position.y < 0 || this.position.y > H || this.life <= 0) this.alive = false;
  }
}

class Fragment {
  static MIN = 18;
  constructor(x, y, radius, velocity, rand) { Object.assign(this, { position: new V(x, y), radius, velocity, rand, alive: true }); }
  update(dt) {
    this.position = this.position.add(this.velocity.mul(dt));
    if (this.position.x < 0 || this.position.x > W) this.velocity.x *= -1;
  }
  split() {
    this.alive = false;
    if (this.radius <= Fragment.MIN) return [];
    const angle = this.rand.uniform(20, 50);
    return [angle, -angle].map(a => new Fragment(this.position.x, this.position.y, this.radius - Fragment.MIN, this.velocity.rotate(a).mul(1.15), this.rand));
  }
}

const collide = (a, b) => a.position.dist(b.position) <= a.radius + b.radius;

export class Sim {
  constructor(ticket) {
    const m = ticket.mission, p = ticket.plane, r = rng(ticket.seed);
    this.rand = r; this.kind = m.type; this.d = m.difficulty; this.params = m.params; this.mission = m;
    this.weather = ticket.weather; this.wind = this.weather === "wind" ? new V(r.choice([-18, 18]), 0) : new V();
    this.vision = VISION[this.weather] ?? 1;
    const hull = 70 + p.armour;
    this.player = new Aircraft(W * 0.18, H * 0.55, { speed: 110 + p.speed * 2, turn: 100 + p.agility * 2.1, grip: 1.6 + p.agility / 28, hp: hull, role: "player", shape: p.silhouette, rotation: -90 });
    this.player.maxHp = hull; this.player.hp = hull * p.condition / 100;
    this.startHp = this.player.hp;
    this.ability = p.ability; this.abilityTimer = 0; this.effectTimer = 0;
    this.ammo = this.startAmmo = p.ammo_now;
    this.missiles = 2 + (["fighter", "interceptor", "bomber"].includes(p.category) ? 1 : 0);
    this.missileTimer = 0; this.fuel = p.fuel_now; this.startFuel = p.fuel_now;
    this.fuelBurn = 0.30 * (1.35 - p.range / 150);
    this.moveSpeed = 90 + p.speed * 2.2;  // pixels per second at full thrust
    this.radar = (260 + p.radar * 6) * this.vision * (ticket.radar_boost || 1);
    this.groundBonus = ["bomber", "heavy"].includes(p.category) ? 1.8 : 1;
    this.enemies = []; this.rounds = []; this.fragments = []; this.particles = []; this.sounds = [];
    this.time = 0; this.spawned = this.kills = this.shots = this.hits = this.escaped = this.destroyed = 0;
    this.spawnTimer = 1; this.outcome = null; this.message = m.objectives[0];
    this.structure = null; this.sites = []; this.wingman = null;
    if (ticket.wingman) this.wingman = new Aircraft(W * 0.12, H * 0.7, { speed: 210, turn: 170, grip: 3, hp: 80, role: "ally", shape: "arrow" });
    this.setup();
  }

  setup() {
    const k = this.kind, r = this.rand, d = this.d;
    if (k === "escort") { this.structure = new Aircraft(40, H * 0.5, { speed: 22, turn: 60, grip: 3, hp: 260 + 20 * d, radius: 30, role: "ally", shape: "heavy", rotation: -90, throttle: 1 }); }
    else if (k === "defence" || k === "airbase") { this.structure = new Aircraft(W / 2, H - 90, { speed: 0, turn: 0, grip: 0, hp: 300 + 20 * d, radius: 46, role: "ally", shape: "base" }); }
    else if (k === "emergency") { this.structure = new Aircraft(W / 2, H + 200, { speed: 0, turn: 0, grip: 0, hp: 100, radius: 1, role: "ally", shape: "ground" }); }
    else if (k === "reconnaissance" || k === "investigation") { for (let i = 0; i < this.params.n; i++) this.sites.push({ pos: new V(r.uniform(280, W - 120), r.uniform(110, H - 110)), progress: 0, done: false }); }
    else if (k === "rescue") { this.sites = [{ pos: new V(W - 170, r.uniform(150, H - 150)), progress: 0, done: false }, { pos: new V(130, H * 0.55), progress: 0, done: false }]; }
    else if (k === "strike") {
      for (let i = 0; i < this.params.n; i++) this.addEnemy(new Aircraft(r.uniform(W * 0.45, W - 80), r.uniform(90, H - 90), { speed: 0, turn: 140, grip: 0, hp: 55 + 9 * d, radius: 22, shape: "ground" }), "ground");
    }
  }
  addEnemy(plane, role) { plane.role = role; plane.state = "patrol"; plane.stateTimer = 0; this.enemies.push(plane); }

  spawnEnemy(role = "hunter") {
    const ace = role === "ace", r = this.rand;
    let x = W + 20, y = r.uniform(70, H - 70);
    if (role === "hunter" && (this.kind === "defence" || this.kind === "airbase")) [x, y] = r.choice([[W + 20, y], [-20, y], [r.uniform(100, W - 100), -20]]);
    const d = this.d;
    const plane = new Aircraft(x, y, { speed: (95 + 11 * d) * (ace ? 1.2 : 1), turn: 75 + 9 * d + (ace ? 35 : 0), grip: 3, hp: (22 + 6 * d) * (ace ? 4 : 1), radius: ace ? 24 : 15, shape: role === "intruder" ? "needle" : ace ? "arrow" : "delta", rotation: 90, lane: y });
    this.addEnemy(plane, role); this.spawned++;
  }

  burst(pos, color, count = 24, power = 190) {
    for (let i = 0; i < count; i++) {
      const vel = new V(1, 0).rotate(this.rand.uniform(0, 360)).mul(this.rand.uniform(20, power));
      this.particles.push({ position: pos.clone(), velocity: vel, life: this.rand.uniform(0.3, 0.9), max: 0, color, size: this.rand.uniform(1.5, 4) });
    }
    for (const q of this.particles.slice(-count)) q.max = q.life;
  }
  detected(target) { return this.player.position.dist(target.position) <= this.radar; }
  fire(plane, side, damage, spread = 0, speed = 520, target = null) {
    const dir = heading(plane.rotation + this.rand.uniform(-spread, spread));
    this.rounds.push(new Round(plane.position.add(dir.mul(plane.radius + 6)), dir.mul(speed), side, damage, target, target ? 2.6 : 1.2));
  }

  playerStep(c, dt) {
    const p = this.player;
    // Direct movement: the arrow keys push the ship in screen directions, and it eases
    // toward that velocity so motion stays smooth while a key is held.
    let mx = clamp(c.move?.x ?? 0, -1, 1), my = clamp(c.move?.y ?? 0, -1, 1);
    if (c.thrust) { const f = heading(p.rotation); mx = clamp(mx + f.x, -1, 1); my = clamp(my + f.y, -1, 1); }  // Shift: push along the nose
    // Analog input keeps its strength (a half-pushed stick moves half speed); digital keys
    // on a diagonal are normalised so they are not faster than straight movement.
    const mag = Math.hypot(mx, my);
    const scale = mag > 1 ? 1 / mag : 1;
    const top = this.moveSpeed * (p.stun > 0 ? 0.3 : 1) * (p.boost > 0 ? 1.8 : 1);
    const target = new V(mx * scale * top, my * scale * top);
    p.velocity = p.velocity.add(target.sub(p.velocity).mul(Math.min(1, 7 * dt)));  // eases; no snap
    // Nose turns toward the movement angle at a limited rate, so it never snaps.
    if (mag > 0.12) {
      const desired = bearing(new V(), new V(mx, my));
      const turn = 540 * dt;  // degrees per second
      p.rotation += clamp(angleDiff(p.rotation, desired), -turn, turn);
    }
    p.position = p.position.add(p.velocity.mul(dt)).add(this.wind.mul(dt));
    p.position = new V(clamp(p.position.x, 20, W - 20), clamp(p.position.y, 20, H - 20));
    p.gunTimer -= dt; p.stun -= dt; p.boost -= dt;
    p.throttle = clamp(p.velocity.len() / top, 0, 1);
    this.fuel = Math.max(0, this.fuel - this.fuelBurn * (0.5 + p.throttle) * dt);
    if (c.fire && p.gunTimer <= 0 && this.ammo > 0 && p.hp > 0) {
      p.gunTimer = 0.14; this.ammo--; this.shots++;
      this.fire(p, "player", 11, 1.5, 640); this.sounds.push("gun");
    }
    this.missileTimer -= dt;
    if (c.missile && this.missiles > 0 && this.missileTimer <= 0) {
      const locks = this.enemies.filter(e => this.detected(e) && Math.abs(angleDiff(p.rotation, bearing(p.position, e.position))) < 60);
      if (locks.length) {
        const target = locks.reduce((a, b) => (p.position.dist(a.position) <= p.position.dist(b.position) ? a : b));
        this.missiles--; this.shots++; this.missileTimer = 0.8;
        this.fire(p, "player", 60 * (target.role === "ground" ? this.groundBonus : 1), 0, 430, target);
        this.sounds.push("missile");
      }
    }
    this.abilityTimer -= dt; this.effectTimer -= dt;
    if (c.ability && this.abilityTimer <= 0) this.useAbility();
  }

  useAbility() {
    const p = this.player, a = this.ability;
    this.abilityTimer = ABILITY_COOLDOWN; this.sounds.push("ability");
    this.burst(p.position, [90, 230, 255], 18, 120);
    if (a === "surge") p.boost = 2.5;
    else if (a === "chaff") this.rounds.forEach(r => { if (r.side === "enemy" && r.position.dist(p.position) < 240) r.alive = false; });
    else if (a === "veil" || a === "deepscan" || a === "ironhull") this.effectTimer = 6;
    else if (a === "pulse") this.enemies.forEach(e => { if (e.position.dist(p.position) < 300) e.stun = 3.5; });
    else if (a === "patch") p.hp = Math.min(p.maxHp, p.hp + p.maxHp * 0.25);
    else if (a === "salvo") for (let off = -24; off <= 24; off += 8) { const dir = heading(p.rotation + off); this.rounds.push(new Round(p.position.add(dir.mul(20)), dir.mul(560), "player", 14, null, 1.2)); this.shots++; }
  }
  active(ability) { return this.ability === ability && this.effectTimer > 0; }

  enemyStep(e, dt) {
    e.stateTimer -= dt;
    if (e.stun > 0) { if (e.role !== "ground") e.fly(dt); else e.stun -= dt; return; }
    let target = this.player, sight = 520 * this.vision * (this.active("veil") ? 0.3 : 1);
    if (this.structure && ["escort", "defence", "airbase"].includes(this.kind) && e.position.dist(this.player.position) > 220) { target = this.structure; sight = 2000; }
    else if (this.wingman && this.wingman.alive && this.rand.next() < 0.001) target = this.wingman;
    const distance = e.position.dist(target.position);
    if (e.role === "intruder" && (e.hp >= e.maxHp || distance > 300)) e.state = "run";
    else if (e.state === "evade" && e.stateTimer > 0) { /* keep evading */ }
    else if (distance < 75 && e.role !== "ground") { e.state = "evade"; e.stateTimer = 1.1; e.breakSide = this.rand.choice([-1, 1]); }
    else if (distance < sight) e.state = "attack";
    else e.state = "patrol";

    if (e.state === "run") e.turnToward(new V(e.position.x - 200, e.lane), dt);
    else if (e.state === "evade") e.steer(e.breakSide, dt);
    else if (e.state === "attack") { const lead = target.velocity.mul(distance / 520 * Math.min(1, this.d / 8)); e.turnToward(target.position.add(lead), dt); }
    else e.turnToward(new V(W / 2, H / 2).add(new V(240, 0).rotate(this.time * 25 + e.maxHp * 7)), dt);
    if (e.role !== "ground") e.fly(dt); else e.gunTimer -= dt;
    const aim = Math.abs(angleDiff(e.rotation, bearing(e.position, target.position)));
    if ((e.state === "attack" || e.state === "run") && distance < 380 && aim < 14 && e.gunTimer <= 0) {
      e.gunTimer = Math.max(0.55, 1.7 - 0.13 * this.d) * (e.role === "ace" ? 0.55 : 1);
      this.fire(e, "enemy", 3.5 + 0.8 * this.d, Math.max(2, 10 - this.d), 360);
    }
    if (e.role === "intruder" && e.position.x < -25) { e.alive = false; this.escaped++; }
  }

  wingmanStep(dt) {
    const w = this.wingman;
    if (!w || !w.alive) return;
    const foes = this.enemies;
    const goal = foes.length ? foes.reduce((a, b) => (w.position.dist(a.position) <= w.position.dist(b.position) ? a : b)).position : this.player.position.add(new V(-70, 60));
    w.turnToward(goal, dt); w.fly(dt);
    if (foes.length && w.gunTimer <= 0 && w.position.dist(goal) < 340 && Math.abs(angleDiff(w.rotation, bearing(w.position, goal))) < 12) { w.gunTimer = 0.8; this.fire(w, "ally", 7); }
  }

  damagePlayer(amount) {
    if (this.active("ironhull")) amount *= 0.35;
    this.player.hp -= amount; this.sounds.push("hit");
    this.burst(this.player.position, [255, 170, 80], 6, 110);
  }
  destroy(enemy, byPlayer) {
    enemy.hp = 0; enemy.alive = false; this.destroyed++; if (byPlayer) this.kills++;
    this.sounds.push("boom"); this.burst(enemy.position, [255, 130, 60], 34, 240);
  }

  collisions() {
    const escort = ["escort", "defence", "airbase"].includes(this.kind);
    for (const r of this.rounds) {
      if (!r.alive) continue;
      if (r.side === "enemy") {
        const victims = [this.player];
        if (this.structure && escort) victims.push(this.structure);
        if (this.wingman && this.wingman.alive) victims.push(this.wingman);
        for (const v of victims) if (collide(r, v)) { r.alive = false; if (v === this.player) this.damagePlayer(r.damage); else v.hp -= r.damage; break; }
        continue;
      }
      const enemy = this.enemies.find(e => e.alive && collide(r, e));
      if (enemy) {
        r.alive = false; enemy.hp -= r.damage; if (r.side === "player") this.hits++;
        this.burst(r.position, [255, 220, 120], 5, 90);
        if (enemy.hp <= 0) this.destroy(enemy, r.side === "player");
        continue;
      }
      const frag = this.fragments.find(f => f.alive && collide(r, f));
      if (frag) {
        r.alive = false; if (r.side === "player") this.hits++;
        this.burst(frag.position, [190, 160, 255], 14, 130);
        this.fragments.push(...frag.split()); this.destroyed++; this.sounds.push("boom");
      }
    }
    for (const f of this.fragments) {
      if (!f.alive) continue;
      if (collide(f, this.player)) { this.damagePlayer(14); f.alive = false; }
      else if (f.position.y > H + f.radius) { if (this.structure) this.structure.hp -= f.radius / 3; f.alive = false; }
    }
    for (const e of this.enemies) if (e.alive && collide(e, this.player) && e.role !== "ground") { this.damagePlayer(18); this.destroy(e, true); }
    if (this.wingman && this.wingman.hp <= 0 && this.wingman.alive) { this.wingman.alive = false; this.burst(this.wingman.position, [120, 200, 255]); }
  }

  spawnWave(dt, role, limit, total = null, interval = 3) {
    this.spawnTimer -= dt;
    if (this.spawnTimer <= 0 && this.enemies.length < limit && (total === null || this.spawned < total)) { this.spawnTimer = interval; this.spawnEnemy(role); }
  }
  scan(site, dt, hold) {
    if (this.player.position.dist(site.pos) < 70) site.progress += dt * (this.active("deepscan") ? 2.5 : 1) / hold;
    else site.progress = Math.max(0, site.progress - dt * 0.15);
    if (site.progress >= 1) { site.progress = 1; site.done = true; this.sounds.push("ability"); }
  }

  objectiveStep(dt) {
    const k = this.kind, n = this.params.n, limit = 2 + Math.floor(this.d / 3), s = this.structure;
    if (k === "interception") {
      this.spawnWave(dt, "intruder", limit, n);
      this.message = `Intercept: ${this.destroyed} down, ${this.escaped}/${this.params.m} slipped past`;
      if (this.escaped >= this.params.m) this.outcome = false;
      else if (this.spawned >= n && !this.enemies.length) this.outcome = true;
    } else if (k === "battle") {
      if (this.spawned < n - 1) this.spawnWave(dt, "hunter", limit, n - 1, 2.5);
      else if (this.spawned < n && this.enemies.length < 2) { this.spawnEnemy("ace"); this.message = "The enemy ace has arrived"; }
      if (this.spawned < n) this.message = `Hostiles defeated: ${this.destroyed}/${n}`;
      else if (!this.enemies.length) this.outcome = true;
    } else if (k === "strike") {
      this.spawnWave(dt, "hunter", Math.max(1, limit - 2), null, 9);
      const left = this.enemies.filter(e => e.role === "ground").length;
      this.message = `Emplacements remaining: ${left}`;
      if (!left) this.outcome = true;
    } else if (k === "defence" || k === "airbase" || k === "escort") {
      this.spawnWave(dt, "hunter", Math.max(2, limit - 1), null, 4.5);
      if (s.hp <= 0) { this.outcome = false; this.burst(s.position, [255, 120, 60], 90, 320); }
      else if (k === "escort") { s.fly(dt); this.message = `Transport hull ${Math.max(0, s.hp).toFixed(0)} | crossing ${Math.round(s.position.x / W * 100)}%`; if (s.position.x > W - 40) this.outcome = true; }
      else { const left = this.params.s - this.time; this.message = `Hold ${Math.max(0, left).toFixed(0)}s | installation ${Math.max(0, s.hp).toFixed(0)}`; if (left <= 0) this.outcome = true; }
    } else if (k === "reconnaissance" || k === "investigation") {
      const pending = this.sites.filter(x => !x.done);
      for (const x of pending) this.scan(x, dt, 3);
      const ambush = k === "investigation" && pending.length < this.sites.length;
      this.spawnWave(dt, "hunter", ambush ? limit - 1 : Math.max(1, limit - 2), null, ambush ? 6 : 11);
      this.message = `Sites scanned: ${this.sites.length - pending.length}/${this.sites.length}`;
      if (this.sites.every(x => x.done)) this.outcome = true;
    } else if (k === "rescue") {
      const [beacon, home] = this.sites;
      this.spawnWave(dt, "hunter", Math.max(1, limit - 1), null, 6);
      if (!beacon.done) { this.scan(beacon, dt, 4); this.message = "Reach the beacon and hold for pickup"; }
      else { this.scan(home, dt, 1); this.message = "Survivors aboard. Return to the extraction point"; this.outcome = home.done ? true : null; }
    } else if (k === "emergency") {
      this.spawnTimer -= dt;
      if (this.spawnTimer <= 0) {
        this.spawnTimer = Math.max(1.1, 2.8 - 0.18 * this.d);
        const r = this.rand;
        this.fragments.push(new Fragment(r.uniform(80, W - 80), -40, Fragment.MIN * r.int(1, 3), new V(r.uniform(-35, 35), r.uniform(35, 55 + 6 * this.d)), r));
      }
      const goal = n * 2;
      this.message = `Fragments broken: ${this.destroyed}/${goal} | ground integrity ${Math.max(0, s.hp).toFixed(0)}%`;
      if (s.hp <= 0) this.outcome = false; else if (this.destroyed >= goal) this.outcome = true;
    }
  }

  step(controls, dt) {
    if (this.outcome !== null) return this.effects(dt);
    this.time += dt;
    this.playerStep(controls, dt);
    for (const e of [...this.enemies]) this.enemyStep(e, dt);
    this.wingmanStep(dt);
    for (const r of this.rounds) r.update(dt);
    for (const f of this.fragments) f.update(dt);
    this.collisions();
    this.objectiveStep(dt);
    this.effects(dt);
    this.enemies = this.enemies.filter(e => e.alive);
    this.rounds = this.rounds.filter(r => r.alive);
    this.fragments = this.fragments.filter(f => f.alive);
    const outOfOptions = this.ammo <= 0 && this.missiles <= 0 && ["strike", "battle", "emergency"].includes(this.kind);
    if (this.player.hp <= 0) { this.outcome = false; this.message = "Aircraft lost. The crew ejected safely."; this.burst(this.player.position, [255, 90, 60], 80, 300); }
    else if (this.time >= TIME_LIMIT || (outOfOptions && !this.rounds.length)) this.outcome = false;
  }
  effects(dt) {
    for (const q of this.particles) { q.life -= dt; q.position = q.position.add(q.velocity.mul(dt)); q.velocity = q.velocity.mul(Math.max(0, 1 - 1.8 * dt)); }
    this.particles = this.particles.filter(q => q.life > 0).slice(-600);
  }
  result() {
    const lost = (this.startHp - Math.max(0, this.player.hp)) / this.player.maxHp * 100;
    return { success: this.outcome === true, kills: this.kills, shots: this.shots, hits: Math.min(this.hits, this.shots),
      damage_taken: Math.max(0, Math.round(lost * 0.8)), duration: Math.round(this.time * 10) / 10,
      fuel_used: Math.round(this.startFuel - this.fuel), ammo_used: this.startAmmo - this.ammo,
      wingman_lost: this.wingman ? (this.wingman.alive ? 0 : 1) : 0 };
  }
}

// Simple pilot used by the tests: flies to objectives and fires at what is in front.
// Bot that moves in four directions toward its goal, fires at what is ahead, and uses
// its ability when hurt. Used by the tests to play every mission type to its end.
export function autopilot(sim) {
  const p = sim.player, pending = sim.sites.filter(s => !s.done);
  const foes = [...sim.enemies, ...sim.fragments];
  const goal = pending.length ? pending[0].pos
    : sim.kind === "escort" && sim.structure ? new V(W - 60, sim.structure.position.y)
    : sim.structure && sim.structure.shape !== "ground" && sim.kind !== "emergency" ? sim.structure.position.add(new V(-120, 0))
    : foes.length ? foes.reduce((a, b) => (p.position.dist(a.position) <= p.position.dist(b.position) ? a : b)).position
    : new V(W / 2, H / 2);
  const d = goal.sub(p.position), n = d.len() || 1;
  const near = n < 30;
  const move = { x: near ? 0 : d.x / n, y: near ? 0 : d.y / n };
  const nearby = foes.some(e => p.position.dist(e.position) < 450 && Math.abs(angleDiff(p.rotation, bearing(p.position, e.position))) < 25);
  return { move, fire: nearby, missile: nearby && sim.rand.next() < 0.03, ability: p.hp < p.maxHp * 0.7 };
}
export const NO_INPUT = { move: { x: 0, y: 0 }, fire: false, missile: false, ability: false };
