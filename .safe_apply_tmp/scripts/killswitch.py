from __future__ import annotations
import argparse, json
from services.risk.killswitch_phase82 import KillSwitch

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--on", action="store_true")
    ap.add_argument("--off", action="store_true")
    a = ap.parse_args()
    if a.on and a.off:
        print(json.dumps({"ok": False, "error": "choose --on or --off"}))
        return 2
    ks = KillSwitch.from_config()
    if a.on: ks.set(True)
    if a.off: ks.set(False)
    print(json.dumps({"ok": True, "killswitch": ks.is_on()}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
