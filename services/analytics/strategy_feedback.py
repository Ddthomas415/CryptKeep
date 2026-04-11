from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from services.analytics.journal_analytics import fifo_pnl_from_fills
from services.os.app_paths import data_dir, ensure_dirs

STRATEGY_FEEDBACK_MIN_CLOSED_TRADES = 3
STRATEGY_FEEDBACK_FULL_SAMPLE_CLOSED_TRADES = 20
STRATEGY_FEEDBACK_MAX_BOOST = 0.05
STRATEGY_FEEDBACK_MAX_PENALTY = 0.08


def _trade_journal_path() -> Path:
    ensure_dirs()
    return (data_dir() / "trade_journal.sqlite").resolve()


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _normalize_strategy_name(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    if text in {"ema_cross", "mean_reversion_rsi", "breakout_donchian"}:
        return text
    if "ema" in text and ("cross" in text or "xover" in text or "crossover" in text):
        return "ema_cross"
    if "mean_reversion" in text or "mean-reversion" in text or "reversion" in text:
        return "mean_reversion_rsi"
    if "breakout" in text or "donchian" in text:
        return "breakout_donchian"
    return None


def _closed_trade_drawdown_quote(closed_trades: list[dict[str, Any]]) -> float:
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for trade in list(closed_trades or []):
        cumulative += _fnum(trade.get("pnl"), 0.0) - _fnum(trade.get("fees"), 0.0)
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, peak - cumulative)
    return float(max_drawdown)


def _summary_for_fills(*, strategy: str, fills: list[dict[str, Any]]) -> dict[str, Any]:
    analytics = fifo_pnl_from_fills(fills)
    summary = dict(analytics.get("summary") or {})
    closed_trades = [dict(item) for item in list(analytics.get("closed_trades") or []) if isinstance(item, dict)]
    wins = [item for item in closed_trades if (_fnum(item.get("pnl"), 0.0) - _fnum(item.get("fees"), 0.0)) > 0.0]
    losses = [item for item in closed_trades if (_fnum(item.get("pnl"), 0.0) - _fnum(item.get("fees"), 0.0)) < 0.0]
    recent = closed_trades[-min(5, len(closed_trades)) :] if closed_trades else []
    recent_net = float(sum(_fnum(item.get("pnl"), 0.0) - _fnum(item.get("fees"), 0.0) for item in recent))
    recent_wins = sum(1 for item in recent if (_fnum(item.get("pnl"), 0.0) - _fnum(item.get("fees"), 0.0)) > 0.0)
    venues = sorted({str(item.get("venue") or "").strip() for item in fills if str(item.get("venue") or "").strip()})
    latest_fill_ts = str(fills[-1].get("fill_ts") or fills[-1].get("journal_ts") or "") if fills else ""
    closed_trade_count = int(summary.get("closed_trades") or 0)
    expectancy = float((_fnum(summary.get("net_realized_pnl"), 0.0) / closed_trade_count) if closed_trade_count > 0 else 0.0)
    avg_win = float(sum((_fnum(item.get("pnl"), 0.0) - _fnum(item.get("fees"), 0.0)) for item in wins) / len(wins)) if wins else 0.0
    avg_loss = float(sum((_fnum(item.get("pnl"), 0.0) - _fnum(item.get("fees"), 0.0)) for item in losses) / len(losses)) if losses else 0.0
    return {
        "strategy": str(strategy or ""),
        "fills": int(len(fills)),
        "closed_trades": closed_trade_count,
        "wins": int(summary.get("wins") or 0),
        "losses": int(summary.get("losses") or 0),
        "win_rate": float(summary.get("win_rate") or 0.0),
        "gross_realized_pnl": float(summary.get("gross_realized_pnl") or 0.0),
        "net_realized_pnl": float(summary.get("net_realized_pnl") or 0.0),
        "total_fees": float(summary.get("total_fees") or 0.0),
        "expectancy_per_closed_trade": expectancy,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "recent_closed_trades": int(len(recent)),
        "recent_net_realized_pnl": recent_net,
        "recent_win_rate": float((recent_wins / len(recent)) if recent else 0.0),
        "max_closed_trade_drawdown_quote": float(_closed_trade_drawdown_quote(closed_trades)),
        "venue_count": int(len(venues)),
        "venues": venues,
        "latest_fill_ts": latest_fill_ts or None,
        "summary_text": (
            f"{closed_trade_count} closed trade(s), "
            f"{_fnum(summary.get('net_realized_pnl'), 0.0):+.2f} net realized PnL, "
            f"{expectancy:+.2f} expectancy per closed trade, "
            f"{float(summary.get('win_rate') or 0.0) * 100.0:.1f}% win rate."
        ),
    }


