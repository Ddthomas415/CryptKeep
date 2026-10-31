"""Deterministic/reference-only SB-1 tests; no RNG, development or audit paths."""
import ast
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import socket
import subprocess
from typing import Optional

import numpy as np
import pytest

from services.backtest import sb1_prototype as sb1


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT/"tests/fixtures/sb1_arch720_reference.py"
CAPTURE = ROOT/"docs/review_artifacts/ed002_sb1_reference_20261027"


@pytest.fixture(autouse=True)
def deterministic_only(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("SB-1 prototype attempted randomness or external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, forbidden)
    for name in ("default_rng", "Generator", "PCG64", "random", "standard_normal"):
        monkeypatch.setattr(np.random, name, forbidden)


def reference_function(name):
    tree = ast.parse(REFERENCE.read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = {"np": np, "Optional": Optional, "Float64Array": np.ndarray, "Int64Array": np.ndarray}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "captured_arch_function_only", "exec"), namespace)
    return namespace[name]


def daily_panel(columns=None):
    columns = {} if columns is None else columns
    return {arm: [{"day_end_ms": (i+1)*sb1.DAY, "return": float(values[i])}
                 for i in range(sb1.DAYS)]
            for arm in sb1.ARMS for values in [columns.get(arm, np.zeros(sb1.DAYS))]}


@pytest.fixture(scope="module")
def supplied_draws():
    starts = np.tile(np.arange(sb1.DAYS, dtype=np.int64), (sb1.REPEATS, 1))
    uniforms = np.full(starts.shape, .5)
    starts.flags.writeable = uniforms.flags.writeable = False
    return starts, uniforms


def test_reference_bytes_and_function_text_match_tagged_capture():
    manifest = json.loads((CAPTURE/"manifest.json").read_text())
    for name, record in manifest["files"].items():
        assert hashlib.sha256((CAPTURE/name).read_bytes()).hexdigest() == record["sha256"]
    local = REFERENCE.read_text()
    for filename, name in (("base.py.txt", "_single_optimal_block"),
                           ("samplers.py.txt", "stationary_bootstrap_sample_python")):
        source = (CAPTURE/filename).read_text()
        a = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
        b = next(n for n in ast.parse(local).body if isinstance(n, ast.FunctionDef) and n.name == name)
        assert ast.get_source_segment(source, a) == ast.get_source_segment(local, b)


@pytest.mark.parametrize("kind", ["linear", "wave", "fast_wave", "alternating", "pulse"])
def test_corrected_selector_matches_arch_reference_without_importing_arch(kind):
    t = np.arange(sb1.DAYS, dtype=float)
    values = {"linear": t/182, "wave": np.sin(t*.31)+.2*np.cos(t*.71),
        "fast_wave": np.sin(t*2.17)+.1*np.cos(t*.77),
        "alternating": (-1.)**t+.2*np.sin(t*.53), "pulse": (t % 11 == 0).astype(float)}[kind]
    expected = reference_function("_single_optimal_block")(values)[0]
    assert sb1.stationary_length(values) == pytest.approx(expected, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("mean", [1, 2, 4, 19])
def test_supplied_sampler_matches_reference_restart_threshold_and_wrap(mean):
    starts = np.array([[7, 3, 2, 6, 1, 5, 4, 0], [4, 7, 1, 2, 6, 0, 3, 5]], dtype=np.int64)
    u = np.array([[.4, 0., .5, 1/mean if mean > 1 else .9, .9, .001, .8, .4],
                  [.5, .9, .01, .9, .01, .9, .01, .9]])
    expected = np.stack([reference_function("stationary_bootstrap_sample_python")(r.copy(), v, 1/mean)
                         for r, v in zip(starts, u)])
    original = starts.copy()
    actual = sb1.stationary_indices(starts, u, mean)
    assert np.array_equal(actual, expected) and np.array_equal(starts, original)
    assert np.array_equal(actual, sb1.stationary_indices(starts.astype(np.uint64), u, mean))


def test_selector_inputs_include_all_arms_differences_and_centered_squares(monkeypatch):
    t = np.arange(sb1.DAYS, dtype=float)
    logs = np.stack([np.sin(t*(i+1)*.19)*.01 for i in range(7)], axis=1)
    seen = []
    def selector(values):
        seen.append(values.copy())
        return 1.25 if len(seen) < 20 else 5.1
    monkeypatch.setattr(sb1, "stationary_length", selector)
    result = sb1.select_mean_block(logs)
    base = [logs[:, i] for i in range(7)] + [logs[:, i]-logs[:, 3] for i in range(3)]
    expected = base+[(x-x.mean())**2 for x in base]
    assert len(seen) == 20 and all(np.array_equal(a, b) for a, b in zip(seen, expected))
    assert result["mean_block_length"] == 6 and result["status"] == "COMPLETE"


def test_constants_and_insufficient_effective_blocks_are_explicit(monkeypatch):
    degenerate = sb1.select_mean_block(np.zeros((182, 7)))
    assert degenerate["degenerate"] and degenerate["mean_block_length"] == 1
    assert len(degenerate["constant_columns"]) == 20
    t = np.arange(sb1.DAYS, dtype=float)
    logs = np.tile(np.sin(t*.3)[:, None], (1, 7))
    monkeypatch.setattr(sb1, "stationary_length", lambda values: 18.1)
    result = sb1.select_mean_block(logs)
    assert result["status"] == "INCOMPLETE" and result["mean_block_length"] == 19
    assert result["reason"] == "insufficient_effective_blocks"


def test_undefined_nonconstant_selector_never_falls_back(monkeypatch):
    def invalid(values):
        raise FloatingPointError("undefined")
    monkeypatch.setattr(sb1, "stationary_length", invalid)
    logs = np.tile(np.arange(182)[:, None], (1, 7))
    result = sb1.select_mean_block(logs)
    assert result["status"] == "INCOMPLETE" and result["reason"].startswith("undefined_selector:")
    assert "mean_block_length" not in result


@pytest.mark.parametrize("effect", [0., .001, -.001])
def test_deterministic_full_recomposition_never_certifies_method(effect, supplied_draws):
    panel = daily_panel({name: np.full(182, effect) for name in sb1.FAMILIES})
    original = deepcopy(panel)
    a = sb1.sb1_screen(panel, initial_cash=1000, starts=supplied_draws[0], uniforms=supplied_draws[1])
    assert a["computation_status"] == "COMPLETE" and panel == original
    expected = 1000*math.expm1(182*math.log1p(effect))
    for contrast in a["contrasts"].values():
        assert contrast["observed_net_wealth_difference"] == pytest.approx(expected)
        assert contrast["approximate_lower_bound"] == pytest.approx(expected)
    assert a["experiment_pass"] is None and a["statistical_validation"] == "INCOMPLETE"
    assert a["coverage_certified"] is False and a["one_based_order_rank"] == 334
    assert a["selection"]["degenerate"] and a["draws_sha256"]


def test_first_day_fee_is_retained_without_rebasing(supplied_draws, monkeypatch):
    values = np.zeros(182)
    values[0] = -.01
    # Isolate compounding, not a choice of selector based on the result.
    monkeypatch.setattr(sb1, "stationary_length", lambda x: 1.)
    result = sb1.sb1_screen(daily_panel(dict.fromkeys(sb1.FAMILIES, values)), initial_cash=1000,
                            starts=supplied_draws[0], uniforms=supplied_draws[1])
    assert result["contrasts"][sb1.FAMILIES[0]]["observed_net_wealth_difference"] == pytest.approx(-10)
    assert result["contrasts"][sb1.FAMILIES[0]]["approximate_lower_bound"] == pytest.approx(-10)


def test_bankruptcy_is_unknown_inference_not_a_deleted_loss(supplied_draws):
    values = np.zeros(182)
    values[0] = -1
    result = sb1.sb1_screen(daily_panel({sb1.FAMILIES[0]: values}), initial_cash=1000,
                            starts=supplied_draws[0], uniforms=supplied_draws[1])
    assert result["computation_status"] == "INCOMPLETE" and result["contrasts"] is None
    assert "exhaustion" in result["reason"]


@pytest.mark.parametrize("fault", ["calendar", "short", "nan", "bool", "capital", "missing_arm"])
def test_invalid_input_refused_without_rng(fault, supplied_draws):
    panel = daily_panel()
    capital = 1000
    if fault == "calendar": panel[sb1.FAMILIES[0]][0]["day_end_ms"] += sb1.DAY
    if fault == "short": panel["cash"].pop()
    if fault == "nan": panel["cash"][0]["return"] = float("nan")
    if fault == "bool": panel["cash"][0]["return"] = True
    if fault == "capital": capital = 1001
    if fault == "missing_arm": panel.pop("cash")
    with pytest.raises(ValueError):
        sb1.sb1_screen(panel, initial_cash=capital, starts=supplied_draws[0], uniforms=supplied_draws[1])


@pytest.mark.parametrize("fault", ["shape", "uniform", "index", "bool", "nan"])
def test_invalid_sampler_draws_are_refused(fault):
    starts, u = np.zeros((2, 8), dtype=np.int64), np.zeros((2, 8))
    if fault == "shape": u = u[:, :7]
    if fault == "uniform": u[0, 0] = 1.
    if fault == "index": starts[0, 0] = 8
    if fault == "bool": starts = starts.astype(bool)
    if fault == "nan": u[0, 0] = float("nan")
    with pytest.raises(ValueError):
        sb1.stationary_indices(starts, u, 2)


def test_full_nonconstant_recomposition_with_reference_indices(monkeypatch):
    # Stub only length selection to isolate the supplied-draw/recomposition path.
    monkeypatch.setattr(sb1, "stationary_length", lambda x: 4.)
    t = np.arange(182, dtype=float)
    base = .01*np.sin(t*.6)
    columns = dict.fromkeys(sb1.ARMS, np.expm1(base))
    columns[sb1.FAMILIES[0]] = np.expm1(base+.001)
    starts_row = ((np.arange(182)*7) % 182).astype(np.int64)
    u_row = np.full(182, .75)
    u_row[::11] = 0.
    starts = np.broadcast_to(starts_row, (20000, 182))
    u = np.broadcast_to(u_row, starts.shape)
    result = sb1.sb1_screen(daily_panel(columns), initial_cash=1000, starts=starts, uniforms=u)
    indices = reference_function("stationary_bootstrap_sample_python")(starts_row.copy(), u_row, .25)
    expected = 1000*(np.exp((base[indices]+.001).sum())-np.exp(base[indices].sum()))
    assert result["computation_status"] == "COMPLETE"
    assert result["selection"]["mean_block_length"] == 4
    assert result["contrasts"][sb1.FAMILIES[0]]["approximate_lower_bound"] == pytest.approx(expected)
    assert result["contrasts"][sb1.FAMILIES[1]]["approximate_lower_bound"] == 0


def test_actual_deterministic_persistent_fixture_abstains_without_length_override(supplied_draws):
    t = np.arange(182, dtype=float)
    logs = .01*(np.sin(t*.6)+.1*np.cos(t*1.71))
    result = sb1.sb1_screen(daily_panel(dict.fromkeys(sb1.ARMS, np.expm1(logs))), initial_cash=1000,
                            starts=supplied_draws[0], uniforms=supplied_draws[1])
    assert result["computation_status"] == "INCOMPLETE" and result["contrasts"] is None
    assert result["reason"] == "insufficient_effective_blocks"


def test_unrepresentable_wealth_is_unknown_not_a_positive_pass(supplied_draws):
    result = sb1.sb1_screen(daily_panel({sb1.FAMILIES[0]: np.full(182, 100.)}), initial_cash=1000,
                            starts=supplied_draws[0], uniforms=supplied_draws[1])
    assert result["computation_status"] == "INCOMPLETE" and result["contrasts"] is None
    assert result["experiment_pass"] is None
