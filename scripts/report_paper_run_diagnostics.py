#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timedelta
import json
import math
import os
import sqlite3
from pathlib import Path
import stat
import sys
from typing import Any

ROOT = Path(".")
STATE_DIR = ROOT / ".cbp_state"
DATA_DIR = STATE_DIR / "data"
RUNTIME_DIR = STATE_DIR / "runtime" / "flags"

STATUS_FILE = RUNTIME_DIR / "strategy_runner.status.json"
INTENT_DB = DATA_DIR / "intent_queue.sqlite"
PAPER_DB = DATA_DIR / "paper_trading.sqlite"
JOURNAL_DB = DATA_DIR / "trade_journal.sqlite"
MAX_EVALUATION_FILLS = 100_000
EVALUATION_FEE_BPS = 50


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        return {"_error": f"failed_to_parse_json: {type(exc).__name__}: {exc}"}


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "select name from sqlite_master where type='table' and name=?",
        (table,),
    ).fetchone()
    return row is not None


def _query_rows(
    conn: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def _print_section(title: str, payload: Any) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2, default=str))


def _build_where(strategy_id: str | None, symbol: str | None, alias: str = "") -> tuple[str, list[Any]]:
    prefix = f"{alias}." if alias else ""
    clauses: list[str] = []
    params: list[Any] = []
    if strategy_id:
        clauses.append(f"{prefix}strategy_id = ?")
        params.append(strategy_id)
    if symbol:
        clauses.append(f"{prefix}symbol = ?")
        params.append(symbol)
    if not clauses:
        return "", params
    return "where " + " and ".join(clauses), params


def latest_runner_status() -> dict[str, Any]:
    return _load_json(STATUS_FILE)


def recent_intents(limit: int, strategy_id: str | None, symbol: str | None) -> list[dict[str, Any]]:
    if not INTENT_DB.exists():
        return [{"_error": f"missing_db: {INTENT_DB}"}]
    conn = _connect(INTENT_DB)
    try:
        if not _table_exists(conn, "trade_intents"):
            return [{"_error": "missing_table: trade_intents"}]
        where_sql, params = _build_where(strategy_id, symbol)
        sql = f"""
        select intent_id, created_ts, ts, source, strategy_id, venue, symbol, side,
               order_type, qty, limit_price, status, last_error,
               client_order_id, linked_order_id, updated_ts
        from trade_intents
        {where_sql}
        order by rowid desc
        limit ?
        """
        return _query_rows(conn, sql, tuple(params + [limit]))
    finally:
        conn.close()


def recent_paper_orders(limit: int, strategy_id: str | None, symbol: str | None) -> list[dict[str, Any]]:
    if not PAPER_DB.exists() or not INTENT_DB.exists():
        return [{"_error": "missing_db: paper_trading.sqlite or intent_queue.sqlite"}]

    paper = _connect(PAPER_DB)
    intent = _connect(INTENT_DB)
    try:
        if not _table_exists(paper, "paper_orders"):
            return [{"_error": "missing_table: paper_orders"}]
        if not _table_exists(intent, "trade_intents"):
            return [{"_error": "missing_table: trade_intents"}]

        where_sql, params = _build_where(strategy_id, symbol, alias="ti")
        sql = f"""
        select po.order_id, po.client_order_id, po.created_ts, po.ts, po.venue, po.symbol,
               po.side, po.order_type, po.qty, po.limit_price, po.status, po.reject_reason,
               ti.intent_id, ti.strategy_id, ti.source, ti.status as intent_status
        from paper_orders po
        left join trade_intents ti
          on ti.linked_order_id = po.order_id
        {where_sql}
        order by po.rowid desc
        limit ?
        """
        # sqlite cannot join across two separate connections, so copy intent table into paper conn temp db
        paper.execute("attach database ? as intent_db", (str(INTENT_DB),))
        sql = f"""
        select po.order_id, po.client_order_id, po.created_ts, po.ts, po.venue, po.symbol,
               po.side, po.order_type, po.qty, po.limit_price, po.status, po.reject_reason,
               ti.intent_id, ti.strategy_id, ti.source, ti.status as intent_status
        from paper_orders po
        left join intent_db.trade_intents ti
          on ti.linked_order_id = po.order_id
        {where_sql}
        order by po.rowid desc
        limit ?
        """
        return _query_rows(paper, sql, tuple(params + [limit]))
    finally:
        try:
            paper.execute("detach database intent_db")
        except Exception:
            pass
        paper.close()
        intent.close()


