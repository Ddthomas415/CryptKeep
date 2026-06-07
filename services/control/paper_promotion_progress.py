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
from services.control.paper_evidence_qualification import qualify_paper_history
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


def _qualification_explanation(
    *,
    qualification: dict[str, Any],
    qualified_round_trips: int,
    all_history_round_trips: int,
) -> dict[str, Any]:
    evidence_fills = int(qualification.get("evidence_fills") or 0)
    unqualified_fills = int(qualification.get("unqualified_evidence_fills") or 0)
    incomplete_fills = int(qualification.get("incomplete_qualified_evidence_fills") or 0)
    missing_journal_order_ids = [
        str(value)
        for value in list(qualification.get("missing_journal_order_ids") or [])
        if str(value).strip()
    ]
    excluded_round_trips = max(0, int(all_history_round_trips) - int(qualified_round_trips))

    clauses: list[str] = []
    if excluded_round_trips:
        noun = "round trip is" if excluded_round_trips == 1 else "round trips are"
        count_verb = "does" if excluded_round_trips == 1 else "do"
        clauses.append(
            f"{excluded_round_trips} all-history {noun} diagnostic only and "
            f"{count_verb} not count toward promotion"
        )
    if evidence_fills <= 0 and excluded_round_trips:
        clauses.append("no JSONL evidence fills are available for provenance qualification")
    elif unqualified_fills:
        clauses.append(
            f"{unqualified_fills}/{evidence_fills} evidence fills lack or mismatch "
            "required provenance"
        )
    if incomplete_fills:
        noun = "fill is" if incomplete_fills == 1 else "fills are"
        clauses.append(
            f"{incomplete_fills} provenance-qualified evidence {noun} not part of a "
            "complete qualified round trip"
        )
    if missing_journal_order_ids:
        noun = "order ID is" if len(missing_journal_order_ids) == 1 else "order IDs are"
        clauses.append(
            f"{len(missing_journal_order_ids)} qualified evidence {noun} missing from "
            "the persisted trade journal"
        )

    if clauses:
        explanation_text = "; ".join(clauses) + "."
    else:
        explanation_text = (
            "No completed all-history round trips are currently excluded by the "
            "promotion provenance contract."
        )

    return {
        "has_excluded_history": bool(excluded_round_trips),
        "excluded_all_history_round_trips": excluded_round_trips,
        "evidence_fills": evidence_fills,
        "unqualified_evidence_fills": unqualified_fills,
        "incomplete_qualified_evidence_fills": incomplete_fills,
        "missing_journal_order_ids": missing_journal_order_ids,
        "summary_text": explanation_text,
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
    qualified = qualify_paper_history(
        evidence_fills=[
            dict(item)
            for item in list(evidence.get("fill") or [])
            if isinstance(item, dict)
        ],
        config=(
            yaml.safe_load(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8")) or {}
            if DEFAULT_CONFIG_PATH.exists()
            else {}
        ),
        journal_path=str(ledger.get("journal_path") or ""),
    )
    round_trips_recorded = int(qualified.get("closed_trades") or 0)
    round_trips_remaining = max(0, PAPER_MIN_ROUND_TRIPS - round_trips_recorded)
    round_trips_state = _threshold_state(
        observed=round_trips_recorded,
        required=PAPER_MIN_ROUND_TRIPS,
    )
    qualification = dict(qualified.get("qualification") or {})
    all_history_fills = int(row.get("fills") or 0)
    all_history_round_trips = int(row.get("closed_trades") or 0)
    qualification_explanation = _qualification_explanation(
        qualification=qualification,
        qualified_round_trips=round_trips_recorded,
        all_history_round_trips=all_history_round_trips,
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
                label=f"{PAPER_MIN_ROUND_TRIPS}+ completed round trips",
                observed=round_trips_recorded,
                required=PAPER_MIN_ROUND_TRIPS,
                remaining=round_trips_remaining,
                state=round_trips_state,
            )
        )

    summary_text = (
        "Promotion threshold progress: "
        f"{days_recorded}/{PAPER_MIN_DAYS} days recorded ({days_remaining} remaining), "
        f"{round_trips_recorded}/{PAPER_MIN_ROUND_TRIPS} qualified round trips recorded "
        f"({round_trips_remaining} remaining)."
    )
    if not blockers:
        summary_text = "Promotion threshold progress: paper-stage day and round-trip thresholds are met."
    if (
        qualification_explanation["has_excluded_history"]
        or qualification_explanation["unqualified_evidence_fills"]
        or qualification_explanation["incomplete_qualified_evidence_fills"]
        or qualification_explanation["missing_journal_order_ids"]
    ):
        summary_text = f"{summary_text} {qualification_explanation['summary_text']}"

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
        "fills": int(qualified.get("fills") or 0),
        "net_realized_pnl": qualified.get("net_realized_pnl"),
        "expectancy_per_closed_trade": qualified.get("expectancy_per_closed_trade"),
        "latest_fill_ts": qualified.get("latest_fill_ts"),
        "qualification": qualification,
        "qualification_explanation": qualification_explanation,
        "all_history_fills": all_history_fills,
        "all_history_round_trips": all_history_round_trips,
        "ledger_status": str(ledger.get("status") or "missing"),
        "ledger_source": str(ledger.get("source") or "trade_journal_sqlite"),
        "journal_path": str(ledger.get("journal_path") or ""),
        "summary_text": summary_text,
    }
