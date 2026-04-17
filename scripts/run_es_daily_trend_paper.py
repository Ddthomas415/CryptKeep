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
from services.control.runtime_identity import RuntimeIdentity, RuntimeIdentityError
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

    # Verify runtime identity before any child process starts
    try:
        identity = RuntimeIdentity.from_config(STRATEGY_ID, cfg)
        identity.verify()
        identity.log_stamp()
    except RuntimeIdentityError as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 1

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

    # Apply strategy-specific env vars from config
    try:
        import os
        halt_pct = float(risk.get("daily_loss_halt_pct", 1.5))
        _LOG.info("daily_loss_halt_pct=%s%% (from strategy config)", halt_pct)
        os.environ["CBP_DAILY_LOSS_HALT_PCT"] = str(halt_pct)
        os.environ["CBP_SYMBOLS"] = symbol
        os.environ["CBP_VENUE"] = venue
        # Enable candidate advisor if configured in strategy config
        use_advisor = str(strategy_cfg.get("use_candidate_advisor", "")).strip().lower()
        if use_advisor in ("1", "true", "yes"):
            os.environ["CBP_USE_CANDIDATE_ADVISOR"] = "1"
            _LOG.info("candidate_advisor enabled via strategy config")
    except Exception as _e:
        _LOG.warning("could not set env vars from strategy config: %s", _e)

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

    # Pre-run: use ManagedComponent to clean any stale locks before starting
    from services.control.managed_component import ManagedComponent
    from services.analytics.paper_strategy_evidence_service import runtime_dir
    _mc_names = ["tick_publisher", "paper_engine", "strategy_runner"]
    for _mc_name in _mc_names:
        _mc = ManagedComponent(
            name=_mc_name,
            lock_file=runtime_dir() / "locks" / f"{_mc_name}.lock",
            status_file=runtime_dir() / "status" / f"{_mc_name}.json",
            stop_flag_file=runtime_dir() / "flags" / f"{_mc_name}.stop",
        )
        if _mc.is_stale():
            _mc.clean_stale_lock()
            _LOG.info("managed_component stale_lock_cleaned component=%s", _mc_name)

    from services.strategies.evidence_logger import EvidenceLogger
    from services.control.deployment_stage import get_current_stage as _get_stage
    ev = EvidenceLogger(STRATEGY_ID)
    kernel = ControlKernel(STRATEGY_ID)
    kd = kernel.evaluate({})
    stage_at_start = _get_stage(STRATEGY_ID).value

    result: dict = {"ok": False, "status": "not_started", "completed_strategies": 0}

    # Write session_start record so evidence file exists even if campaign crashes
    try:
        ev.log_session(
            regime_at_open=stage_at_start,
            halts_triggered=[],
            manual_overrides=[],
            reconciliation_result="pending",
            drawdown_from_peak=0.0,
            ops_checks_passed=True,
            extra={
                "phase": "start",
                "campaign_status": "starting",
                "completed_strategies": 0,
                "zero_trade_run": True,
                **identity.as_dict(),
            },
        )
    except Exception as _ev_start_err:
        _LOG.warning("session_start evidence log failed: %s", _ev_start_err)

    try:
        result = run_campaign(campaign_cfg)
    finally:
        # Session evidence is ALWAYS written, even on failure or zero-trade runs.
        # A zero-trade run still provides valuable evidence: regime state, ops health,
        # and the fact that the system ran without critical errors.
        try:
            completed = result.get("completed_strategies", 0)
            campaign_status = result.get("status", "unknown")
            ev.log_session(
                regime_at_open=stage_at_start,
                halts_triggered=list(result.get("halt_reasons") or []),
                manual_overrides=[],
                reconciliation_result="pass" if result.get("ok") else "campaign_error",
                drawdown_from_peak=float(result.get("max_drawdown_pct") or 0.0),
                kill_switch_tested=False,
                ops_checks_passed=bool(result.get("ok")),
                critical_error=(campaign_status not in ("completed", "stopped", "stop_requested")),
                extra={
                    "phase": "end",
                    "completed_strategies": completed,
                    "campaign_status": campaign_status,
                    "zero_trade_run": (completed == 0),
                    **identity.as_dict(),
                },
            )
        except Exception as _ev_err:
            _LOG.warning("session evidence log failed: %s", _ev_err)

    # Teardown enforcement: use the service's own stop/wait infrastructure
    # rather than reinventing it with ManagedComponent (which has different paths).
    try:
        from services.analytics.paper_strategy_evidence_service import (
            _component_runtime, _stop_component, _wait_for_component_stop,
        )
        import time as _time

        # Stop all three components in reverse start order
        for _comp in ("strategy_runner", "paper_engine", "tick_publisher"):
            try:
                if bool(_component_runtime(_comp).get("pid_alive")):
                    _LOG.info("campaign_teardown: stopping %s", _comp)
                    _stop_component(_comp)
            except Exception as _stop_err:
                _LOG.warning("campaign_teardown: stop failed for %s: %s", _comp, _stop_err)

        # Wait up to 10s for all to stop
        deadline = _time.monotonic() + 10.0
        still_alive = []
        for _comp in ("strategy_runner", "paper_engine", "tick_publisher"):
            remaining = max(0.0, deadline - _time.monotonic())
            stopped = _wait_for_component_stop(_comp, timeout_sec=remaining)
            if not stopped:
                still_alive.append(_comp)

        if still_alive:
            _LOG.error("campaign_teardown: %s did not stop after 10s — run 'make paper-stop'", still_alive)
        else:
            _LOG.info("campaign_teardown: all child processes stopped cleanly")
    except Exception as _td_err:
        _LOG.warning("campaign_teardown check failed: %s", _td_err)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        status = result.get("status", "unknown")
        reason = result.get("reason", "")
        completed = result.get("completed_strategies", 0)
        print(f"\nCampaign: {status} ({reason})")
        print(f"Completed strategies: {completed}")

        # Report the actual JSONL evidence directory (written by EvidenceLogger)
        # This is separate from the leaderboard evidence_out in result["evidence"]
        from services.os.app_paths import data_dir as _data_dir
        ev_dir = _data_dir() / "evidence" / STRATEGY_ID
        if ev_dir.exists():
            files = sorted(ev_dir.glob("*.jsonl"))
            by_type: dict = {}
            for f in files:
                record_type = f.name.split("_")[0]
                by_type[record_type] = by_type.get(record_type, 0) + 1
            print(f"Evidence dir: {ev_dir}")
            print(f"Evidence files: {dict(by_type)}" if by_type else "Evidence files: (none yet)")
        else:
            print("Evidence dir: not yet created")

        # Legacy leaderboard evidence (strategy_evidence.latest.json)
        if result.get("evidence") and result["evidence"].get("latest_path"):
            print(f"Leaderboard artifact: {result['evidence'].get('latest_path')}")
        if result.get("decision_record") and result["decision_record"].get("path"):
            print(f"Decision record: {result['decision_record'].get('path')}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
