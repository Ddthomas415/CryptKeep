from __future__ import annotations

import argparse
import json

from services.risk.killswitch import KillSwitch

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--on", action="store_true")
    ap.add_argument("--off", action="store_true")
    args = ap.parse_args()

    if args.on and args.off:
        print(json.dumps({"ok": False, "error": "choose --on or --off"}, indent=2))
        return 2

    ks = KillSwitch.from_config()
    if args.on:
        ks.set(True)
    elif args.off:
        ks.set(False)

    print(json.dumps({"ok": True, "killswitch": ks.is_on()}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
