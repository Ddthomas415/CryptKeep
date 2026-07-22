from __future__ import annotations

import json

from services.analytics.price_action_context_labels import (
    build_price_action_context_labels,
    run_archive_price_action_context_labels,
)
from storage.market_store_sqlite import MarketStore


BASE_TS = 1_700_000_000_000


def _row(idx: int, o: float, h: float, l: float, c: float, v: float = 10.0) -> list[float]:
    return [BASE_TS + idx * 60_000, o, h, l, c, v]


def _label_rows() -> list[list[float]]:
    return [
        _row(0, 100.0, 101.0, 99.0, 100.0),
        _row(1, 101.0, 102.0, 98.0, 99.0),
        _row(2, 98.5, 102.0, 98.0, 101.5),  # bullish engulfing
        _row(3, 103.0, 105.0, 102.5, 104.5),  # bullish FVG vs row 1
        _row(4, 105.2, 106.0, 104.2, 105.5),
        _row(5, 105.4, 108.0, 104.5, 105.0),  # bearish swing failure
        _row(6, 105.2, 105.4, 99.0, 99.5),  # displacement down
        _row(7, 99.7, 103.0, 99.2, 102.8),  # retest/recovery candidate
    ]


def test_price_action_context_labels_detect_core_ohlcv_patterns() -> None:
    report = build_price_action_context_labels(
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1m",
        rows=_label_rows(),
        swing_lookback=3,
        range_lookback=3,
        displacement_range_multiplier=1.3,
    )

    assert report["ok"] is True
    assert report["research_only"] is True
    assert report["not_strategy_config"] is True
    assert report["not_campaign_evidence"] is True
    assert report["not_promotion_evidence"] is True
    assert report["not_profitability_evidence"] is True
    assert len(report["dataset_hash"]) == 64
    assert len(report["artifact_hash"]) == 64

    labels = [row["labels"] for row in report["labels"]]
    assert labels[2]["engulfing_candle"] == "bullish"
    assert labels[3]["fair_value_gap"] == "bullish"
    assert labels[5]["swing_failure"] == "bearish"
    assert labels[6]["displacement_bar"] == "bearish"
    assert report["label_counts"]["engulfing_candle:bullish"] == 1
    assert "databento_deferred_to_separate_data_source_rfc" in report["limitations"]


def test_price_action_context_labels_report_insufficient_rows() -> None:
    report = build_price_action_context_labels(
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1m",
        rows=[_row(0, 100.0, 101.0, 99.0, 100.0)],
    )

    assert report["ok"] is False
    assert report["reason"] == "insufficient_ohlcv_rows"
    assert report["labels"] == []


def test_archive_price_action_context_labels_loads_archive_and_preserves_hash(tmp_path) -> None:
    db = tmp_path / "market_raw.sqlite"
    store = MarketStore(db)
    for row in _label_rows():
        store.upsert_ohlcv(
            ts_ms=int(row[0]),
            exchange="coinbase",
            symbol="BTC/USD",
            timeframe="1m",
            o=float(row[1]),
            h=float(row[2]),
            l=float(row[3]),
            cl=float(row[4]),
            v=float(row[5]),
        )

    report = run_archive_price_action_context_labels(
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1m",
        limit=len(_label_rows()),
        db_path=db,
        swing_lookback=3,
        range_lookback=3,
    )

    assert report["ok"] is True
    assert report["source"] == "market_ohlcv_archive"
    assert report["dataset_hash"] == report["archive"]["dataset_hash"]
    assert report["row_count"] == len(_label_rows())


def test_price_action_context_labels_cli_writes_artifact(tmp_path, capsys) -> None:
    from scripts.research import run_price_action_context_labels as cli

    db = tmp_path / "market_raw.sqlite"
    out_path = tmp_path / "price_action.json"
    store = MarketStore(db)
    for row in _label_rows():
        store.upsert_ohlcv(
            ts_ms=int(row[0]),
            exchange="coinbase",
            symbol="BTC/USD",
            timeframe="1m",
            o=float(row[1]),
            h=float(row[2]),
            l=float(row[3]),
            cl=float(row[4]),
            v=float(row[5]),
        )

    rc = cli.main(
        [
            "--archive-db",
            str(db),
            "--venue",
            "coinbase",
            "--symbol",
            "BTC/USD",
            "--timeframe",
            "1m",
            "--limit",
            str(len(_label_rows())),
            "--output",
            str(out_path),
            "--fail-if-not-ok",
        ]
    )

    printed = json.loads(capsys.readouterr().out)
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert printed == written
    assert printed["artifact_type"] == "price_action_context_labels_v1"


def test_price_action_context_labels_cli_returns_2_for_missing_archive(tmp_path, capsys) -> None:
    from scripts.research import run_price_action_context_labels as cli

    rc = cli.main(["--archive-db", str(tmp_path / "missing.sqlite"), "--limit", "10", "--fail-if-not-ok"])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert payload["reason"] == "archive_missing"
