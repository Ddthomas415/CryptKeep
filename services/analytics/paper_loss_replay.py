from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from services.analytics.journal_analytics import fifo_pnl_from_fills
from services.backtest.evidence_cycle import default_trade_journal_path
from services.market_data.ohlcv_fetcher import fetch_ohlcv


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


def _ts_ms(value: Any) -> int | None:
    parsed = _parse_ts(value)
    if parsed is None:
        return None
    return int(parsed.timestamp() * 1000.0)


def _timeframe_ms(timeframe: str) -> int | None:
    text = str(timeframe or "").strip().lower()
    if len(text) < 2:
        return None
    unit = text[-1]
    try:
        amount = int(text[:-1])
    except Exception:
        return None
    multipliers = {
        "m": 60_000,
        "h": 3_600_000,
        "d": 86_400_000,
    }
    base = multipliers.get(unit)
    if base is None or amount <= 0:
        return None
    return int(amount * base)


def _find_row_index(rows: list[list], target_ms: int) -> int | None:
    if not rows:
        return None
    for idx, row in enumerate(rows):
        try:
            if int(row[0]) >= int(target_ms):
                return idx
        except Exception:
            continue
    return len(rows) - 1


def _slice_rows(rows: list[list], center_idx: int | None, context_bars: int) -> list[list]:
    if center_idx is None or not rows:
        return []
    start = max(0, int(center_idx) - int(context_bars))
    end = min(len(rows), int(center_idx) + int(context_bars) + 1)
    return rows[start:end]


def _build_ohlcv_context(
    *,
    trade: dict[str, Any],
    timeframe: str,
    context_bars: int,
    ohlcv_fetcher: Any,
) -> dict[str, Any] | None:
    symbol = str(trade.get("symbol") or "").strip()
    venue = str(trade.get("entry_venue") or trade.get("exit_venue") or trade.get("venue") or "").strip()
    if not symbol or not venue:
        return None
    bar_ms = _timeframe_ms(timeframe)
    entry_ms = _ts_ms(trade.get("entry_ts"))
    exit_ms = _ts_ms(trade.get("exit_ts"))
    if bar_ms is None or entry_ms is None or exit_ms is None:
        return None
    before_bars = max(int(context_bars), 0)
    trade_bars = max(int((max(exit_ms, entry_ms) - entry_ms) / bar_ms), 0)
    limit = max((before_bars * 2) + trade_bars + 3, 5)
    since_ms = max(entry_ms - (before_bars * bar_ms), 0)
    try:
        rows = list(
            ohlcv_fetcher(
                venue,
                symbol,
                timeframe=str(timeframe),
                limit=int(limit),
                since_ms=int(since_ms),
            )
            or []
        )
    except Exception as exc:
        return {
            "ok": False,
            "venue": venue,
            "symbol": symbol,
            "timeframe": str(timeframe),
            "context_bars": int(before_bars),
            "error": str(exc),
        }
    entry_idx = _find_row_index(rows, entry_ms)
    exit_idx = _find_row_index(rows, exit_ms)
    return {
        "ok": True,
        "venue": venue,
        "symbol": symbol,
        "timeframe": str(timeframe),
        "context_bars": int(before_bars),
        "since_ms": int(since_ms),
        "fetched_count": int(len(rows)),
        "entry_bar_index": entry_idx,
        "exit_bar_index": exit_idx,
        "entry_window": _slice_rows(rows, entry_idx, before_bars),
        "exit_window": _slice_rows(rows, exit_idx, before_bars),
    }


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
    timeframe: str = "",
    context_bars: int = 3,
    ohlcv_fetcher: Any = fetch_ohlcv,
) -> dict[str, Any]:
    fills = load_journal_fills(journal_path=journal_path, strategy_id=strategy_id, symbol=symbol)
    analytics = fifo_pnl_from_fills(fills)
    closed_trades = [dict(item) for item in list(analytics.get("closed_trades") or [])]
    symbol_venue_map: dict[str, str] = {}
    for fill in fills:
        fill_symbol = str(fill.get("symbol") or "").strip()
        fill_venue = str(fill.get("venue") or "").strip()
        if fill_symbol and fill_venue and fill_symbol not in symbol_venue_map:
            symbol_venue_map[fill_symbol] = fill_venue
    replay_rows: list[dict[str, Any]] = []
    for trade in closed_trades:
        gross_pnl = float(trade.get("pnl") or 0.0)
        fees = float(trade.get("fees") or 0.0)
        net_pnl = gross_pnl - fees
        if net_pnl >= 0.0:
            continue
        row = {
            "strategy_id": str(strategy_id or "").strip(),
            "symbol": str(trade.get("symbol") or ""),
            "venue": str(symbol_venue_map.get(str(trade.get("symbol") or "").strip()) or ""),
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
        if str(timeframe or "").strip():
            row["ohlcv_context"] = _build_ohlcv_context(
                trade=row,
                timeframe=str(timeframe).strip(),
                context_bars=int(context_bars),
                ohlcv_fetcher=ohlcv_fetcher,
            )
        replay_rows.append(row)
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
        "timeframe": str(timeframe).strip() or None,
        "context_bars": None if not str(timeframe or "").strip() else int(context_bars),
        "summary": dict(analytics.get("summary") or {}),
        "loss_replays": limited_rows,
    }
