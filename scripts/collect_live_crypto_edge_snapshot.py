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

from services.analytics.crypto_edge_collector import collect_live_crypto_edge_snapshot
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite


def _load_plan(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return dict(payload or {})


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect read-only live crypto structural edge snapshots.")
    ap.add_argument("--plan-file", required=True, help="JSON plan describing funding, basis, and quote fetches")
    ap.add_argument("--db-path", default="", help="Optional sqlite path override")
    ap.add_argument("--source", default="live_public", help="Snapshot source label")
    ap.add_argument("--capture-ts", default="", help="Optional capture timestamp override")
    ap.add_argument("--print-report", action="store_true", help="Print latest stored report after ingest")
    args = ap.parse_args()

    plan = _load_plan(str(args.plan_file))
    collected = collect_live_crypto_edge_snapshot(plan)

    funding_rows = list(collected.get("funding_rows") or [])
    basis_rows = list(collected.get("basis_rows") or [])
    quote_rows = list(collected.get("quote_rows") or [])
    if not (funding_rows or basis_rows or quote_rows):
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "no_live_rows_collected",
                    "checks": list(collected.get("checks") or []),
                    "research_only": True,
                    "execution_enabled": False,
                },
                indent=2,
                default=str,
            )
        )
        return 1

    store = CryptoEdgeStoreSQLite(path=str(args.db_path or ""))
    out: dict[str, Any] = {
        "ok": True,
        "research_only": True,
        "execution_enabled": False,
        "store_path": "redacted",
        "checks": list(collected.get("checks") or []),
    }
    if funding_rows:
        out["funding_snapshot_id"] = store.append_funding_rows(
            funding_rows,
            source=str(args.source or "live_public"),
            capture_ts=str(args.capture_ts or "") or None,
        )
        out["funding_count"] = int(len(funding_rows))
    if basis_rows:
        out["basis_snapshot_id"] = store.append_basis_rows(
            basis_rows,
            source=str(args.source or "live_public"),
            capture_ts=str(args.capture_ts or "") or None,
        )
        out["basis_count"] = int(len(basis_rows))
    if quote_rows:
        out["quote_snapshot_id"] = store.append_quote_rows(
            quote_rows,
            source=str(args.source or "live_public"),
            capture_ts=str(args.capture_ts or "") or None,
        )
        out["quote_count"] = int(len(quote_rows))
    if args.print_report:
        out["report"] = store.latest_report()
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
