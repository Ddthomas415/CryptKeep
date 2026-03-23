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

SAMPLE_DIR = ROOT / "sample_data" / "crypto_edges"


def _load_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [dict(item or {}) for item in list(payload or [])]


def main() -> int:
    ap = argparse.ArgumentParser(description="Load bundled sample crypto-edge snapshots into the local research store.")
    ap.add_argument("--db-path", default="", help="Optional sqlite path override")
    ap.add_argument("--sample-dir", default="", help="Optional sample data directory override")
    ap.add_argument("--source", default="sample_bundle", help="Snapshot source label")
    ap.add_argument("--capture-ts", default="2026-03-18T14:00:00+00:00", help="Capture timestamp to store")
    ap.add_argument("--print-report", action="store_true", help="Print the latest report after ingest")
    args = ap.parse_args()

    sample_dir = Path(str(args.sample_dir or "")).expanduser() if args.sample_dir else SAMPLE_DIR
    funding_rows = _load_rows(sample_dir / "funding.json")
    basis_rows = _load_rows(sample_dir / "basis.json")
    quote_rows = _load_rows(sample_dir / "quotes.json")

    store = CryptoEdgeStoreSQLite(path=str(args.db_path or ""))
    out: dict[str, Any] = {
        "ok": True,
        "store_path": "redacted",
        "sample_dir": str(sample_dir),
        "funding_snapshot_id": store.append_funding_rows(
            funding_rows,
            source=str(args.source or "sample_bundle"),
            capture_ts=str(args.capture_ts or "") or None,
        ),
        "basis_snapshot_id": store.append_basis_rows(
            basis_rows,
            source=str(args.source or "sample_bundle"),
            capture_ts=str(args.capture_ts or "") or None,
        ),
        "quote_snapshot_id": store.append_quote_rows(
            quote_rows,
            source=str(args.source or "sample_bundle"),
            capture_ts=str(args.capture_ts or "") or None,
        ),
        "funding_count": int(len(funding_rows)),
        "basis_count": int(len(basis_rows)),
        "quote_count": int(len(quote_rows)),
    }
    if args.print_report:
        out["report"] = store.latest_report()
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