def load_strategy_feedback_ledger(*, journal_path: str = "", symbol: str = "") -> dict[str, Any]:
    path = Path(journal_path).expanduser().resolve() if journal_path else _trade_journal_path()
    symbol_filter = str(symbol or "").strip()
    if not path.exists():
        return {
            "ok": False,
            "status": "missing",
            "journal_path": str(path),
            "symbol_filter": symbol_filter or None,
            "source": "trade_journal_sqlite",
            "as_of": None,
            "fills_count": 0,
            "strategy_count": 0,
            "rows": [],
            "unmapped_strategy_ids": [],
            "caveat": "No persisted trade journal exists yet, so strategy feedback is unavailable.",
        }

    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    try:
        table = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='journal_fills'"
        ).fetchone()
        if not table:
            return {
                "ok": False,
                "status": "missing",
                "journal_path": str(path),
                "symbol_filter": symbol_filter or None,
                "source": "trade_journal_sqlite",
                "as_of": None,
                "fills_count": 0,
                "strategy_count": 0,
                "rows": [],
                "unmapped_strategy_ids": [],
                "caveat": "Persisted trade journal exists but has no journal_fills table yet, so strategy feedback is unavailable.",
            }

        rows = con.execute(
            "SELECT fill_id, journal_ts, strategy_id, fill_ts, venue, symbol, side, qty, price, fee, fee_currency "
            "FROM journal_fills ORDER BY fill_ts ASC"
        ).fetchall()
    except Exception as exc:
        return {
            "ok": False,
            "status": "missing",
            "journal_path": str(path),
            "symbol_filter": symbol_filter or None,
            "source": "trade_journal_sqlite",
            "as_of": None,
            "fills_count": 0,
            "strategy_count": 0,
            "rows": [],
            "unmapped_strategy_ids": [],
            "caveat": f"Persisted trade journal could not be read ({type(exc).__name__}); strategy feedback is unavailable.",
        }
    finally:
        con.close()

    grouped: dict[str, list[dict[str, Any]]] = {}
    latest_ts: str | None = None
    unmapped: set[str] = set()
    total_fills = 0
    for row in rows:
        item = dict(row)
        latest_ts = str(item.get("fill_ts") or item.get("journal_ts") or latest_ts or "") or latest_ts
        item_symbol = str(item.get("symbol") or "").strip()
        if symbol_filter and item_symbol != symbol_filter:
            continue
        raw_strategy_id = str(item.get("strategy_id") or "").strip()
        strategy_name = _normalize_strategy_name(raw_strategy_id)
        if strategy_name is None:
            if raw_strategy_id:
                unmapped.add(raw_strategy_id)
            continue
        grouped.setdefault(strategy_name, []).append(item)
        total_fills += 1

    if not grouped:
        caveat = "Persisted trade journal has no strategy-attributed fills available for feedback yet."
        if unmapped:
            caveat += f" Unmapped strategy IDs were ignored: {', '.join(sorted(unmapped)[:5])}."
        return {
            "ok": False,
            "status": "missing",
            "journal_path": str(path),
            "symbol_filter": symbol_filter or None,
            "source": "trade_journal_sqlite",
            "as_of": latest_ts,
            "fills_count": 0,
            "strategy_count": 0,
            "rows": [],
            "unmapped_strategy_ids": sorted(unmapped),
            "caveat": caveat,
        }

    summaries = [_summary_for_fills(strategy=strategy, fills=fills) for strategy, fills in grouped.items()]
    summaries.sort(key=lambda item: (-int(item.get("closed_trades") or 0), str(item.get("strategy") or "")))
    return {
        "ok": True,
        "status": "available",
        "journal_path": str(path),
        "symbol_filter": symbol_filter or None,
        "source": "trade_journal_sqlite",
        "as_of": latest_ts,
        "fills_count": int(total_fills),
        "strategy_count": int(len(summaries)),
        "rows": summaries,
        "unmapped_strategy_ids": sorted(unmapped),
        "caveat": (
            "Strategy feedback is descriptive research metadata from persisted paper fills. "
            "It is not live-sizing authority and it does not prove profitability by itself."
        ),
    }


