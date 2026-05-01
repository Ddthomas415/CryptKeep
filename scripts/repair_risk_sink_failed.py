#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, sqlite3, sys
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

def missing_fills(exec_db: str) -> list[dict]:
    con = sqlite3.connect(exec_db)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute("""
            SELECT cf.venue, cf.fill_id, cf.realized_pnl_usd, cf.fee_usd
            FROM canonical_fills cf
            LEFT JOIN risk_daily_fills rdf
              ON cf.venue = rdf.venue AND cf.fill_id = rdf.fill_id
            WHERE rdf.fill_id IS NULL
            ORDER BY cf.created_at ASC
        """).fetchall()]
    finally:
        con.close()

def replay(exec_db: str, fill: dict, *, allow_null_pnl: bool) -> tuple[bool, str]:
    from services.risk.risk_daily import RiskDailyDB

    if fill.get("realized_pnl_usd") is None and not allow_null_pnl:
        return False, "null_realized_pnl_refusing_replay_use_allow_null_pnl"

    return (
        True,
        "applied" if RiskDailyDB(exec_db).apply_fill_once(
            venue=str(fill["venue"]),
            fill_id=str(fill["fill_id"]),
            realized_pnl_usd=float(fill.get("realized_pnl_usd") or 0.0),
            fee_usd=float(fill.get("fee_usd") or 0.0),
        ) else "already_present",
    )

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exec-db", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-clear-flag", action="store_true")
    ap.add_argument("--allow-null-pnl", action="store_true")
    args = ap.parse_args()

    exec_db = args.exec_db or default_exec_db()
    flag = flag_path()

    if not flag.exists():
        print("risk_sink_failed.flag not present; nothing to repair")
        raise SystemExit(2)

    before = missing_fills(exec_db)
    print(f"missing_before={len(before)}")

    if args.dry_run:
        for f in before:
            print(f"would_replay venue={f['venue']} fill_id={f['fill_id']} pnl={f['realized_pnl_usd']} fee={f['fee_usd']}")
        raise SystemExit(0)

    failures = []
    for f in before:
        try:
            ok, reason = replay(exec_db, f, allow_null_pnl=args.allow_null_pnl)
        except Exception as e:
            ok, reason = False, f"{type(e).__name__}:{e}"
        print(f"replay venue={f['venue']} fill_id={f['fill_id']} ok={ok} reason={reason}")
        if not ok:
            failures.append((f, reason))

    if failures:
        print("repair_failed; flag NOT cleared")
        raise SystemExit(1)

    after = missing_fills(exec_db)
    print(f"missing_after={len(after)}")
    if after:
        print("verify_failed_missing_remain; flag NOT cleared")
        raise SystemExit(1)

    if args.no_clear_flag:
        print("verified but --no-clear-flag set; flag NOT cleared")
        raise SystemExit(0)

    flag.unlink(missing_ok=True)
    print(f"flag_cleared={flag}")
    print("repair_complete")

if __name__ == "__main__":
    main()
