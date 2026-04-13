from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from statistics import pstdev
from typing import Any, Dict, Iterable, List

from services.analytics.journal_analytics import fifo_pnl_from_fills
from services.analytics.strategy_feedback import (
    build_strategy_feedback_weighting,
    load_strategy_feedback_ledger,
)
from services.backtest.leaderboard import rank_strategy_rows, run_strategy_leaderboard
from services.backtest.walk_forward import run_anchored_walk_forward
from services.os.app_paths import code_root, data_dir, ensure_dirs
from services.strategies.presets import apply_preset
from services.strategies.hypotheses import get_strategy_hypothesis


from services.backtest.evidence_shared import (
    default_trade_journal_path,
    _normalize_strategy_name,
)

def load_paper_history_evidence(*, journal_path: str = "", symbol: str = "") -> dict[str, Any]:
    path = Path(journal_path).expanduser().resolve() if journal_path else default_trade_journal_path()
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
            "caveat": "No persisted trade journal exists yet, so strategy-attributed paper-history evidence is unavailable.",
        }

    try:
        con = sqlite3.connect(str(path))
        con.row_factory = sqlite3.Row
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
            "caveat": f"Persisted trade journal could not be opened ({type(exc).__name__}); strategy-attributed paper-history evidence is unavailable.",
        }

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
                "caveat": "Persisted trade journal exists but has no journal_fills table yet, so strategy-attributed paper-history evidence is unavailable.",
            }

        rows = con.execute(
            "SELECT fill_id, journal_ts, strategy_id, fill_ts, symbol, side, qty, price, fee, realized_pnl_total "
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
            "caveat": f"Persisted trade journal could not be read ({type(exc).__name__}); strategy-attributed paper-history evidence is unavailable.",
        }
    finally:
        con.close()

    grouped: dict[str, list[dict[str, Any]]] = {}
    strategy_ids_by_name: dict[str, set[str]] = {}
    unmapped: set[str] = set()
    latest_ts: str | None = None

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
        strategy_ids_by_name.setdefault(strategy_name, set()).add(raw_strategy_id)

    if not grouped:
        caveat = "Persisted trade journal has no strategy-attributed paper-history fills yet."
        if unmapped:
            caveat = (
                caveat
                + f" Unmapped strategy IDs were present: {', '.join(sorted(unmapped)[:5])}."
            )
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

    summary_rows: list[dict[str, Any]] = []
    total_fills = 0
    for strategy_name, fills in grouped.items():
        analytics = fifo_pnl_from_fills(fills)
        summary = dict(analytics.get("summary") or {})
        total_fills += len(fills)
        latest_fill_ts = str(fills[-1].get("fill_ts") or fills[-1].get("journal_ts") or "")
        summary_rows.append(
            {
                "strategy": strategy_name,
                "source_strategy_ids": sorted(strategy_ids_by_name.get(strategy_name) or []),
                "fills": int(len(fills)),
                "closed_trades": int(summary.get("closed_trades") or 0),
                "wins": int(summary.get("wins") or 0),
                "losses": int(summary.get("losses") or 0),
                "win_rate": float(summary.get("win_rate") or 0.0),
                "gross_realized_pnl": float(summary.get("gross_realized_pnl") or 0.0),
                "net_realized_pnl": float(summary.get("net_realized_pnl") or 0.0),
                "total_fees": float(summary.get("total_fees") or 0.0),
                "latest_fill_ts": latest_fill_ts or None,
            }
        )
    summary_rows.sort(key=lambda item: (-int(item.get("fills") or 0), str(item.get("strategy") or "")))

    caveat = "Persisted paper-history evidence is supplemental. It improves operator truth, but it is not enough by itself to prove profitability or promotion readiness."
    if unmapped:
        caveat += f" Unmapped strategy IDs were ignored: {', '.join(sorted(unmapped)[:5])}."
    if symbol_filter:
        caveat += f" Current summary is filtered to persisted paper-history fills for `{symbol_filter}` only."
    return {
        "ok": True,
        "status": "available",
        "journal_path": str(path),
        "symbol_filter": symbol_filter or None,
        "source": "trade_journal_sqlite",
        "as_of": latest_ts,
        "fills_count": int(total_fills),
        "strategy_count": int(len(summary_rows)),
        "rows": summary_rows,
        "unmapped_strategy_ids": sorted(unmapped),
        "caveat": caveat,
    }


