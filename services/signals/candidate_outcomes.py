from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir
from services.os.file_utils import atomic_write
from services.signals.candidate_store import load_history


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _candidate_outcomes_dir() -> Path:
    path = data_dir() / "candidate_outcomes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_journal_fills(*, db_path: Path | None = None) -> list[dict[str, Any]]:
    db = Path(db_path) if db_path is not None else data_dir() / "trade_journal.sqlite"
    if not db.exists():
        return []

    fills: list[dict[str, Any]] = []
    try:
        con = sqlite3.connect(str(db), check_same_thread=False, timeout=5)
        con.row_factory = sqlite3.Row
        tables = {
            str(row[0])
            for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        for table in ("fills", "journal", "trades"):
            if table not in tables:
                continue
            rows = con.execute(f'SELECT * FROM "{table}"').fetchall()
            fills.extend(dict(row) for row in rows)
        con.close()
    except Exception:
        return []
    return fills


def _fills_for_symbol(fills: list[dict[str, Any]], symbol: str) -> list[dict[str, Any]]:
    target = str(symbol or "").strip().upper()
    return [
        fill
        for fill in fills
        if str(fill.get("symbol") or fill.get("pair") or "").strip().upper() == target
    ]


def _closed_fills(fills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    closed: list[dict[str, Any]] = []
    for fill in fills:
        side = str(fill.get("side") or "").strip().lower()
        status = str(fill.get("status") or "").strip().lower()
        if side == "sell" or status in {"closed", "filled"}:
            closed.append(fill)
    return closed


def _pnl(fill: dict[str, Any]) -> float:
    try:
        return float(fill.get("realized_pnl") or fill.get("pnl") or 0.0)
    except Exception:
        return 0.0


def _stats_from_closed(closed: list[dict[str, Any]]) -> dict[str, Any]:
    if not closed:
        return {
            "closed_trades": 0,
            "net_pnl": 0.0,
            "win_rate_pct": None,
            "avg_pnl": None,
        }

    pnls = [_pnl(fill) for fill in closed]
    wins = sum(1 for pnl in pnls if pnl > 0)
    net = sum(pnls)
    return {
        "closed_trades": len(closed),
        "net_pnl": round(net, 4),
        "win_rate_pct": round((wins / len(closed)) * 100.0, 1),
        "avg_pnl": round(net / len(closed), 4),
    }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed: list[dict[str, Any]] = []
    for row in rows:
        closed.extend(list(row.get("_closed_fills") or []))
    return _stats_from_closed(closed)


def _verdict(stats: dict[str, Any], *, rank: int) -> str:
    closed = int(stats.get("closed_trades") or 0)
    net = float(stats.get("net_pnl") or 0.0)
    win_rate = stats.get("win_rate_pct")
    if closed <= 0:
        return "no_outcome_data"
    if net > 0 and float(win_rate or 0.0) >= 50.0:
        return "positive_top_rank" if rank == 1 else "positive_non_top_rank"
    if net < 0:
        return "negative"
    return "neutral"


def build_candidate_outcome_report(
    *,
    limit: int = 30,
    since_ts: str | None = None,
    top_n: int = 3,
    db_path: Path | None = None,
) -> dict[str, Any]:
    history = load_history(limit=int(limit), since_ts=since_ts)
    fills = _load_journal_fills(db_path=db_path)

    rows: list[dict[str, Any]] = []
    for snapshot in history:
        candidates = list(snapshot.get("candidates") or [])[: int(top_n)]
        for index, candidate in enumerate(candidates):
            rank = index + 1
            symbol = str(candidate.get("symbol") or "")
            score = candidate.get("score") or candidate.get("composite_score") or 0.0
            symbol_fills = _fills_for_symbol(fills, symbol)
            closed = _closed_fills(symbol_fills)
            stats = _stats_from_closed(closed)
            rows.append(
                {
                    "scan_ts": str(snapshot.get("ts") or ""),
                    "scan_id": str(snapshot.get("scan_id") or ""),
                    "symbol": symbol,
                    "candidate_rank": rank,
                    "candidate_score": round(float(score or 0.0), 3),
                    "preferred_strategy": str(
                        candidate.get("preferred_strategy") or candidate.get("strategy") or ""
                    ),
                    "trade_type": str(candidate.get("trade_type") or ""),
                    "total_fills": len(symbol_fills),
                    **stats,
                    "verdict": _verdict(stats, rank=rank),
                    "_closed_fills": closed,
                }
            )

    top_rows = [row for row in rows if int(row.get("candidate_rank") or 0) == 1]
    non_top_rows = [row for row in rows if int(row.get("candidate_rank") or 0) > 1]
    outcome_rows = [row for row in rows if int(row.get("closed_trades") or 0) > 0]

    status = "ok"
    recommendations: list[str] = []
    if not history:
        status = "insufficient_candidate_history"
        recommendations.append("run_candidate_scan")
    elif not outcome_rows:
        status = "no_candidate_outcome_data"
        recommendations.append("continue_read_only_candidate_observation")

    clean_rows = []
    for row in rows:
        clean = dict(row)
        clean.pop("_closed_fills", None)
        clean_rows.append(clean)

    return {
        "generated_at": _now_iso(),
        "report_type": "candidate_outcomes",
        "status": status,
        "parameters": {
            "limit": int(limit),
            "since_ts": since_ts,
            "top_n": int(top_n),
        },
        "summary": {
            "snapshots_reviewed": len(history),
            "candidates_reviewed": len(rows),
            "candidates_with_outcome_data": len(outcome_rows),
            "no_outcome_count": len(rows) - len(outcome_rows),
            "insufficient_history": not bool(history),
            "top_rank": _aggregate(top_rows),
            "non_top_rank": _aggregate(non_top_rows),
            "all_with_outcomes": _aggregate(outcome_rows),
        },
        "rows": clean_rows,
        "recommendations": recommendations,
        "limitations": [
            "symbol_level_attribution_only",
            "repeated_candidate_rows_can_reference_the_same_paper_fills",
        ],
        "safety": {
            "read_only": True,
            "candidate_advisor_enabled": False,
            "orders_routed": False,
            "promotion_gate_mutated": False,
        },
    }


def write_candidate_outcome_report(report: dict[str, Any]) -> dict[str, str]:
    out_dir = _candidate_outcomes_dir()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dated = out_dir / f"candidate_outcomes_{stamp}.json"
    latest = out_dir / "candidate_outcomes.latest.json"
    text = json.dumps(report, indent=2, sort_keys=True)
    atomic_write(dated, text)
    atomic_write(latest, text)
    return {
        "latest": str(latest),
        "dated": str(dated),
    }
