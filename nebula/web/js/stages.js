// Ranked stages, treaty table, stage report and joint air command.
import { S, act, go } from "./app.js";
import { esc, cap, flag, meter } from "./ui.js";
import { face } from "./story.js";

const G = () => S.game, nation = id => G().countries[id];
const label = (key, id) => S.world.terms[key][1].find(o => o[0] === id)[1];
const line = (id, text) => { const p = S.world.characters[id]; return `<div class="speech">${face(id, 88)}<div><div class="gold small">${esc(nation(p.country).name.toUpperCase())} · ${esc(p.role.toUpperCase())}</div><b>${esc(p.name)}</b><p>${esc(text)}</p></div></div>`; };

export const airChart = () => `<div class="ranks">${G().air_ranking.map((r, i) => `<div class="rank ${r.country === "lumeris" ? "mine" : ""}"><b>${i + 1}</b>${flag(nation(r.country))}<span>${esc(r.country === "lumeris" ? "Lumeris joint command" : nation(r.country).name)}</span><span class="small">${r.rating}</span></div>`).join("")}</div>
<p>Actual joint air strength: <b class="gold">${G().joint_strength}</b><br>Competitive rank: <b class="gold">${10 - G().signed_stages} of 10</b> · stage progression ${G().signed_stages}/9 treaties</p>
<p class="small dim">Rank rises one place for each completed stage with a signed treaty. The numbers are actual calculated strength (speed, agility, armour and radar of the aircraft under each command), so they need not follow rank order. This is separate from the national military ranking.</p>`;

function currentStage() {
  const open = G().stages.find(s => !G().stage_reports[s.stage]);
  return open ? open.stage : 9;
}

function report(r) {
  const n = nation(r.country);
  return `<div class="panel"><h3>Stage ${r.stage} complete</h3><div class="row">${flag(n)}<b>${esc(n.name)}</b> <span class="dim">remains a sovereign nation with its own government and army</span></div>
  <p style="font-size:22px">Joint air rank <b>${r.previous_rank}</b> → <b class="gold">${r.new_rank}</b></p>
  ${r.signed ? `<p><b>Aircraft added to joint command:</b> ${esc(r.aircraft.join(", "))}</p><p><b>Received at signing:</b> ${Object.entries(r.resources).map(([k, v]) => `${v} ${k}`).join(", ")}</p>
  <table>${Object.entries(r.terms).map(([k, v]) => `<tr><th>${esc(S.world.terms[k][0])}</th><td>${esc(label(k, v))}</td></tr>`).join("")}</table>` : `<p class="dim">The treaty was postponed. No aircraft or resources were shared.</p>`}
  <p class="good">Unlocked: ${esc(r.unlocked)}</p></div>`;
}

function table(stage, country) {
  const talks = G().talks[country], terms = S.ui.terms ??= { ...S.world.default_terms };
  const changes = talks?.counter ? Object.keys(talks.counter).filter(k => talks.counter[k] !== talks.terms[k]) : [];
  return `<div class="panel"><h3>Negotiating table · ${esc(nation(country).name)}</h3><p class="dim">They remain independent. Their army is not part of this agreement. Trust ${nation(country).trust}, relations ${nation(country).relation}, your reputation ${G().reputation}. Demanding more makes agreement less likely. Each proposal takes a day.</p>
  ${talks && talks.outcome !== "accept" ? `<h3 class="${talks.outcome === "reject" ? "bad" : "gold"}">${talks.outcome === "reject" ? "Rejected" : "Counteroffer"} · day ${talks.day}</h3>${talks.lines.map(l => line(l.speaker, l.text)).join("")}
  ${talks.counter ? `<table><tr><th>Term they would change</th><th>You asked</th><th>They offer</th></tr>${changes.map(k => `<tr><td>${esc(S.world.terms[k][0])}</td><td>${esc(label(k, talks.terms[k]))}</td><td class="gold">${esc(label(k, talks.counter[k]))}</td></tr>`).join("")}</table><div class="row"><button class="primary" data-act="joint_counter" data-stage="${stage}">Accept counteroffer</button></div>` : ""}` : ""}
  <div class="grid">${Object.entries(S.world.terms).map(([k, [name, options]]) => `<label>${esc(name)}<br><select data-term="${k}" style="width:100%">${options.map(([id, text]) => `<option value="${id}" ${terms[k] === id ? "selected" : ""}>${esc(text)}</option>`).join("")}</select></label>`).join("")}</div>
  <div class="row"><button class="primary" data-propose="${stage}">Put proposal to ${esc(nation(country).name)}</button>${G().stage_reports[stage] ? "" : `<button data-act="joint_postpone" data-stage="${stage}">Postpone treaty and advance</button>`}</div></div>`;
}

