#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# CBP_BOOTSTRAP_SYS_PATH

try:
    from _bootstrap import add_repo_root_to_syspath  # noqa: E402
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath  # noqa: E402

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.analytics.paper_campaign_recovery import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    load_campaign_specs,
    manage_campaigns,
)


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


def _find_gate(gates: list[dict[str, Any]], needle: str) -> dict[str, Any]:
    needle_l = str(needle).strip().lower()
    for gate in gates:
        label = str(gate.get("label") or "").strip().lower()
        if needle_l in label:
            return dict(gate)
    return {}


def _campaign_row(row: dict[str, Any]) -> dict[str, Any]:
    collector = dict(row.get("collector") or {})
    last_result = dict(collector.get("last_result") or {})
    results = [dict(item) for item in list(last_result.get("results") or []) if isinstance(item, dict)]
    latest_result = results[-1] if results else {}
    return {
        "name": str(row.get("name") or ""),
        "ok": bool(row.get("ok")),
        "running": bool(row.get("running")),
        "status": str(row.get("status") or "unknown"),
        "reason": str(row.get("reason") or ""),
        "strategy": str(row.get("strategy") or ""),
        "session_strategy_id": str(row.get("session_strategy_id") or ""),
        "last_completed_day": row.get("last_completed_day"),
        "pid": row.get("pid"),
        "summary_text": str(collector.get("summary_text") or ""),
        "latest_fill_ts": latest_result.get("latest_fill_ts"),
        "fills_total": _as_int(latest_result.get("fills_total")),
        "closed_trades_total": _as_int(latest_result.get("closed_trades_total")),
        "net_realized_pnl_total": _as_float(latest_result.get("net_realized_pnl_total")),
        "signal_action": str(latest_result.get("signal_action") or ""),
        "runner_status": str(latest_result.get("runner_status") or ""),
    }


def _gate_summary(gate_payload: dict[str, Any]) -> dict[str, Any]:
    gates = [dict(item) for item in list(gate_payload.get("gates") or []) if isinstance(item, dict)]
    manual = dict(gate_payload.get("manual_review") or {})
    outstanding = [
        dict(item)
        for item in list(manual.get("outstanding_items") or [])
        if isinstance(item, dict)
    ]
    round_trip_gate = _find_gate(gates, "round trip")
    days_gate = _find_gate(gates, "calendar days")
    expectancy_gate = _find_gate(gates, "expectancy")
    return {
        "strategy_id": str(gate_payload.get("strategy_id") or ""),
        "stage": str(gate_payload.get("stage") or ""),
        "current_stage": str(gate_payload.get("current_stage") or ""),
        "ready": bool(gate_payload.get("ready")),
        "machine_ready": bool(gate_payload.get("machine_ready")),
        "manual_review_required": bool(gate_payload.get("manual_review_required")),
        "summary": dict(gate_payload.get("summary") or {}),
        "round_trips": round_trip_gate,
        "days": days_gate,
        "expectancy": expectancy_gate,
        "manual_review_summary": str(manual.get("summary") or ""),
        "outstanding_manual_items": [
            {
                "id": str(item.get("id") or ""),
                "label": str(item.get("label") or ""),
                "status": str(item.get("status") or ""),
                "reason": str(item.get("reason") or ""),
            }
            for item in outstanding
        ],
    }


def _recommendations(campaigns: dict[str, Any], gate: dict[str, Any]) -> list[str]:
    recs: list[str] = []
    if not bool(campaigns.get("all_running")):
        recs.append("investigate_campaign_processes")
    if bool(gate.get("manual_review_required")):
        recs.append("manual_strategy_review_required")
    if not bool(gate.get("machine_ready")):
        recs.append("continue_paper_observation")
    if not recs:
        recs.append("ready_for_operator_gate_review")
    return recs


def build_report(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    selected_campaigns: list[str] | None = None,
    stage: str = "paper",
) -> dict[str, Any]:
    from scripts.check_promotion_gates import run_check

    selected = list(selected_campaigns or [])
    specs = load_campaign_specs(config_path, repo_root=ROOT)
    campaigns = manage_campaigns(specs, restore=False, selected_names=selected)
    gate = _gate_summary(run_check(stage_override=stage))
    rows = [_campaign_row(dict(row)) for row in list(campaigns.get("campaigns") or [])]
    recommendations = _recommendations(campaigns, gate)
    ok = bool(campaigns.get("ok")) and "investigate_campaign_processes" not in recommendations
    return {
        "ok": ok,
        "action": "report_supervised_soak_status",
        "read_only": True,
        "campaigns_ok": bool(campaigns.get("ok")),
        "all_running": bool(campaigns.get("all_running")),
        "campaign_count": _as_int(campaigns.get("campaign_count")),
        "running_count": _as_int(campaigns.get("running_count")),
        "campaigns": rows,
        "gate": gate,
        "recommendations": recommendations,
    }


def print_report(payload: dict[str, Any]) -> None:
    print("=== Supervised Paper Soak Status ===")
    print(
        "Campaigns: "
        f"{payload.get('running_count', 0)}/{payload.get('campaign_count', 0)} running "
        f"(all_running={bool(payload.get('all_running'))})"
    )
    for row in list(payload.get("campaigns") or []):
        if not isinstance(row, dict):
            continue
        pnl = row.get("net_realized_pnl_total")
        pnl_text = "-" if pnl is None else f"{float(pnl):.4f}"
        print(
            f"- {row.get('name')}: {row.get('status')} "
            f"reason={row.get('reason') or '-'} "
            f"strategy={row.get('strategy') or '-'} "
            f"fills={row.get('fills_total', 0)} "
            f"closed={row.get('closed_trades_total', 0)} "
            f"pnl={pnl_text}"
        )

    gate = dict(payload.get("gate") or {})
    print("")
    print(
        "Gate: "
        f"ready={bool(gate.get('ready'))} "
        f"machine_ready={bool(gate.get('machine_ready'))} "
        f"manual_review_required={bool(gate.get('manual_review_required'))}"
    )
    round_trip = dict(gate.get("round_trips") or {})
    if round_trip:
        print(f"- round trips: {round_trip.get('detail') or '-'}")
    days = dict(gate.get("days") or {})
    if days:
        print(f"- days: {days.get('detail') or '-'}")
    expectancy = dict(gate.get("expectancy") or {})
    if expectancy:
        print(f"- expectancy: {expectancy.get('detail') or '-'}")
    if gate.get("manual_review_summary"):
        print(f"- manual review: {gate.get('manual_review_summary')}")

    print("")
    print("Recommendations: " + ", ".join(str(item) for item in payload.get("recommendations") or []))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only supervised paper soak status report")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero when campaigns need investigation")
    ap.add_argument("--stage", default="paper", help="Promotion gate stage override, default: paper")
    ap.add_argument(
        "--campaign",
        action="append",
        default=[],
        help="Limit campaign status to a configured campaign name; may be repeated",
    )
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Paper campaign manifest path")
    args = ap.parse_args(argv)

    try:
        payload = build_report(
            config_path=args.config,
            selected_campaigns=list(args.campaign or []),
            stage=str(args.stage or "paper"),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "ok": False,
            "action": "report_supervised_soak_status",
            "read_only": True,
            "reason": f"report_failed:{type(exc).__name__}",
            "recommendations": ["investigate_report_failure"],
        }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print_report(payload)

    if args.strict and not bool(payload.get("ok")):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
