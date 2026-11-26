// Voice narration (the browser's built-in speech synthesis), music and audio preferences.
const DEFAULTS = { muted: false, narration: true, subtitles: true, voice: 0.9, music: 0.4, rate: 1, voiceName: "" };
export const prefs = () => ({ ...DEFAULTS, ...JSON.parse(localStorage.getItem("nebula.audio") || "{}") });
export function setPref(key, value) {
  const next = { ...prefs(), [key]: value };
  localStorage.setItem("nebula.audio", JSON.stringify(next));
  localStorage.setItem("nebula.sound", next.muted ? "off" : "on"); // interface cues
  if (next.muted || !next.narration) window.speechSynthesis?.cancel();
  levelMusic();
}
const synth = window.speechSynthesis;
synth?.getVoices(); // voices load asynchronously in some browsers
export const voices = () => (synth?.getVoices() ?? []).filter(v => v.lang.startsWith("en"));
export const voiceAvailable = () => !!synth && voices().length > 0;
export const soundUnlocked = () => navigator.userActivation?.hasBeenActive ?? true;

const hash = text => [...text].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7);
let run = 0, timers = [];
export function stopSpeech() {
  run++;
  timers.forEach(clearTimeout); timers = [];
  synth?.cancel();
}
// Speaks lines in order. Without a usable voice, each line stays up for its reading time.
export function say(lines, onLine, onDone) {
  stopSpeech();
  const mine = run;
  const next = i => {
    if (mine !== run) return;
    if (i >= lines.length) return onDone?.();
    const line = lines[i], p = prefs();
    const spoken = p.narration && !p.muted && voiceAvailable() && soundUnlocked();
    onLine?.(line, spoken);
    const reading = Math.max(2600, line.text.length * 58);
    let finished = false;
    const advance = () => { if (!finished && mine === run) { finished = true; timers.push(setTimeout(() => next(i + 1), 450)); } };
    if (!spoken) { timers.push(setTimeout(advance, reading)); return; }
    const u = new SpeechSynthesisUtterance(line.text), list = voices(), h = hash(line.id ?? "narrator");
    u.voice = line.id ? list[h % list.length] : list.find(v => v.name === p.voiceName) ?? list[0];
    u.pitch = line.id ? 0.75 + (h % 60) / 100 : 0.95;
    u.rate = p.rate * (line.id ? 0.94 + (h % 12) / 100 : 0.96);
    u.volume = p.voice;
    u.onend = u.onerror = advance;
    synth.speak(u);
    timers.push(setTimeout(advance, reading * 2 + 4000)); // some engines never report the end
  };
  next(0);
}

const CHORDS = [[110, 164.8, 220, 261.6], [87.3, 130.8, 174.6, 220], [98, 146.8, 196, 246.9], [82.4, 123.5, 164.8, 196]];
let music;
function levelMusic() {
  if (music) music.gain.gain.setTargetAtTime(prefs().muted ? 0 : prefs().music * 0.045, music.ctx.currentTime, 0.4);
}
export function startMusic() {
  if (music || !soundUnlocked()) return;
  try {
    const ctx = new AudioContext(), gain = ctx.createGain(), filter = ctx.createBiquadFilter();
    filter.frequency.value = 700; gain.gain.value = 0; filter.connect(gain).connect(ctx.destination);
    const oscillators = CHORDS[0].map((f, i) => { const o = ctx.createOscillator(); o.type = i ? "triangle" : "sine"; o.frequency.value = f; o.detune.value = i * 3; o.connect(filter); o.start(); return o; });
    let step = 0;
    const timer = setInterval(() => { const chord = CHORDS[++step % CHORDS.length]; oscillators.forEach((o, i) => o.frequency.setTargetAtTime(chord[i], ctx.currentTime, 1.2)); }, 7000);
    music = { ctx, gain, timer };
    levelMusic();
  } catch { /* music is optional */ }
}
export function stopMusic() {
  if (!music) return;
  clearInterval(music.timer); music.ctx.close(); music = null;
}

// Compact controls for spoken campaign events. The on-screen text is the subtitle.
export const voiceBar = () => `<div class="voicebar"><button data-v="replay">▶ Replay voice</button><button data-v="skip">Skip voice</button><button data-v="mute">${prefs().muted ? "Unmute" : "Mute"}</button><span class="subtitle small" aria-live="polite"></span></div>`;
export function bindVoice(el, lines, auto = true) {
  const bar = el.querySelector(".voicebar");
  if (!bar) return;
  const caption = bar.querySelector(".subtitle");
  const play = () => say(lines, line => { caption.textContent = prefs().subtitles || !voiceAvailable() ? `${line.name}: ${line.text}` : ""; }, () => { caption.textContent = ""; });
  bar.querySelector('[data-v="replay"]').onclick = play;
  bar.querySelector('[data-v="skip"]').onclick = () => { stopSpeech(); caption.textContent = ""; };
  bar.querySelector('[data-v="mute"]').onclick = e => { setPref("muted", !prefs().muted); e.target.textContent = prefs().muted ? "Unmute" : "Mute"; };
  if (auto) play();
}
