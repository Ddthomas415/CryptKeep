from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts import run_signal_quality_report as script


def test_run_signal_quality_report_writes_artifacts(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    ohlcv_path = tmp_path / "ohlcv.json"
    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    rows = []
    for day, close_price in enumerate((100.0, 102.0, 101.0, 112.0, 113.0)):
        ts = int((start + timedelta(days=day)).timestamp() * 1000.0)
        rows.append([ts, close_price, close_price + 2.0, close_price - 1.0, close_price, 1.0])
    ohlcv_path.write_text(json.dumps(rows), encoding="utf-8")

    ev_dir = tmp_path / "data" / "evidence" / "demo_strategy"
    ev_dir.mkdir(parents=True, exist_ok=True)
    signal = {
        "record_type": "signal",
        "timestamp": datetime.fromtimestamp(rows[2][0] / 1000.0, tz=timezone.utc).isoformat(),
        "price": 101.0,
        "signal_direction": "long",
        "entry_allowed": True,
        "regime_flag": "trending",
        "market_data_source": "public_ohlcv",
        "ohlcv_sample_mode": False,
        "ohlcv_venue": "coinbase",
        "ohlcv_timeframe": "1d",
    }
    (ev_dir / "signal_2026-05-24.jsonl").write_text(json.dumps(signal) + "\n", encoding="utf-8")

    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "run_signal_quality_report.py",
            "--strategy-id",
            "demo_strategy",
            "--evidence-dir",
            str(ev_dir),
            "--ohlcv-path",
            str(ohlcv_path),
            "--horizon-bars",
            "2",
            "--target-move-pct",
            "0.10",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["summary"]["signals_scored"] == 1
    assert out["artifacts"]["latest_path"].endswith("signal_quality.latest.json")
    assert Path(out["artifacts"]["latest_path"]).exists()
    assert Path(out["artifacts"]["history_path"]).exists()


def test_run_signal_quality_report_allows_explicit_unqualified_research(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    ohlcv_path = tmp_path / "ohlcv.json"
    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    rows = []
    for day, close_price in enumerate((100.0, 102.0, 101.0, 112.0)):
        ts = int((start + timedelta(days=day)).timestamp() * 1000.0)
        rows.append([ts, close_price, close_price + 2.0, close_price - 1.0, close_price, 1.0])
    ohlcv_path.write_text(json.dumps(rows), encoding="utf-8")

    ev_dir = tmp_path / "data" / "evidence" / "demo_strategy"
    ev_dir.mkdir(parents=True, exist_ok=True)
    signal = {
        "record_type": "signal",
        "timestamp": datetime.fromtimestamp(rows[2][0] / 1000.0, tz=timezone.utc).isoformat(),
        "price": 101.0,
        "signal_direction": "long",
        "entry_allowed": True,
    }
    (ev_dir / "signal_2026-05-24.jsonl").write_text(json.dumps(signal) + "\n", encoding="utf-8")

    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "run_signal_quality_report.py",
            "--strategy-id",
            "demo_strategy",
            "--evidence-dir",
            str(ev_dir),
            "--ohlcv-path",
            str(ohlcv_path),
            "--horizon-bars",
            "1",
            "--allow-unqualified-evidence",
            "--no-persist",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["provenance_policy"]["required"] is False
    assert out["summary"]["matching_provenance_signal_records"] == 0
    assert out["summary"]["unqualified_signal_records"] == 1
    assert out["summary"]["eligible_signal_records"] == 1
    assert out["summary"]["excluded_unqualified_signals"] == 0
    assert out["summary"]["signals_scored"] == 1
