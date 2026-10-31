"""Offline counterexample, NOT a reconstruction or a changed acceptance rule."""
import ast
from copy import deepcopy
from pathlib import Path

from scripts.research import companion_evidence_checks as checks
from tests.test_companion_evidence_checks import case, offline, orchestrator_functions


def unavailable_snapshot():
    root = Path(__file__).resolve().parents[1]
    path = root / "phase1_research_copilot/shared/tools.py"
    names = {"_asset_symbol", "_default_market_snapshot"}
    nodes = [n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == names
    ns = {"Any": object}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), ns)
    return ns["_default_market_snapshot"]("BTC")


def test_controlled_empty_market_fixture_still_passes(case):
    result = checks.evaluate_diagnostic(*case)
    assert result["diagnostic"] == {"stage": "complete", "code": "ok"}


def test_real_unavailable_snapshot_shape_rejected_by_existing_verifier(case):
    snapshot = unavailable_snapshot()
    assert snapshot["ok"] is False and snapshot["price"] is None
    assert snapshot["asset"] == "BTC" and snapshot["symbol"] == "BTC/USDT"
    assert snapshot["reason"] == "market_service_unavailable"
    producer = orchestrator_functions()["_build_evidence_bundle"]
    bundle = producer({"get_market_snapshot": snapshot})
    assert bundle["market_snapshot"] == snapshot
    assert set(snapshot) - {"latest_price", "price", "ok", "reason", "change_pct", "window_samples"}
    raw, view, actual, approvals = deepcopy(case)
    raw["evidence_bundle"]["market_snapshot"] = bundle["market_snapshot"]
    result = checks.evaluate_diagnostic(raw, view, actual, approvals)
    assert result["diagnostic"] == {"stage": "bundle_market", "code": "rejected"}
    assert result["checks"] == dict.fromkeys(checks.KEYS, False)
