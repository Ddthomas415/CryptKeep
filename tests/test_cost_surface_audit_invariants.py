from __future__ import annotations

import inspect
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _grep(pattern: str, *paths: str) -> list[str]:
    try:
        proc = subprocess.run(
            ["grep", "-rn", "--include=*.py", pattern, *paths],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception:
        pytest.skip("grep unavailable")
    lines: list[str] = []
    for line in proc.stdout.splitlines():
        if line.startswith("tests/"):
            continue
        if "cost_assumptions.py" in line:
            continue
        lines.append(line)
    return lines


def test_backtest_defaults_are_derived_from_walk_forward_signature():
    from services.analytics.cost_assumptions import backtest_cost_defaults
    from services.backtest.walk_forward import run_anchored_walk_forward

    defaults = backtest_cost_defaults()
    sig = inspect.signature(run_anchored_walk_forward)

    assert defaults["derivable"] is True
    assert defaults["fee_bps"] == sig.parameters["fee_bps"].default
    assert defaults["slippage_bps"] == sig.parameters["slippage_bps"].default


def test_evidence_service_defaults_are_derived_from_dataclass():
    from services.analytics.cost_assumptions import evidence_service_cost_defaults
    from services.analytics.paper_strategy_evidence_service import PaperStrategyEvidenceServiceCfg

    defaults = evidence_service_cost_defaults()
    cfg = PaperStrategyEvidenceServiceCfg()

    assert defaults["derivable"] is True
    assert defaults["fee_bps"] == cfg.fee_bps
    assert defaults["slippage_bps"] == cfg.slippage_bps


def test_paper_engine_default_constants_match_cfg_defaults(monkeypatch):
    from services.analytics import cost_assumptions
    from services.execution import paper_engine

    monkeypatch.setattr(paper_engine, "load_user_yaml", lambda: {})

    cfg = paper_engine._cfg()

    assert cfg["fee_bps"] == cost_assumptions.ENGINE_DEFAULT_FEE_BPS
    assert cfg["slippage_bps"] == cost_assumptions.ENGINE_DEFAULT_SLIPPAGE_BPS


def test_audit_claim_backtest_costs_do_not_read_user_yaml():
    suspects = _grep("load_user_yaml\\|load_user_config\\|paper_trading", "services/backtest")

    assert suspects == [], (
        "services/backtest now appears to read user config for costs. Update "
        "cost_assumptions.py's backtest surface note and this invariant.\n"
        + "\n".join(suspects)
    )


def test_audit_claim_paper_fees_lookup_still_has_no_production_callers():
    callers = _grep("fee_bps_paper\\|fee_cost_for_notional", "services", "scripts", "dashboard")
    callers = [line for line in callers if not line.startswith("services/execution/paper_fees.py")]

    assert callers == [], (
        "paper_fees now has production callers. Its dormant role in "
        "cost_assumptions.py must be revised.\n" + "\n".join(callers)
    )


def test_audit_claim_paper_engine_still_reads_paper_trading_config():
    src = (REPO / "services/execution/paper_engine.py").read_text(encoding="utf-8")

    assert "paper_trading" in src
    assert "fee_bps" in src
    assert "slippage_bps" in src
