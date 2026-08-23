from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from services.analytics.cost_assumptions import check_cost_assumptions
from services.analytics.operator_next_actions import build_operator_next_actions
from services.analytics.operator_status_bundle import build_operator_status_bundle
from services.analytics.paper_campaign_recovery import (
    DEFAULT_CONFIG_PATH,
    load_campaign_specs,
    manage_campaigns,
)
from services.control.paper_gate_velocity import build_paper_gate_velocity_report


REPORT_TYPE = "operator_briefing"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _source(name: str, builder: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        payload = builder()
    except Exception as exc:
        return {
            "ok": False,
            "source": name,
            "status": "source_failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "source": name,
            "status": "source_invalid",
            "error": "source_payload_not_object",
        }
    return {"ok": True, "source": name, "status": "available", "payload": payload}


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _latest_result(collector: dict[str, Any]) -> dict[str, Any]:
    last_result = dict(collector.get("last_result") or {})
    results = [dict(item) for item in list(last_result.get("results") or []) if isinstance(item, dict)]
    return results[-1] if results else {}


def build_paper_campaign_status_report() -> dict[str, Any]:
    specs = load_campaign_specs(DEFAULT_CONFIG_PATH)
    return manage_campaigns(specs, restore=False)


def _campaign_summary(campaigns: dict[str, Any]) -> dict[str, Any]:
    rows = [dict(row) for row in list(campaigns.get("campaigns") or []) if isinstance(row, dict)]
    return {
        "ok": bool(campaigns.get("ok")),
        "all_running": bool(campaigns.get("all_running")),
        "running_count": _as_int(campaigns.get("running_count")),
        "campaign_count": _as_int(campaigns.get("campaign_count")),
        "statuses": [
            {
                "name": str(row.get("name") or ""),
                "status": str(row.get("status") or "unknown"),
                "reason": str(row.get("reason") or ""),
                "strategy": str(row.get("strategy") or ""),
                "session_strategy_id": str(row.get("session_strategy_id") or ""),
                "closed_trades_total": _as_int(_latest_result(dict(row.get("collector") or {})).get("closed_trades_total")),
                "fills_total": _as_int(_latest_result(dict(row.get("collector") or {})).get("fills_total")),
                "net_realized_pnl_total": _as_float(
                    _latest_result(dict(row.get("collector") or {})).get("net_realized_pnl_total")
                ),
                "last_completed_day": row.get("last_completed_day"),
            }
            for row in rows
        ],
    }


def _gate_summary(gate: dict[str, Any]) -> dict[str, Any]:
    round_trips = dict(gate.get("round_trips") or {})
    qualified_bars = dict(gate.get("qualified_bars") or {})
    velocity = dict(gate.get("velocity") or {})
    overall = dict(gate.get("overall_velocity") or {})
    return {
        "ok": bool(gate.get("ok")),
        "strategy_id": gate.get("strategy_id"),
        "policy_id": gate.get("policy_id"),
        "thresholds_ready": bool(gate.get("thresholds_ready")),
        "round_trips": {
            "qualified": _as_int(round_trips.get("qualified")),
            "required": _as_int(round_trips.get("required")),
            "remaining": _as_int(round_trips.get("remaining")),
            "excluded_all_history": _as_int(round_trips.get("excluded_all_history")),
        },
        "qualified_bars": {
            "enabled": bool(qualified_bars.get("enabled")),
            "recorded": _as_int(qualified_bars.get("recorded")),
            "required": _as_int(qualified_bars.get("required")),
            "remaining": _as_int(qualified_bars.get("remaining")),
            "ready": bool(qualified_bars.get("ready")),
        },
        "completion_estimate": {
            "round_trip_status": velocity.get("status"),
            "round_trip_days_remaining": velocity.get("estimated_days_remaining"),
            "overall_status": overall.get("status"),
            "overall_blocking_threshold": overall.get("blocking_threshold"),
            "overall_estimated_completion_ts": overall.get("estimated_completion_ts"),
        },
        "findings": list(gate.get("findings") or []),
    }


def _cost_summary(cost: dict[str, Any]) -> dict[str, Any]:
    return {
        "overall": str(cost.get("overall") or "unknown"),
        "round_trip_bps": cost.get("round_trip_bps"),
        "policy_floor_bps": cost.get("policy_floor_bps"),
        "checks": [
            {
                "name": str(row.get("name") or ""),
                "status": str(row.get("status") or ""),
                "detail": str(row.get("detail") or ""),
            }
            for row in list(cost.get("checks") or [])
            if isinstance(row, dict)
        ],
    }


def _next_action_summary(actions: dict[str, Any]) -> dict[str, Any]:
    rows = [dict(row) for row in list(actions.get("actions") or []) if isinstance(row, dict)]
    return {
        "ok": bool(actions.get("ok")),
        "action_count_total": _as_int(actions.get("action_count_total")),
        "action_count_available": _as_int(actions.get("action_count_available")),
        "action_count_returned": _as_int(actions.get("action_count_returned")),
        "summary": dict(actions.get("summary") or {}),
        "actions": [
            {
                "lane": str(row.get("lane") or ""),
                "source": str(row.get("source") or ""),
                "blocking_reason": str(row.get("blocking_reason") or ""),
                "next_action": str(row.get("next_action") or ""),
            }
            for row in rows
        ],
    }


def _source_payload(sources: dict[str, dict[str, Any]], name: str) -> dict[str, Any]:
    row = sources.get(name) or {}
    return dict(row.get("payload") or {}) if bool(row.get("ok")) else {}


def _recommendations(
    *,
    campaigns: dict[str, Any],
    gate: dict[str, Any],
    cost: dict[str, Any],
    next_actions: dict[str, Any],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if campaigns and not bool(campaigns.get("all_running")):
        out.append(
            {
                "id": "campaign_process_attention",
                "priority": "high",
                "confidence": "high",
                "action": "Investigate or restore stopped paper campaign processes using the existing recovery path.",
                "evidence_source": "paper_campaign_status",
            }
        )
    round_trips = dict(gate.get("round_trips") or {})
    if _as_int(round_trips.get("remaining")) > 0:
        out.append(
            {
                "id": "paper_gate_continue_evidence",
                "priority": "medium",
                "confidence": "high",
                "action": "Keep the current paper gate running under the approved provenance policy.",
                "evidence_source": "paper_gate_velocity",
            }
        )
    if str(cost.get("overall") or "").lower() not in {"", "ok"}:
        out.append(
            {
                "id": "cost_assumption_attention",
                "priority": "medium",
                "confidence": "medium",
                "action": "Review local paper/backtest cost assumptions before relying on expectancy comparisons.",
                "evidence_source": "cost_assumptions",
            }
        )
    for row in list(next_actions.get("actions") or [])[:3]:
        if not isinstance(row, dict):
            continue
        action = str(row.get("next_action") or "").strip()
        if not action:
            continue
        out.append(
            {
                "id": "operator_next_action",
                "priority": "medium",
                "confidence": "high",
                "action": action,
                "evidence_source": f"{row.get('lane')}:{row.get('source')}",
            }
        )
    if not out:
        out.append(
            {
                "id": "no_immediate_operator_action",
                "priority": "low",
                "confidence": "medium",
                "action": "No immediate read-only action surfaced; continue scheduled campaign observation.",
                "evidence_source": "operator_briefing",
            }
        )
    return out


def build_operator_briefing(
    *,
    repo_root: str | Path | None = None,
    max_actions: int = 8,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    sources = {
        "operator_status": _source(
            "operator_status",
            lambda: build_operator_status_bundle(repo_root=root),
        ),
        "operator_next_actions": _source(
            "operator_next_actions",
            lambda: build_operator_next_actions(repo_root=root, max_actions=max_actions),
        ),
        "paper_campaign_status": _source("paper_campaign_status", build_paper_campaign_status_report),
        "paper_gate_velocity": _source("paper_gate_velocity", build_paper_gate_velocity_report),
        "cost_assumptions": _source("cost_assumptions", check_cost_assumptions),
    }
    source_status = {
        name: {
            "ok": bool(row.get("ok")),
            "status": row.get("status"),
            "error_type": row.get("error_type"),
            "error": row.get("error"),
        }
        for name, row in sources.items()
    }
    operator_status = _source_payload(sources, "operator_status")
    next_actions = _next_action_summary(_source_payload(sources, "operator_next_actions"))
    gate = _gate_summary(_source_payload(sources, "paper_gate_velocity"))
    cost = _cost_summary(_source_payload(sources, "cost_assumptions"))
    campaigns = _campaign_summary(_source_payload(sources, "paper_campaign_status"))
    recommendations = _recommendations(
        campaigns=campaigns,
        gate=gate,
        cost=cost,
        next_actions=next_actions,
    )
    failed_sources = [name for name, row in source_status.items() if not bool(row.get("ok"))]
    return {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "generated_at": _now_iso(),
        "ok": not failed_sources,
        "reason": "source_failed" if failed_sources else None,
        "read_only": True,
        "advisory_only": True,
        "capital_authority": "none",
        "does_not_mutate_state": True,
        "does_not_run_campaigns": True,
        "does_not_start_or_stop_campaigns": True,
        "does_not_fetch_market_data": True,
        "does_not_change_config": True,
        "does_not_promote_strategies": True,
        "repo_root": str(root),
        "source_status": source_status,
        "summaries": {
            "campaigns": campaigns,
            "paper_gate": gate,
            "cost_assumptions": cost,
            "operator_next_actions": next_actions,
            "operator_status": {
                "ok": bool(operator_status.get("ok")),
                "summary": dict(operator_status.get("summary") or {}),
            },
        },
        "recommendations": recommendations,
        "boundary": {
            "role": "operator_briefing",
            "allowed": [
                "summarize existing status reports",
                "rank already-surfaced operator next actions",
                "explain evidence sources for recommendations",
            ],
            "prohibited": [
                "move capital",
                "start or stop campaigns",
                "change config or manifests",
                "promote strategies",
                "alter execution or routing policy",
            ],
        },
    }
