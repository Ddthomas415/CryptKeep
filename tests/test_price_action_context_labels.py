from __future__ import annotations

import json
from pathlib import Path

from scripts.research import run_price_action_context_labels as runner
from services.backtest.price_action_context import (
    LIMITATIONS,
    build_price_action_context_artifact,
    label_price_action_context,
)
from storage.market_store_sqlite import MarketStore


def _rows() -> list[list[float]]:
    base = 1_700_000_000_000
    minute = 60_000
    return [
        [base + minute * 0, 100.0, 101.0, 99.0, 100.5, 10.0],
        [base + minute * 1, 100.6, 101.2, 100.1, 100.2, 11.0],
        [base + minute * 2, 100.1, 100.3, 99.8, 100.0, 12.0],
        [base + minute * 3, 99.8, 103.0, 99.7, 102.8, 30.0],  # bullish engulfing + displacement
        [base + minute * 4, 103.0, 103.2, 100.9, 101.2, 28.0],  # bearish swing failure
        [base + minute * 5, 101.1, 101.2, 98.5, 100.9, 31.0],  # lower rejection + bullish sweep
        [base + minute * 6, 104.0, 105.0, 103.8, 104.8, 40.0],  # bullish fair value gap
        [base + minute * 7, 104.6, 104.9, 103.2, 103.6, 19.0],
        [base + minute * 8, 103.4, 103.6, 102.9, 103.1, 18.0],
        [base + minute * 9, 102.9, 103.0, 100.0, 100.2, 34.0],
        [base + minute * 10, 100.1, 100.3, 99.8, 100.0, 15.0],
        [base + minute * 11, 100.1, 100.4, 99.9, 100.2, 15.0],
    ]


def _seed_archive(db_path, rows: list[list[float]]) -> None:
    store = MarketStore(db_path)
    for row in rows:
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


def test_price_action_labels_capture_requested_contexts() -> None:
    labels = label_price_action_context(
        _rows(),
        swing_lookback=3,
        range_lookback=3,
        displacement_lookback=3,
        opening_range_bars=3,
    )

    assert len(labels) == len(_rows())
    assert any(row["engulfing_candle"] == "bullish" for row in labels)
    assert any(row["rejection_wick"] == "lower" for row in labels)
    assert any(row["swing_failure"] == "bearish" for row in labels)
    assert any(row["swing_failure"] == "bullish" for row in labels)
    assert any(row["fair_value_gap"] == "bullish" for row in labels)
    assert any(row["displacement_bar"] is True for row in labels)
    assert any(str(row["acceptance_rejection"]).startswith("acceptance_") for row in labels)
    assert any(str(row["opening_range_state"]).startswith("acceptance_") for row in labels)
    assert all(row["volume_profile_acceptance"] == "requires_trade_or_tick_volume_profile" for row in labels)


def test_price_action_artifact_is_research_only_and_hashed() -> None:
    artifact = build_price_action_context_artifact(
        _rows(),
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1m",
        generated_at="2026-07-22T00:00:00Z",
    )

    assert artifact["ok"] is True
    assert artifact["artifact_type"] == "price_action_context_labels_v1"
    assert artifact["research_only"] is True
    assert artifact["limitations"] == LIMITATIONS
    assert artifact["databento_policy"] == "separate_data_source_rfc_required"
    assert len(artifact["dataset_hash"]) == 64
    assert len(artifact["artifact_hash"]) == 64
    assert artifact["label_counts"]["engulfing_candle"] >= 1
    assert artifact["label_counts"]["volume_profile_acceptance"] == 0


def test_price_action_context_cli_writes_archive_backed_artifact(tmp_path, capsys) -> None:
    db = tmp_path / "market_raw.sqlite"
    output = tmp_path / "price_action_labels.json"
    _seed_archive(db, _rows())

    rc = runner.main(
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
            str(len(_rows())),
            "--swing-lookback",
            "3",
            "--range-lookback",
            "3",
            "--displacement-lookback",
            "3",
            "--output",
            str(output),
        ]
    )

    printed = json.loads(capsys.readouterr().out)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload == printed
    assert payload["ok"] is True
    assert payload["archive"]["source"] == "market_ohlcv_archive"
    assert payload["archive"]["complete"] is True
    assert payload["dataset_hash"] == payload["archive"]["dataset_hash"]
    assert payload["research_only"] is True


def test_price_action_context_cli_fails_closed_for_missing_archive(tmp_path, capsys) -> None:
    rc = runner.main(
        [
            "--archive-db",
            str(tmp_path / "missing.sqlite"),
            "--venue",
            "coinbase",
            "--symbol",
            "BTC/USD",
            "--timeframe",
            "1m",
            "--limit",
            "12",
            "--fail-if-not-ok",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert payload["reason"] == "archive_missing"
    assert payload["research_only"] is True


def test_price_action_research_docs_and_make_target_preserve_boundary() -> None:
    doc = Path("docs/research/pattern_strategy_backlog.md").read_text(encoding="utf-8")
    remaining = Path("REMAINING_TASKS.md").read_text(encoding="utf-8")
    makefile = Path("Makefile").read_text(encoding="utf-8")

    for text in (doc, remaining):
        assert "services/backtest/price_action_context.py" in text
        assert "scripts/research/run_price_action_context_labels.py" in text
        assert "research-only" in text
        assert "Databento" in text
        assert "volume" in text.lower()
        assert "profile" in text.lower()
    assert "price-action-context-labels:" in makefile
    assert "run_price_action_context_labels.py" in makefile
