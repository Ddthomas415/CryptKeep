from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
import socket
import sqlite3

import pytest

from services.analytics import crypto_edges as edges
from dashboard.services import crypto_edge_research as research
from storage import crypto_edge_store_sqlite as storage


ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / "docs/review_artifacts/funding_archive_views_20261029/before"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise AssertionError("external boundary forbidden")
    connect = sqlite3.connect
    def temporary(database, *args, **kwargs):
        assert Path(database).resolve().is_relative_to(tmp_path.resolve())
        return connect(database, *args, **kwargs)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(sqlite3, "connect", temporary)
    monkeypatch.setattr(storage, "ensure_dirs", refuse)


def test_legacy_archive_rate_does_not_become_verified_annualized_estimate():
    report = edges.build_crypto_edge_report(
        funding_rows=[{"symbol": "EXAMPLE", "venue": "okx",
                       "funding_rate": 0.0001, "interval_hours": 8.0}])
    assert report["funding"]["annualized_carry_pct"] is None
    assert report["funding"]["dominant_bias"] == "unknown"


@pytest.mark.parametrize("rows", [
    [], [{"funding_rate": 0}], [{"funding_rate": None}],
    [{"funding_rate": -0.0001, "interval_hours": 1}],
    [{"funding_rate": 0.0004, "interval_hours": 4}, {"funding_rate": 0.0008, "interval_hours": 8}],
    [{"funding_rate": 0.1, "normalization_eligible": True}],
])
def test_archive_reporting_never_qualifies_unknown_or_claimed_metadata(rows):
    original = deepcopy(rows)
    summary = edges.build_crypto_edge_report(funding_rows=rows, funding_interval_hours=1)["funding"]
    assert summary["normalization_eligible"] is False
    assert summary["count"] == len(rows) and summary["ok"] is False
    for field in ("avg_funding_rate", "last_funding_rate", "annualized_carry_pct",
                  "positive_ratio", "negative_ratio"):
        assert summary[field] is None
    assert summary["dominant_bias"] == "unknown"
    assert [r["raw_observation"] for r in summary["rows"]] == original
    assert rows == original


def test_diagnostic_rows_own_their_raw_copy():
    row = {"funding_rate": 0.001, "info": {"unverified": "value"}}
    summary = edges.summarize_unverified_funding([row])
    row["info"]["unverified"] = "changed"
    assert summary["rows"][0]["raw_observation"]["info"]["unverified"] == "value"


def test_archive_reads_preserve_exact_stored_rows_and_other_reports(tmp_path):
    store = storage.CryptoEdgeStoreSQLite(path=str(tmp_path / "archive.sqlite"))
    for index, rate in enumerate((0.0001, 0.0002), start=1):
        store.append_funding_rows(
            [{"symbol": "EXAMPLE", "venue": "okx", "funding_rate": rate, "interval_hours": 8}],
            source="synthetic", capture_ts=f"2026-10-29T0{index}:00:00Z")
    store.append_basis_rows([{"symbol": "EXAMPLE", "venue": "okx", "spot_px": 100, "perp_px": 101}],
                            source="synthetic")
    with sqlite3.connect(store.path) as conn:
        before = conn.execute("SELECT * FROM funding_snapshots ORDER BY id").fetchall()
    report = store.latest_report_for_source(source="synthetic")
    history = store.recent_funding_history(limit=2)
    assert report["funding"]["count"] == 1
    assert report["funding"]["annualized_carry_pct"] is None
    assert all(row["annualized_carry_pct"] is None and row["positive_ratio"] is None for row in history)
    assert [r["capture_ts"] for r in history] == ["2026-10-29T02:00:00Z", "2026-10-29T01:00:00Z"]
    assert report["basis"]["avg_basis_bps"] == pytest.approx(100)
    assert len(store.latest_funding_rows_for_source(source="synthetic")) == 1
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT * FROM funding_snapshots ORDER BY id").fetchall() == before


@pytest.mark.parametrize("interval", [1, 4, 8])
def test_frozen_uniform_interval_model_function_is_unchanged(interval):
    before = ast.parse((BEFORE / "crypto_edges.py").read_bytes())
    current = ast.parse((ROOT / "services/analytics/crypto_edges.py").read_bytes())
    name = "summarize_funding_carry"
    old_node = next(n for n in before.body if isinstance(n, ast.FunctionDef) and n.name == name)
    new_node = next(n for n in current.body if isinstance(n, ast.FunctionDef) and n.name == name)
    assert ast.dump(old_node, include_attributes=False) == ast.dump(new_node, include_attributes=False)
    ns = dict(vars(edges))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[old_node], type_ignores=[])), str(BEFORE), "exec"), ns)
    rows = [{"funding_rate": 0.0001}, {"funding_rate": -0.00005}]
    assert edges.summarize_funding_carry(rows, interval_hours=interval) == ns[name](rows, interval_hours=interval)


