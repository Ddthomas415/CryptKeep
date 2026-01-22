from __future__ import annotations

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
