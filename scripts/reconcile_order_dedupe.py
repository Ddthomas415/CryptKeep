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
import os
from typing import Optional

from services.os.app_paths import data_dir, ensure_dirs
from services.execution.exchange_client import ExchangeClient
from storage.order_dedupe_store_sqlite import OrderDedupeStore

def _extract_client_id(o: dict) -> Optional[str]:
    for k in ("clientOrderId", "client_order_id", "clientOrderID", "text"):
        v = o.get(k)
        if v:
            return str(v)
    info = o.get("info")
    if isinstance(info, dict):
        for k in ("clientOrderId", "client_order_id", "clientOrderID", "text", "client_id"):
            v = info.get(k)
            if v:
                return str(v)
    return None

def main() -> int:
    ensure_dirs()
    ap = argparse.ArgumentParser()
    ap.add_argument("--exchange", required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--exec-db", default=os.environ.get("EXEC_DB_PATH") or os.environ.get("CBP_DB_PATH") or str(data_dir() / "execution.sqlite"))
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()

    ex_id = args.exchange.lower().strip()
    store = OrderDedupeStore(exec_db=args.exec_db)
    client = ExchangeClient(exchange_id=ex_id, sandbox=False)

    rows = store.list_needs_reconcile(exchange_id=ex_id, limit=args.limit)

    want = {}
    for r in rows:
        cid = r.get("client_order_id")
        if cid:
            want[str(cid)] = str(r["intent_id"])

    matched_open = 0
    try:
        open_orders = client.fetch_open_orders(symbol=args.symbol)
    except Exception:
        open_orders = []

    for o in open_orders or []:
        cid = _extract_client_id(o) or ""
        if cid and cid in want:
            intent_id = want[cid]
            rid = o.get("id")
            if rid:
                store.set_remote_id_if_empty(exchange_id=ex_id, intent_id=intent_id, remote_order_id=str(rid))
                store.mark_submitted(exchange_id=ex_id, intent_id=intent_id, remote_order_id=str(rid))
                matched_open += 1

    checked = 0
    marked_terminal = 0
    for r in rows:
        rid = r.get("remote_order_id")
        if not rid:
            continue
        checked += 1
        try:
            o = client.fetch_order(order_id=str(rid), symbol=args.symbol)
        except Exception:
            continue
        st = str(o.get("status") or "").lower()
        if st in ("closed", "filled", "canceled", "cancelled", "rejected", "expired"):
            store.mark_terminal(exchange_id=ex_id, intent_id=str(r["intent_id"]), terminal_status=st)
            marked_terminal += 1

    print(json.dumps({
        "ok": True,
        "checked_rows": len(rows),
        "matched_open_orders": matched_open,
        "checked_with_remote_id": checked,
        "marked_terminal": marked_terminal,
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
