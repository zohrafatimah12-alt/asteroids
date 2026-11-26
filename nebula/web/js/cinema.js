// The self-playing introduction: animated scenes synchronised to each spoken line.
import { S, go } from "./app.js";
import { esc, flag } from "./ui.js";
import { portrait, star, planet } from "./art.js";
import { prefs, setPref, say, stopSpeech, startMusic, stopMusic, voiceAvailable, soundUnlocked } from "./voice.js";

const nations = () => S.world.nations;
const leaderArt = (id, size) => { const p = S.world.characters[id]; return portrait(p, nations()[p.country].colors, size); };
const narrate = text => ({ name: "Narrator", text });
const speak = (id, text) => ({ id, name: S.world.characters[id].name, text });
const MOTTOS = {
  lumeris: "We are small. We are not blind.", aerovant: "The sky belongs to those who study it.",
  varkhen: "Strength keeps our people fed.", elyndra: "Our passes shelter anyone who asks.",
  zorvania: "We prefer to know first.", thalmora: "The sea lanes stay open.",
  kryvos: "A water debt is never forgotten.", frostara: "Nobody is left outside.",
  drakoria: "What we build, holds.", ostraven: "Everything has a price. Even peace.",
};
const close = id => `<div class="closeup">${leaderArt(id, 230)}<div class="gold small">${esc(nations()[S.world.characters[id].country].name.toUpperCase())} · ${esc(S.world.characters[id].role.toUpperCase())}</div></div>`;

function scenes() {
  const world = () => planet(S.world, nations());
  return [
    { art: star, line: narrate("Far beyond the Milky Way burns a star called Nebula.") },
    { art: world, line: narrate("One world circles it. Veyra. Ten nations share it, and none of them fully trusts another.") },
    ...Object.keys(MOTTOS).map(c => {
      const id = S.world.leaders[c];
      return { art: () => `<div class="reveal">${planet(S.world, nations(), c)}<div class="closeup">${flag(nations()[c])}<h2>${esc(nations()[c].name.toUpperCase())}</h2>${leaderArt(id, 150)}</div></div>`, line: speak(id, MOTTOS[c]) };
    }),
    ...[["lu_intel", "A signal suggests someone is preparing to move. I cannot confirm it."],
      ["zv_head", "Our flights are research. Treat them otherwise at your risk."],
      ["vk_head", "Weakness has consequences."],
      ["ae_head", "One mistake now could set the whole continent alight."]].map(([id, text]) => ({ art: () => close(id), line: speak(id, text) })),
    { art: () => `<div class="threat">${planet(S.world, nations())}<div class="shard"></div></div>`, line: speak("fr_head", "Something is coming out of the dark. It is not one of ours.") },
    { art: () => `<h1 class="title-card">NEBULA</h1>`, line: narrate("Build trust. Face what comes. Protect Veyra.") },
  ];
}

export function startIntro(next = "menu") {
  S.ui.introNext = next;
  if (location.hash === "#intro") go("intro"); else location.hash = "intro";
}

export function intro(el) {
  el.innerHTML = `<section class="film"><div class="shot"></div><p class="subtitle caption" aria-live="polite"></p><div class="progress"><i></i></div>
  <div class="controls"><button data-i="skip">SKIP INTRO</button><button data-i="replay">REPLAY</button><button data-i="mute"></button></div><p class="small dim notice"></p></section>`;
  return () => {
    const list = scenes(), q = s => el.querySelector(s);
    let index = 0;
    const label = () => { q('[data-i="mute"]').textContent = !soundUnlocked() ? "TAP FOR SOUND" : prefs().muted ? "UNMUTE" : "MUTE"; };
    const finish = () => { stopSpeech(); stopMusic(); localStorage.setItem("nebula.introSeen", "1"); go(S.ui.introNext || "menu"); };
    const play = i => {
      if (!el.contains(q(".shot"))) return;
      if (i >= list.length) return finish();
      index = i;
      q(".shot").innerHTML = list[i].art();
      q(".shot").style.animation = "none"; void q(".shot").offsetWidth; q(".shot").style.animation = "";
      q(".progress i").style.width = `${(i + 1) / list.length * 100}%`;
      say([list[i].line], (line, spoken) => {
        q(".subtitle").innerHTML = prefs().subtitles || !spoken ? `<span class="gold">${esc(line.name)}</span><br>${esc(line.text)}` : "";
        q(".notice").textContent = voiceAvailable() ? (soundUnlocked() ? "" : "Your browser blocks sound until you tap. Playing with subtitles.")
          : "No speech voice is available in this browser. Playing with subtitles.";
        label();
      }, () => play(i + 1));
    };
    q('[data-i="skip"]').onclick = finish;
    q('[data-i="replay"]').onclick = () => { startMusic(); play(0); };
    q('[data-i="mute"]').onclick = e => {
      if (e.target.textContent !== "TAP FOR SOUND") setPref("muted", !prefs().muted); else setPref("muted", false);
      startMusic(); label(); play(index);
    };
    startMusic(); label(); play(0);
  };
}
