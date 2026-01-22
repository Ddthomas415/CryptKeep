from __future__ import annotations

import argparse
from storage.execution_audit_reader import list_orders, list_fills, list_statuses, db_exists, DB_PATH

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orders", action="store_true")
    ap.add_argument("--fills", action="store_true")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--venue", default=None)
    ap.add_argument("--symbol", default=None)
    ap.add_argument("--status", default=None)
    ap.add_argument("--exchange_order_id", default=None)
    args = ap.parse_args()

    if not db_exists():
        print({"ok": False, "reason": "db_missing", "expected_path": str(DB_PATH)})
        return

    if args.orders:
        print(list_orders(limit=args.limit, venue=args.venue, symbol=args.symbol, status=args.status)); return
    if args.fills:
        print(list_fills(limit=args.limit, venue=args.venue, symbol=args.symbol, exchange_order_id=args.exchange_order_id)); return

    print({"ok": True, "db_path": str(DB_PATH), "statuses": list_statuses()})

if __name__ == "__main__":
    main()
