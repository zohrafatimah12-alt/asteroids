// Browser combat screen: canvas renderer, HUD, keyboard and multi-touch controls.
// Uses the simulation in flight.js; the campaign result is returned via onFinish.
import { Sim, NO_INPUT, W, H, V } from "./flight.js";
import { esc } from "./ui.js";

const HULLS = {
  delta: [[0, 1.3], [.95, -.9], [.25, -.55], [-.25, -.55], [-.95, -.9]],
  arrow: [[0, 1.5], [.22, .3], [1.1, -.5], [.25, -.45], [.5, -1.1], [-.5, -1.1], [-.25, -.45], [-1.1, -.5], [-.22, .3]],
  needle: [[0, 1.7], [.18, .1], [.75, -.95], [0, -.65], [-.75, -.95], [-.18, .1]],
  glider: [[0, 1.1], [.18, .2], [1.6, -.1], [1.5, -.35], [.15, -.3], [.45, -1.1], [-.45, -1.1], [-.15, -.3], [-1.5, -.35], [-1.6, -.1], [-.18, .2]],
  heavy: [[0, 1.25], [.35, .55], [1.4, 0], [1.35, -.4], [.35, -.3], [.35, -.9], [.75, -1.2], [-.75, -1.2], [-.35, -.9], [-.35, -.3], [-1.35, -.4], [-1.4, 0], [-.35, .55]],
};
const COLORS = { player: "#52dcf0", ally: "#f0c870", enemy: "#ff6b7a", ace: "#9a7dff" };
const ABILITY_TEXT = { surge: "SURGE", chaff: "CHAFF", veil: "VEIL", pulse: "PULSE", patch: "PATCH", salvo: "SALVO", deepscan: "DEEP SCAN", ironhull: "IRON HULL" };

const html = (ticket, lines) => `
<div class="flight" role="application" aria-label="Flight combat">
  <canvas width="${W}" height="${H}"></canvas>
  <div class="hud">
    <div class="hud-top"><b class="gold" data-f="title"></b><span data-f="type"></span><span class="dim" data-f="weather"></span></div>
    <div class="hud-msg" data-f="message"></div>
    <div class="hud-pause"><button class="pause-pill" data-f="pause" aria-label="Pause">❚❚</button></div>
    <div class="hud-left">
      <div class="bar"><span>HULL</span><i data-f="hull"></i></div>
      <div class="bar"><span>FUEL</span><i data-f="fuel" class="fuel"></i></div>
      <div class="bar"><span>THRUST</span><i data-f="thrust" class="thrust"></i></div>
    </div>
    <div class="hud-ammo"><span data-f="guns"></span><span data-f="missiles"></span><span data-f="ability"></span></div>
    <button class="hud-btn exit" data-f="exit">Exit (Esc)</button>
  </div>
  <div class="pad left" role="group" aria-label="Movement joystick">
    <div class="stick" data-stick><div class="stick-base"><div class="stick-thumb"></div></div></div>
  </div>
  <div class="pad right" role="group" aria-label="Actions">
    <button data-ctl="missile" class="round small m" aria-label="Missile"><span>MSL</span><small>F</small></button>
    <button data-ctl="ability" class="round small a" aria-label="Ability"><span>ABL</span><small>Q</small></button>
    <button data-ctl="fire" class="round fire" aria-label="Fire"><span>FIRE</span><small>Space</small></button>
  </div>
  <div class="overlay" data-f="overlay">${lines}</div>
  <p class="help">Arrows or joystick move · Shift thrust forward · Space fire · F missile · Q ability · P pause · Esc exit</p><p class="rot">Turn your phone sideways for the best view</p>
</div>`;

