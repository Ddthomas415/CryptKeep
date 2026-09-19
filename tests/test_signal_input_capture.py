import hashlib
import json

import pytest

from services.strategies import signal_input_capture as capture
from services.strategies.strategy_registry import compute_signal


@pytest.fixture
def inputs(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_CAPTURE_ES_SIGNAL_INPUTS", "1")
    monkeypatch.setattr(capture, "data_dir", lambda: tmp_path)
    return {
        "strategy": {
            "name": "sma_200_trend", "sma_period": 200, "atr_period": 20,
            "evidence_extra": {"market_data_source": "public_ohlcv", "ohlcv_timeframe": "1d"},
            "api_secret": "DO_NOT_STORE",
        },
        "symbol": "BTC/USDT", "venue": "coinbase",
        "ohlcv": [[1700000000000 + i * 86400000, 100+i, 102+i, 99+i, 101+i, 10] for i in range(210)],
    }


def test_capture_replay_and_dedup(inputs, tmp_path):
    first = capture.capture_es_inputs(**inputs)
    assert first["signal_input_capture_status"] == "captured"
    second = capture.capture_es_inputs(**inputs)
    assert second["signal_input_sha256"] == first["signal_input_sha256"]
    path = tmp_path / "signal_inputs" / f"{first['signal_input_sha256']}.json"
    assert len(list(path.parent.iterdir())) == 1
    payload = json.loads(path.read_text())
    assert payload["ohlcv"] == inputs["ohlcv"]
    assert "DO_NOT_STORE" not in path.read_text()
    expected = compute_signal(cfg={"strategy": dict(inputs["strategy"], emit_evidence=False)},
                              symbol=inputs["symbol"], ohlcv=inputs["ohlcv"])
    assert capture.replay_es_inputs(path, expected_sha256=first["signal_input_sha256"]) == expected
    inputs["ohlcv"][-1][4] += 0.01
    third = capture.capture_es_inputs(**inputs)
    assert third["signal_input_sha256"] != first["signal_input_sha256"]
    assert json.loads(path.read_text()) == payload


def test_disabled_and_other_strategy_no_write(inputs, monkeypatch, tmp_path):
    monkeypatch.delenv("CBP_CAPTURE_ES_SIGNAL_INPUTS")
    assert capture.capture_es_inputs(**inputs) == {}
    monkeypatch.setenv("CBP_CAPTURE_ES_SIGNAL_INPUTS", "1")
    inputs["strategy"]["name"] = "ema_cross"
    assert capture.capture_es_inputs(**inputs) == {}
    assert not list(tmp_path.iterdir())


def test_corruption_never_overwritten(inputs, tmp_path):
    ref = capture.capture_es_inputs(**inputs)["signal_input_sha256"]
    path = tmp_path / "signal_inputs" / f"{ref}.json"
    path.write_text("corrupt")
    assert capture.capture_es_inputs(**inputs)["signal_input_capture_status"] == "failed"
    assert path.read_text() == "corrupt"
    with pytest.raises(ValueError, match="hash_mismatch"):
        capture.replay_es_inputs(path, expected_sha256=ref)


def test_code_mismatch_refuses_replay(inputs, tmp_path, monkeypatch):
    ref = capture.capture_es_inputs(**inputs)["signal_input_sha256"]
    monkeypatch.setattr(capture, "_code_identity", lambda: {"changed": True})
    with pytest.raises(ValueError, match="code_mismatch"):
        capture.replay_es_inputs(tmp_path / "signal_inputs" / f"{ref}.json", expected_sha256=ref)


@pytest.mark.parametrize("fail", [False, True])
def test_runner_links_evidence_without_changing_signal(inputs, monkeypatch, tmp_path, fail):
    from services.execution import strategy_runner as runner
    from services.strategies.evidence_logger import EvidenceLogger

    records = []
    monkeypatch.setattr(EvidenceLogger, "log_signal", lambda self, **kw: records.append(kw))
    expected = compute_signal(cfg={"strategy": dict(inputs["strategy"], emit_evidence=False)},
                              symbol=inputs["symbol"], ohlcv=inputs["ohlcv"])
    if fail:
        def broken(_payload):
            raise OSError("DO_NOT_LEAK")
        monkeypatch.setattr(capture, "_store", broken)
    out = runner._registry_signal_with_context(cfg={}, strategy_block=inputs["strategy"],
                                               symbol=inputs["symbol"], venue=inputs["venue"],
                                               ohlcv=inputs["ohlcv"])
    for key, value in expected.items():
        assert out[key] == value
    extra = records[-1]["extra"]
    assert extra["signal_input_capture_status"] == ("failed" if fail else "captured")
    assert "DO_NOT_LEAK" not in str(extra)
    assert "signal_input_capture_status" not in inputs["strategy"]["evidence_extra"]
    if fail:
        assert "signal_input_sha256" not in extra
    else:
        path = tmp_path / "signal_inputs" / f"{extra['signal_input_sha256']}.json"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == extra["signal_input_sha256"]


def test_nonfinite_inputs_fail_without_artifact(inputs, tmp_path):
    inputs["ohlcv"][-1][4] = float("nan")
    assert capture.capture_es_inputs(**inputs)["signal_input_capture_status"] == "failed"
    assert not list(tmp_path.iterdir())


def test_concurrent_publication_is_complete_and_deduplicated(inputs, tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=4) as pool:
        refs = list(pool.map(lambda _: capture.capture_es_inputs(**inputs), range(8)))
    assert all(r["signal_input_capture_status"] == "captured" for r in refs)
    assert len({r["signal_input_sha256"] for r in refs}) == 1
    files = list((tmp_path / "signal_inputs").iterdir())
    assert len(files) == 1
    assert json.loads(files[0].read_text())["ohlcv"] == inputs["ohlcv"]


def test_replay_in_fresh_process(inputs, tmp_path):
    import subprocess
    import sys

    ref = capture.capture_es_inputs(**inputs)["signal_input_sha256"]
    path = tmp_path / "signal_inputs" / f"{ref}.json"
    subprocess.run([
        sys.executable, "-c",
        "from pathlib import Path; import sys; "
        "from services.strategies.signal_input_capture import replay_es_inputs; "
        "assert replay_es_inputs(Path(sys.argv[1]), expected_sha256=sys.argv[2])['ok']",
        str(path), ref,
    ], check=True, capture_output=True, text=True)


def test_omitted_parameter_defaults_match_registry(inputs, tmp_path):
    inputs["strategy"].pop("sma_period")
    inputs["strategy"].pop("atr_period")
    ref = capture.capture_es_inputs(**inputs)["signal_input_sha256"]
    expected = compute_signal(cfg={"strategy": dict(inputs["strategy"], emit_evidence=False)},
                              symbol=inputs["symbol"], ohlcv=inputs["ohlcv"])
    assert capture.replay_es_inputs(tmp_path / "signal_inputs" / f"{ref}.json", expected_sha256=ref) == expected