SUMMARIES = [None, {}, {"annualized_carry_pct": None},
             {"annualized_carry_pct": 0, "dominant_bias": "flat"},
             {"annualized_carry_pct": 12, "dominant_bias": "long_pays"},
             {"annualized_carry_pct": 99, "normalization_eligible": True},
             {"annualized_carry_pct": float("nan")}]


@pytest.mark.parametrize("summary", SUMMARIES)
def test_formatter_never_upgrades_cached_values_or_flags(summary):
    view = edges.funding_display(summary)
    assert view["carry"] == "N/A" and view["bias"] == "Unknown"


@pytest.mark.parametrize("path", ["dashboard/pages/35_Research.py", "dashboard/pages/60_Operations.py"])
@pytest.mark.parametrize("summary", SUMMARIES)
def test_actual_page_funding_cards_show_missing_not_zero(path, summary):
    tree = ast.parse((ROOT / path).read_bytes())
    card = next(n for n in ast.walk(tree) if isinstance(n, ast.Dict) and any(
        isinstance(k, ast.Constant) and k.value == "label" and isinstance(v, ast.Constant)
        and v.value == "Funding Carry" for k, v in zip(n.keys, n.values)))
    ns = {"funding": summary, "funding_display": edges.funding_display}
    result = eval(compile(ast.fix_missing_locations(ast.Expression(body=card)), path, "eval"), ns)
    assert result["value"] == "N/A" and result["delta"] == "Unknown"


@pytest.mark.parametrize("summary", SUMMARIES)
def test_summary_component_uses_the_same_guard(summary):
    path = ROOT / "dashboard/components/summary_panels.py"
    tree = ast.parse(path.read_bytes())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_structural_edge_metrics")
    ns = {"funding_display": edges.funding_display}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec"), ns)
    rows = ns["build_structural_edge_metrics"]({"funding": summary, "basis": {"avg_basis_bps": 1.2}})
    funding = next(row for row in rows if row["label"] == "Funding Bias")
    assert funding["value"] == "Unknown" and funding["delta"] == "N/A"
    assert next(row for row in rows if row["label"] == "Average Basis")["value"] == "1.20 bps"


@pytest.mark.parametrize("summary", SUMMARIES)
def test_digest_funding_expression_does_not_report_a_cached_yield(summary):
    path = ROOT / "dashboard/services/digest/builders.py"
    tree = ast.parse(path.read_bytes())
    item = next(n for n in ast.walk(tree) if isinstance(n, ast.Dict) and any(
        isinstance(k, ast.Constant) and k.value == "name" and isinstance(v, ast.Constant)
        and v.value == "Funding analytics" for k, v in zip(n.keys, n.values)))
    ns = {"live_snapshot": {"funding": summary}, "funding_display": edges.funding_display}
    result = eval(compile(ast.fix_missing_locations(ast.Expression(body=item)), str(path), "eval"), ns)
    if isinstance(summary, dict):
        assert result["summary"] == "Bias Unknown / carry N/A"
    else:
        assert result["summary"] is None


def test_cached_funding_trend_is_unverified_not_a_numeric_delta():
    funding = [{"annualized_carry_pct": 12, "dominant_bias": "long_pays"},
               {"annualized_carry_pct": 8, "dominant_bias": "long_pays"}]
    rows = research._build_trend_rows(funding_history=funding,
                                    basis_history=[{"avg_basis_bps": 6}, {"avg_basis_bps": 4}],
                                    dislocation_history=[])
    assert rows[0]["theme"] == "funding" and rows[0]["latest"] == "N/A"
    assert rows[0]["vs_prior"] == "Unverified comparison"
    assert rows[1]["theme"] == "basis" and rows[1]["latest"] == "6.00 bps"


def test_old_archive_report_is_a_negative_control():
    tree = ast.parse((BEFORE / "crypto_edges.py").read_bytes())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_crypto_edge_report")
    ns = dict(vars(edges))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(BEFORE), "exec"), ns)
    report = ns["build_crypto_edge_report"](funding_rows=[{"funding_rate": 0.0001}])
    assert report["funding"]["annualized_carry_pct"] == pytest.approx(10.95)