def recent_paper_fills(limit: int, strategy_id: str | None, symbol: str | None) -> list[dict[str, Any]]:
    if not PAPER_DB.exists() or not INTENT_DB.exists():
        return [{"_error": "missing_db: paper_trading.sqlite or intent_queue.sqlite"}]

    paper = _connect(PAPER_DB)
    try:
        if not _table_exists(paper, "paper_fills") or not _table_exists(paper, "paper_orders"):
            return [{"_error": "missing_table: paper_fills or paper_orders"}]

        paper.execute("attach database ? as intent_db", (str(INTENT_DB),))
        where_sql, params = _build_where(strategy_id, symbol, alias="ti")
        sql = f"""
        select pf.fill_id, pf.order_id, pf.ts, pf.price, pf.qty, pf.fee, pf.fee_currency,
               po.symbol, po.side, po.status as order_status,
               ti.intent_id, ti.strategy_id, ti.source
        from paper_fills pf
        join paper_orders po
          on po.order_id = pf.order_id
        left join intent_db.trade_intents ti
          on ti.linked_order_id = pf.order_id
        {where_sql}
        order by pf.rowid desc
        limit ?
        """
        return _query_rows(paper, sql, tuple(params + [limit]))
    finally:
        try:
            paper.execute("detach database intent_db")
        except Exception:
            pass
        paper.close()


def recent_journal_fills(limit: int, strategy_id: str | None, symbol: str | None) -> list[dict[str, Any]]:
    if not JOURNAL_DB.exists():
        return [{"_error": f"missing_db: {JOURNAL_DB}"}]
    conn = _connect(JOURNAL_DB)
    try:
        if not _table_exists(conn, "journal_fills"):
            return [{"_error": "missing_table: journal_fills"}]
        where_sql, params = _build_where(strategy_id, symbol)
        sql = f"""
        select fill_id, journal_ts, intent_id, source, strategy_id, client_order_id,
               order_id, fill_ts, venue, symbol, side, qty, price, fee, fee_currency,
               cash_quote, pos_qty, pos_avg_price, realized_pnl_total
        from journal_fills
        {where_sql}
        order by rowid desc
        limit ?
        """
        return _query_rows(conn, sql, tuple(params + [limit]))
    finally:
        conn.close()


def summary_counts() -> dict[str, Any]:
    out: dict[str, Any] = {}
    if INTENT_DB.exists():
        conn = _connect(INTENT_DB)
        try:
            if _table_exists(conn, "trade_intents"):
                out["intent_status_counts"] = _query_rows(
                    conn,
                    """
                    select status, count(*) as n
                    from trade_intents
                    group by status
                    order by n desc
                    """,
                )
                out["intent_strategy_counts"] = _query_rows(
                    conn,
                    """
                    select coalesce(strategy_id, '') as strategy_id, count(*) as n
                    from trade_intents
                    group by strategy_id
                    order by n desc
                    """,
                )
        finally:
            conn.close()

    if JOURNAL_DB.exists():
        conn = _connect(JOURNAL_DB)
        try:
            if _table_exists(conn, "journal_fills"):
                out["journal_strategy_counts"] = _query_rows(
                    conn,
                    """
                    select coalesce(strategy_id, '') as strategy_id, count(*) as n
                    from journal_fills
                    group by strategy_id
                    order by n desc
                    """,
                )
        finally:
            conn.close()
    return out


