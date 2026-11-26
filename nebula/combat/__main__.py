"""python -m nebula.combat [--level N] [--aircraft ID] [--autopilot]"""

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from nebula.combat.app import run  # noqa: E402
from nebula.combat.ticket import practice_ticket  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="NEBULA air combat")
    parser.add_argument("--ticket", type=Path, help="sortie ticket written by the command server")
    parser.add_argument("--level", type=int, default=1, help="practice level (nothing is saved)")
    parser.add_argument("--aircraft", default="lm_wren")
    parser.add_argument("--autopilot", action="store_true")
    parser.add_argument("--mute", action="store_true")
    args = parser.parse_args()
    ticket = json.loads(args.ticket.read_text()) if args.ticket else practice_ticket(args.level, args.aircraft)
    if ticket["mission"]["type"] in ("diplomacy", "intelligence", "economy", "research"):
        parser.error("that level is a strategic mission; play it in the command interface")
    result = run(ticket, auto=args.autopilot, sound=not args.mute)
    if result is None:
        return
    if args.ticket:
        target = args.ticket.with_name(args.ticket.stem + ".result.json")
        temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(result))
        temp.replace(target)  # atomic: the server never reads a half-written file
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