export function startFlight(ticket, { story, onFinish }) {
  const host = document.createElement("div");
  host.className = "flight-host";
  host.innerHTML = html(ticket, `<h2>${esc(ticket.mission.title)}</h2><p class="story">${esc(story || ticket.mission.objectives[0])}</p>
    <p class="dim small">${esc(ticket.mission.objectives.join(" · "))}</p><button class="primary big-go" data-f="launch">TAKE OFF (Enter)</button>`);
  document.body.append(host);
  document.body.classList.add("in-flight");
  const q = s => host.querySelector(`[data-f="${s}"]`);
  const canvas = host.querySelector("canvas"), g = canvas.getContext("2d");
  const sim = new Sim(ticket);
  const held = new Map(), keys = new Set(), tapped = { missile: false, ability: false };
  const stick = { x: 0, y: 0, pointer: null };  // analog input in [-1, 1], from the joystick's own finger
  let phase = "brief", paused = false, last = 0, raf = 0, elapsed = 0, finished = false;
  const stars = Array.from({ length: 150 }, (_, i) => ({ x: (i * 997) % W, y: (i * 571) % H, z: 1 + (i % 3), s: 5 + (i % 7) * 4 }));

  // ---- input: keyboard and touch both set the same control flags ----
  const KEYS = { ArrowLeft: "left", a: "left", ArrowRight: "right", d: "right", ArrowUp: "up", w: "up", ArrowDown: "down", s: "down", " ": "fire", Shift: "thrust" };
  const keyDown = e => {
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    if (k === "Escape") { e.preventDefault(); return exit(); }
    if (k === "Enter" && phase === "brief") { e.preventDefault(); return launch(); }
    if (k === "p" && !e.repeat) return togglePause();
    if (KEYS[k] !== undefined || KEYS[e.key] !== undefined) e.preventDefault();
    if (e.repeat) return; // holding a key keeps it on; repeats do not re-fire tap actions
    if (k === "f") tapped.missile = true;
    if (k === "q") tapped.ability = true;
    keys.add(KEYS[k] ?? KEYS[e.key] ?? "");
  };
  const keyUp = e => { const k = e.key.length === 1 ? e.key.toLowerCase() : e.key; keys.delete(KEYS[k] ?? KEYS[e.key] ?? ""); };
  const blur = () => keys.clear();
  addEventListener("keydown", keyDown); addEventListener("keyup", keyUp); addEventListener("blur", blur);

  // Each finger has its own pointer id, so several buttons can be held together.
  const base = host.querySelector(".stick-base"), thumb = host.querySelector(".stick-thumb");
  const setStick = (e) => {
    const r = base.getBoundingClientRect(), R = r.width / 2;
    let dx = e.clientX - (r.left + R), dy = e.clientY - (r.top + R);
    const len = Math.hypot(dx, dy), clampTo = len > R ? R / len : 1;
    dx *= clampTo; dy *= clampTo;  // the thumb stays inside the circle
    thumb.style.transform = `translate(${dx}px, ${dy}px)`;
    const mag = Math.hypot(dx, dy) / R, dead = 0.12;  // small dead zone so a resting thumb does not drift
    const k = mag < dead ? 0 : (mag - dead) / (1 - dead) / (mag || 1);
    stick.x = dx * k / R; stick.y = dy * k / R;
  };
  const releaseStick = () => { stick.x = stick.y = 0; stick.pointer = null; thumb.style.transform = "translate(0px, 0px)"; };
  const press = (e) => {
    if (e.target.closest("[data-stick]")) {
      e.preventDefault();
      stick.pointer = e.pointerId;
      try { base.setPointerCapture(e.pointerId); } catch { /* capture is a bonus; move/up events still reach the page */ }
      setStick(e);
      return;
    }
    const btn = e.target.closest("[data-ctl]");
    if (!btn) return;
    e.preventDefault();
    const ctl = btn.dataset.ctl;
    if (ctl === "missile") tapped.missile = true;
    else if (ctl === "ability") tapped.ability = true;
    else { held.set(e.pointerId, ctl); btn.classList.add("on"); }
  };
  const release = e => {
    if (e.pointerId === stick.pointer) return releaseStick();
    if (!held.has(e.pointerId)) return;
    const ctl = held.get(e.pointerId); held.delete(e.pointerId);
    if (![...held.values()].includes(ctl)) host.querySelector(`[data-ctl="${ctl}"]`)?.classList.remove("on");
  };
  host.addEventListener("pointerdown", press);
  host.addEventListener("pointermove", e => { if (e.pointerId === stick.pointer) setStick(e); });
  host.addEventListener("pointerup", release);
  base.addEventListener("lostpointercapture", releaseStick);
  host.addEventListener("pointercancel", release);
  host.addEventListener("pointerleave", release);
  host.addEventListener("contextmenu", e => e.preventDefault());
  host.addEventListener("touchmove", e => e.preventDefault(), { passive: false });

  const controls = () => {
    const on = c => keys.has(c) || [...held.values()].includes(c);
    // The joystick, when touched, is analog and wins; otherwise the keys give digital input.
    const keyX = (on("right") ? 1 : 0) - (on("left") ? 1 : 0), keyY = (on("down") ? 1 : 0) - (on("up") ? 1 : 0);
    const useStick = stick.x || stick.y;
    const c = { move: useStick ? { x: stick.x, y: stick.y } : { x: keyX, y: keyY },
      thrust: on("thrust"), fire: on("fire"), missile: tapped.missile, ability: tapped.ability };
    tapped.missile = tapped.ability = false;
    return c;
  };

  function launch() { if (phase === "brief") { phase = "flight"; host.querySelector('[data-f="overlay"]').hidden = true; } }
  function togglePause() { if (phase === "flight" && !sim.outcome) { paused = !paused; q("overlay").hidden = !paused; if (paused) q("overlay").innerHTML = `<h2>Paused</h2><button class="primary" data-f="resume">Resume (P)</button>`; } }
  function exit() {
    if (phase === "done") return;
    if (phase === "brief") return cleanup(null, true);
    if (sim.outcome === null) { sim.outcome = false; sim.message = "Mission abandoned"; }
    phase = "end";
  }

  function cleanup(result, left) {
    cancelAnimationFrame(raf);
    removeEventListener("keydown", keyDown); removeEventListener("keyup", keyUp); removeEventListener("blur", blur);
    host.remove(); document.body.classList.remove("in-flight");
    if (!finished) { finished = true; onFinish(result, left); }
  }

  function showEnd() {
    if (phase === "done") return;  // the result is shown and reported once
    const r = sim.result();
    const ov = q("overlay");
    ov.hidden = false;
    ov.innerHTML = `<h2 class="${r.success ? "good" : "bad"}">${r.success ? "MISSION ACCOMPLISHED" : "MISSION FAILED"}</h2>
      <p>Kills ${r.kills} · Accuracy ${r.shots ? Math.round(r.hits / r.shots * 100) : 0}% · Hull damage ${r.damage_taken}% · Time ${r.duration}s</p>
      <button class="primary big-go" data-f="report">Return to debrief</button>`;
    phase = "done";
    q("report").onclick = () => cleanup(r, false);
  }

  function update(dt) {
    if (phase === "flight" && !paused) {
      sim.step(controls(), dt);
      sim.sounds = [];  // sound cues are not played in the browser yet
      if (sim.outcome !== null) { elapsed = 0; phase = "end"; }
    } else if (phase === "end") {
      elapsed += dt; sim.step(NO_INPUT, dt);
      if (elapsed > 1.2) showEnd();
    }
    if (phase === "brief") sim.step(NO_INPUT, dt * 0.4);
  }

  function drawWorld() {
    const p = sim.player;
    g.fillStyle = "#050a1e"; g.fillRect(0, 0, W, H);
    const sky = g.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, "#060a1c"); sky.addColorStop(1, "#1a1a48");
    g.fillStyle = sky; g.fillRect(0, 0, W, H);
    g.fillStyle = "#b9c8ff";
    for (const st of stars) { const x = ((st.x - sim.time * st.s * st.z) % W + W) % W; g.globalAlpha = 0.4 + 0.15 * st.z; g.fillRect(x, st.y, st.z, st.z); }
    g.globalAlpha = 1;
    g.fillStyle = "rgba(255,214,140,.85)"; g.beginPath(); g.arc(W - 130, 90, 16, 0, Math.PI * 2); g.fill();
    g.strokeStyle = "rgba(82,220,240,.5)"; g.lineWidth = 2;
    for (const site of sim.sites) {
      g.beginPath(); g.arc(site.pos.x, site.pos.y, 70, 0, Math.PI * 2); g.stroke();
      if (site.progress > 0) { g.strokeStyle = COLORS.player; g.lineWidth = 5; g.beginPath(); g.arc(site.pos.x, site.pos.y, 56, -Math.PI / 2, -Math.PI / 2 + site.progress * Math.PI * 2); g.stroke(); g.strokeStyle = "rgba(82,220,240,.5)"; g.lineWidth = 2; }
    }
    for (const f of sim.fragments) { g.fillStyle = "#301e4a"; g.strokeStyle = "#9a7dff"; g.beginPath(); for (let i = 0; i < 11; i++) { const a = i / 11 * Math.PI * 2 + sim.time * 0.5; const r = f.radius * (0.8 + 0.2 * Math.sin(i * 3)); const x = f.position.x + Math.cos(a) * r, y = f.position.y + Math.sin(a) * r; i ? g.lineTo(x, y) : g.moveTo(x, y); } g.closePath(); g.fill(); g.stroke(); }
    if (sim.structure && sim.kind !== "emergency") { if (sim.structure.shape === "base") { g.strokeStyle = COLORS.ally; g.lineWidth = 2; for (const r of [46, 30, 12]) { g.beginPath(); g.arc(sim.structure.position.x, sim.structure.position.y, r, 0, Math.PI * 2); g.stroke(); } } else drawHull(sim.structure, COLORS.ally); }
    for (const e of sim.enemies) {
      if (!(sim.detected(e) || e.role === "ground")) continue;
      drawHull(e, e.role === "ace" ? COLORS.ace : COLORS.enemy);
      if (e.hp < e.maxHp) { g.fillStyle = COLORS.enemy; g.fillRect(e.position.x - 18, e.position.y - e.radius - 12, 36 * Math.max(0, e.hp) / e.maxHp, 3); }
    }
    if (sim.wingman && sim.wingman.alive) drawHull(sim.wingman, COLORS.ally);
    for (const r of sim.rounds) { g.strokeStyle = r.side === "enemy" ? "#ff9a5a" : "#bef8ff"; g.lineWidth = r.target ? 4 : 2; g.beginPath(); g.moveTo(r.position.x, r.position.y); g.lineTo(r.position.x - r.velocity.x * 0.02, r.position.y - r.velocity.y * 0.02); g.stroke(); }
    if (p.hp > 0) { drawHull(p, COLORS.player); if (sim.effectTimer > 0) { g.strokeStyle = COLORS.player; g.beginPath(); g.arc(p.position.x, p.position.y, 32, 0, Math.PI * 2); g.stroke(); } }
    for (const q2 of sim.particles) { const fade = Math.max(0, q2.life / q2.max); g.fillStyle = `rgba(${q2.color.join(",")},${fade})`; g.beginPath(); g.arc(q2.position.x, q2.position.y, Math.max(1, q2.size * fade), 0, Math.PI * 2); g.fill(); }
    drawRadar();
  }

  function drawHull(plane, color) {
    const pts = HULLS[plane.shape];
    if (!pts) return;
    g.save(); g.translate(plane.position.x, plane.position.y); g.rotate(plane.rotation * Math.PI / 180);
    const s = plane.radius;
    // Hull points are drawn with +y forward. The simulation's heading is (-sin, cos) of the
    // rotation, which is exactly canvas rotation applied to +y, so the nose matches movement.
    g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x * s, y * s) : g.moveTo(x * s, y * s))); g.closePath();
    g.fillStyle = color + "40"; g.fill(); g.strokeStyle = color; g.lineWidth = 2; g.stroke(); g.restore();
  }

  function drawRadar() {
    const cx = W - 110, cy = H - 110, rad = 80;
    g.fillStyle = "rgba(8,22,34,.85)"; g.beginPath(); g.arc(cx, cy, rad, 0, Math.PI * 2); g.fill();
    g.strokeStyle = "rgba(82,220,240,.35)"; g.stroke();
    for (const e of sim.enemies) if (sim.detected(e)) {
      const d = e.position.sub(sim.player.position), k = rad / sim.radar;
      g.fillStyle = COLORS.enemy; g.beginPath(); g.arc(cx + d.x * k, cy + d.y * k, 3, 0, Math.PI * 2); g.fill();
    }
    g.fillStyle = COLORS.player; g.beginPath(); g.arc(cx, cy, 3, 0, Math.PI * 2); g.fill();
  }

  function updateHud() {
    const p = sim.player, m = sim.mission;
    q("title").textContent = `LEVEL ${m.level} · ${m.title}`;
    q("type").textContent = m.type_label || m.type;
    q("weather").textContent = sim.weather;
    q("message").textContent = sim.message;
    q("hull").style.width = `${Math.max(0, p.hp / p.maxHp * 100)}%`;
    q("fuel").style.width = `${Math.max(0, sim.fuel)}%`;
    q("thrust").style.width = `${p.throttle * 100}%`;
    q("guns").textContent = `GUNS ${sim.ammo}`;
    q("missiles").textContent = `MISSILES ${sim.missiles}`;
    const cd = Math.max(0, sim.abilityTimer);
    q("ability").textContent = `${ABILITY_TEXT[sim.ability] || sim.ability} ${cd > 0 ? Math.ceil(cd) + "s" : "READY"}`;
    q("pause").hidden = phase !== "flight";
    q("exit").hidden = phase === "done";
  }

  function frame(t) {
    if (!last) last = t;
    const dt = Math.min(0.05, (t - last) / 1000); last = t;
    update(dt);
    drawWorld(); updateHud();
    if (phase !== "done") raf = requestAnimationFrame(frame);  // the world stops once the result is shown
  }
  host.addEventListener("click", e => {
    if (e.target.closest('[data-f="launch"]')) launch();
    else if (e.target.closest('[data-f="resume"]')) togglePause();
    else if (e.target.closest('[data-f="pause"]')) togglePause();
    else if (e.target.closest('[data-f="exit"]')) exit();
  });
  // Starts the screen still in briefing: the pilot must press take off.
  raf = requestAnimationFrame(frame);
  return { stop: () => cleanup(null, true) };
}