def _utc_stamp(value):
    if type(value) is not str:
        raise ValueError("invalid_utc_timestamp")
    stamp = datetime.fromisoformat(value)
    if stamp.utcoffset() != timedelta(0):
        raise ValueError("invalid_utc_timestamp")
    return stamp


def _bid_ask_input(row, stamp, assess_quote, decode):
    evidence_raw = row.pop("quote_receipt")
    row["quote"] = None
    row["bid_ask_model"] = None
    text_keys = ("fill_id", "order_id", "venue", "symbol", "side", "fee_currency")
    for key in text_keys:
        if type(row[key]) is not str or not row[key]:
            row[key] = None
    for key in ("price", "qty", "fee"):
        if type(row[key]) not in (int, float) or not math.isfinite(row[key]):
            row[key] = None
    values = row["price"], row["qty"], row["fee"]
    if (any(row[key] is None for key in text_keys) or row["side"] not in {"buy", "sell"}
            or None in values or min(values[:2]) <= 0 or values[2] < 0):
        row["reason"] = "invalid_fill"
        return row
    if evidence_raw is None:
        row["reason"] = "missing_quote_receipt"
        return row
    raw = decode(evidence_raw)
    if raw is None:
        row["reason"] = "invalid_quote_receipt"
        return row
    quote, reason = assess_quote(raw, venue=row["venue"], symbol=row["symbol"], now=stamp)
    if quote is None or raw != quote or type(raw.get("version")) is not int:
        row["reason"] = reason or "invalid_quote_receipt"
        return row
    _, separator, quote_currency = quote["symbol"].partition("/")
    if not separator or not quote_currency or quote_currency != row["fee_currency"]:
        row["reason"] = "quote_currency_unverified"
        return row
    price = quote["ask"] if row["side"] == "buy" else quote["bid"]
    notional = price * row["qty"]
    fee = notional * (EVALUATION_FEE_BPS / 10000)
    cash_flow = -notional - fee if row["side"] == "buy" else notional - fee
    if not all(math.isfinite(v) for v in (notional, fee, cash_flow)) or notional <= 0:
        row["reason"] = "invalid_modeled_cash_flow"
        return row
    row.update(reason="ok", quote=quote, bid_ask_model={
        "price": price, "fee": fee, "cash_flow_quote": cash_flow, "quote_currency": quote_currency,
    })
    return row


def _standalone_archive_identity(path):
    try:
        for suffix in ("-wal", "-shm", "-journal"):
            if os.path.lexists(str(path) + suffix):
                return None, "account_archive_has_sidecars"
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                return None, "account_database_unreadable"
            header = stream.read(20)
    except OSError:
        return None, "account_database_unreadable"
    if len(header) != 20 or not header.startswith(b"SQLite format 3\x00"):
        return None, "account_database_unreadable"
    # A detached WAL-mode main file cannot prove its committed frames were copied.
    if header[18:20] != b"\x01\x01":
        return None, "account_archive_requires_rollback_format"
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns), None


