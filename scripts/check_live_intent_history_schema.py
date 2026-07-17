#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

_REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json
import sqlite3
import time
from typing import Any

from storage import live_intent_queue_sqlite as live_queue

EXIT_READY = 0
EXIT_NOT_READY = 1
EXIT_ERROR = 2

REQUIRED_EVENT_COLUMNS = (
    "event_id",
    "intent_id",
    "event_ts",
    "actor",
    "action",
    "pre_status",
    "post_status",
    "reason",
    "last_error",
    "client_order_id",
    "exchange_order_id",
    "source",
    "meta",
)


def _table_columns(db_path: Path, table: str) -> list[str]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return [str(row[1]) for row in con.execute(f"PRAGMA table_info({table})").fetchall()]
    finally:
        con.close()


def inspect_live_intent_history_schema(*, initialize: bool = False) -> dict[str, Any]:
    init_error = ""
    if initialize:
        try:
            live_queue.LiveIntentQueueSQLite()
        except Exception as exc:
            init_error = f"schema_init_failed:{type(exc).__name__}"

    db_path = live_queue.DB_PATH
    report: dict[str, Any] = {
        "ok": False,
        "status": "schema_uninitialized",
        "initialized": bool(initialize),
        "db_path": str(db_path),
        "db_exists": db_path.exists(),
        "event_history_declared": "live_trade_intent_events" in str(getattr(live_queue, "SCHEMA", "")),
        "event_history_table_exists": False,
        "event_columns": [],
        "missing_event_columns": list(REQUIRED_EVENT_COLUMNS),
    }

    if init_error:
        report["status"] = "init_failed"
        report["reason"] = init_error
        return report

    if not db_path.exists():
        report["reason"] = "live_intent_queue_db_missing"
        return report

    try:
        event_cols = _table_columns(db_path, "live_trade_intent_events")
    except Exception as exc:
        return {
            **report,
            "status": "inspect_failed",
            "reason": f"sqlite_inspect_failed:{type(exc).__name__}",
        }

    missing_cols = [col for col in REQUIRED_EVENT_COLUMNS if col not in event_cols]
    report.update(
        {
            "event_history_table_exists": bool(event_cols),
            "event_columns": event_cols,
            "missing_event_columns": missing_cols,
        }
    )

    if not event_cols:
        report["reason"] = "live_trade_intent_events_missing"
        return report
    if missing_cols:
        report["status"] = "schema_incomplete"
        report["reason"] = "live_trade_intent_events_incomplete"
        return report

    report["ok"] = True
    report["status"] = "ready"
    report["reason"] = "live_trade_intent_events_ready"
    return report


def _write_evidence(report: dict[str, Any], dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_path = dest / f"live-intent-history-schema-{stamp}.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether live intent transition-history schema exists in the current runtime DB."
    )
    parser.add_argument("--init", action="store_true", help="explicitly initialize/migrate the live intent queue schema before checking")
    parser.add_argument("--json", action="store_true", help="print the full JSON report")
    parser.add_argument("--evidence-dest", default="", help="write the JSON report into this directory")
    args = parser.parse_args()

    report = inspect_live_intent_history_schema(initialize=bool(args.init))
    if args.evidence_dest:
        path = _write_evidence(report, Path(args.evidence_dest))
        report["evidence_path"] = str(path)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        verdict = "ok" if report["ok"] else "FAIL"
        print(f"live intent history schema: {verdict}")
        print(f"status: {report['status']}")
        print(f"reason: {report.get('reason')}")
        print(f"db: {report['db_path']}")
        print(f"initialized: {report['initialized']}")
        print(f"event table: {report['event_history_table_exists']}")
        missing = report.get("missing_event_columns") or []
        if missing:
            print(f"missing columns: {', '.join(missing)}")
        if "evidence_path" in report:
            print(f"evidence: {report['evidence_path']}")

    if report.get("ok"):
        return EXIT_READY
    if report.get("status") == "inspect_failed":
        return EXIT_ERROR
    return EXIT_NOT_READY


if __name__ == "__main__":
    raise SystemExit(main())
