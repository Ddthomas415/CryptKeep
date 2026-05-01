#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def data_dir() -> Path:
    from services.os.app_paths import data_dir as _dd
    return _dd()


def default_exec_db() -> str:
    from services.risk.risk_daily import _default_exec_db
    return _default_exec_db()


def flag_path() -> Path:
    return data_dir() / "risk_sink_failed.flag"


def find_missing(exec_db: str) -> list[dict]:
    con = sqlite3.connect(exec_db)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute("""
            SELECT
                cf.venue,
                cf.fill_id,
                cf.symbol,
                cf.side,
                cf.qty,
                cf.price,
                cf.ts,
                cf.realized_pnl_usd,
                cf.fee_usd,
                cf.created_at
            FROM canonical_fills cf
            LEFT JOIN risk_daily_fills rdf
                ON cf.venue = rdf.venue
                AND cf.fill_id = rdf.fill_id
            WHERE rdf.fill_id IS NULL
            ORDER BY cf.created_at ASC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def write_flag(missing_count: int) -> None:
    try:
        flag = flag_path()
        flag.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "failed_at": time.time(),
            "venue": "invariant_checker",
            "fill_id": "canonical_risk_mismatch",
            "missing_count": int(missing_count),
            "reason": (
                "risk_accounting_invariant_violated:"
                f"{missing_count}_canonical_fills_missing_from_risk_daily_fills"
            ),
        }
        tmp = flag.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        tmp.replace(flag)
        print(f"flag_written={flag}")
    except Exception as e:
        print(f"WARN: could not write flag: {type(e).__name__}: {e}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check that every canonical_fills row has a matching risk_daily_fills row."
    )
    ap.add_argument("--exec-db", default=None, help="Path to execution.sqlite")
    args = ap.parse_args()

    exec_db = args.exec_db or default_exec_db()
    print(f"exec_db={exec_db}")

    try:
        missing = find_missing(exec_db)
    except sqlite3.OperationalError as e:
        print(f"query_error={type(e).__name__}:{e}")
        print("SKIP (accounting tables absent or not initialized)")
        return 0
    except Exception as e:
        print(f"FATAL: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    if not missing:
        print("invariant=OK")
        print("canonical_fills_missing_from_risk_daily_fills=0")
        return 0

    print("invariant=VIOLATED")
    print(f"canonical_fills_missing_from_risk_daily_fills={len(missing)}")
    print()
    print(f"sample_rows (showing {min(20, len(missing))} of {len(missing)}):")
    for row in missing[:20]:
        print(
            f"  venue={row['venue']!r}"
            f" fill_id={row['fill_id']!r}"
            f" symbol={row.get('symbol')!r}"
            f" side={row.get('side')!r}"
            f" qty={row.get('qty')}"
            f" price={row.get('price')}"
            f" realized_pnl_usd={row.get('realized_pnl_usd')}"
            f" fee_usd={row.get('fee_usd')}"
            f" created_at={row.get('created_at')!r}"
        )

    print()
    write_flag(len(missing))
    print()
    print("Run scripts/repair_risk_sink_failed.py to replay missing fills and clear the flag after verification.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
