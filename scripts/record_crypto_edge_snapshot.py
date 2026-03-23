from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path
import sys

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json
from typing import Any

from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite


def _load_rows(path: str) -> list[dict[str, Any]]:
    if not path:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [dict(item or {}) for item in list(payload or [])]


def main() -> int:
    ap = argparse.ArgumentParser(description="Record research-only crypto structural edge snapshots.")
    ap.add_argument("--db-path", default="", help="Optional sqlite path override")
    ap.add_argument("--source", default="manual", help="Snapshot source label")
    ap.add_argument("--capture-ts", default="", help="Optional capture timestamp override")
    ap.add_argument("--funding-file", default="", help="JSON file with funding rows")
    ap.add_argument("--basis-file", default="", help="JSON file with basis rows")
    ap.add_argument("--quotes-file", default="", help="JSON file with quote rows")
    ap.add_argument("--print-report", action="store_true", help="Print the latest report after ingest")
    args = ap.parse_args()

    funding_rows = _load_rows(args.funding_file)
    basis_rows = _load_rows(args.basis_file)
    quote_rows = _load_rows(args.quotes_file)
    if not (funding_rows or basis_rows or quote_rows):
        print(json.dumps({"ok": False, "reason": "no_rows_supplied"}))
        return 1

    store = CryptoEdgeStoreSQLite(path=str(args.db_path or ""))
    out: dict[str, Any] = {"ok": True, "store_path": "redacted"}
    if funding_rows:
        out["funding_snapshot_id"] = store.append_funding_rows(
            funding_rows,
            source=str(args.source or "manual"),
            capture_ts=str(args.capture_ts or "") or None,
        )
        out["funding_count"] = int(len(funding_rows))
    if basis_rows:
        out["basis_snapshot_id"] = store.append_basis_rows(
            basis_rows,
            source=str(args.source or "manual"),
            capture_ts=str(args.capture_ts or "") or None,
        )
        out["basis_count"] = int(len(basis_rows))
    if quote_rows:
        out["quote_snapshot_id"] = store.append_quote_rows(
            quote_rows,
            source=str(args.source or "manual"),
            capture_ts=str(args.capture_ts or "") or None,
        )
        out["quote_count"] = int(len(quote_rows))
    if args.print_report:
        out["report"] = store.latest_report()
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
