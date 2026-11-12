"""Synthetic archive/replay checks. No account or runtime configuration is read."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from services.strategies import signal_input_capture as capture


@pytest.fixture
def archive(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_CAPTURE_RUNNER_DECISIONS", "1")
    monkeypatch.delenv("CBP_RUNNER_DECISION_OBJECT_DIR", raising=False)
    monkeypatch.setattr(capture, "data_dir", lambda: tmp_path)
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "synthetic_state"))
    monkeypatch.setattr(capture, "_runner_commit_identity", lambda: "a" * 40)
    return tmp_path


def make_record(strategy="breakout_donchian", *, computed=True, position=1.0, forming_delta=0):
    from services.execution.runner_decision import (
        position_aware_signal_action, select_exit_decision, signal_transition,
    )
    from services.strategies.strategy_registry import compute_signal

    rows = [[1793664000000 + i * 3600000, 100 + i, 102 + i, 99 + i, 101 + i, 10]
            for i in range(65)]
    rows[-1][4] += forming_delta
    selected = {"name": strategy, "trade_enabled": True}
    cfg = {"strategy_id": strategy, "position_aware": True, "stop_loss_pct": .03,
           "take_profit_pct": .06, "trailing_stop_pct": .02, "max_bars_hold": 60,
           "timeframe": "1h", "signal_source": "public_ohlcv"}
    raw = {}
    signal = compute_signal(cfg={"strategy": selected}, symbol="BTC/USDT", ohlcv=rows,
                            observer=raw.update) if computed else {
                                "ok": True, "action": "hold", "reason": "no_signal"}
    decision = position_aware_signal_action(signal, strategy_id=strategy, position_qty=position)
    inputs = dict(strategy_id=strategy, decision=decision, pos_qty=position, warmed=True,
                  last_action="hold", allow_first_signal_trade=False)
    transition = signal_transition(**inputs)
    exits = dict(cfg=cfg, signal=signal, decision=decision, changed=transition["changed"],
                 pos_qty=position, entry_price=100.0, trailing_peak_price=170.0,
                 bars_held=65, current_price=float(rows[-1][4]))
    exit_result = select_exit_decision(**exits, observe=True, raw_signal=raw)
    return {"version": 2, "session_id": "1" * 32, "account_id": "2" * 64, "loop": 1,
            "symbol": "BTC/USDT", "venue": "coinbase", "observed_at": "2026-11-05T16:30:00+00:00",
            "kind": "decision", "pipeline_stage": "gates", "timeframe": "1h",
            "settings": {"runner": cfg, "strategy": selected}, "ohlcv": rows,
            "signal_computed": computed, "raw_signal": raw, "signal": signal,
            "transition_inputs": inputs, "exit_inputs": exits,
            "decision": {"transition": transition, "exit": exit_result},
            "actual": {"intended_action": exit_result["action"], "outcome": "no_intent", "gates": {}},
            "reason": None}


def save(root, record):
    receipt = capture.capture_runner_decision(record)
    assert receipt["ok"], receipt
    assert receipt["status"] == "captured"
    path = root / receipt["relativepath"]
    records = capture.read_runner_records(path)
    return receipt, path, records[-1]


@pytest.mark.parametrize("strategy", ["ema_cross", "mean_reversion_rsi", "breakout_donchian"])
def test_real_trio_replays_exact_signal_raw_transition_and_all_conditions(archive, strategy):
    record = make_record(strategy)
    receipt, path, envelope = save(archive, record)
    assert envelope["sha256"] == receipt["sha256"]
    assert envelope["payload"]["signal"] == record["signal"]
    assert envelope["payload"]["raw_signal"] == record["raw_signal"]
    assert envelope["payload"]["decision"] == record["decision"]
    assert capture.replay_runner_decision(envelope)["decision_match"] is True
    result = capture.replay_runner_decision(envelope, object_directory=archive / receipt["object_directory"])
    assert result["status"] == "decision_match" and result["signal_recomputed"] is True
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert len(capture.read_runner_records(path, expected_sha256=expected)) == 1


def test_cas_dedup_prefix_sharing_and_forming_version_inline(archive):
    record = make_record()
    _, _, first = save(archive, record)
    objects = set((archive / "signal_inputs").iterdir())
    _, _, second = save(archive, record)
    assert second["sha256"] == first["sha256"]
    assert set((archive / "signal_inputs").iterdir()) == objects
    assert any(not slot["complete"] for slot in first["payload"]["ohlcv"])
    assert any(slot["complete"] for slot in first["payload"]["ohlcv"])
    record["loop"] += 1
    record["ohlcv"][-1][4] += .01
    _, _, third = save(archive, record)
    assert third["sha256"] != first["sha256"]
    assert set((archive / "signal_inputs").iterdir()) == objects
    assert third["payload"]["completed_prefix_sha256"] == first["payload"]["completed_prefix_sha256"]
    record["observed_at"] = "2026-11-05T17:30:00+00:00"
    save(archive, record)
    assert len(set((archive / "signal_inputs").iterdir()) - objects) == 2
    assert all(path.suffix == ".json" for path in objects)


def test_duplicate_timestamps_and_exact_input_order(archive):
    record = make_record()
    record.update(kind="skipped", signal_computed=False)
    record["ohlcv"] = [record["ohlcv"][3], record["ohlcv"][0], record["ohlcv"][3], record["ohlcv"][-1]]
    _, _, envelope = save(archive, record)
    assert capture.replay_runner_decision(envelope)["status"] == "diagnostic_verified"
    assert [slot["timestamp"] for slot in envelope["payload"]["ohlcv"]] == [row[0] for row in record["ohlcv"]]


@pytest.mark.parametrize("kind", ["skipped", "error"])
def test_diagnostic_receipts_never_claim_decision_recomputation(archive, kind, monkeypatch):
    record = make_record()
    record.update(kind=kind, signal_computed=False)
    _, _, envelope = save(archive, record)
    from services.strategies import strategy_registry

    # Swapping the binding changes its loaded fingerprint, so tripwire at the
    # call site without changing loaded functions/defaults/constants.
    def trace(frame, event, arg):
        if event == "call" and frame.f_code is strategy_registry.compute_signal.__code__:
            raise AssertionError("diagnostic_called_registry")
        return trace

    sys.setprofile(trace)
    try:
        result = capture.replay_runner_decision(envelope)
    finally:
        sys.setprofile(None)
    assert result["status"] == "diagnostic_verified"
    assert result["recomputed"] is False and result["decision_match"] is None


def test_default_no_signal_decision_replays_exit_without_registry(archive):
    _, _, envelope = save(archive, make_record(computed=False))
    result = capture.replay_runner_decision(envelope)
    assert result["status"] == "decision_match"
    assert result["signal_recomputed"] is False
    assert result["reason"] == "default_no_signal_replayed"


def test_disabled_is_exact_opt_in_and_performs_no_reads(monkeypatch):
    def forbidden():
        raise AssertionError("disabled_capture_touched_disk")

    monkeypatch.setattr(capture, "data_dir", forbidden)
    for setting in (None, "0", "true", "yes", " 1"):
        if setting is None:
            monkeypatch.delenv("CBP_CAPTURE_RUNNER_DECISIONS", raising=False)
        else:
            monkeypatch.setenv("CBP_CAPTURE_RUNNER_DECISIONS", setting)
        assert capture.runner_capture_enabled() is False
        assert capture.capture_runner_decision(None) == {"ok": True, "status": "disabled"}


@pytest.mark.parametrize("mutate", [
    lambda r: r["ohlcv"][-1].__setitem__(4, float("nan")),
    lambda r: r["ohlcv"][-1].__setitem__(0, True),
    lambda r: r["ohlcv"].__setitem__(0, "bad-row"),
    lambda r: r["exit_inputs"].__setitem__("current_price", float("inf")),
    lambda r: r["transition_inputs"].__setitem__("pos_qty", "1"),
    lambda r: r["transition_inputs"].__setitem__("warmed", 1),
    lambda r: r["settings"]["strategy"].__setitem__("ema_fast", {"token": "SECRET"}),
    lambda r: r.__setitem__("loop", True),
    lambda r: r.__setitem__("observed_at", "2026-11-06T16:30:00"),
    lambda r: r.__setitem__("session_id", "../outside"),
    lambda r: r.__setitem__("account_id", "../../outside"),
    lambda r: r["signal"].__setitem__("action", {"bad": "type"}),
    lambda r: r["exit_inputs"].pop("current_price"),
])
def test_bad_types_nonfinite_or_incomplete_are_nonfatal_and_never_journaled(archive, mutate):
    record = make_record()
    mutate(record)
    result = capture.capture_runner_decision(record)
    assert result["ok"] is False and result["status"] == "failed"
    assert not list(archive.rglob("*.jsonl"))
    assert set(result) == {"ok", "status", "error_type"}


@pytest.mark.parametrize("bad_exit_price", [False, True])
def test_invalid_hourly_input_retains_only_a_diagnostic(archive, bad_exit_price):
    from services.market_data.hourly_candle_quality import assess_hourly_candles

    record = make_record()
    record["ohlcv"][-1][4] = float("nan")
    now = record["ohlcv"][-1][0] / 1000 + 1800
    record["candle_quality"] = assess_hourly_candles(record["ohlcv"], now=now)
    assert record["candle_quality"]["reason"] == "invalid_ohlcv"
    record["candle_quality"]["extra"] = {"token": "DO_NOT_STORE_SENTINEL"}
    if bad_exit_price:
        record["exit_inputs"]["current_price"] = float("nan")
    _, journal, _ = save(archive, make_record())
    before = journal.read_bytes()
    receipt = capture.capture_runner_decision(record)
    assert not receipt["ok"] and receipt["status"] == "failed"
    assert receipt["diagnostic_status"] == "captured"
    path = archive / receipt["diagnostic_relativepath"]
    assert path.parts[-3] == "runner_candle_diagnostics"
    assert journal.read_bytes() == before
    assert len(capture.read_runner_records(journal)) == 1
    envelope = json.loads(path.read_bytes())
    assert envelope["payload"] == {
        "version": 1, "type": "candle_capture_diagnostic",
        "account_id": record["account_id"], "session_id": record["session_id"],
        "loop": 1, "venue": "coinbase", "symbol": "BTC/USDT", "timeframe": "1h",
        "observed_at": record["observed_at"], "reason": "invalid_ohlcv",
        "policy_version": 1, "capture_error_type": "ValueError", "source": "unknown",
    }
    assert envelope["sha256"] == hashlib.sha256(capture._encode(envelope["payload"])).hexdigest()
    with pytest.raises(ValueError, match="unsupported_runner_schema"):
        capture.read_runner_records(path)


def test_stale_candles_with_only_bad_settings_do_not_get_a_diagnostic(archive):
    from services.market_data.hourly_candle_quality import assess_hourly_candles

    record = make_record()
    now = (record["ohlcv"][-1][0] + 3600000) / 1000 + 600
    record["candle_quality"] = assess_hourly_candles(record["ohlcv"], now=now)
    assert record["candle_quality"]["reason"] == "current_hour_stale"
    capture._bar_layout(record["ohlcv"], capture._observed(record["observed_at"]), {"timeframe": "1h"})
    record["settings"]["runner"]["qty"] = {"token": "DO_NOT_STORE_SENTINEL"}
    assert capture.capture_runner_decision(record) == {
        "ok": False, "status": "failed", "error_type": "ValueError",
    }
    assert not list(archive.rglob("*.jsonl"))


@pytest.mark.parametrize("field,value", [
    ("ok", 0), ("ok", True), ("reason", "DO_NOT_STORE_SENTINEL"),
    ("reason", []), ("policy_version", True), ("timeframe", "1d"),
])
def test_invalid_capture_does_not_archive_untrusted_assessment(archive, field, value):
    record = make_record()
    record["ohlcv"][-1][4] = float("inf")
    record["candle_quality"] = {"ok": False, "reason": "invalid_ohlcv",
                                "policy_version": 1, "timeframe": "1h"}
    record["candle_quality"][field] = value
    assert capture.capture_runner_decision(record) == {
        "ok": False, "status": "failed", "error_type": "ValueError",
    }
    assert not list(archive.rglob("*.jsonl"))


@pytest.mark.parametrize("mode", ["disabled", "bad_identity", "write_failure", "partial_tail", "normal"])
def test_candle_diagnostic_write_boundary(archive, monkeypatch, mode):
    record = make_record()
    record["candle_quality"] = {"ok": False, "reason": "invalid_candles",
                                "policy_version": 1, "timeframe": "1h"}
    if mode != "normal":
        record["ohlcv"][-1] = {"token": "DO_NOT_STORE_SENTINEL"}
    path = archive / "runner_candle_diagnostics" / record["account_id"] / (record["session_id"] + ".jsonl")
    if mode == "disabled":
        monkeypatch.setenv("CBP_CAPTURE_RUNNER_DECISIONS", "0")
    elif mode == "bad_identity":
        record["session_id"] = "../../escape"
    elif mode == "write_failure":
        def fail(*_):
            raise OSError("DO_NOT_STORE_SENTINEL")

        monkeypatch.setattr(capture, "_append_runner", fail)
    elif mode == "partial_tail":
        path.parent.mkdir(parents=True)
        path.write_bytes(b"partial")
    result = capture.capture_runner_decision(record)
    if mode in {"write_failure", "partial_tail"}:
        assert result == {"ok": False, "status": "failed", "error_type": "ValueError",
                          "diagnostic_status": "failed"}
    elif mode == "disabled":
        assert result == {"ok": True, "status": "disabled"}
    elif mode == "normal":
        assert result["status"] == "captured"
    else:
        assert result == {"ok": False, "status": "failed", "error_type": "ValueError"}
    if mode == "partial_tail":
        assert path.read_bytes() == b"partial"
    else:
        assert not path.exists()


def test_whitelist_recurses_and_never_persists_raw_exception_or_config_extras(archive, monkeypatch):
    record = make_record()
    for mapping in (record, record["settings"], record["settings"]["runner"],
                    record["settings"]["strategy"], record["signal"], record["signal"]["ind"],
                    record["decision"]["exit"]["conditions"], record["actual"]):
        mapping["api_secret"] = {"token": "DO_NOT_STORE_SENTINEL"}
        mapping["exception"] = "DO_NOT_STORE_SENTINEL raw error"
    record["actual"]["gates"] = {"kill": {"ok": False, "token": "DO_NOT_STORE_SENTINEL"}}
    _, path, envelope = save(archive, record)
    for artifact in archive.rglob("*"):
        if artifact.is_file():
            assert b"DO_NOT_STORE_SENTINEL" not in artifact.read_bytes()
    assert envelope["payload"]["actual"]["gates"] == {"kill": {"ok": False}}

    def broken(_payload):
        raise OSError("DO_NOT_STORE_SENTINEL")

    monkeypatch.setattr(capture, "_runner_store", broken)
    result = capture.capture_runner_decision(record)
    assert result == {"ok": False, "status": "failed", "error_type": "OSError"}
    assert "DO_NOT_STORE_SENTINEL" not in str(result)
    assert path.exists()


@pytest.mark.parametrize("field", ["code_sha256", "settings_sha256", "completed_prefix_sha256"])
def test_tampered_objects_refuse_replay_and_are_never_replaced(archive, field):
    record = make_record()
    _, _, envelope = save(archive, record)
    path = archive / "signal_inputs" / f"{envelope['payload'][field]}.json"
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="object_hash_mismatch"):
        capture.replay_runner_decision(envelope)
    assert capture.capture_runner_decision(record)["ok"] is False
    assert path.read_bytes() == b"corrupt"


def test_tampered_individual_completed_bar_refuses(archive):
    _, _, envelope = save(archive, make_record())
    objects = archive / "signal_inputs"
    prefix = json.loads((objects / f"{envelope['payload']['completed_prefix_sha256']}.json").read_bytes())
    (objects / f"{prefix['bar_refs'][0]}.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="object_hash_mismatch"):
        capture.replay_runner_decision(envelope)


def test_record_and_whole_journal_hashes_checked(archive):
    _, path, envelope = save(archive, make_record())
    with pytest.raises(ValueError, match="journal_hash_mismatch"):
        capture.read_runner_records(path, expected_sha256="f" * 64)
    envelope["payload"]["signal"]["action"] = "buy"
    with pytest.raises(ValueError, match="record_hash_mismatch"):
        capture.replay_runner_decision(envelope)
    path.write_text(json.dumps(envelope) + "\n")
    with pytest.raises(ValueError, match="record_hash_mismatch"):
        capture.read_runner_records(path)


@pytest.mark.parametrize("change", ["default", "alias", "constant", "runner"])
def test_loaded_identity_is_fresh_on_capture_and_replay(archive, monkeypatch, change):
    from services.strategies import ema_cross, indicators, strategy_registry
    from services.execution import strategy_runner

    record = make_record()
    _, _, envelope = save(archive, record)
    original = envelope["payload"]["code_sha256"]
    if change == "default":
        monkeypatch.setattr(ema_cross.signal_from_ohlcv, "__defaults__", (99, 101))
    elif change == "alias":
        monkeypatch.setattr(ema_cross, "canonical_compute_signal", lambda state: 0)
    elif change == "constant":
        monkeypatch.setattr(strategy_registry, "SUPPORTED", {**strategy_registry.SUPPORTED, "ema_cross": indicators.ema})
    else:
        monkeypatch.setattr(strategy_runner, "_synth_ohlcv", lambda prices, **kw: [])
    with pytest.raises(ValueError, match="runner_code_mismatch"):
        capture.replay_runner_decision(envelope)
    _, _, new = save(archive, record)
    assert new["payload"]["code_sha256"] != original


@pytest.mark.parametrize("binding", ["_position_aware_signal_action", "position_aware_signal_action",
                                   "signal_transition", "select_exit_decision",
                                   "evaluate_strategy_exit_stack", "compute_signal"])
def test_active_runner_alias_change_cannot_claim_matching_code(archive, monkeypatch, binding):
    from services.execution import strategy_runner

    record = make_record()
    _, _, envelope = save(archive, record)
    before = capture._runner_code_identity()
    monkeypatch.setattr(strategy_runner, binding, lambda *_args, **_kwargs: "changed")
    assert capture._runner_code_identity() != before
    with pytest.raises(ValueError, match="runner_code_mismatch"):
        capture.replay_runner_decision(envelope)


def test_capture_fingerprints_explicit_active_caller_not_canonical_import(archive):
    from services.execution import strategy_runner

    record = make_record()
    bindings = {name: getattr(strategy_runner, name) for name in capture._RUNNER_BINDING_NAMES}
    bindings["signal_transition"] = lambda **_kwargs: {"changed": False}
    receipt = capture.capture_runner_decision(record, runner_bindings=bindings)
    assert receipt["ok"]
    envelope = capture.read_runner_records(archive / receipt["relativepath"])[0]
    with pytest.raises(ValueError, match="runner_code_mismatch"):
        capture.replay_runner_decision(envelope)


def test_equal_code_fingerprint_is_independent_of_constant_object_sharing():
    import ast
    import __future__
    from services.execution import strategy_runner

    path = Path(strategy_runner.__file__).resolve()
    node = next(node for node in ast.parse(path.read_text()).body
                if isinstance(node, ast.FunctionDef) and node.name == "_strategy_signal")
    namespace = dict(strategy_runner.__dict__)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec",
                 flags=__future__.annotations.compiler_flag), namespace)
    original = strategy_runner._strategy_signal
    recompiled = namespace["_strategy_signal"]
    assert original.__code__ == recompiled.__code__
    assert capture._fingerprint_value(original) == capture._fingerprint_value(recompiled)
    assert capture._fingerprint_value((1,)) != capture._fingerprint_value([1])


def test_storage_accounting_method_is_part_of_loaded_decision_identity(archive, monkeypatch):
    from storage.exit_event_journal import ExitEventJournal

    record = make_record()
    _, _, envelope = save(archive, record)
    monkeypatch.setattr(ExitEventJournal, "apply", lambda *_args, **_kwargs: False)
    with pytest.raises(ValueError, match="runner_code_mismatch"):
        capture.replay_runner_decision(envelope)


def test_concurrent_append_keeps_all_complete_envelopes(archive):
    record = make_record()
    # Warm the lazy imports before competing archive writers.
    capture._runner_code_identity()
    with ThreadPoolExecutor(max_workers=6) as pool:
        receipts = list(pool.map(capture.capture_runner_decision,
                                [dict(record, loop=i) for i in range(24)]))
    assert all(item["ok"] for item in receipts)
    path = archive / receipts[0]["relativepath"]
    envelopes = capture.read_runner_records(path)
    assert len(envelopes) == 24
    assert {item["payload"]["loop"] for item in envelopes} == set(range(24))
    assert not list(archive.rglob(".capture-*"))


def test_partial_tail_is_refused_without_truncate_repair_or_append(archive):
    record = make_record()
    _, path, _ = save(archive, record)
    with path.open("ab") as out:
        out.write(b'{"sha256":')
    before = path.read_bytes()
    assert capture.capture_runner_decision(record)["ok"] is False
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="partial_journal_tail"):
        capture.read_runner_records(path)


def test_short_append_is_nonfatal_and_leaves_tail_for_explicit_failure(archive, monkeypatch):
    original = capture.os.write

    def partial(fd, raw):
        return original(fd, raw[:10])

    monkeypatch.setattr(capture.os, "write", partial)
    record = make_record()
    assert capture.capture_runner_decision(record)["ok"] is False
    path = next(archive.rglob("*.jsonl"))
    before = path.read_bytes()
    assert before and not before.endswith(b"\n")
    assert capture.capture_runner_decision(record)["ok"] is False
    assert path.read_bytes() == before


def test_missing_account_uses_stable_nonplaintext_data_root_hash(archive):
    record = make_record()
    record.pop("account_id")
    receipt, _, envelope = save(archive, record)
    expected = hashlib.sha256(str(archive.resolve()).encode()).hexdigest()
    assert envelope["payload"]["account_id"] == expected
    assert expected in receipt["relativepath"]
    assert str(archive) not in json.dumps(envelope["payload"])


def test_observation_errors_are_never_exact_replay(archive):
    record = make_record()
    record["observation_error"] = "ValueError"
    _, _, envelope = save(archive, record)
    with pytest.raises(ValueError, match="observation_incomplete"):
        capture.replay_runner_decision(envelope)


def test_replay_does_not_call_trading_network_or_runtime_configuration(archive, monkeypatch):
    import socket
    from services.execution import strategy_runner

    _, _, envelope = save(archive, make_record())
    # Profile tripwires do not alter loaded code identity.
    forbidden = {strategy_runner.run_forever.__code__, strategy_runner.load_user_yaml.__code__,
                 strategy_runner._fetch_mid.__code__, strategy_runner.make_exchange.__code__}

    def profile(frame, event, arg):
        if event == "call" and frame.f_code in forbidden:
            raise AssertionError("replay_entered_runtime_or_trading")

    def network(*args, **kwargs):
        raise AssertionError("network_not_allowed")

    monkeypatch.setattr(socket, "create_connection", network)
    monkeypatch.setattr(socket, "socket", network)
    sys.setprofile(profile)
    try:
        assert capture.replay_runner_decision(envelope)["status"] == "decision_match"
    finally:
        sys.setprofile(None)


def test_cli_fresh_process_folder_journal_and_corruption(archive):
    _, journal, _ = save(archive, make_record())
    command = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/replay_runner_decisions.py")]
    for path in (journal, archive / "runner_decisions"):
        result = subprocess.run([*command, str(path)], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        summary = json.loads(result.stdout.splitlines()[-1])["summary"]
        assert summary == {"decision_match": 1, "decision_mismatch": 0, "diagnostic_verified": 0, "errors": 0}
    with journal.open("ab") as out:
        out.write(b"partial")
    result = subprocess.run([*command, str(journal)], capture_output=True, text=True)
    assert result.returncode == 1
    assert json.loads(result.stdout.splitlines()[-1])["summary"]["errors"] == 1
    result = subprocess.run([*command, str(archive / "missing")], capture_output=True, text=True)
    assert result.returncode == 1


def test_cli_distinguishes_diagnostics_and_decision_mismatches(archive):
    record = make_record()
    record.update(kind="skipped", signal_computed=False)
    _, journal, _ = save(archive, record)
    record = make_record()
    record["decision"]["exit"]["action"] = "buy"
    save(archive, record)
    command = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/replay_runner_decisions.py"), str(journal)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 1
    summary = json.loads(result.stdout.splitlines()[-1])["summary"]
    assert summary["diagnostic_verified"] == 1 and summary["decision_mismatch"] == 1


def test_synthetic_hour_all_records_exact_and_no_per_turn_cas_files(archive):
    for minute in range(61):
        record = make_record(forming_delta=minute / 1000)
        record["loop"] = minute
        record["observed_at"] = f"2026-11-05T{16 + minute // 60:02d}:{minute % 60:02d}:30+00:00"
        receipt = capture.capture_runner_decision(record)
        assert receipt["ok"], receipt
    journal = archive / receipt["relativepath"]
    records = capture.read_runner_records(journal)
    results = [capture.replay_runner_decision(record) for record in records]
    assert len(results) == 61 and all(result["decision_match"] for result in results)
    objects = list((archive / "signal_inputs").iterdir())
    assert len(objects) == 69  # 65 bars, two prefixes, one settings, one code.
    assert len({record["payload"]["code_sha256"] for record in records}) == 1
    assert len({record["payload"]["settings_sha256"] for record in records}) == 1


def test_synthetic_ticks_are_never_certified_as_completed_market_candles(archive):
    record = make_record()
    record["timeframe"] = "synthetic_ticks_1s"
    _, _, envelope = save(archive, record)
    assert all(slot["complete"] is False for slot in envelope["payload"]["ohlcv"])
    assert capture.replay_runner_decision(envelope)["status"] == "decision_match"


def test_gate_public_fields_preserved_exactly(archive):
    record = make_record()
    gates = {"scaling": {"ok": True, "reason": "scale:pass", "is_scale": True, "size_multiplier": .5},
             "cooldown_protective_exit": True, "open_intent_lookup": "unknown_existing_fail_open",
             "kill": {"ok": False, "reason": "kill:cooldown_active", "remaining_loops": 5}}
    record["actual"]["gates"] = gates
    _, _, envelope = save(archive, record)
    assert envelope["payload"]["actual"]["gates"] == gates


def test_multiprocess_append_is_complete_and_immutable(archive):
    record = make_record()
    program = (
        "import json,sys; from pathlib import Path; "
        "from services.strategies import signal_input_capture as c; "
        "c.data_dir=lambda:Path(sys.argv[1]); c._runner_commit_identity=lambda:'a'*40; "
        "print(json.dumps(c.capture_runner_decision(json.load(sys.stdin))))"
    )
    processes = [subprocess.Popen([sys.executable, "-c", program, str(archive)],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True) for _ in range(4)]
    receipts = []
    for index, process in enumerate(processes):
        out, err = process.communicate(json.dumps(dict(record, loop=index)), timeout=10)
        assert process.returncode == 0, err
        receipts.append(json.loads(out))
    assert all(receipt["ok"] for receipt in receipts)
    records = capture.read_runner_records(archive / receipts[0]["relativepath"])
    assert len(records) == 4
    assert all(capture.replay_runner_decision(record)["decision_match"] for record in records)


def test_missing_object_observation_error_and_empty_folder_cli_fail(archive):
    record = make_record()
    record["observation_error"] = "TypeError"
    _, journal, _ = save(archive, record)
    command = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/replay_runner_decisions.py")]
    result = subprocess.run([*command, str(journal)], capture_output=True, text=True)
    assert result.returncode == 1
    record.pop("observation_error")
    _, journal, envelope = save(archive, record)
    (archive / "signal_inputs" / f"{envelope['payload']['settings_sha256']}.json").unlink()
    result = subprocess.run([*command, str(journal)], capture_output=True, text=True)
    assert result.returncode == 1
    empty = archive / "empty"
    empty.mkdir()
    result = subprocess.run([*command, str(empty)], capture_output=True, text=True)
    assert result.returncode == 1


def test_intended_action_and_settings_disagreement_cannot_claim_matching_replay(archive):
    record = make_record()
    record["actual"]["intended_action"] = "buy"
    _, _, envelope = save(archive, record)
    result = capture.replay_runner_decision(envelope)
    assert result["status"] == "decision_mismatch"
    assert result["matches"]["intended_action"] is False
    record = make_record()
    record["settings"]["runner"] = dict(record["settings"]["runner"], qty=5)
    _, _, envelope = save(archive, record)
    result = capture.replay_runner_decision(envelope)
    assert result["status"] == "decision_mismatch"
    assert result["matches"]["exit_inputs"] is False


def test_cli_is_read_only_with_no_network_config_or_subprocess_access(archive):
    _, journal, _ = save(archive, make_record())
    program = r'''
import os, sys
sys.dont_write_bytecode = True
def audit(event, args):
    if event in {"socket.connect", "subprocess.Popen"}:
        raise AssertionError("offline_boundary_crossed")
    if event == "open":
        path, mode, flags = args
        if isinstance(path, (str, bytes)):
            path = os.fsdecode(path)
            if os.path.basename(path).startswith(".env") or "/runtime/config/" in path:
                raise AssertionError("configuration_read_forbidden")
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise AssertionError("offline_write_forbidden")
sys.addaudithook(audit)
from scripts.replay_runner_decisions import main
raise SystemExit(main([sys.argv[1]]))
'''
    result = subprocess.run([sys.executable, "-c", program, str(journal)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout.splitlines()[-1])["summary"]["decision_match"] == 1


def test_explicit_v2_shared_cas_deduplicates_across_distinct_account_roots(archive, monkeypatch):
    shared = archive / "shared_objects"
    monkeypatch.setenv("CBP_RUNNER_DECISION_OBJECT_DIR", str(shared))
    account_one, account_two = archive / "account_one", archive / "account_two"
    record = make_record()
    record.pop("account_id")
    monkeypatch.setattr(capture, "data_dir", lambda: account_one)
    receipt_one, journal_one, first = save(account_one, record)
    objects = {path.name for path in shared.iterdir()}
    monkeypatch.setattr(capture, "data_dir", lambda: account_two)
    receipt_two, journal_two, second = save(account_two, record)
    assert {path.name for path in shared.iterdir()} == objects
    assert first["payload"]["account_id"] != second["payload"]["account_id"]
    for key in ("code_sha256", "settings_sha256", "completed_prefix_sha256"):
        assert first["payload"][key] == second["payload"][key]
    assert not (account_one / "signal_inputs").exists()
    assert not (account_two / "signal_inputs").exists()
    for receipt, envelope in ((receipt_one, first), (receipt_two, second)):
        assert receipt["shared_objects"] is True and receipt["object_directory"] is None
        assert str(shared) not in json.dumps(receipt)
        assert str(shared) not in json.dumps(envelope)
        with pytest.raises(ValueError, match="missing_object_directory"):
            capture.replay_runner_decision(envelope)
        assert capture.replay_runner_decision(envelope, object_directory=shared)["decision_match"] is True
    command = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/replay_runner_decisions.py")]
    for journal in (journal_one, journal_two):
        result = subprocess.run([*command, str(journal), "--object-directory", str(shared)],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    # ES v1 retains its own local store even when v2 sharing is explicitly enabled.
    monkeypatch.setenv("CBP_CAPTURE_ES_SIGNAL_INPUTS", "1")
    es_receipt = capture.capture_es_inputs(strategy={"name": "sma_200_trend"},
                                            symbol="BTC/USDT", venue="coinbase", ohlcv=record["ohlcv"])
    assert es_receipt["signal_input_capture_status"] == "captured"
    assert (account_two / "signal_inputs" / f"{es_receipt['signal_input_sha256']}.json").exists()
    assert {path.name for path in shared.iterdir()} == objects


def test_shared_cas_relative_path_refused_without_disclosing_path(archive, monkeypatch):
    monkeypatch.setenv("CBP_RUNNER_DECISION_OBJECT_DIR", "DO_NOT_LEAK/relative")
    receipt = capture.capture_runner_decision(make_record())
    assert receipt == {"ok": False, "status": "failed", "error_type": "ValueError"}
    assert not list(archive.rglob("*.jsonl"))
