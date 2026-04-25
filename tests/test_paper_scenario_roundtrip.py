"""
tests/test_paper_scenario_roundtrip.py

End-to-end contract tests for scripts/run_paper_scenario.py.
Contract: v1.3 — section 20 (blocking).

All tests use pytest tmp_path as the state root.
No writes to the repo tree.
No shared directories between tests.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_paper_scenario import (  # noqa: E402
    EXIT_ENV_INVALID,
    EXIT_INVARIANT,
    EXIT_MANIFEST_INVALID,
    EXIT_SCENARIO_INVALID,
    EXIT_STATE_INVALID,
    EXIT_SUCCESS,
    FinalizationController,
    InvariantViolationError,
    ScenarioInvalidError,
    StateInvalidError,
    StateRoot,
    _build_allowlisted_env,
    main,
)

STRATEGY_ID  = "es_daily_trend_v1"
FIXED_TIME   = "2026-01-01T00:00:00Z"
FIXED_SEED   = 42
STAGE        = "paper"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def scenario_file(tmp_path: Path) -> Path:
    f = tmp_path / "buy_then_sell_roundtrip.json"
    f.write_text(json.dumps({"name": "buy_then_sell_roundtrip", "steps": []}))
    return f


@pytest.fixture()
def config_template(tmp_path: Path) -> Path:
    f = tmp_path / "user.yaml"
    f.write_text("mode: paper\n")
    return f


@pytest.fixture()
def state_root(tmp_path: Path) -> Path:
    """A fresh, non-existent state root path under tmp_path."""
    return tmp_path / "run-001"


def _make_argv(
    state_root: Path,
    scenario: Path,
    config_template: Path,
    strategy: str = STRATEGY_ID,
    stage: str = STAGE,
    fixed_time: str = FIXED_TIME,
    fixed_seed: int = FIXED_SEED,
) -> list[str]:
    return [
        "--state-root",      str(state_root),
        "--scenario",        str(scenario),
        "--config-template", str(config_template),
        "--strategy",        strategy,
        "--stage",           stage,
        "--fixed-time",      fixed_time,
        "--fixed-seed",      str(fixed_seed),
    ]


def _seed_artifacts(sr: StateRoot) -> None:
    """
    Write minimal valid artifacts so the invariant checks pass.
    Simulates what a real paper runner would produce.
    """
    sr.evidence_dir.mkdir(parents=True, exist_ok=True)

    (sr.evidence_dir / "signal.jsonl").write_text(
        json.dumps({"signal_id": "s1", "strategy_id": STRATEGY_ID}) + "\n"
    )
    (sr.evidence_dir / "order.jsonl").write_text(
        json.dumps({"order_id": "o1", "signal_id": "s1"}) + "\n"
    )
    (sr.evidence_dir / "fill.jsonl").write_text(
        json.dumps({"fill_id": "f1", "order_id": "o1"}) + "\n"
    )
    (sr.evidence_dir / "session.jsonl").write_text(
        json.dumps({
            "session_id": "sess1",
            "kill_switch_tested": True,   # required invariant — section 10
            "round_trip_count": 1,
        }) + "\n"
    )


def _run_main(argv: list[str]) -> int:
    """Run main() and capture the SystemExit code."""
    with pytest.raises(SystemExit) as exc_info:
        main(argv)
    return exc_info.value.code

# ---------------------------------------------------------------------------
# Section 20 assertion 1: clean run succeeds
# ---------------------------------------------------------------------------

def test_clean_run_exits_zero(tmp_path, scenario_file, config_template, monkeypatch):
    """
    Section 20, assertion 1: a complete valid run exits 0.

    Goes through the real entrypoint path:
        main() -> run_with_determinism_guard() -> RuntimeEntrypoint.run()
            -> FinalizationController.finalize_and_exit()

    _execute_scenario is a v1 stub (pass). We monkeypatch it to seed the
    required artifacts, which is what a real paper runner would produce.
    This exercises every layer of the harness without bypassing the entry contract.
    """
    sr_path = tmp_path / "run-clean"

    def _fake_execute(self, *, finalizer):
        # Simulate paper runner writing artifacts to state_root
        _seed_artifacts(self.state_root_obj)

    monkeypatch.setattr(
        "scripts.run_paper_scenario.RuntimeEntrypoint._execute_scenario",
        _fake_execute,
    )

    argv = _make_argv(sr_path, scenario_file, config_template)
    code = _run_main(argv)
    assert code == EXIT_SUCCESS, f"expected 0, got {code}"

    # Manifest must exist and reflect success
    sr = StateRoot(root=sr_path, strategy_id=STRATEGY_ID)
    manifest = json.loads(sr.manifest_path.read_text())
    assert manifest["final_status"] == "SUCCESS"
    assert manifest["invariants_passed"] is True

# ---------------------------------------------------------------------------
# Section 20 assertion 2: manifest is schema-valid
# ---------------------------------------------------------------------------

def test_manifest_is_schema_valid(tmp_path, scenario_file, config_template):
    sr = StateRoot(root=tmp_path / "run-schema", strategy_id=STRATEGY_ID)
    sr.initialize()
    _seed_artifacts(sr)

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    manifest = json.loads(sr.manifest_path.read_text())

    required_keys = {
        "manifest_schema_version",
        "strategy_id", "scenario_name", "stage",
        "run_started_at", "run_finished_at",
        "final_status", "failure_category",
        "signal_count", "order_count", "fill_count", "session_count",
        "round_trip_count", "invariants_passed", "promotion_gates_passed",
        "signal_ids", "order_signal_refs", "fill_order_refs",
        "promotion_gate_skipped_reason",
    }
    missing = required_keys - manifest.keys()
    assert not missing, f"Manifest missing keys: {missing}"
    assert manifest["manifest_schema_version"] == "1.3"

# ---------------------------------------------------------------------------
# Section 20 assertion 3: all evidence artifacts exist
# ---------------------------------------------------------------------------

def test_all_evidence_artifacts_exist(tmp_path):
    sr = StateRoot(root=tmp_path / "run-artifacts", strategy_id=STRATEGY_ID)
    sr.initialize()
    _seed_artifacts(sr)

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    for name in ("signal.jsonl", "order.jsonl", "fill.jsonl", "session.jsonl", "manifest.json"):
        assert (sr.evidence_dir / name).exists(), f"Missing artifact: {name}"

# ---------------------------------------------------------------------------
# Section 20 assertion 4: manifest counts reconcile with artifacts
# ---------------------------------------------------------------------------

def test_manifest_counts_reconcile_with_artifacts(tmp_path):
    sr = StateRoot(root=tmp_path / "run-counts", strategy_id=STRATEGY_ID)
    sr.initialize()
    _seed_artifacts(sr)

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    manifest = json.loads(sr.manifest_path.read_text())

    def _count(path: Path) -> int:
        return sum(
            1 for line in path.read_text().splitlines() if line.strip()
        )

    assert manifest["signal_count"]  == _count(sr.evidence_dir / "signal.jsonl")
    assert manifest["order_count"]   == _count(sr.evidence_dir / "order.jsonl")
    assert manifest["fill_count"]    == _count(sr.evidence_dir / "fill.jsonl")
    assert manifest["session_count"] == _count(sr.evidence_dir / "session.jsonl")

# ---------------------------------------------------------------------------
# Section 20 assertion 4b: manifest reference fields reconcile with artifacts
# ---------------------------------------------------------------------------

def test_manifest_reference_fields_reconcile(tmp_path):
    """CI structural check: signal_ids, order_signal_refs, fill_order_refs match artifacts."""
    sr = StateRoot(root=tmp_path / "run-refs", strategy_id=STRATEGY_ID)
    sr.initialize()
    _seed_artifacts(sr)

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    manifest = json.loads(sr.manifest_path.read_text())

    assert manifest["signal_ids"] == ["s1"]
    assert manifest["order_signal_refs"] == {"o1": "s1"}
    assert manifest["fill_order_refs"] == {"f1": "o1"}

    # Referential integrity: every order refs a known signal
    known_signals = set(manifest["signal_ids"])
    for oid, sid in manifest["order_signal_refs"].items():
        assert sid in known_signals, f"order {oid} refs unknown signal {sid}"

    # Every fill refs a known order
    known_orders = set(manifest["order_signal_refs"].keys())
    for fid, oid in manifest["fill_order_refs"].items():
        assert oid in known_orders, f"fill {fid} refs unknown order {oid}"

# ---------------------------------------------------------------------------
# Section 20 assertion 5: invariants_passed is correct
# ---------------------------------------------------------------------------

def test_invariants_passed_true_when_artifacts_complete(tmp_path):
    sr = StateRoot(root=tmp_path / "run-inv-pass", strategy_id=STRATEGY_ID)
    sr.initialize()
    _seed_artifacts(sr)

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    manifest = json.loads(sr.manifest_path.read_text())
    assert manifest["invariants_passed"] is True


def test_invariants_passed_false_when_artifacts_missing(tmp_path):
    sr = StateRoot(root=tmp_path / "run-inv-fail", strategy_id=STRATEGY_ID)
    sr.initialize()
    # No artifacts seeded — invariants must fail

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit) as exc_info:
        finalizer.finalize_and_exit(exc=None)

    assert exc_info.value.code == EXIT_INVARIANT, (
        "invariants_passed==False with exc=None must exit EXIT_INVARIANT, not 0"
    )
    manifest = json.loads(sr.manifest_path.read_text())
    assert manifest["invariants_passed"] is False
    assert manifest["final_status"] == "FAILURE"
    assert manifest["failure_category"] == "INVARIANT_VIOLATION"


def test_invariants_passed_false_when_kill_switch_missing(tmp_path):
    """Section 10: kill_switch_tested is a required invariant field."""
    sr = StateRoot(root=tmp_path / "run-no-ks", strategy_id=STRATEGY_ID)
    sr.initialize()
    _seed_artifacts(sr)
    # Overwrite session without kill_switch_tested
    (sr.evidence_dir / "session.jsonl").write_text(
        json.dumps({"session_id": "sess1", "round_trip_count": 1}) + "\n"
    )

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit) as exc_info:
        finalizer.finalize_and_exit(exc=None)

    assert exc_info.value.code == EXIT_INVARIANT
    manifest = json.loads(sr.manifest_path.read_text())
    assert manifest["invariants_passed"] is False

# ---------------------------------------------------------------------------
# Section 20 assertion 6: promotion_gates_passed
# ---------------------------------------------------------------------------

def test_promotion_gates_passed_false_on_failure(tmp_path):
    sr = StateRoot(root=tmp_path / "run-promo-fail", strategy_id=STRATEGY_ID)
    sr.initialize()

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=RuntimeError("upstream failure"))

    manifest = json.loads(sr.manifest_path.read_text())
    assert manifest["promotion_gates_passed"] is False
    assert manifest["promotion_gate_skipped_reason"] == "upstream_execution_failure"

# ---------------------------------------------------------------------------
# Section 20 assertion 7: tampering with required artifact causes failure
# ---------------------------------------------------------------------------

def test_deleting_signal_artifact_fails_invariants(tmp_path):
    sr = StateRoot(root=tmp_path / "run-tamper-signal", strategy_id=STRATEGY_ID)
    sr.initialize()
    _seed_artifacts(sr)
    (sr.evidence_dir / "signal.jsonl").unlink()  # tamper

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    manifest = json.loads(sr.manifest_path.read_text())
    assert manifest["invariants_passed"] is False
    assert manifest["signal_count"] == 0


def test_deleting_fill_artifact_fails_invariants(tmp_path):
    sr = StateRoot(root=tmp_path / "run-tamper-fill", strategy_id=STRATEGY_ID)
    sr.initialize()
    _seed_artifacts(sr)
    (sr.evidence_dir / "fill.jsonl").unlink()

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    manifest = json.loads(sr.manifest_path.read_text())
    assert manifest["invariants_passed"] is False


def test_corrupted_order_artifact_fails_referential_integrity(tmp_path):
    sr = StateRoot(root=tmp_path / "run-tamper-order", strategy_id=STRATEGY_ID)
    sr.initialize()
    _seed_artifacts(sr)
    # Corrupt: order refs a signal_id that does not exist
    (sr.evidence_dir / "order.jsonl").write_text(
        json.dumps({"order_id": "o1", "signal_id": "UNKNOWN"}) + "\n"
    )

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    manifest = json.loads(sr.manifest_path.read_text())
    assert manifest["invariants_passed"] is False

# ---------------------------------------------------------------------------
# Section 20 assertion 8: missing required CLI args causes failure
# ---------------------------------------------------------------------------

def test_missing_state_root_arg_exits_nonzero(scenario_file, config_template):
    argv = [
        "--scenario",        str(scenario_file),
        "--config-template", str(config_template),
        "--strategy",        STRATEGY_ID,
        "--stage",           STAGE,
    ]
    with pytest.raises(SystemExit) as exc_info:
        main(argv)
    assert exc_info.value.code != 0


def test_missing_strategy_arg_exits_nonzero(tmp_path, scenario_file, config_template):
    argv = [
        "--state-root",      str(tmp_path / "run-nostr"),
        "--scenario",        str(scenario_file),
        "--config-template", str(config_template),
        "--stage",           STAGE,
    ]
    with pytest.raises(SystemExit) as exc_info:
        main(argv)
    assert exc_info.value.code != 0


def test_nonexistent_scenario_exits_scenario_invalid(tmp_path, config_template):
    """Section 18: bad --scenario must exit EXIT_SCENARIO_INVALID (12), not STATE_INVALID."""
    argv = _make_argv(
        state_root=tmp_path / "run-no-scen",
        scenario=tmp_path / "does_not_exist.json",
        config_template=config_template,
    )
    code = _run_main(argv)
    assert code == EXIT_SCENARIO_INVALID


def test_nonexistent_config_template_exits_state_invalid(tmp_path, scenario_file):
    argv = _make_argv(
        state_root=tmp_path / "run-no-cfg",
        scenario=scenario_file,
        config_template=tmp_path / "missing.yaml",
    )
    code = _run_main(argv)
    assert code == EXIT_STATE_INVALID


def test_invalid_stage_exits_state_invalid(tmp_path, scenario_file, config_template):
    argv = _make_argv(
        state_root=tmp_path / "run-bad-stage",
        scenario=scenario_file,
        config_template=config_template,
        stage="production",
    )
    code = _run_main(argv)
    assert code == EXIT_STATE_INVALID

# ---------------------------------------------------------------------------
# Section 20 assertion 9: pre-existing state-root causes failure
# ---------------------------------------------------------------------------

def test_preexisting_state_root_exits_state_invalid(tmp_path, scenario_file, config_template):
    sr_path = tmp_path / "run-preexist"
    sr_path.mkdir()  # create it before the run

    argv = _make_argv(
        state_root=sr_path,
        scenario=scenario_file,
        config_template=config_template,
    )
    code = _run_main(argv)
    assert code == EXIT_STATE_INVALID

# ---------------------------------------------------------------------------
# Section 20 assertion 10: crash before finalization still produces manifest
# ---------------------------------------------------------------------------

def test_crash_before_finalization_produces_failure_manifest(tmp_path):
    sr = StateRoot(root=tmp_path / "run-crash", strategy_id=STRATEGY_ID)
    sr.initialize()
    # No artifacts — simulates crash before any paper runner output

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    # Simulate crash exception routed through finalizer
    with pytest.raises(SystemExit) as exc_info:
        finalizer.finalize_and_exit(exc=RuntimeError("simulated crash"))

    assert exc_info.value.code != EXIT_SUCCESS
    assert sr.manifest_path.exists(), "manifest must be written even on crash"

    manifest = json.loads(sr.manifest_path.read_text())
    assert manifest["final_status"] == "FAILURE"
    assert manifest["failure_category"] is not None
    assert manifest["invariants_passed"] is False

# ---------------------------------------------------------------------------
# Environment construction contract — section 5
# ---------------------------------------------------------------------------

def test_build_allowlisted_env_starts_from_empty(tmp_path, monkeypatch):
    """No ambient env keys pass through to the constructed env."""
    monkeypatch.setenv("SECRET_TOKEN", "should-not-appear")
    monkeypatch.setenv("HOME", "/home/user")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "leak")

    env = _build_allowlisted_env(
        state_root=tmp_path / "run-env",
        fixed_time=FIXED_TIME,
        fixed_seed=FIXED_SEED,
        include_path=False,
    )

    assert "SECRET_TOKEN" not in env
    assert "HOME" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "CBP_STATE_ROOT" in env
    assert "CBP_FIXED_TIME" in env
    assert "CBP_FIXED_SEED" in env


def test_build_allowlisted_env_path_is_opt_in(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    env_with = _build_allowlisted_env(
        state_root=tmp_path / "a",
        fixed_time=FIXED_TIME,
        fixed_seed=FIXED_SEED,
        include_path=True,
    )
    env_without = _build_allowlisted_env(
        state_root=tmp_path / "b",
        fixed_time=FIXED_TIME,
        fixed_seed=FIXED_SEED,
        include_path=False,
    )

    assert "PATH" in env_with
    assert "PATH" not in env_without


def test_build_allowlisted_env_cbp_values_are_correct(tmp_path):
    sr_path = tmp_path / "run-cbp"
    env = _build_allowlisted_env(
        state_root=sr_path,
        fixed_time=FIXED_TIME,
        fixed_seed=FIXED_SEED,
        include_path=False,
    )
    assert env["CBP_STATE_ROOT"] == str(sr_path)
    assert env["CBP_FIXED_TIME"] == FIXED_TIME
    assert env["CBP_FIXED_SEED"] == str(FIXED_SEED)

# ---------------------------------------------------------------------------
# Finalization authority — section 13
# ---------------------------------------------------------------------------

def test_double_finalization_exits_manifest_invalid(tmp_path):
    """Second call to finalize_and_exit must exit MANIFEST_INVALID, not re-run logic."""
    sr = StateRoot(root=tmp_path / "run-double", strategy_id=STRATEGY_ID)
    sr.initialize()

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    with pytest.raises(SystemExit) as exc_info:
        finalizer.finalize_and_exit(exc=None)

    assert exc_info.value.code == EXIT_MANIFEST_INVALID


def test_finalized_lock_is_written(tmp_path):
    sr = StateRoot(root=tmp_path / "run-lock", strategy_id=STRATEGY_ID)
    sr.initialize()

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    assert sr.finalized_lock.exists()

# ---------------------------------------------------------------------------
# State root isolation — section 4
# ---------------------------------------------------------------------------

def test_state_root_dirs_are_created(tmp_path):
    sr = StateRoot(root=tmp_path / "run-dirs", strategy_id=STRATEGY_ID)
    sr.initialize()

    assert sr.config_path.parent.exists()
    assert sr.scenario_dir.exists()
    assert sr.logs_dir.exists()
    assert sr.evidence_dir.exists()
    assert sr.sqlite_dir.exists()


def test_no_writes_outside_state_root(tmp_path, scenario_file, config_template):
    """After a run, only the declared state_root and tmp_path-rooted files are written."""
    sr_path = tmp_path / "run-isolation"
    sr = StateRoot(root=sr_path, strategy_id=STRATEGY_ID)
    sr.initialize()
    _seed_artifacts(sr)

    before = set(tmp_path.rglob("*"))

    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=STRATEGY_ID,
        scenario_name="buy_then_sell_roundtrip",
        stage=STAGE,
        run_started_at=FIXED_TIME,
    )
    with pytest.raises(SystemExit):
        finalizer.finalize_and_exit(exc=None)

    after = set(tmp_path.rglob("*"))
    new_paths = after - before

    # Every new path must be under state_root
    outside = [p for p in new_paths if not str(p).startswith(str(sr_path))]
    assert not outside, f"Writes outside state_root: {outside}"
