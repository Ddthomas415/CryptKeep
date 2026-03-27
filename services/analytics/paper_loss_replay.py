from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from services.analytics.journal_analytics import fifo_pnl_from_fills
from services.backtest.evidence_cycle import default_trade_journal_path


def _parse_ts(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def _duration_seconds(entry_ts: Any, exit_ts: Any) -> float | None:
    start = _parse_ts(entry_ts)
    end = _parse_ts(exit_ts)
    if start is None or end is None:
        return None
    return float((end - start).total_seconds())


def load_journal_fills(*, journal_path: str = "", strategy_id: str = "", symbol: str = "") -> list[dict[str, Any]]:
    path = Path(journal_path).expanduser().resolve() if journal_path else default_trade_journal_path()
    if not path.exists():
        return []
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    try:
        table = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_fills'").fetchone()
        if not table:
            return []
        clauses: list[str] = []
        params: list[Any] = []
        if str(strategy_id or "").strip():
            clauses.append("strategy_id = ?")
            params.append(str(strategy_id).strip())
        if str(symbol or "").strip():
            clauses.append("symbol = ?")
            params.append(str(symbol).strip())
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = con.execute(
            "SELECT fill_id, journal_ts, intent_id, source, strategy_id, client_order_id, "
            "order_id, fill_ts, venue, symbol, side, qty, price, fee, fee_currency, "
            "cash_quote, pos_qty, pos_avg_price, realized_pnl_total "
            f"FROM journal_fills{where} ORDER BY fill_ts ASC",
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def build_loss_replay(
    *,
    strategy_id: str,
    symbol: str = "",
    journal_path: str = "",
    limit: int = 10,
) -> dict[str, Any]:
    fills = load_journal_fills(journal_path=journal_path, strategy_id=strategy_id, symbol=symbol)
    analytics = fifo_pnl_from_fills(fills)
    closed_trades = [dict(item) for item in list(analytics.get("closed_trades") or [])]
    replay_rows: list[dict[str, Any]] = []
    for trade in closed_trades:
        gross_pnl = float(trade.get("pnl") or 0.0)
        fees = float(trade.get("fees") or 0.0)
        net_pnl = gross_pnl - fees
        if net_pnl >= 0.0:
            continue
        replay_rows.append(
            {
                "strategy_id": str(strategy_id or "").strip(),
                "symbol": str(trade.get("symbol") or ""),
                "entry_ts": str(trade.get("entry_ts") or ""),
                "exit_ts": str(trade.get("exit_ts") or ""),
                "duration_sec": _duration_seconds(trade.get("entry_ts"), trade.get("exit_ts")),
                "qty": float(trade.get("qty") or 0.0),
                "entry_price": float(trade.get("entry_price") or 0.0),
                "exit_price": float(trade.get("exit_price") or 0.0),
                "gross_pnl": gross_pnl,
                "fees": fees,
                "net_pnl": net_pnl,
            }
        )
    replay_rows.sort(key=lambda row: str(row.get("exit_ts") or ""), reverse=True)
    limited_rows = replay_rows[: max(0, int(limit))]
    symbols = sorted({str(row.get("symbol") or "") for row in closed_trades if str(row.get("symbol") or "").strip()})
    return {
        "ok": True,
        "strategy_id": str(strategy_id or "").strip(),
        "symbol_filter": str(symbol or "").strip() or None,
        "journal_path": str(Path(journal_path).expanduser().resolve() if journal_path else default_trade_journal_path()),
        "fills_count": int(len(fills)),
        "closed_trade_count": int(len(closed_trades)),
        "losing_trade_count": int(len(replay_rows)),
        "symbols": symbols,
        "summary": dict(analytics.get("summary") or {}),
        "loss_replays": limited_rows,
    }
