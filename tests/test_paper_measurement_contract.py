from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]


def _policy_config() -> dict:
    return {
        "signal_source": "public_ohlcv_1d",
        "strategy": {
            "venue": "coinbase",
            "symbol": "BTC/USDT",
            "signal": {"timeframe": "1d"},
        },
    }


def _provenance() -> dict:
    return {
        "market_data_source": "public_ohlcv",
        "ohlcv_sample_mode": False,
        "ohlcv_timeframe": "1d",
        "ohlcv_venue": "coinbase",
        "ohlcv_symbol": "BTC/USDT",
    }


def _write_journal(path: Path, rows: list[tuple]) -> None:
    con = sqlite3.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE journal_fills (
              fill_id TEXT PRIMARY KEY,
              journal_ts TEXT NOT NULL,
              order_id TEXT NOT NULL,
              fill_ts TEXT NOT NULL,
              venue TEXT NOT NULL,
              symbol TEXT NOT NULL,
              side TEXT NOT NULL,
              qty REAL NOT NULL,
              price REAL NOT NULL,
              fee REAL NOT NULL,
              fee_currency TEXT NOT NULL
            )
            """
        )
        con.executemany("INSERT INTO journal_fills VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
        con.commit()
    finally:
        con.close()


def test_paper_gate_metric_names_authoritative_expectancy_unit() -> None:
    from scripts.check_promotion_gates import _paper_gate_trade_metrics

    jsonl_fills = []
    for _ in range(5):
        jsonl_fills.append({"side": "buy", "size": 1.0, "pnl_usd": None})
        jsonl_fills.append({"side": "sell", "size": 1.0, "pnl_usd": -999.0})

    metrics = _paper_gate_trade_metrics(
        jsonl_fills,
        {
            "ok": True,
            "source": "jsonl_provenance+trade_journal_sqlite",
            "fills": 10,
            "closed_trades": 5,
            "all_history_closed_trades": 5,
            "expectancy_per_closed_trade": 4.25,
            "qualification": {
                "evidence_fills": 10,
                "unqualified_evidence_fills": 0,
                "incomplete_qualified_evidence_fills": 0,
            },
        },
    )

    assert metrics["expectancy_value"] == pytest.approx(4.25)
    assert metrics["expectancy_unit"] == "closed_trade"
    assert metrics["expectancy_denominator"] == "closed_trades"
    assert metrics["expectancy_authoritative_for_paper_promotion"] is True
    assert "avg pnl/round trip" in metrics["expectancy_detail"]


def test_jsonl_pnl_fallback_is_explicitly_non_authoritative() -> None:
    from scripts.check_promotion_gates import _paper_gate_trade_metrics

    fills = [
        {"side": "buy", "size": 1.0, "pnl_usd": None},
        {"side": "sell", "size": 1.0, "pnl_usd": 10.0},
    ] * 5

    metrics = _paper_gate_trade_metrics(fills, paper_history=None)

    assert metrics["source"] == "jsonl_evidence"
    assert metrics["expectancy_ok"] is None
    assert metrics["expectancy_value"] is None
    assert metrics["expectancy_unit"] is None
    assert metrics["expectancy_denominator"] is None
    assert metrics["expectancy_authoritative_for_paper_promotion"] is False
    assert "do not use JSONL per-fill" in metrics["expectancy_hint"]


def test_qualified_paper_history_expectancy_is_net_of_fees_per_closed_trade(tmp_path) -> None:
    from services.control.paper_evidence_qualification import qualify_paper_history

    provenance = _provenance()
    evidence_fills = [
        {"timestamp": "2026-07-01T00:00:00+00:00", "order_id": "buy-1", "side": "buy", "size": 1.0, **provenance},
        {"timestamp": "2026-07-02T00:00:00+00:00", "order_id": "sell-1", "side": "sell", "size": 1.0, **provenance},
        {"timestamp": "2026-07-03T00:00:00+00:00", "order_id": "buy-2", "side": "buy", "size": 1.0, **provenance},
        {"timestamp": "2026-07-04T00:00:00+00:00", "order_id": "sell-2", "side": "sell", "size": 1.0, **provenance},
    ]
    journal = tmp_path / "trade_journal.sqlite"
    _write_journal(
        journal,
        [
            ("fill-buy-1", "2026-07-01T00:00:00+00:00", "buy-1", "2026-07-01T00:00:00+00:00", "coinbase", "BTC/USDT", "buy", 1.0, 100.0, 0.10, "USD"),
            ("fill-sell-1", "2026-07-02T00:00:00+00:00", "sell-1", "2026-07-02T00:00:00+00:00", "coinbase", "BTC/USDT", "sell", 1.0, 100.0, 0.10, "USD"),
            ("fill-buy-2", "2026-07-03T00:00:00+00:00", "buy-2", "2026-07-03T00:00:00+00:00", "coinbase", "BTC/USDT", "buy", 1.0, 200.0, 0.20, "USD"),
            ("fill-sell-2", "2026-07-04T00:00:00+00:00", "sell-2", "2026-07-04T00:00:00+00:00", "coinbase", "BTC/USDT", "sell", 1.0, 210.0, 0.21, "USD"),
        ],
    )

    out = qualify_paper_history(
        evidence_fills=evidence_fills,
        config=_policy_config(),
        journal_path=str(journal),
    )

    assert out["closed_trades"] == 2
    assert out["net_realized_pnl"] == pytest.approx(9.39)
    assert out["expectancy_per_closed_trade"] == pytest.approx(4.695)
    assert out["qualification"]["qualified_evidence_fills"] == 4


def test_paper_execution_surface_classification_matches_source_tree() -> None:
    doc = (REPO / "docs/architecture/paper_execution_surfaces.md").read_text(encoding="utf-8")

    assert (REPO / "services/execution/paper_engine.py").is_file()
    assert (REPO / "services/paper_trader/main.py").is_file()
    assert (REPO / "services/trading_runner/run_trader.py").is_file()
    retired_source_files = list((REPO / "services/paper").glob("*.py"))
    assert retired_source_files == []

    assert "`services/execution/paper_engine.py` | `core`" in doc
    assert "`services/paper_trader/` | `compatibility`" in doc
    assert "`services/trading_runner/run_trader.py` | `legacy_compatibility_runner`" in doc
    assert "`services/paper/` | `retired`" in doc
    assert "New paper execution behavior goes through `services/execution/paper_engine.py`" in doc
