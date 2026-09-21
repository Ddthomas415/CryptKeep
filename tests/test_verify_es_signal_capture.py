import json

import pytest

from scripts.research.verify_es_signal_capture import timestamp, verify
from services.strategies import signal_input_capture as capture
from services.strategies.strategy_registry import compute_signal


@pytest.fixture
def recorded(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_CAPTURE_ES_SIGNAL_INPUTS", "1")
    monkeypatch.setattr(capture, "data_dir", lambda: tmp_path / "data")
    rows = [[1700000000000+i*86400000, 100+i, 102+i, 99+i, 101+i, 10] for i in range(210)]
    extra = {"ohlcv_venue": "coinbase", "ohlcv_symbol": "BTC/USDT",
             "ohlcv_timeframe": "1d", "market_data_source": "public_ohlcv"}
    strategy = {"name": "sma_200_trend", "evidence_extra": extra}
    ref = capture.capture_es_inputs(strategy=strategy, symbol="BTC/USDT", venue="coinbase", ohlcv=rows)
    result = compute_signal(cfg={"strategy": dict(strategy, emit_evidence=False)}, symbol="BTC/USDT", ohlcv=rows)
    record = dict(extra, **ref, record_type="signal", timestamp="2026-09-22T00:01:00Z",
                  signal_direction=result["signal"], regime_flag=result["regime"],
                  entry_allowed=result["entry_allowed"], sma_200=result["sma_200"], atr_ratio=result["atr_ratio"])
    path = tmp_path / "data/evidence/es_daily_trend_v1/signal_2026-09-22.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record)+"\n")
    return tmp_path, path, record


def check(root):
    return verify(root, since=timestamp("2026-09-22T00:00:00Z"), until=timestamp("2026-09-23T00:00:00Z"))


def test_real_replay_is_read_only(recorded):
    root, _, _ = recorded
    before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert check(root)["status"] == "passed"
    assert before == {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("field,value", [("signal_direction", "flat"), ("sma_200", 1.0),
                                        ("ohlcv_venue", "other"), ("signal_input_sha256", "../escape"),
                                        ("signal_input_capture_status", "failed")])
def test_mismatch_or_missing_capture_fails(recorded, field, value):
    root, path, record = recorded
    record[field] = value
    path.write_text(json.dumps(record)+"\n")
    assert check(root)["status"] == "failed"


def test_no_records_not_success(tmp_path):
    assert check(tmp_path)["status"] == "no_records"


def test_corrupt_artifact_fails(recorded):
    root, _, record = recorded
    (root / "data/signal_inputs" / (record["signal_input_sha256"]+".json")).write_text("{}")
    assert check(root)["status"] == "failed"


def test_window_excludes_prior_evidence(recorded):
    root, path, record = recorded
    record["timestamp"] = "2026-09-21T00:01:00Z"
    record.pop("signal_input_sha256")
    path.write_text(json.dumps(record)+"\n")
    assert check(root)["status"] == "no_records"


def test_malformed_line_not_silently_skipped(recorded):
    root, path, _ = recorded
    with path.open("a") as out:
        out.write("broken\n")
    assert check(root)["status"] == "failed"


def test_timezone_required():
    with pytest.raises(ValueError):
        timestamp("2026-09-22T00:00:00")


def test_missing_state_refused(tmp_path):
    with pytest.raises(ValueError, match="state_directory_missing"):
        check(tmp_path / "missing")


def test_cli_exit_codes(recorded, monkeypatch, capsys):
    from scripts.research.verify_es_signal_capture import main

    root, path, record = recorded
    args = ["verify", "--state-dir", str(root), "--since", "2026-09-22T00:00:00Z",
            "--until", "2026-09-23T00:00:00Z"]
    monkeypatch.setattr("sys.argv", args)
    assert main() == 0
    path.write_text("")
    assert main() == 2
    record["signal_direction"] = "wrong"
    path.write_text(json.dumps(record)+"\n")
    assert main() == 1
