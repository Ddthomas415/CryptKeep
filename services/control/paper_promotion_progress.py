from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from services.analytics.strategy_feedback import load_strategy_feedback_ledger
from services.control.promotion_thresholds import (
    ES_DAILY_TREND_STRATEGY_ID,
    ES_DAILY_TREND_TARGET_STRATEGY,
    PAPER_MIN_DAYS,
    PAPER_MIN_ROUND_TRIPS,
)
from services.control.retirement_checker import load_all_evidence
from services.os.app_paths import data_dir

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "strategies" / "es_daily_trend_v1.yaml"


def _session_ts(row: dict[str, Any]) -> datetime | None:
    raw = row.get("timestamp") or row.get("date") or row.get("session_start")
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _days_of_operation(sessions: list[dict[str, Any]]) -> int:
    dates = {
        parsed.date()
        for row in list(sessions or [])
        if (parsed := _session_ts(dict(row))) is not None
    }
    return int(len(dates))


def _config_symbol(path: Path = DEFAULT_CONFIG_PATH) -> str:
    if not path.exists():
        return ""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return ""
    strategy = payload.get("strategy") if isinstance(payload.get("strategy"), dict) else {}
    return str(strategy.get("symbol") or "").strip()


def _feedback_row(*, ledger: dict[str, Any], target_strategy: str) -> dict[str, Any]:
    rows = [dict(row) for row in list(ledger.get("rows") or []) if isinstance(row, dict)]
    return next((row for row in rows if str(row.get("strategy") or "") == str(target_strategy)), {})


def _threshold_state(*, observed: int, required: int) -> str:
    if observed <= 0:
        return "unknown"
    if observed >= required:
        return "pass"
    return "fail"


def _blocker(*, label: str, observed: int, required: int, remaining: int, state: str) -> dict[str, Any]:
    return {
        "label": label,
        "state": state,
        "observed": int(observed),
        "required": int(required),
        "remaining": int(remaining),
    }


def load_paper_promotion_progress(
    *,
    strategy_id: str = ES_DAILY_TREND_STRATEGY_ID,
    target_strategy: str = ES_DAILY_TREND_TARGET_STRATEGY,
    symbol: str = "",
) -> dict[str, Any]:
    resolved_strategy_id = str(strategy_id or ES_DAILY_TREND_STRATEGY_ID).strip()
    resolved_target_strategy = str(target_strategy or ES_DAILY_TREND_TARGET_STRATEGY).strip()
    symbol_filter = str(symbol or _config_symbol()).strip()

    ev_dir = data_dir() / "evidence" / resolved_strategy_id
    evidence = load_all_evidence(ev_dir)
    sessions = [dict(row) for row in list(evidence.get("session") or []) if isinstance(row, dict)]
    days_recorded = _days_of_operation(sessions)
    days_remaining = max(0, PAPER_MIN_DAYS - days_recorded)
    days_state = _threshold_state(observed=days_recorded, required=PAPER_MIN_DAYS)

    ledger = load_strategy_feedback_ledger(symbol=symbol_filter)
    row = _feedback_row(ledger=dict(ledger or {}), target_strategy=resolved_target_strategy)
    round_trips_recorded = int(row.get("closed_trades") or 0)
    round_trips_remaining = max(0, PAPER_MIN_ROUND_TRIPS - round_trips_recorded)
    round_trips_state = _threshold_state(
        observed=round_trips_recorded,
        required=PAPER_MIN_ROUND_TRIPS,
    )

    blockers: list[dict[str, Any]] = []
    if days_state != "pass":
        blockers.append(
            _blocker(
                label="30 calendar days of operation",
                observed=days_recorded,
                required=PAPER_MIN_DAYS,
                remaining=days_remaining,
                state=days_state,
            )
        )
    if round_trips_state != "pass":
        blockers.append(
            _blocker(
                label="50+ completed round trips",
                observed=round_trips_recorded,
                required=PAPER_MIN_ROUND_TRIPS,
                remaining=round_trips_remaining,
                state=round_trips_state,
            )
        )

    summary_text = (
        "Promotion threshold progress: "
        f"{days_recorded}/{PAPER_MIN_DAYS} days recorded ({days_remaining} remaining), "
        f"{round_trips_recorded}/{PAPER_MIN_ROUND_TRIPS} round trips recorded "
        f"({round_trips_remaining} remaining)."
    )
    if not blockers:
        summary_text = "Promotion threshold progress: paper-stage day and round-trip thresholds are met."

    return {
        "ok": True,
        "source": "paper_promotion_progress",
        "strategy_id": resolved_strategy_id,
        "target_strategy": resolved_target_strategy,
        "symbol_filter": symbol_filter or None,
        "evidence_dir": str(ev_dir),
        "days_recorded": days_recorded,
        "days_required": PAPER_MIN_DAYS,
        "days_remaining": days_remaining,
        "days_state": days_state,
        "round_trips_recorded": round_trips_recorded,
        "round_trips_required": PAPER_MIN_ROUND_TRIPS,
        "round_trips_remaining": round_trips_remaining,
        "round_trips_state": round_trips_state,
        "thresholds_ready": not blockers,
        "blocking_thresholds": blockers,
        "fills": int(row.get("fills") or 0),
        "net_realized_pnl": row.get("net_realized_pnl"),
        "expectancy_per_closed_trade": row.get("expectancy_per_closed_trade"),
        "latest_fill_ts": row.get("latest_fill_ts"),
        "ledger_status": str(ledger.get("status") or "missing"),
        "ledger_source": str(ledger.get("source") or "trade_journal_sqlite"),
        "journal_path": str(ledger.get("journal_path") or ""),
        "summary_text": summary_text,
    }
