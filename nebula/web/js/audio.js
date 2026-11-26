// Audio hooks for the strategy layer: tiny synthesised cues, no asset files.
let ctx;
const CUES = { click: [520, 0.04], good: [740, 0.18], bad: [180, 0.22], open: [360, 0.09] };
export function cue(name) {
  if (localStorage.getItem("nebula.sound") === "off") return;
  try {
    ctx ??= new AudioContext();
    const [freq, length] = CUES[name], osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.05, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + length);
    osc.connect(gain).connect(ctx.destination);
    osc.start(); osc.stop(ctx.currentTime + length);
  } catch { /* audio is optional */ }
}
export function starfield(canvas) {
  const g = canvas.getContext("2d");
  const stars = Array.from({ length: 180 }, () => [Math.random(), Math.random(), Math.random()]);
  const draw = t => {
    canvas.width = innerWidth; canvas.height = innerHeight;
    for (const [x, y, z] of stars) {
      g.fillStyle = `rgba(190,205,255,${0.25 + 0.5 * z})`;
      g.fillRect((x * innerWidth + t * z * 0.004) % innerWidth, y * innerHeight, z * 1.7, z * 1.7);
    }
  };
  draw(0);
  let last = 0;
  const loop = t => { // ~20fps is enough for a slow drift
    if (t - last > 50 && !document.body.classList.contains("calm")) { draw(t); last = t; }
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
}
