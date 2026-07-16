from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.ai_copilot.policy import report_root
from services.ai_copilot.providers import call_llm
from services.ai_copilot.report_audit import record_ai_copilot_report_write
from services.analytics.paper_sim_monitor import load_runtime_status as load_paper_sim_monitor_status
from services.os.app_paths import code_root
from services.os.file_utils import atomic_write

REPORT_TYPE = "ai_operator_oversight"

_SYSTEM_PROMPT = """You are the CryptKeep AI operator oversight copilot.

You are read-only. Summarize machine-observed facts for a human operator.

Hard constraints:
- Do not suggest live trading, order submission, order cancellation, or gate mutation.
- Do not suggest changing strategy selection or enabling candidate advisor.
- Do not invent facts beyond the provided JSON.
- Keep recommendations human-operated and reversible.
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _config_candidate_advisor_enabled() -> bool | None:
    path = code_root() / "configs" / "strategies" / "es_daily_trend_v1.yaml"
    if not path.exists():
        return None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip().lower()
        if not line.startswith("use_candidate_advisor:"):
            continue
        value = line.split(":", 1)[1].strip().split("#", 1)[0].strip()
        if value in {"true", "yes", "on", "1"}:
            return True
        if value in {"false", "no", "off", "0"}:
            return False
        return None
    return None


def _gate_payload() -> dict[str, Any]:
    try:
        from scripts.check_promotion_gates import run_check

        return _safe_dict(run_check(stage_override="paper"))
    except Exception as exc:
        return {
            "ready": False,
            "machine_ready": False,
            "manual_review_required": True,
            "error": f"gate_unavailable:{type(exc).__name__}",
            "gates": [],
        }


def _gate_blockers(gate: dict[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for item in _safe_list(gate.get("gates")):
        row = _safe_dict(item)
        if row.get("passed") is True:
            continue
        blockers.append(
            {
                "label": str(row.get("label") or ""),
                "passed": row.get("passed"),
                "detail": str(row.get("detail") or ""),
                "hint": str(row.get("hint") or ""),
            }
        )
    manual = _safe_dict(gate.get("manual_review"))
    for item in _safe_list(manual.get("outstanding_items")):
        row = _safe_dict(item)
        blockers.append(
            {
                "label": str(row.get("label") or row.get("id") or ""),
                "passed": False,
                "detail": str(row.get("reason") or row.get("status") or ""),
                "hint": "manual_review_required",
            }
        )
    return blockers


def _monitor_facts(monitor: dict[str, Any]) -> dict[str, Any]:
    watches = [_safe_dict(item) for item in _safe_list(monitor.get("watches"))]
    reports = [_safe_dict(item) for item in _safe_list(monitor.get("recent_watch_reports"))]
    latest_report = reports[0] if reports else {}
    return {
        "has_status": bool(monitor.get("has_status")),
        "status": str(monitor.get("status") or ""),
        "reason": str(monitor.get("reason") or ""),
        "pid_alive": bool(monitor.get("pid_alive")),
        "campaign_status": str(monitor.get("campaign_status") or ""),
        "campaign_reason": str(monitor.get("campaign_reason") or ""),
        "recommendation": str(monitor.get("recommendation") or ""),
        "recommendation_reason": str(monitor.get("recommendation_reason") or ""),
        "strategy_label": str(monitor.get("strategy_label") or ""),
        "symbol": str(monitor.get("symbol") or ""),
        "summary_text": str(monitor.get("summary_text") or ""),
        "watch_count": len(watches),
        "active_watch_names": [
            str(row.get("name") or "")
            for row in watches
            if bool(row.get("active", True)) and str(row.get("name") or "").strip()
        ],
        "recent_watch_report_count": len(reports),
        "latest_watch_report": {
            "watch_name": str(latest_report.get("watch_name") or ""),
            "trigger": str(latest_report.get("trigger") or ""),
            "severity": str(latest_report.get("severity") or ""),
            "summary": str(latest_report.get("summary") or ""),
            "generated_at": str(latest_report.get("generated_at") or ""),
            "json_path": str(latest_report.get("json_path") or ""),
            "markdown_path": str(latest_report.get("markdown_path") or ""),
        },
    }


def _paper_gate_facts(gate: dict[str, Any]) -> dict[str, Any]:
    paper_history = _safe_dict(gate.get("paper_history"))
    qualification = _safe_dict(paper_history.get("qualification"))
    return {
        "ready": bool(gate.get("ready")),
        "machine_ready": bool(gate.get("machine_ready")),
        "manual_review_required": bool(gate.get("manual_review_required")),
        "strategy_id": str(gate.get("strategy_id") or ""),
        "stage": str(gate.get("stage") or ""),
        "blockers": _gate_blockers(gate),
        "paper_history": {
            "source": str(paper_history.get("source") or ""),
            "fills": paper_history.get("fills"),
            "closed_trades": paper_history.get("closed_trades"),
            "latest_fill_ts": paper_history.get("latest_fill_ts"),
            "all_history_fills": paper_history.get("all_history_fills"),
            "all_history_closed_trades": paper_history.get("all_history_closed_trades"),
        },
        "qualification": {
            "evidence_fills": qualification.get("evidence_fills"),
            "qualified_evidence_fills": qualification.get("qualified_evidence_fills"),
            "completed_evidence_round_trips": qualification.get("completed_evidence_round_trips"),
            "incomplete_qualified_evidence_fills": qualification.get("incomplete_qualified_evidence_fills"),
            "unqualified_evidence_fills": qualification.get("unqualified_evidence_fills"),
            "latest_completed_qualified_round_trip_close_ts": qualification.get(
                "latest_completed_qualified_round_trip_close_ts"
            ),
        },
    }


def _action_items(*, monitor: dict[str, Any], monitor_facts: dict[str, Any], gate_facts: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if not bool(monitor_facts.get("has_status")):
        actions.append(
            {
                "id": "restore_monitor_status",
                "severity": "warn",
                "summary": "Paper sim monitor status is missing.",
                "operator_action": "Run the paper sim monitor one-shot status or restore the accepted monitor path before relying on oversight.",
            }
        )

    reports = [_safe_dict(item) for item in _safe_list(monitor.get("recent_watch_reports"))]
    if not reports:
        actions.append(
            {
                "id": "no_recent_watch_reports",
                "severity": "info",
                "summary": "No recent paper-sim watch reports are available.",
                "operator_action": "Confirm the monitor is running and watches are registered if you expected a wake-up event.",
            }
        )

    for report in reports:
        trigger = str(report.get("trigger") or "").strip()
        watch_name = str(report.get("watch_name") or "").strip()
        if trigger == "recommendation_investigate" or watch_name == "investigate":
            actions.append(
                {
                    "id": "investigate_watch_report",
                    "severity": "warn",
                    "summary": str(report.get("summary") or "Paper sim monitor requested investigation."),
                    "operator_action": "Open the referenced watch report and inspect the machine facts before changing any campaign state.",
                }
            )
            break

    for blocker in list(gate_facts.get("blockers") or [])[:5]:
        row = _safe_dict(blocker)
        label = str(row.get("label") or "paper gate blocker")
        detail = str(row.get("detail") or "")
        actions.append(
            {
                "id": "paper_gate_blocker",
                "severity": "info",
                "summary": f"{label}: {detail}".strip(),
                "operator_action": "Continue paper observation or perform the documented manual review; do not mutate the gate output.",
            }
        )

    if not actions:
        actions.append(
            {
                "id": "no_action_required",
                "severity": "info",
                "summary": "No immediate operator action was identified from current machine facts.",
                "operator_action": "Continue normal read-only monitoring.",
            }
        )
    return actions


def _overall_status(*, monitor_facts: dict[str, Any], gate_facts: dict[str, Any]) -> str:
    if not bool(monitor_facts.get("has_status")):
        return "insufficient_status"
    if str(monitor_facts.get("recommendation") or "").strip().lower() == "investigate":
        return "investigate"
    latest_report = _safe_dict(monitor_facts.get("latest_watch_report"))
    if str(latest_report.get("trigger") or "") == "recommendation_investigate":
        return "investigate"
    if not bool(gate_facts.get("ready")):
        return "paper_gate_blocked"
    return "ready_for_operator_review"


def _machine_summary(*, status: str, monitor_facts: dict[str, Any], gate_facts: dict[str, Any]) -> str:
    strategy = str(monitor_facts.get("strategy_label") or gate_facts.get("strategy_id") or "unknown_strategy")
    symbol = str(monitor_facts.get("symbol") or "unknown_symbol")
    gate_state = "ready" if bool(gate_facts.get("ready")) else "not ready"
    recommendation = str(monitor_facts.get("recommendation") or "unknown")
    blocker_count = len(list(gate_facts.get("blockers") or []))
    return (
        f"Operator oversight status is {status}. Monitor sees {strategy} on {symbol} "
        f"with recommendation={recommendation}; paper gate is {gate_state} with "
        f"{blocker_count} blocker(s)."
    )


def _ai_summary(*, report: dict[str, Any], use_ai: bool) -> dict[str, Any]:
    if not bool(use_ai):
        return {
            "status": "machine_only",
            "reason": "ai_not_requested",
            "text": report["machine_summary"],
        }
    payload = {
        "status": report.get("status"),
        "machine_facts": report.get("machine_facts"),
        "action_items": report.get("action_items"),
        "do_not_touch": report.get("do_not_touch"),
    }
    response = call_llm(system=_SYSTEM_PROMPT, user=json.dumps(payload, indent=2, sort_keys=True, default=str))
    if not bool(response.get("ok")):
        return {
            "status": "machine_only",
            "reason": str(response.get("error") or "ai_provider_unavailable"),
            "text": report["machine_summary"],
            "provider": response.get("provider"),
            "model": response.get("model"),
        }
    return {
        "status": "generated",
        "reason": "",
        "text": str(response.get("text") or "").strip(),
        "provider": response.get("provider"),
        "model": response.get("model"),
    }


def build_operator_oversight_report(*, use_ai: bool = False) -> dict[str, Any]:
    monitor = _safe_dict(load_paper_sim_monitor_status())
    gate = _gate_payload()
    monitor_facts = _monitor_facts(monitor)
    gate_facts = _paper_gate_facts(gate)
    status = _overall_status(monitor_facts=monitor_facts, gate_facts=gate_facts)
    candidate_advisor_enabled = _config_candidate_advisor_enabled()
    report: dict[str, Any] = {
        "generated_at": _now_iso(),
        "report_type": REPORT_TYPE,
        "status": status,
        "read_only": True,
        "watch_report_status": (
            "available" if int(monitor_facts.get("recent_watch_report_count") or 0) > 0 else "no_recent_watch_reports"
        ),
        "machine_facts": {
            "monitor": monitor_facts,
            "paper_gate": gate_facts,
            "candidate_advisor": {
                "enabled": candidate_advisor_enabled,
                "expected_enabled": False,
                "status": (
                    "disabled"
                    if candidate_advisor_enabled is False
                    else "unknown" if candidate_advisor_enabled is None else "enabled"
                ),
            },
        },
        "action_items": [],
        "do_not_touch": [
            "do_not_start_or_stop_campaigns_from_this_report",
            "do_not_enable_candidate_advisor",
            "do_not_mutate_promotion_gates",
            "do_not_route_or_cancel_orders",
            "do_not_change_live_execution_state",
        ],
        "safety": {
            "read_only": True,
            "background_monitor_started": False,
            "watch_config_mutated": False,
            "external_notifications_dispatched": False,
            "candidate_advisor_enabled": candidate_advisor_enabled is True,
            "orders_routed": False,
            "promotion_gate_mutated": False,
            "live_execution_touched": False,
        },
    }
    report["action_items"] = _action_items(
        monitor=monitor,
        monitor_facts=monitor_facts,
        gate_facts=gate_facts,
    )
    report["machine_summary"] = _machine_summary(
        status=status,
        monitor_facts=monitor_facts,
        gate_facts=gate_facts,
    )
    report["ai_summary"] = _ai_summary(report=report, use_ai=use_ai)
    return report


def render_operator_oversight_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AI Operator Oversight Report",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Status: `{report.get('status')}`",
        f"- Read-only: `{bool(report.get('read_only'))}`",
        f"- Watch reports: `{report.get('watch_report_status')}`",
        "",
        "## Machine Summary",
        str(report.get("machine_summary") or ""),
        "",
        "## Action Items",
    ]
    for item in list(report.get("action_items") or []):
        row = _safe_dict(item)
        lines.append(
            f"- `{row.get('id')}` [{row.get('severity')}]: {row.get('summary')} "
            f"Action: {row.get('operator_action')}"
        )
    lines.extend(
        [
            "",
            "## AI Summary",
            str(_safe_dict(report.get("ai_summary")).get("text") or ""),
            "",
            "## Do Not Touch",
        ]
    )
    for item in list(report.get("do_not_touch") or []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Machine Facts", "```json", json.dumps(report.get("machine_facts") or {}, indent=2, sort_keys=True, default=str), "```"])
    return "\n".join(lines) + "\n"


def write_operator_oversight_report(report: dict[str, Any]) -> dict[str, str]:
    root = report_root()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    latest_json = root / f"{REPORT_TYPE}.latest.json"
    dated_json = root / f"{REPORT_TYPE}_{stamp}.json"
    latest_md = root / f"{REPORT_TYPE}.latest.md"
    dated_md = root / f"{REPORT_TYPE}_{stamp}.md"
    json_text = json.dumps(report, indent=2, sort_keys=True, default=str)
    markdown_text = render_operator_oversight_markdown(report)
    for path, text in (
        (latest_json, json_text),
        (dated_json, json_text),
        (latest_md, markdown_text),
        (dated_md, markdown_text),
    ):
        atomic_write(Path(path), text)
    paths = {
        "latest_json": str(latest_json),
        "dated_json": str(dated_json),
        "latest_markdown": str(latest_md),
        "dated_markdown": str(dated_md),
    }
    return {
        **paths,
        "operator_event": record_ai_copilot_report_write(
            report_type=REPORT_TYPE,
            report=report,
            paths=paths,
            source="services.ai_copilot.operator_oversight",
        ),
    }