def bid_ask_inputs(paper_db: Path, start_utc: str, end_utc: str) -> dict[str, Any]:
    """Export fill inputs, not returns, using one archived account database."""
    from services.market_data.paper_snapshot_quote import assess_paper_quote
    from storage.exit_event_journal import _decode_payload

    start, end = _utc_stamp(start_utc), _utc_stamp(end_utc)
    if start >= end:
        raise ValueError("invalid_utc_window")
    result = {"status": "INCOMPLETE", "start_utc": start.isoformat(), "end_utc": end.isoformat(),
              "basis": "modeled_bid_ask_fill_inputs_only", "fee_bps_per_side": EVALUATION_FEE_BPS,
              "fills": [], "unclassified_timestamp_count": 0}
    path = paper_db.resolve()
    identity, reason = _standalone_archive_identity(path)
    if identity is None:
        return {**result, "reason": reason}
    seen_fills, seen_orders, selected = set(), set(), []
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        rows = conn.execute("""
            SELECT f.fill_id, f.order_id, f.ts, f.price, f.qty, f.fee, f.fee_currency,
                   o.venue, o.symbol, o.side, s.v AS quote_receipt
            FROM paper_fills f
            LEFT JOIN paper_orders o ON o.order_id=f.order_id
            LEFT JOIN paper_state s ON s.k='paper_fill_quote:' || f.fill_id
            ORDER BY f.rowid LIMIT ?
        """, (MAX_EVALUATION_FILLS + 1,))
        for index, row in enumerate(rows):
            if index == MAX_EVALUATION_FILLS:
                return {**result, "reason": "account_fill_budget_exceeded"}
            fill_id, order_id = row["fill_id"], row["order_id"]
            if fill_id in seen_fills or order_id in seen_orders:
                return {**result, "reason": "ambiguous_fill_associations"}
            seen_fills.add(fill_id)
            seen_orders.add(order_id)
            try:
                stamp = _utc_stamp(row["ts"])
            except (TypeError, ValueError, OverflowError):
                result["unclassified_timestamp_count"] += 1
                continue
            if start <= stamp < end:
                selected.append((dict(row), stamp))
    if _standalone_archive_identity(path)[0] != identity:
        return {**result, "reason": "account_archive_changed"}
    result["fills"] = [_bid_ask_input(row, stamp, assess_paper_quote, _decode_payload)
                       for row, stamp in selected]
    fills = result["fills"]
    fills.sort(key=lambda row: (_utc_stamp(row["ts"]), row["fill_id"] or ""))
    if result["unclassified_timestamp_count"]:
        result["reason"] = "unclassifiable_fill_timestamps"
    elif not fills:
        result["reason"] = "no_fills_in_window"
    elif any(row["reason"] != "ok" for row in fills):
        result["reason"] = "missing_or_invalid_fill_evidence"
    else:
        result.update(status="complete_fill_inputs", reason="ok")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Report paper-run diagnostics across runner/queue/fills/journal.")
    parser.add_argument("--strategy-id", default=None, help="Optional strategy_id filter")
    parser.add_argument("--symbol", default=None, help="Optional symbol filter, e.g. 2Z/USD")
    parser.add_argument("--limit", type=int, default=20, help="Number of recent rows to show per section")
    parser.add_argument("--bid-ask-inputs", action="store_true", help="Export one archived paper account as JSON")
    parser.add_argument("--paper-db", type=Path, help="Explicit standalone frozen SQLite archive (no WAL or journals)")
    parser.add_argument("--start-utc", help="Inclusive UTC ISO timestamp")
    parser.add_argument("--end-utc", help="Exclusive UTC ISO timestamp")
    args = parser.parse_args()

    if args.bid_ask_inputs:
        if (args.paper_db is None or args.start_utc is None or args.end_utc is None
                or args.strategy_id is not None or args.symbol is not None):
            parser.error("--bid-ask-inputs requires --paper-db, --start-utc and --end-utc; no filters")
        if __package__ in (None, ""):
            sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        try:
            result = bid_ask_inputs(args.paper_db, args.start_utc, args.end_utc)
        except ValueError:
            parser.error("invalid UTC window; provide ordered UTC ISO timestamps")
        except sqlite3.Error:
            result = {"status": "INCOMPLETE", "reason": "account_database_unreadable", "fills": []}
        print(json.dumps(result, allow_nan=False))
        return 0 if result["status"] == "complete_fill_inputs" else 1
    if args.paper_db is not None or args.start_utc is not None or args.end_utc is not None:
        parser.error("--paper-db, --start-utc and --end-utc require --bid-ask-inputs")

    _print_section("runner_status", latest_runner_status())
    _print_section("recent_intents", recent_intents(args.limit, args.strategy_id, args.symbol))
    _print_section("recent_paper_orders", recent_paper_orders(args.limit, args.strategy_id, args.symbol))
    _print_section("recent_paper_fills", recent_paper_fills(args.limit, args.strategy_id, args.symbol))
    _print_section("recent_journal_fills", recent_journal_fills(args.limit, args.strategy_id, args.symbol))
    _print_section("summary_counts", summary_counts())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
