from __future__ import annotations

import argparse
import yaml
from storage.execution_store_sqlite import ExecutionStore

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--side", required=True, choices=["buy","sell"])
    ap.add_argument("--qty", required=True, type=float)
    ap.add_argument("--type", default="market", choices=["market","limit"])
    ap.add_argument("--limit", default=None, type=float)
    ap.add_argument("--dedupe", default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8").read()) or {}
    live = cfg.get("live") or {}
    ex = str(live.get("exchange_id") or "coinbase").lower()
    ex_cfg = cfg.get("execution") or {}
    db = str(ex_cfg.get("db_path") or "data/execution.sqlite")

    store = ExecutionStore(path=db)
    intent_id = store.submit_intent(
        mode="live",
        exchange=ex,
        symbol=args.symbol,
        side=args.side,
        order_type=args.type,
        qty=float(args.qty),
        limit_price=(float(args.limit) if args.limit is not None else None),
        dedupe_key=args.dedupe,
        meta={"cli": True},
    )
    print({"intent_id": intent_id})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
