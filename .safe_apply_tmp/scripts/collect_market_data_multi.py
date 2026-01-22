from __future__ import annotations

import argparse
from services.data.multi_exchange_collector import cfg_from_yaml, run_once, run_loop

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    cfg = cfg_from_yaml()
    if args.once:
        print(run_once(cfg))
        return 0
    run_loop(cfg)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
