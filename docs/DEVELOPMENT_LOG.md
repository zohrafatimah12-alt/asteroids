# Development log

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
