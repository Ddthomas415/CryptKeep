#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(".")
STATE_DIR = ROOT / ".cbp_state"
DATA_DIR = STATE_DIR / "data"
RUNTIME_DIR = STATE_DIR / "runtime" / "flags"

STATUS_FILE = RUNTIME_DIR / "strategy_runner.status.json"
INTENT_DB = DATA_DIR / "intent_queue.sqlite"
PAPER_DB = DATA_DIR / "paper_trading.sqlite"
JOURNAL_DB = DATA_DIR / "trade_journal.sqlite"


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Report paper-run diagnostics across runner/queue/fills/journal.")
    parser.add_argument("--strategy-id", default=None, help="Optional strategy_id filter")
    parser.add_argument("--symbol", default=None, help="Optional symbol filter, e.g. 2Z/USD")
    parser.add_argument("--limit", type=int, default=20, help="Number of recent rows to show per section")
    args = parser.parse_args()

    _print_section("runner_status", latest_runner_status())
    _print_section("recent_intents", recent_intents(args.limit, args.strategy_id, args.symbol))
    _print_section("recent_paper_orders", recent_paper_orders(args.limit, args.strategy_id, args.symbol))
    _print_section("recent_paper_fills", recent_paper_fills(args.limit, args.strategy_id, args.symbol))
    _print_section("recent_journal_fills", recent_journal_fills(args.limit, args.strategy_id, args.symbol))
    _print_section("summary_counts", summary_counts())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
