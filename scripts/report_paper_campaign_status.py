#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
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


def _latest_result(collector: dict[str, Any]) -> dict[str, Any]:
    last_result = dict(collector.get("last_result") or {})
    results = [
        dict(item)
        for item in list(last_result.get("results") or [])
        if isinstance(item, dict)
    ]
    return results[-1] if results else {}


def _campaign_row(row: dict[str, Any]) -> dict[str, Any]:
    collector = dict(row.get("collector") or {})
    latest_result = _latest_result(collector)
    return {
        "name": str(row.get("name") or ""),
        "ok": bool(row.get("ok")),
        "running": bool(row.get("running")),
        "status": str(row.get("status") or "unknown"),
        "reason": str(row.get("reason") or ""),
        "strategy": str(row.get("strategy") or ""),
        "session_strategy_id": str(row.get("session_strategy_id") or ""),
        "state_dir": str(row.get("state_dir") or ""),
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


def _recommendations(payload: dict[str, Any]) -> list[str]:
    if not bool(payload.get("ok")):
        return ["investigate_campaign_status"]
    if not bool(payload.get("all_running")):
        return ["restore_or_investigate_campaign_processes"]
    return ["continue_paper_observation"]


def build_report(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    selected_campaigns: list[str] | None = None,
) -> dict[str, Any]:
    selected = list(selected_campaigns or [])
    specs = load_campaign_specs(config_path, repo_root=ROOT)
    campaigns = manage_campaigns(specs, restore=False, selected_names=selected)
    return build_report_from_status(campaigns)


def build_report_from_status(campaigns: dict[str, Any]) -> dict[str, Any]:
    rows = [_campaign_row(dict(row)) for row in list(campaigns.get("campaigns") or [])]
    payload = {
        "ok": bool(campaigns.get("ok")),
        "action": "report_paper_campaign_status",
        "read_only": True,
        "all_running": bool(campaigns.get("all_running")),
        "campaign_count": _as_int(campaigns.get("campaign_count")),
        "running_count": _as_int(campaigns.get("running_count")),
        "campaigns": rows,
    }
    payload["recommendations"] = _recommendations(payload)
    return payload


def print_report(payload: dict[str, Any]) -> None:
    print("=== Paper Campaign Status ===")
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
        if row.get("latest_fill_ts"):
            print(f"  latest_fill={row.get('latest_fill_ts')}")
        if row.get("summary_text"):
            print(f"  summary={row.get('summary_text')}")

    print("")
    print("Recommendations: " + ", ".join(str(item) for item in payload.get("recommendations") or []))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only paper campaign status report")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero when campaigns need investigation")
    ap.add_argument(
        "--from-json",
        type=Path,
        help="Format an existing restore_paper_campaigns.py --status JSON payload; use '-' for stdin",
    )
    ap.add_argument(
        "--campaign",
        action="append",
        default=[],
        help="Limit campaign status to a configured campaign name; may be repeated",
    )
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Paper campaign manifest path")
    args = ap.parse_args(argv)

    try:
        if args.from_json:
            raw = (
                sys.stdin.read()
                if str(args.from_json) == "-"
                else args.from_json.read_text(encoding="utf-8")
            )
            payload = build_report_from_status(json.loads(raw))
        else:
            payload = build_report(
                config_path=args.config,
                selected_campaigns=list(args.campaign or []),
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "ok": False,
            "action": "report_paper_campaign_status",
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
