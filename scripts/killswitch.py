from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)




import argparse
import json

from services.admin.kill_switch import get_state, set_armed

def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--arm", action="store_true")
    group.add_argument("--disarm", action="store_true")
    group.add_argument("--status", action="store_true")
    group.add_argument("--on", action="store_true")
    group.add_argument("--off", action="store_true")
    args = ap.parse_args()

    if args.arm or args.on:
        state = set_armed(True, note="scripts.killswitch:arm")
    elif args.disarm or args.off:
        state = set_armed(False, note="scripts.killswitch:disarm")
    else:
        state = get_state()

    payload = {
        "ok": True,
        "killswitch": bool((state or {}).get("armed", True)),
        "state": state,
    }
    print(json.dumps(payload, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
