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
import yaml
from storage.execution_store_sqlite import ExecutionStore
from services.os.app_paths import data_dir, ensure_dirs

def main() -> int:
    ensure_dirs()
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
    db = str(ex_cfg.get("db_path") or (data_dir() / "execution.sqlite"))

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
