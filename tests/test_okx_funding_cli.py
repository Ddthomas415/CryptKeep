from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import subprocess

import pytest

from scripts import run_crypto_edge_collector_loop as cli
from services.analytics import crypto_edge_collector_service as svc
from services.analytics.okx_funding_pair_batch import validate_okx_pair_plan
from storage import crypto_edge_store_sqlite as storage


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "config/templates/crypto_edge_okx_pairs_plan.json"
OPTIONS = ROOT / "config/templates/crypto_edge_okx_pair_options.json"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise AssertionError("external/control boundary forbidden")
    connect = sqlite3.connect
    def temporary(database, *args, **kwargs):
        assert Path(database).resolve().is_relative_to(tmp_path.resolve())
        return connect(database, *args, **kwargs)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(sqlite3, "connect", temporary)
    monkeypatch.setattr(storage, "ensure_dirs", refuse)
    monkeypatch.setattr(cli, "run_forever", refuse)
    monkeypatch.setattr(cli, "request_stop", refuse)
    monkeypatch.setattr(cli, "load_runtime_status", refuse)


def args(tmp_path):
    return ["--okx-pairs", "--plan-file", str(PLAN),
            "--okx-pair-options-file", str(OPTIONS), "--db-path", str(tmp_path / "not-created.sqlite"),
            "--source", "fixture", "--raw-funding-max-rows", "1",
            "--raw-funding-max-bytes", "4194304", "--max-loops", "1"]


def test_preview_has_hashes_and_no_lifecycle_or_database_side_effect(tmp_path, capsys):
    assert cli.main(args(tmp_path) + ["--check-config"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["configuration_valid"] is True and out["will_start"] is False
    assert out["runtime_state"] == out["database_ownership"] == "UNVERIFIED"
    assert out["plan_sha256"] == hashlib.sha256(PLAN.read_bytes()).hexdigest()
    assert out["options_sha256"] == hashlib.sha256(OPTIONS.read_bytes()).hexdigest()
    assert out["funding_capture_limits"]["max_requests"] == 2
    assert out["other_stream_row_counts"] == {"open_interest": 1, "basis": 1, "quotes": 2, "order_books": 1}
    assert out["other_streams_outside_funding_budget"] is True
    assert out["execution_enabled"] is False and not (tmp_path / "not-created.sqlite").exists()


def test_template_preserves_original_families_with_only_native_id_added():
    original = json.loads((ROOT / "sample_data/crypto_edges/live_collector_plan.json").read_bytes())
    template = json.loads(PLAN.read_bytes())
    assert template["funding"][0].pop("inst_id") == "BTC-USDT-SWAP"
    assert template == original


def test_shared_validator_copies_critical_configuration_without_capture():
    plan = json.loads(PLAN.read_bytes())["funding"]
    options = json.loads(OPTIONS.read_bytes())
    original = deepcopy(plan), deepcopy(options)
    rows, limits = validate_okx_pair_plan(plan, options)
    rows[0]["inst_id"], limits["max_requests"] = "OTHER-USDT-SWAP", 999
    assert (plan, options) == original


def test_cli_to_real_service_with_fake_transport_and_disposable_store(monkeypatch, tmp_path, capsys):
    path = ROOT / "docs/review_artifacts/okx_funding_pair_transport_20261029/20261029T145936Z_eddbeac2a3134ea68bc7f2b649d64b1a"
    calls = []
    def transport(command, **kwargs):
        calls.append(command)
        name = "history" if "funding-rate-history?" in command[-1] else "current"
        return subprocess.CompletedProcess(command, 0, (path / (name + ".body")).read_bytes() + b"\n200", b"")
    monkeypatch.setattr(svc, "_now_iso", lambda: "2026-10-29T14:59:37Z")
    def other(plan, **kwargs):
        assert plan["funding"] == [] and len(plan["quotes"]) == 2
        return {"funding_rows": [], "funding_observations": [], "checks": []}
    monkeypatch.setattr(svc, "collect_live_crypto_edge_snapshot", other)
    def lifecycle(cfg, *, max_loops):
        assert max_loops == 1 and cfg.raw_funding_only is True
        assert cfg.okx_pair_options["max_requests"] == 2
        result = svc.collect_once(cfg, pair_run=transport)
        return {"ok": True, "reason": "max_loops", "errors": 0, "last_result": result}
    monkeypatch.setattr(cli, "run_forever", lifecycle)
    assert cli.main(args(tmp_path)) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["paired_run_succeeded"] is True and len(calls) == 2
    assert out["last_result"]["funding_pair_capture"]["successful_pairs"] == 1
    assert out["last_result"]["execution_enabled"] is False
    assert (tmp_path / "not-created.sqlite").is_file()


@pytest.mark.parametrize("result", [
    {"ok": True, "reason": "already_running"},
    {"ok": True, "reason": "max_loops", "errors": 1, "last_result": {"ok": False}},
    {"ok": True, "reason": "max_loops", "errors": 0, "last_result": {}},
    {"ok": False, "errors": 0, "last_result": {"ok": True}},
])
def test_pair_exit_status_does_not_claim_failed_or_unverified_run_succeeded(monkeypatch, tmp_path, capsys, result):
    monkeypatch.setattr(cli, "run_forever", lambda *a, **kw: deepcopy(result))
    assert cli.main(args(tmp_path)) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False and out["paired_run_succeeded"] is False


@pytest.mark.parametrize("extra", [["--stop"], ["--status"], ["--stop", "--check-config"]])
def test_control_conflicts_refuse_before_lifecycle(tmp_path, extra):
    with pytest.raises(SystemExit) as exc:
        cli.main(args(tmp_path) + extra)
    assert exc.value.code == 2


@pytest.mark.parametrize("change", [
    ["--db-path", ""], ["--raw-funding-max-rows", "0"], ["--raw-funding-max-bytes", "0"],
    ["--interval-sec", "nan"], ["--max-loops", "-1"],
])
def test_invalid_execution_settings_refuse_before_start(tmp_path, change):
    with pytest.raises(SystemExit) as exc:
        cli.main(args(tmp_path) + change)
    assert exc.value.code == 2


@pytest.mark.parametrize("body", [
    b'{"max_requests":2,"max_requests":4}',
    b'{"max_requests":2,"total_timeout_seconds":NaN}',
    b'{"max_requests":2,"total_timeout_seconds":1e309}',
    b'{"extra":' + b'[' * 2000 + b'0' + b']' * 2000 + b'}',
    b'{"private-looking-config-value":',
])
def test_bad_configuration_is_sanitized_and_never_starts(tmp_path, capsys, body):
    path = tmp_path / "options.json"
    path.write_bytes(body)
    with pytest.raises(SystemExit) as exc:
        cli.main(args(tmp_path) + ["--okx-pair-options-file", str(path), "--check-config"])
    assert exc.value.code == 2
    assert "private-looking-config-value" not in capsys.readouterr().err
    assert not (tmp_path / "not-created.sqlite").exists()


@pytest.mark.parametrize("argv", [["--check-config"], ["--raw-funding-max-rows", "1"]])
def test_pair_arguments_require_opt_in(argv):
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    assert exc.value.code == 2
