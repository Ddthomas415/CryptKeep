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


import argparse, json
from services.markets.prereq import check_market_rules_prereq

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttl-hours", type=float, default=6.0)
    args = ap.parse_args()

    pr = check_market_rules_prereq(ttl_s=float(args.ttl_hours) * 3600.0)
    print(json.dumps(pr.__dict__, indent=2))
    return 0 if pr.ok else 2

if __name__ == "__main__":
    raise SystemExit(main())
