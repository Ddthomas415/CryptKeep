"""
scripts/show_control_kernel_status.py

Show the current deployment stage and kernel status for all tracked strategies.

Usage:
    python scripts/show_control_kernel_status.py
    python scripts/show_control_kernel_status.py --json
    python scripts/show_control_kernel_status.py --strategy canonical_200sma_trend
    python scripts/show_control_kernel_status.py --promote <strategy_id>
    python scripts/show_control_kernel_status.py --demote <strategy_id>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.os.app_paths import data_dir
from services.control.deployment_stage import (
    stage_summary, promote, demote, force_safe_degraded, Stage, load_stage,
)
from services.control.cognitive_budget import budget_summary
from services.control.kernel import ControlKernel, METRIC_THRESHOLDS, UTILITY_CONSTRAINTS


def _list_strategy_ids() -> list[str]:
    """Scan the stages directory for tracked strategies."""
    stages_dir = data_dir() / "control" / "stages"
    if not stages_dir.exists():
        return []
    return [p.stem for p in sorted(stages_dir.glob("*.json"))]


def _print_status(strategy_id: str) -> None:
    summary = stage_summary(strategy_id)
    budget = budget_summary(strategy_id)
    stage = summary["stage"]
    alerts = budget["alert_count"]
    breach = budget["breach"]

    stage_icon = {
        "paper": "📄",
        "shadow": "👻",
        "capped_live": "⚡",
        "scaled_live": "🚀",
        "safe_degraded": "🛑",
    }.get(stage, "❓")

    breach_flag = " ⚠️ COGNITIVE BUDGET BREACH" if breach else ""
    print(f"\n{stage_icon}  {strategy_id}")
    print(f"   Stage:        {stage}")
    print(f"   Since:        {summary.get('since_ts', 'unknown')[:19]}")
    print(f"   Max alloc:    {summary['max_alloc_frac']:.0%}")
    print(f"   Active alerts:{alerts}/{METRIC_THRESHOLDS['alert_count']['crit']}{breach_flag}")
    print(f"   Allowed:      {', '.join(summary['allowed_actions']) or 'none'}")
    if budget.get("active_alerts"):
        for a in budget["active_alerts"]:
            print(f"     alert: {a['type']} ({a.get('level','?')})")


def main() -> int:
    ap = argparse.ArgumentParser(description="Control kernel status")
    ap.add_argument("--strategy", type=str, default=None,
                    help="Show status for a specific strategy ID")
    ap.add_argument("--promote", type=str, default=None, metavar="STRATEGY_ID",
                    help="Promote a strategy to the next stage")
    ap.add_argument("--demote", type=str, default=None, metavar="STRATEGY_ID",
                    help="Demote a strategy to safe_degraded")
    ap.add_argument("--reason", type=str, default="manual_operator_action",
                    help="Reason for promotion/demotion")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()

    # Mutations
    if args.promote:
        result = promote(args.promote, reason=args.reason, actor="operator_script")
        print(json.dumps(result, indent=2) if args.json else
              f"Promoted {args.promote}: {result}")
        return 0

    if args.demote:
        result = force_safe_degraded(args.demote, reason=args.reason, actor="operator_script")
        print(json.dumps(result, indent=2) if args.json else
              f"Demoted {args.demote}: {result}")
        return 0

    # Status display
    ids = [args.strategy] if args.strategy else _list_strategy_ids()

    if not ids:
        print("No strategies tracked yet. Run a candidate scan or paper strategy first.")
        return 0

    if args.json:
        out = [stage_summary(sid) for sid in ids]
        print(json.dumps(out, indent=2))
        return 0

    print("=== Control Kernel Status ===")
    print(f"Utility constraints: {UTILITY_CONSTRAINTS}")
    for sid in ids:
        _print_status(sid)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
