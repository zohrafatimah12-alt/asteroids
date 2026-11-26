# Contributing
- Run `uv sync`, then `uv run pytest` before committing.
- Rules belong in `nebula/core`; the web client only presents. Raise `RuleError` for forbidden actions, before changing state where possible.
- Change resources and relations through the helpers in `core/state.py`, so analytics records them.
- Content changes go in `nebula/data`; then run `uv run python -m docs.generate_docs`.
- Analytics must stay read-only and must never show invented numbers.
- Keep the original Asteroids files working.
- Escape any user-provided text with `esc()` in the web client.
- Rules must use `home(state)` for the player's nation, never assume Lumeris.
- Never commit databases, secrets or `saves/`. Do not force-push.
