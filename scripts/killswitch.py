from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


# CBP_BOOTSTRAP: ensure repo root on sys.path so `import services` works when running scripts directly
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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
