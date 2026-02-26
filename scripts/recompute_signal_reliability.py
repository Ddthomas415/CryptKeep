#!/usr/bin/env python3
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
from storage.signal_inbox_sqlite import SignalInboxSQLite
from services.signals.reliability import compute_and_store_reliability

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default="coinbase")
    ap.add_argument("--timeframe", default="1h")
    ap.add_argument("--horizon", type=int, default=6)
    ap.add_argument("--threshold-bps", type=float, default=5.0)
    ap.add_argument("--symbol", default=None)
    args = ap.parse_args()
    inbox = SignalInboxSQLite()
    rows = inbox.list_signals(limit=5000, status=None, symbol=args.symbol)
    res = compute_and_store_reliability(
        inbox_rows=rows,
        venue=args.venue,
        timeframe=args.timeframe,
        horizon_candles=int(args.horizon),
        threshold_bps=float(args.threshold_bps),
        symbol=(args.symbol.strip() or None),
    )
    print(json.dumps(res, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