function treaties() {
  return Object.entries(G().joint).map(([c, t]) => {
    const planes = G().fleet.filter(p => p.owner === c);
    return `<div class="panel"><div class="row">${flag(nation(c))}<b>${esc(nation(c).name)}</b><span class="tag ${t.status === "active" ? "confirmed" : "rumour"}">${esc(t.status)}</span></div>${meter("Stability", t.stability)}
    <p class="small">${t.expires ? "Expires day " + t.expires : "No end date"} · ${esc(label("rules", t.terms.rules))} · ${esc(label("command", t.terms.command))} · ${esc(label("withdrawal", t.terms.withdrawal))}</p>
    ${planes.map(p => `<div class="small">#${p.uid} ${esc(p.stats.name)} · owned by ${esc(nation(c).name)} · condition ${p.condition} · fuel ${p.fuel} ${p.grounded ? '<span class="bad">grounded</span>' : ""}</div>`).join("") || `<div class="small dim">No aircraft under joint command.</div>`}
    ${t.log.slice().reverse().map(x => `<div class="small dim">${esc(x)}</div>`).join("")}<div class="row"><button data-act="aid" data-country="${c}">Send aid to repair trust (80c, 20m)</button></div></div>`;
  }).join("") || `<p class="dim">No joint command treaties yet.</p>`;
}

export function jointScreen(el) {
  const stage = S.ui.stage ??= currentStage(), entry = G().stages[stage - 1], c = entry.country;
  const inForce = ["active", "restricted"].includes(G().joint[c]?.status);
  const result = G().stage_reports[stage];
  el.innerHTML = `<h2>Joint Air Command</h2><div class="row">${G().stages.map(s => `<button data-pickstage="${s.stage}" class="${s.stage === stage ? "on" : ""}">${s.stage}. ${esc(nation(s.country).name)} ${G().stage_reports[s.stage] ? "✔" : s.complete ? "●" : ""}</button>`).join("")}</div>
  <div class="split"><div>${result ? report(result) : ""}
  ${!entry.complete ? `<div class="panel"><h3>Stage ${stage}: ${esc(nation(c).name)}</h3><p>${entry.done}/10 missions complete. Treaty talks open after all ten.</p><button data-go="campaign">Open campaign</button></div>`
    : inForce ? `<p class="good">A treaty with ${esc(nation(c).name)} is in force.</p>` : table(stage, c)}</div>
  <aside class="panel"><h3>Joint air-force ranking</h3>${airChart()}</aside></div><h2 style="margin-top:18px">Treaty archive</h2><div class="grid">${treaties()}</div>`;
  return () => {
    el.querySelectorAll("[data-pickstage]").forEach(b => b.onclick = () => { S.ui.stage = Number(b.dataset.pickstage); S.ui.terms = null; go("joint"); });
    el.querySelectorAll("[data-term]").forEach(s => s.onchange = () => S.ui.terms[s.dataset.term] = s.value);
    const propose = el.querySelector("[data-propose]");
    if (propose) propose.onclick = () => { propose.disabled = true; act("joint_propose", { stage, terms: S.ui.terms }).then(ok => { if (!ok) propose.disabled = false; }); };
  };
}
