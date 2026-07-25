from __future__ import annotations

import json
from pathlib import Path

from services.backtest.price_action_context import (
    ARTIFACT_TYPE,
    build_price_action_context_artifact,
    compute_price_action_labels,
    run_archive_price_action_context,
)
from storage.market_store_sqlite import MarketStore


BASE_TS = 1_700_000_000_000


def _row(idx: int, o: float, h: float, l: float, c: float, v: float = 10.0) -> list[float]:
    return [BASE_TS + idx * 60_000, o, h, l, c, v]


def test_price_action_labels_detect_engulfing_fvg_and_opening_range() -> None:
    rows = [
        _row(0, 100.0, 101.0, 97.0, 98.0),
        _row(1, 97.0, 102.0, 96.0, 101.0),
        _row(2, 102.0, 103.0, 101.5, 102.5),
    ]

    labels = compute_price_action_labels(
        rows,
        opening_range_bars=2,
        displacement_lookback=2,
    )

    assert labels[1]["labels"]["engulfing_candle"] == "bullish"
    assert labels[2]["labels"]["fair_value_gap"] == "bullish"
    assert labels[2]["labels"]["opening_range_state"] == "accepted_above"
    assert labels[2]["labels"]["acceptance_rejection"] == "acceptance_above_opening_range"


def test_price_action_labels_detect_rejection_swing_failure_and_manipulation_candidate() -> None:
    rows = [
        _row(0, 99.0, 100.0, 95.0, 98.0),
        _row(1, 98.0, 101.0, 96.0, 100.0),
        _row(2, 100.0, 106.0, 96.0, 97.5),
    ]

    labels = compute_price_action_labels(
        rows,
        swing_lookback=2,
        displacement_lookback=2,
        displacement_range_multiplier=1.1,
        displacement_body_fraction=0.2,
    )

    assert labels[2]["labels"]["rejection_wick"] == "bearish_upper"
    assert labels[2]["labels"]["swing_failure"] == "bearish"
    assert labels[2]["labels"]["displacement_bar"] is True
    assert labels[2]["labels"]["manipulation_candidate"] == "liquidity_sweep_reversal"


def test_price_action_labels_detect_break_and_retest() -> None:
    rows = [
        _row(0, 99.0, 100.0, 95.0, 98.0),
        _row(1, 98.0, 101.0, 96.0, 99.0),
        _row(2, 100.0, 103.0, 99.0, 102.0),
        _row(3, 102.0, 103.0, 100.5, 101.5),
    ]

    labels = compute_price_action_labels(rows, swing_lookback=2)

    assert labels[3]["labels"]["break_and_retest"] == "bullish_hold"


def test_price_action_artifact_is_research_only_and_dataset_hashed() -> None:
    rows = [
        _row(0, 100.0, 101.0, 99.0, 100.5),
        _row(1, 100.5, 102.0, 100.0, 101.5),
        _row(2, 101.5, 103.0, 101.0, 102.5),
    ]

    artifact = build_price_action_context_artifact(
        rows=rows,
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1h",
        archive_path="/tmp/archive.sqlite",
    )

    assert artifact["ok"] is True
    assert artifact["artifact_type"] == ARTIFACT_TYPE
    assert artifact["research_only"] is True
    assert artifact["not_strategy_config"] is True
    assert artifact["not_campaign_evidence"] is True
    assert artifact["not_promotion_evidence"] is True
    assert artifact["not_profitability_evidence"] is True
    assert len(artifact["dataset"]["dataset_hash"]) == 64
    assert artifact["dataset"]["bars"] == 3
    assert len(artifact["labels"]) == 3
    assert artifact["deferred_data_sources"]["databento"].startswith("deferred")


def test_archive_runner_refuses_missing_archive_without_live_fallback(tmp_path: Path) -> None:
    out = run_archive_price_action_context(
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1h",
        limit=3,
        db_path=str(tmp_path / "missing.sqlite"),
    )

    assert out["ok"] is False
    assert out["reason"] == "archive_missing"
    assert out["labels"] == []
    assert out["research_only"] is True


def test_archive_runner_reads_complete_archive(tmp_path: Path) -> None:
    db_path = tmp_path / "market.sqlite"
    store = MarketStore(db_path)
    for row in [
        _row(0, 100.0, 101.0, 99.0, 100.5),
        _row(1, 100.5, 102.0, 100.0, 101.5),
        _row(2, 101.5, 103.0, 101.0, 102.5),
    ]:
        store.upsert_ohlcv(
            ts_ms=int(row[0]),
            exchange="coinbase",
            symbol="BTC/USDT",
            timeframe="1h",
            o=row[1],
            h=row[2],
            l=row[3],
            cl=row[4],
            v=row[5],
        )

    out = run_archive_price_action_context(
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1h",
        limit=3,
        db_path=str(db_path),
    )

    assert out["ok"] is True
    assert out["dataset"]["bars"] == 3
    assert len(out["dataset"]["dataset_hash"]) == 64
    assert len(out["labels"]) == 3


def test_price_action_context_cli_writes_artifact_and_uses_exit_2_for_missing_archive(
    tmp_path: Path,
) -> None:
    from scripts.research.run_price_action_context_labels import main

    missing_rc = main(
        [
            "--archive-db",
            str(tmp_path / "missing.sqlite"),
            "--limit",
            "3",
            "--fail-if-not-ok",
        ]
    )
    assert missing_rc == 2

    db_path = tmp_path / "market.sqlite"
    out_path = tmp_path / "labels.json"
    store = MarketStore(db_path)
    for row in [
        _row(0, 100.0, 101.0, 99.0, 100.5),
        _row(1, 100.5, 102.0, 100.0, 101.5),
        _row(2, 101.5, 103.0, 101.0, 102.5),
    ]:
        store.upsert_ohlcv(
            ts_ms=int(row[0]),
            exchange="coinbase",
            symbol="BTC/USDT",
            timeframe="1h",
            o=row[1],
            h=row[2],
            l=row[3],
            cl=row[4],
            v=row[5],
        )

    rc = main(
        [
            "--archive-db",
            str(db_path),
            "--limit",
            "3",
            "--output",
            str(out_path),
            "--fail-if-not-ok",
        ]
    )
    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["script"] == "scripts/research/run_price_action_context_labels.py"
