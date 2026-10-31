"""Closed exclusion marker and retained evidence gates, synthetic inputs only."""
import ast
from copy import deepcopy
from pathlib import Path
import tarfile

import pytest

from scripts.research import companion_evidence_checks as checks
from tests.test_companion_evidence_checks import case, offline, remote


def excluded(case):
    raw, view, actual, approvals = deepcopy(case)
    raw["probe_protocol"] = raw["assistant_status"]["probe_protocol"] = "single-cited-query-v1"
    raw["evidence_bundle"]["market"] = {
        "ok": False, "reason": "excluded_by_archival_probe", "latest_price": None,
        "change_pct": 0.0, "window_samples": 0}
    return raw, view, actual, approvals


def test_explicit_bound_exclusion_passes_existing_evidence(case):
    assert all(checks.evaluate(*excluded(case)).values())


def test_existing_no_market_contract_remains_accepted(case):
    assert all(checks.evaluate(*case).values())


def test_remote_diagnostic_accepts_bound_exclusion_without_new_query(monkeypatch, case):
    value = excluded(case)
    result, calls = remote(monkeypatch, value, diagnostic=True)
    assert result["diagnostic"] == {"stage": "complete", "code": "ok"}
    assert all(result["checks"].values())
    assert sum(type(call) is tuple and call[0] == checks.SOURCE_SQL for call in calls) == 1


@pytest.mark.parametrize("change", [
    "raw_protocol_missing", "status_protocol_missing", "raw_protocol_wrong", "snapshot_location",
    "extra", "missing", "nonnull_price", "zero_price", "available", "numeric_ok",
    "positive_change", "bool_change", "positive_samples", "float_samples", "bool_samples",
    "unknown_reason", "asset", "archive", "witness", "execution",
])
def test_exclusion_cannot_waive_evidence_or_no_price_contract(case, change):
    raw, view, actual, approvals = excluded(case)
    market = raw["evidence_bundle"]["market"]
    if change == "raw_protocol_missing": raw.pop("probe_protocol")
    elif change == "status_protocol_missing": raw["assistant_status"].pop("probe_protocol")
    elif change == "raw_protocol_wrong": raw["probe_protocol"] = "unknown"
    elif change == "snapshot_location": raw["evidence_bundle"]["market_snapshot"] = raw["evidence_bundle"].pop("market")
    elif change == "extra": market["source"] = "PRIVATE"
    elif change == "missing": market.pop("latest_price")
    elif change == "nonnull_price": market["latest_price"] = 100.0
    elif change == "zero_price": market["latest_price"] = 0.0
    elif change == "available": market["ok"] = True
    elif change == "numeric_ok": market["ok"] = 0
    elif change == "positive_change": market["change_pct"] = 1.0
    elif change == "bool_change": market["change_pct"] = False
    elif change == "positive_samples": market["window_samples"] = 1
    elif change == "float_samples": market["window_samples"] = 0.0
    elif change == "bool_samples": market["window_samples"] = False
    elif change == "unknown_reason": market["reason"] = "excluded"
    elif change == "asset": raw["asset"] = "ETH"
    elif change == "archive": raw["archive_view"]["derived_sha256"] = "f" * 64
    elif change == "witness": approvals.clear()
    else: raw["execution_disabled"] = False
    result = checks.evaluate_diagnostic(raw, view, actual, approvals)
    assert result["checks"] == dict.fromkeys(checks.KEYS, False)
    assert result["diagnostic"]["code"] == "rejected"


def test_ordinary_market_sql_and_summary_ast_are_unchanged():
    root = Path(__file__).resolve().parents[1]
    path = "phase1_research_copilot/memory_retrieval/main.py"
    with tarfile.open(root / "docs/review_artifacts/companion_archival_market_exclusion_20261026/prechange.tar") as archive:
        before = ast.parse(archive.extractfile(path).read())
    after = ast.parse((root / path).read_text())

    def sql(tree):
        return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
                and isinstance(n.value, str) and "FROM market_ticks" in n.value]

    def summary(tree):
        return ast.dump(next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                             and n.name == "_compute_market_summary"))

    assert sql(before) == sql(after) and len(sql(before)) == 1
    assert summary(before) == summary(after)
