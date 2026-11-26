# Development log

## Nation choice, voiced intro, logout and crises
- Added selectable nations, a self-playing voiced introduction, home page with How to Play, settings, local log out and log in, misunderstandings, war and ceasefire. This replaces the earlier no-voice introduction.
- Found and fixed: Aerovant and Drakoria campaigns failing to load; diplomacy defaulting to the player's own nation.

## Ranked stages and joint air command
- Reordered the campaign to face national ranks 9 to 1, then a global crisis; wrote a new Ostraven stage and adapted Stage 1 to Zorvania.
- Added treaty talks (accept, counteroffer, reject, postpone), partner-owned aircraft, operating rules, stability, restriction, withdrawal, expiry, stage reports and a data-computed joint air ranking.
- Verified: 51 tests; a scripted player completes 100 levels on three seeds; headless Chrome click-through of a counteroffer, acceptance and Stage 2 briefing with no script errors.

## Cinematic and first-mission slice
- Added written cinematic introduction, permanent command philosophy, 21 characters, branching messages, command centre with training and adviser, nations screen, Level 1 dossier, preparations and debrief. All art is original SVG; there is no voice audio.
- Level 1 now opposes Zorvania, which ranks ninth by the existing military data.
- Verified: 42 tests; a headless Chrome click-through from new game to debrief with no script errors.

## 2026-11-26: first NEBULA foundation (branch `nebula`)
- Inspected the Asteroids project; left its source files unchanged.
- Built world data and shared-vertex map; rules; SQLite and API; Pygame combat; web interface; analytics.
- Tests found and led to fixes for: a crash applying combat results; two Thalmoran cities drawn in the sea; level 1 being winnable without input.
- Visual checks led to fixes for overlapping combat HUD text, squashed profile meters and an invisible one-point chart. These last fixes were not re-screenshotted.
- Verified: 34 automated tests; a scripted strategist completes 100 levels and reaches the Great Union on three seeds; a real Pygame window flew a ticket by autopilot and wrote its result; the original game starts.