def build_strategy_feedback_weighting(feedback_row: dict[str, Any] | None) -> dict[str, Any]:
    row = dict(feedback_row or {})
    closed_trades = int(row.get("closed_trades") or 0)
    if not row:
        return {
            "status": "missing",
            "adjustment": 0.0,
            "summary": "No persisted strategy feedback row is available yet.",
            "closed_trades": 0,
            "sample_ratio": 0.0,
        }
    if closed_trades < STRATEGY_FEEDBACK_MIN_CLOSED_TRADES:
        return {
            "status": "thin",
            "adjustment": 0.0,
            "summary": (
                f"Persisted strategy feedback remains thin at {closed_trades} closed trade(s); "
                "no leaderboard weighting adjustment is applied yet."
            ),
            "closed_trades": int(closed_trades),
            "sample_ratio": min(float(closed_trades) / float(STRATEGY_FEEDBACK_FULL_SAMPLE_CLOSED_TRADES), 1.0),
        }

    sample_ratio = min(float(closed_trades) / float(STRATEGY_FEEDBACK_FULL_SAMPLE_CLOSED_TRADES), 1.0)
    expectancy = _fnum(row.get("expectancy_per_closed_trade"), 0.0)
    net_realized_pnl = _fnum(row.get("net_realized_pnl"), 0.0)
    recent_net_realized_pnl = _fnum(row.get("recent_net_realized_pnl"), 0.0)
    win_rate = _fnum(row.get("win_rate"), 0.0)

    if expectancy <= 0.0 or net_realized_pnl <= 0.0 or recent_net_realized_pnl < 0.0:
        adjustment = -float(STRATEGY_FEEDBACK_MAX_PENALTY) * sample_ratio
        return {
            "status": "penalty",
            "adjustment": float(adjustment),
            "summary": (
                f"Persisted paper feedback is negative or fragile for this strategy "
                f"({expectancy:+.2f} expectancy, {net_realized_pnl:+.2f} net realized PnL), "
                "so the research leaderboard applies a conservative penalty."
            ),
            "closed_trades": int(closed_trades),
            "sample_ratio": float(sample_ratio),
        }

    if win_rate >= 0.5 and expectancy > 0.0 and net_realized_pnl > 0.0:
        adjustment = float(STRATEGY_FEEDBACK_MAX_BOOST) * sample_ratio
        return {
            "status": "boost",
            "adjustment": float(adjustment),
            "summary": (
                f"Persisted paper feedback is positive for this strategy "
                f"({expectancy:+.2f} expectancy, {win_rate * 100.0:.1f}% win rate), "
                "so the research leaderboard applies a small boost."
            ),
            "closed_trades": int(closed_trades),
            "sample_ratio": float(sample_ratio),
        }

    return {
        "status": "neutral",
        "adjustment": 0.0,
        "summary": "Persisted paper feedback is mixed, so no leaderboard weighting adjustment is applied.",
        "closed_trades": int(closed_trades),
        "sample_ratio": float(sample_ratio),
    }
