from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from services.analytics.strategy_feedback import load_strategy_feedback_ledger
from services.control.paper_evidence_qualification import (
    _expected_contract,
    _fill_rejection_reasons,
    _record_ts,
    qualify_paper_history,
)
from services.control.paper_promotion_policy import (
    before_policy_cohort,
    record_timestamp,
    resolve_paper_promotion_policy,
)
from services.control.promotion_thresholds import (
    ES_DAILY_TREND_STRATEGY_ID,
    ES_DAILY_TREND_TARGET_STRATEGY,
)
from services.control.retirement_checker import load_all_evidence
from services.os.app_paths import data_dir

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "strategies" / "es_daily_trend_v1.yaml"


def _load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _config_symbol(config: dict[str, Any]) -> str:
    strategy = config.get("strategy") if isinstance(config.get("strategy"), dict) else {}
    return str(strategy.get("symbol") or "").strip()


def _fill_status(
    *,
    reasons: list[str],
    order_id: str,
    counted_order_ids: set[str],
    excluded_before_cohort: bool = False,
) -> str:
    if excluded_before_cohort:
        return "excluded_before_cohort"
    if reasons:
        return "rejected"
    if order_id and order_id in counted_order_ids:
        return "counted"
    return "incomplete"


def _fill_row(
    *,
    fill: dict[str, Any],
    index: int,
    expected: dict[str, str],
    counted_order_ids: set[str],
    policy: Any,
) -> dict[str, Any]:
    excluded_before_cohort = before_policy_cohort(fill, policy)
    if excluded_before_cohort:
        reasons = []
    elif policy.cohort_start_dt is not None and record_timestamp(fill) is None:
        reasons = ["invalid_timestamp_for_cohort"]
    else:
        reasons = _fill_rejection_reasons(fill, expected)
    order_id = str(fill.get("order_id") or "").strip()
    return {
        "index": int(index),
        "timestamp": fill.get("timestamp") or fill.get("_logged_at"),
        "side": str(fill.get("side") or "").strip().lower(),
        "order_id": order_id,
        "status": _fill_status(
            reasons=reasons,
            order_id=order_id,
            counted_order_ids=counted_order_ids,
            excluded_before_cohort=excluded_before_cohort,
        ),
        "rejection_reasons": reasons,
        "excluded_before_cohort": excluded_before_cohort,
        "size": fill.get("size", fill.get("qty")),
        "market_data_source": fill.get("market_data_source"),
        "ohlcv_sample_mode": fill.get("ohlcv_sample_mode"),
        "ohlcv_timeframe": fill.get("ohlcv_timeframe"),
        "ohlcv_venue": fill.get("ohlcv_venue"),
        "ohlcv_symbol": fill.get("ohlcv_symbol"),
    }


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "counted": sum(1 for row in rows if row.get("status") == "counted"),
        "incomplete": sum(1 for row in rows if row.get("status") == "incomplete"),
        "rejected": sum(1 for row in rows if row.get("status") == "rejected"),
        "excluded_before_cohort": sum(
            1 for row in rows if row.get("status") == "excluded_before_cohort"
        ),
        "total": len(rows),
    }


def _filter_rows(rows: list[dict[str, Any]], row_filter: str) -> list[dict[str, Any]]:
    selected = str(row_filter or "all").strip().lower()
    if selected == "all":
        return rows
    return [dict(row) for row in rows if str(row.get("status") or "") == selected]


def build_paper_gate_qualification_report(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    strategy_id: str = ES_DAILY_TREND_STRATEGY_ID,
    target_strategy: str = ES_DAILY_TREND_TARGET_STRATEGY,
    row_filter: str = "all",
    limit: int | None = None,
) -> dict[str, Any]:
    """Build a read-only fill-level paper gate qualification report."""

    config = _load_config(config_path)
    policy = resolve_paper_promotion_policy(config)
    evidence_dir = data_dir() / "evidence" / str(strategy_id or ES_DAILY_TREND_STRATEGY_ID)
    evidence = load_all_evidence(evidence_dir)
    evidence_fills = [
        dict(row)
        for row in list(evidence.get("fill") or [])
        if isinstance(row, dict)
    ]
    ledger = load_strategy_feedback_ledger(symbol=_config_symbol(config))
    qualified = qualify_paper_history(
        evidence_fills=evidence_fills,
        config=config,
        journal_path=str(ledger.get("journal_path") or ""),
    )
    qualification = dict(qualified.get("qualification") or {})
    expected = dict(qualification.get("expected") or _expected_contract(config))
    counted_order_ids = {
        str(order_id).strip()
        for order_id in list(qualification.get("qualified_order_ids") or [])
        if str(order_id).strip()
    }
    all_rows = [
        _fill_row(
            fill=fill,
            index=idx,
            expected=expected,
            counted_order_ids=counted_order_ids,
            policy=policy,
        )
        for idx, fill in enumerate(
            sorted(evidence_fills, key=_record_ts),
            start=1,
        )
    ]
    filtered = _filter_rows(all_rows, row_filter)
    if limit is not None and int(limit) >= 0:
        filtered = filtered[: int(limit)]
    all_history_rows = [
        dict(row)
        for row in list(ledger.get("rows") or [])
        if str((row or {}).get("strategy") or "") == str(target_strategy)
    ]
    all_history = all_history_rows[0] if all_history_rows else {}
    counts = _status_counts(all_rows)

    return {
        "ok": True,
        "action": "paper_gate_qualification_report",
        "read_only": True,
        "strategy_id": str(strategy_id or ES_DAILY_TREND_STRATEGY_ID),
        "target_strategy": str(target_strategy or ES_DAILY_TREND_TARGET_STRATEGY),
        "evidence_dir": str(evidence_dir),
        "journal_path": str(ledger.get("journal_path") or ""),
        "expected_contract": expected,
        "policy": policy.to_dict(),
        "summary": {
            "qualified_round_trips": int(qualified.get("closed_trades") or 0),
            "all_history_round_trips": int(all_history.get("closed_trades") or 0),
            "evidence_fills": int(qualification.get("evidence_fills") or 0),
            "provenance_qualified_evidence_fills": int(
                qualification.get("provenance_qualified_evidence_fills") or 0
            ),
            "counted_evidence_fills": counts["counted"],
            "incomplete_evidence_fills": counts["incomplete"],
            "rejected_evidence_fills": counts["rejected"],
            "excluded_before_cohort_evidence_fills": counts["excluded_before_cohort"],
            "cohort_start": policy.cohort_start,
            "unqualified_reason_counts": dict(
                qualification.get("unqualified_reason_counts") or {}
            ),
            "unqualified_date_counts": dict(
                qualification.get("unqualified_date_counts") or {}
            ),
            "first_provenance_qualified_fill_ts": qualification.get(
                "first_provenance_qualified_fill_ts"
            ),
            "latest_provenance_qualified_fill_ts": qualification.get(
                "latest_provenance_qualified_fill_ts"
            ),
            "first_completed_qualified_round_trip_close_ts": qualification.get(
                "first_completed_qualified_round_trip_close_ts"
            ),
            "latest_completed_qualified_round_trip_close_ts": qualification.get(
                "latest_completed_qualified_round_trip_close_ts"
            ),
            "missing_journal_order_ids": list(
                qualification.get("missing_journal_order_ids") or []
            ),
        },
        "filter": str(row_filter or "all"),
        "returned_fills": len(filtered),
        "fills": filtered,
    }
