from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)



import argparse, json, datetime, yaml
from services.journal.fill_sink import CanonicalFillSink
from services.os.app_paths import data_dir, ensure_dirs

def main() -> int:
    ensure_dirs()
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTC/USDT")
    ap.add_argument("--side", default="buy")
    ap.add_argument("--qty", type=float, default=0.001)
    ap.add_argument("--price", type=float, default=100.0)
    ap.add_argument("--venue", default="test")
    args = ap.parse_args()

    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8")) or {}
    exec_db = str(cfg.get("execution", {}).get("db_path") or (data_dir() / "execution.sqlite"))

    sink = CanonicalFillSink(exec_db=exec_db)
    fill = {
        "venue": args.venue,
        "fill_id": "",
        "symbol": args.symbol,
        "side": args.side,
        "qty": args.qty,
        "price": args.price,
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "fee_usd": 0.0,
        "realized_pnl_usd": 0.0,
    }
    sink.on_fill(fill)
    print(json.dumps({"ok": True, "exec_db": exec_db, "fill": fill}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
