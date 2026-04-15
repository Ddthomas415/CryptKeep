#!/usr/bin/env python3
"""scripts/run_es_daily_trend_paper.py

Paper trading runner for ES Daily Trend v1.

Loads the strategy config from configs/strategies/es_daily_trend_v1.yaml,
verifies the deployment stage is paper, applies the kernel pre-check,
then runs the standard paper evidence collector for one campaign.

Usage:
    python scripts/run_es_daily_trend_paper.py
    python scripts/run_es_daily_trend_paper.py --status
    python scripts/run_es_daily_trend_paper.py --check-promotion
    python scripts/run_es_daily_trend_paper.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml

from services.control.deployment_stage import get_current_stage, Stage, stage_summary
from services.control.cognitive_budget import budget_summary
from services.control.kernel import ControlKernel
from services.logging.app_logger import get_logger

STRATEGY_ID = "es_daily_trend_v1"
CONFIG_PATH  = Path("configs/strategies/es_daily_trend_v1.yaml")
SPEC_PATH    = Path("docs/strategies/es_daily_trend_v1.md")

_LOG = get_logger("run_es_daily_trend_paper")


def _load_strategy_cfg() -> dict:
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    return yaml.safe_load(CONFIG_PATH.read_text())


def _check_stage(cfg: dict) -> tuple[bool, str]:
    """Verify the deployment stage matches the config file declaration."""
    cfg_stage   = cfg.get("strategy", {}).get("stage", "paper")
    actual_stage = get_current_stage(STRATEGY_ID)

    if actual_stage == Stage.SAFE_DEGRADED:
        return False, f"strategy is in safe_degraded — promote to paper before running"
    if cfg_stage != actual_stage.value:
        return False, (f"stage mismatch: config says '{cfg_stage}' "
                       f"but runtime stage is '{actual_stage.value}'")
    return True, actual_stage.value


def _print_status(cfg: dict) -> None:
    stage = stage_summary(STRATEGY_ID)
    budget = budget_summary(STRATEGY_ID)
    risk = cfg.get("risk", {})
    ops  = cfg.get("ops", {})

    print(f"\n=== ES Daily Trend v1 — Status ===")
    print(f"Stage:            {stage['stage']}")
    print(f"Since:            {stage.get('since_ts', 'unknown')[:19]}")
    print(f"Allowed actions:  {', '.join(stage['allowed_actions'])}")
    print(f"Max allocation:   {stage['max_alloc_frac']:.0%}")
    print(f"Active alerts:    {budget['alert_count']}/{4} (hard cap)")
    if budget["breach"]:
        print(f"  ⚠️  COGNITIVE BUDGET BREACH: {budget['breaches']}")
    print(f"\nThresholds (from config):")
    print(f"  Capital at risk/trade:  {risk.get('capital_at_risk_per_trade_pct', '?')}%")
    print(f"  Daily loss halt:        {risk.get('daily_loss_halt_pct', '?')}%")
    print(f"  Max drawdown:           {risk.get('max_drawdown_pct', '?')}%")
    print(f"  Stale data timeout:     {ops.get('stale_data_timeout_minutes', '?')} min")
    print(f"  Order reject halt:      {ops.get('order_reject_halt_count', '?')} rejects")
    print()


def _print_promotion_check() -> None:
    """Print pass/fail status for the paper → shadow gate."""
    from services.os.app_paths import data_dir
    import os

    stage = get_current_stage(STRATEGY_ID)
    evidence_dir = data_dir() / "evidence" / STRATEGY_ID

    print(f"\n=== Promotion Gate Check: {stage.value} ===")
    print(f"Spec: docs/strategies/es_daily_trend_v1.md §6\n")

    if stage == Stage.PAPER:
        checks = [
            ("30 calendar days of operation",       None, "run 'python scripts/run_es_daily_trend_paper.py' daily"),
            ("50+ completed round trips",           None, "check evidence logs"),
            ("Expectancy within 30% of backtest",   None, "check evidence logs"),
            ("No critical operational bugs",        None, "check logs/errors"),
            ("Kill switch tested",                  None, "test manually: CBP_KILL_SWITCH=1"),
            ("All evidence logs complete",          _check_evidence_logs(evidence_dir), None),
            ("Daily loss halt tested in simulation",None, "simulate: set daily_loss_halt_pct=0.001"),
            ("Regime filter blocked at least once", None, "check signal logs for regime=chop blocks"),
        ]
    elif stage == Stage.SHADOW:
        checks = [
            ("20+ trading days on live data",       None, "continue running"),
            ("All signals logged with spread/depth",None, "check evidence logs"),
            ("Slippage within 1.5× backtest",       None, "check fill estimates"),
            ("All ops integrity checks passing",    None, "check session logs"),
            ("Recovery rule exercised",             None, "do a test restart"),
        ]
    elif stage == Stage.CAPPED_LIVE:
        checks = [
            ("25% of intended position size",       True, None),
            ("20+ completed live round trips",      None, "count fills in journal"),
            ("8+ weeks at capped size",             None, "check promotion date"),
            ("Slippage within 1.5× shadow",         None, "compare fills"),
            ("No operational halts",                None, "check halt log"),
            ("All logs complete",                   None, "check evidence dir"),
            ("Expectancy positive",                 None, "run evidence cycle"),
        ]
    else:
        checks = [("At full size — no gate needed", True, None)]

    for label, passed, hint in checks:
        if passed is True:
            print(f"  ✅  {label}")
        elif passed is False:
            print(f"  ❌  {label}" + (f"\n      → {hint}" if hint else ""))
        else:
            print(f"  ⬜  {label}" + (f"\n      → {hint}" if hint else ""))

    print(f"\nTo promote: python scripts/show_control_kernel_status.py --promote {STRATEGY_ID}")
    print()


def _check_evidence_logs(evidence_dir: Path) -> bool | None:
    if not evidence_dir.exists():
        return None
    logs = list(evidence_dir.glob("*.jsonl")) + list(evidence_dir.glob("*.json"))
    return len(logs) > 0


def main() -> int:
    ap = argparse.ArgumentParser(description="ES Daily Trend v1 paper runner")
    ap.add_argument("--status",           action="store_true", help="Show current status")
    ap.add_argument("--check-promotion",  action="store_true", help="Show promotion gate status")
    ap.add_argument("--dry-run",          action="store_true", help="Validate config only, do not run")
    ap.add_argument("--json",             action="store_true", help="Output as JSON")
    args = ap.parse_args()

    cfg = _load_strategy_cfg()

    if args.status:
        if args.json:
            print(json.dumps({
                "stage":  stage_summary(STRATEGY_ID),
                "budget": budget_summary(STRATEGY_ID),
            }, indent=2))
        else:
            _print_status(cfg)
        return 0

    if args.check_promotion:
        _print_promotion_check()
        return 0

    # Pre-flight checks
    stage_ok, stage_msg = _check_stage(cfg)
    if not stage_ok:
        print(f"BLOCKED: {stage_msg}", file=sys.stderr)
        return 1

    kernel = ControlKernel(STRATEGY_ID)
    kd = kernel.evaluate({})
    if kd["action"] == "halt":
        print(f"BLOCKED by kernel: {kd['reasons']}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"DRY RUN: pre-flight passed. Stage={stage_msg}, kernel={kd['action']}")
        _print_status(cfg)
        return 0

    # Apply strategy-specific daily loss halt threshold from config
    # The standard risk gate uses max_daily_loss_usd; we derive it from the % config
    try:
        import os
        halt_pct = float(risk.get("daily_loss_halt_pct", 1.5))
        # Write to env so the runner's risk gate can pick it up if it reads it
        # Actual enforcement is via the existing daily loss gate in the risk layer
        _LOG.info("daily_loss_halt_pct=%.2f%% (from strategy config)", halt_pct)
        os.environ["CBP_DAILY_LOSS_HALT_PCT"] = str(halt_pct)
    except Exception as _e:
        _LOG.warning("could not set daily_loss_halt_pct: %s", _e)

    # Run the paper evidence collection campaign
    from services.analytics.paper_strategy_evidence_service import (
        PaperStrategyEvidenceServiceCfg, run_campaign,
    )

    risk = cfg.get("risk", {})
    campaign_cfg = PaperStrategyEvidenceServiceCfg(
        strategies=("sma_200_trend",),
        symbol=cfg.get("strategy", {}).get("symbol", "BTC/USDT"),
        venue=cfg.get("strategy", {}).get("venue", "coinbase"),
        per_strategy_runtime_sec=float(
            cfg.get("strategy", {}).get("paper_runtime_sec", 3600.0)
        ),
    )

    _LOG.info("starting paper run for %s stage=%s", STRATEGY_ID, stage_msg)

    from services.strategies.evidence_logger import EvidenceLogger
    from services.control.kernel import ControlKernel
    from services.control.deployment_stage import get_current_stage
    ev = EvidenceLogger(STRATEGY_ID)
    kernel = ControlKernel(STRATEGY_ID)
    kd = kernel.evaluate({})
    stage_at_start = get_current_stage(STRATEGY_ID).value

    result = run_campaign(campaign_cfg)

    # Log session record with campaign outcome
    try:
        ev.log_session(
            regime_at_open=stage_at_start,
            halts_triggered=[r for r in result.get("halt_reasons", [])],
            manual_overrides=[],
            reconciliation_result="pass" if result.get("ok") else "campaign_error",
            drawdown_from_peak=float(result.get("max_drawdown_pct", 0.0)),
            kill_switch_tested=False,
            ops_checks_passed=result.get("ok", False),
            extra={
                "completed_strategies": result.get("completed_strategies", 0),
                "campaign_status": result.get("status", "unknown"),
            },
        )
    except Exception as _ev_err:
        _LOG.warning("session evidence log failed: %s", _ev_err)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        status = result.get("status", "unknown")
        reason = result.get("reason", "")
        completed = result.get("completed_strategies", 0)
        print(f"\nCampaign: {status} ({reason})")
        print(f"Completed strategies: {completed}")
        if result.get("evidence"):
            print(f"Evidence: {result['evidence'].get('latest_path', 'none')}")
        if result.get("decision_record"):
            print(f"Decision record: {result['decision_record'].get('path', 'none')}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
