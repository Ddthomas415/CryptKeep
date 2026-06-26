from __future__ import annotations

import json
import sqlite3


def _write_jsonl(path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _create_journal(path, rows) -> None:
    con = sqlite3.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE journal_fills (
              fill_id TEXT PRIMARY KEY,
              journal_ts TEXT NOT NULL,
              strategy_id TEXT,
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
        con.executemany("INSERT INTO journal_fills VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        con.commit()
    finally:
        con.close()


def test_build_paper_gate_qualification_report_classifies_fill_rows(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    from services.control.paper_gate_qualification_report import build_paper_gate_qualification_report
    from services.control.promotion_thresholds import ES_DAILY_TREND_STRATEGY_ID
    from services.os.app_paths import data_dir

    ev_dir = data_dir() / "evidence" / ES_DAILY_TREND_STRATEGY_ID
    provenance = {
        "market_data_source": "public_ohlcv",
        "ohlcv_sample_mode": False,
        "ohlcv_timeframe": "1d",
        "ohlcv_venue": "coinbase",
        "ohlcv_symbol": "BTC/USDT",
    }
    _write_jsonl(
        ev_dir / "fill_progress.jsonl",
        [
            {
                "timestamp": "2026-06-01T00:00:00+00:00",
                "side": "buy",
                "size": 1.0,
                "order_id": "old-buy",
            },
            {
                "timestamp": "2026-06-01T01:00:00+00:00",
                "side": "sell",
                "size": 1.0,
                "order_id": "old-sell",
            },
            {
                "timestamp": "2026-06-02T01:00:00+00:00",
                "side": "sell",
                "size": 1.0,
                "order_id": "lonely-sell",
                **provenance,
            },
            {
                "timestamp": "2026-06-03T00:00:00+00:00",
                "side": "buy",
                "size": 1.0,
                "order_id": "qualified-buy",
                **provenance,
            },
            {
                "timestamp": "2026-06-03T01:00:00+00:00",
                "side": "sell",
                "size": 1.0,
                "order_id": "qualified-sell",
                **provenance,
            },
        ],
    )
    _create_journal(
        data_dir() / "trade_journal.sqlite",
        [
            (
                "fill-old-buy",
                "2026-06-01T00:00:00+00:00",
                "sma_200_trend",
                "old-buy",
                "2026-06-01T00:00:00+00:00",
                "coinbase",
                "BTC/USDT",
                "buy",
                1.0,
                100.0,
                0.0,
                "USD",
            ),
            (
                "fill-old-sell",
                "2026-06-01T01:00:00+00:00",
                "sma_200_trend",
                "old-sell",
                "2026-06-01T01:00:00+00:00",
                "coinbase",
                "BTC/USDT",
                "sell",
                1.0,
                101.0,
                0.0,
                "USD",
            ),
            (
                "fill-lonely-sell",
                "2026-06-02T01:00:00+00:00",
                "sma_200_trend",
                "lonely-sell",
                "2026-06-02T01:00:00+00:00",
                "coinbase",
                "BTC/USDT",
                "sell",
                1.0,
                102.0,
                0.0,
                "USD",
            ),
            (
                "fill-qualified-buy",
                "2026-06-03T00:00:00+00:00",
                "sma_200_trend",
                "qualified-buy",
                "2026-06-03T00:00:00+00:00",
                "coinbase",
                "BTC/USDT",
                "buy",
                1.0,
                103.0,
                0.0,
                "USD",
            ),
            (
                "fill-qualified-sell",
                "2026-06-03T01:00:00+00:00",
                "sma_200_trend",
                "qualified-sell",
                "2026-06-03T01:00:00+00:00",
                "coinbase",
                "BTC/USDT",
                "sell",
                1.0,
                104.0,
                0.0,
                "USD",
            ),
        ],
    )

    report = build_paper_gate_qualification_report()

    assert report["ok"] is True
    assert report["summary"]["qualified_round_trips"] == 1
    assert report["summary"]["counted_evidence_fills"] == 2
    assert report["summary"]["incomplete_evidence_fills"] == 1
    assert report["summary"]["rejected_evidence_fills"] == 2
    rows_by_order = {row["order_id"]: row for row in report["fills"]}
    assert rows_by_order["old-buy"]["status"] == "rejected"
    assert "missing_market_data_source" in rows_by_order["old-buy"]["rejection_reasons"]
    assert rows_by_order["lonely-sell"]["status"] == "incomplete"
    assert rows_by_order["qualified-buy"]["status"] == "counted"
    assert rows_by_order["qualified-sell"]["status"] == "counted"


def test_build_paper_gate_qualification_report_filters_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    from services.control.paper_gate_qualification_report import build_paper_gate_qualification_report
    from services.control.promotion_thresholds import ES_DAILY_TREND_STRATEGY_ID
    from services.os.app_paths import data_dir

    ev_dir = data_dir() / "evidence" / ES_DAILY_TREND_STRATEGY_ID
    _write_jsonl(
        ev_dir / "fill_progress.jsonl",
        [
            {
                "timestamp": "2026-06-01T00:00:00+00:00",
                "side": "buy",
                "size": 1.0,
                "order_id": "old-buy",
            }
        ],
    )
    _create_journal(data_dir() / "trade_journal.sqlite", [])

    report = build_paper_gate_qualification_report(row_filter="rejected")

    assert report["returned_fills"] == 1
    assert report["fills"][0]["status"] == "rejected"
