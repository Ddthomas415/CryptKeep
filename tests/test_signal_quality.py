from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


def _iso(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).isoformat()


def _write_signal_file(ev_dir: Path, records: list[dict]) -> None:
    ev_dir.mkdir(parents=True, exist_ok=True)
    (ev_dir / "signal_2026-05-24.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def test_build_signal_quality_dedupes_and_scores_hit(tmp_path) -> None:
    from services.analytics.signal_quality import build_signal_quality_report

    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    rows = []
    for day, close_price in enumerate((100.0, 102.0, 101.0, 112.0, 113.0, 114.0)):
        ts = int((start + timedelta(days=day)).timestamp() * 1000.0)
        rows.append([ts, close_price, close_price + 2.0, close_price - 1.0, close_price, 1.0])

    ev_dir = tmp_path / "data" / "evidence" / "demo_strategy"
    signal_ts = _iso(rows[2][0])
    _write_signal_file(
        ev_dir,
        [
            {
                "record_type": "signal",
                "timestamp": signal_ts,
                "price": 101.0,
                "signal_direction": "long",
                "entry_allowed": True,
                "regime_flag": "trending",
            },
            {
                "record_type": "signal",
                "timestamp": signal_ts,
                "price": 101.0,
                "signal_direction": "long",
                "entry_allowed": True,
                "regime_flag": "trending",
            },
        ],
    )

    report = build_signal_quality_report(
        strategy_id="demo_strategy",
        evidence_dir=ev_dir,
        ohlcv_rows=rows,
        horizon_bars=2,
        target_move_pct=0.10,
        lookback_bars=2,
        require_matching_provenance=False,
    )

    assert report["ok"] is True
    assert report["summary"]["actionable_signals"] == 2
    assert report["summary"]["deduped_signals"] == 1
    assert report["summary"]["signals_scored"] == 1
    assert report["summary"]["target_move_hits"] == 1
    assert report["summary"]["late_hits"] == 0
    assert report["rows"][0]["classification"] == "hit"
    assert report["rows"][0]["match_method"] == "timestamp"


def test_build_signal_quality_uses_price_fallback_for_late_hit(tmp_path) -> None:
    from services.analytics.signal_quality import build_signal_quality_report

    start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    rows = []
    spec = [
        (100.0, 101.0, 99.0, 100.0),
        (110.0, 125.0, 109.0, 124.0),
        (124.0, 130.0, 123.0, 129.0),
        (129.0, 131.0, 127.0, 130.0),
    ]
    for day, (open_price, high_price, low_price, close_price) in enumerate(spec):
        ts = int((start + timedelta(days=day)).timestamp() * 1000.0)
        rows.append([ts, open_price, high_price, low_price, close_price, 1.0])

    ev_dir = tmp_path / "data" / "evidence" / "demo_strategy"
    _write_signal_file(
        ev_dir,
        [
            {
                "record_type": "signal",
                "timestamp": "2026-05-24T00:00:00+00:00",
                "price": 124.0,
                "signal_direction": "long",
                "entry_allowed": True,
                "regime_flag": "trending",
            }
        ],
    )

    report = build_signal_quality_report(
        strategy_id="demo_strategy",
        evidence_dir=ev_dir,
        ohlcv_rows=rows,
        horizon_bars=2,
        target_move_pct=0.04,
        lookback_bars=2,
        late_threshold_share=0.25,
        require_matching_provenance=False,
    )

    assert report["ok"] is True
    assert report["summary"]["signals_scored"] == 1
    assert report["summary"]["late_hits"] == 1
    assert report["rows"][0]["classification"] == "late_hit"
    assert report["rows"][0]["match_method"] == "price_fallback"
    assert report["rows"][0]["pre_signal_move_share"] > 0.25


def test_build_signal_quality_uses_canonical_local_snapshot(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    from services.analytics.signal_quality import build_signal_quality_report
    from services.market_data.local_data_reader import write_local_ohlcv_snapshot

    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    rows = []
    for day, close_price in enumerate((100.0, 102.0, 101.0, 112.0, 113.0, 114.0)):
        ts = int((start + timedelta(days=day)).timestamp() * 1000.0)
        rows.append([ts, close_price, close_price + 2.0, close_price - 1.0, close_price, 1.0])

    write_local_ohlcv_snapshot("coinbase", "BTC/USDT", rows, timeframe="1d")

    ev_dir = tmp_path / "data" / "evidence" / "demo_strategy"
    signal_ts = _iso(rows[2][0])
    _write_signal_file(
        ev_dir,
        [
            {
                "record_type": "signal",
                "timestamp": signal_ts,
                "price": 101.0,
                "signal_direction": "long",
                "entry_allowed": True,
                "regime_flag": "trending",
            }
        ],
    )

    report = build_signal_quality_report(
        strategy_id="demo_strategy",
        evidence_dir=ev_dir,
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1d",
        horizon_bars=2,
        target_move_pct=0.10,
        require_matching_provenance=False,
    )

    assert report["ok"] is True
    assert report["ohlcv_source"]["type"] == "local_snapshot"
    assert report["summary"]["signals_scored"] == 1


def test_build_signal_quality_marks_price_mismatch_unscored(tmp_path) -> None:
    from services.analytics.signal_quality import build_signal_quality_report

    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    rows = []
    for day, close_price in enumerate((78000.0, 79000.0, 80000.0)):
        ts = int((start + timedelta(days=day)).timestamp() * 1000.0)
        rows.append([ts, close_price, close_price + 500.0, close_price - 500.0, close_price, 1.0])

    ev_dir = tmp_path / "data" / "evidence" / "demo_strategy"
    _write_signal_file(
        ev_dir,
        [
            {
                "record_type": "signal",
                "timestamp": _iso(rows[1][0]),
                "price": 120.9,
                "signal_direction": "long",
                "entry_allowed": True,
                "regime_flag": "trending",
            }
        ],
    )

    report = build_signal_quality_report(
        strategy_id="demo_strategy",
        evidence_dir=ev_dir,
        ohlcv_rows=rows,
        horizon_bars=1,
        target_move_pct=0.10,
        require_matching_provenance=False,
    )

    assert report["ok"] is True
    assert report["summary"]["signals_scored"] == 0
    assert report["summary"]["price_mismatch_signals"] == 1
    assert report["rows"][0]["classification"] == "unscored"
    assert report["rows"][0]["reason"] == "price_ohlcv_mismatch"


def test_build_signal_quality_excludes_sample_backed_signals(tmp_path) -> None:
    from services.analytics.signal_quality import build_signal_quality_report

    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    rows = []
    for day, close_price in enumerate((100.0, 102.0, 101.0, 112.0)):
        ts = int((start + timedelta(days=day)).timestamp() * 1000.0)
        rows.append([ts, close_price, close_price + 2.0, close_price - 1.0, close_price, 1.0])

    ev_dir = tmp_path / "data" / "evidence" / "demo_strategy"
    _write_signal_file(
        ev_dir,
        [
            {
                "record_type": "signal",
                "timestamp": _iso(rows[2][0]),
                "price": 101.0,
                "signal_direction": "long",
                "entry_allowed": True,
                "regime_flag": "trending",
                "market_data_source": "sample_ohlcv",
                "ohlcv_sample_mode": True,
            }
        ],
    )

    report = build_signal_quality_report(
        strategy_id="demo_strategy",
        evidence_dir=ev_dir,
        ohlcv_rows=rows,
        horizon_bars=1,
        target_move_pct=0.10,
    )

    assert report["ok"] is True
    assert report["summary"]["excluded_sample_signals"] == 1
    assert report["summary"]["actionable_signals"] == 0
    assert report["summary"]["signals_scored"] == 0


def test_build_signal_quality_requires_matching_public_provenance_by_default(tmp_path) -> None:
    from services.analytics.signal_quality import build_signal_quality_report

    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    rows = []
    for day, close_price in enumerate((100.0, 102.0, 101.0, 112.0)):
        ts = int((start + timedelta(days=day)).timestamp() * 1000.0)
        rows.append([ts, close_price, close_price + 2.0, close_price - 1.0, close_price, 1.0])

    ev_dir = tmp_path / "data" / "evidence" / "demo_strategy"
    signal_ts = _iso(rows[2][0])
    base = {
        "record_type": "signal",
        "timestamp": signal_ts,
        "price": 101.0,
        "signal_direction": "long",
        "entry_allowed": True,
        "regime_flag": "trending",
    }
    _write_signal_file(
        ev_dir,
        [
            dict(base),
            {
                **base,
                "market_data_source": "unknown_ohlcv",
                "ohlcv_sample_mode": False,
            },
            {
                **base,
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
                "ohlcv_venue": "coinbase",
                "ohlcv_symbol": "ETH/USDT",
                "ohlcv_timeframe": "1d",
            },
            {
                **base,
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
                "ohlcv_venue": "coinbase",
                "ohlcv_symbol": "BTC/USDT",
                "ohlcv_timeframe": "1d",
            },
        ],
    )

    report = build_signal_quality_report(
        strategy_id="demo_strategy",
        evidence_dir=ev_dir,
        ohlcv_rows=rows,
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1d",
        horizon_bars=1,
        target_move_pct=0.10,
    )

    assert report["provenance_policy"]["required"] is True
    assert report["summary"]["matching_provenance_signal_records"] == 1
    assert report["summary"]["unqualified_signal_records"] == 3
    assert report["summary"]["eligible_signal_records"] == 1
    assert report["summary"]["excluded_unqualified_signals"] == 3
    assert report["summary"]["excluded_signal_reason_counts"] == {
        "market_data_source_mismatch": 1,
        "missing_market_data_source": 1,
        "ohlcv_symbol_mismatch": 1,
    }
    assert report["summary"]["actionable_signals"] == 1
    assert report["summary"]["signals_scored"] == 1


def test_build_signal_quality_short_mae_uses_single_relative_move(tmp_path) -> None:
    from services.analytics.signal_quality import build_signal_quality_report

    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    spec = [
        (100.0, 101.0, 99.0, 100.0),
        (100.0, 100.0, 99.0, 100.0),
        (100.0, 110.0, 90.0, 95.0),
    ]
    rows = []
    for day, (open_price, high_price, low_price, close_price) in enumerate(spec):
        ts = int((start + timedelta(days=day)).timestamp() * 1000.0)
        rows.append([ts, open_price, high_price, low_price, close_price, 1.0])

    ev_dir = tmp_path / "data" / "evidence" / "short_strategy"
    _write_signal_file(
        ev_dir,
        [
            {
                "record_type": "signal",
                "timestamp": _iso(rows[1][0]),
                "price": 100.0,
                "signal_direction": "short",
                "entry_allowed": True,
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
                "ohlcv_venue": "coinbase",
                "ohlcv_symbol": "BTC/USDT",
                "ohlcv_timeframe": "1d",
            }
        ],
    )

    report = build_signal_quality_report(
        strategy_id="short_strategy",
        evidence_dir=ev_dir,
        ohlcv_rows=rows,
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1d",
        horizon_bars=1,
        target_move_pct=0.05,
    )

    assert report["summary"]["signals_scored"] == 1
    assert report["rows"][0]["mfe_pct"] == pytest.approx((100.0 / 90.0) - 1.0)
    assert report["rows"][0]["mae_pct"] == pytest.approx((100.0 / 110.0) - 1.0)
