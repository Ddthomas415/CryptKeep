from __future__ import annotations

import json
from pathlib import Path

import scripts.research.run_es_daily_trend_backtest_baseline as baseline


def _candles(closes: list[float]) -> list[list[float]]:
    rows: list[list[float]] = []
    prev = float(closes[0]) if closes else 0.0
    for i, close in enumerate(closes):
        c = float(close)
        o = float(prev)
        rows.append(
            [1_700_000_000_000 + (i * baseline.MS_PER_DAY), o, max(o, c) + 0.2, min(o, c) - 0.2, c, 1.0]
        )
        prev = c
    return rows


def test_dedupe_sort_ohlcv_normalizes_timestamps() -> None:
    rows = [
        [3000, 3, 3, 3, 3, 1],
        [1000, 1, 1, 1, 1, 1],
        [1, 9, 9, 9, 9, 1],
        ["bad", 0, 0, 0, 0, 0],
    ]

    out = baseline.dedupe_sort_ohlcv(rows)

    assert [row[0] for row in out] == [1000, 1_000_000, 3_000_000]
    assert out[0][4] == 9


def test_fetch_paginated_ohlcv_advances_since_cursor() -> None:
    calls: list[int | None] = []
    fetched_symbols: list[str] = []
    start = baseline.parse_utc_ms("2020-01-01")
    assert start is not None

    def fake_fetcher(_venue, symbol, *, timeframe, limit, since_ms):
        calls.append(since_ms)
        fetched_symbols.append(symbol)
        assert timeframe == "1d"
        assert limit == 2
        if since_ms == start:
            return [[start, 1, 1, 1, 1, 1], [start + baseline.MS_PER_DAY, 2, 2, 2, 2, 1]]
        if since_ms == start + baseline.MS_PER_DAY + 1:
            return [[start + (2 * baseline.MS_PER_DAY), 3, 3, 3, 3, 1]]
        return []

    opts = baseline.BaselineOptions(
        symbol="BTC/USDT",
        data_symbol="BTC/USD",
        since="2020-01-01",
        page_limit=2,
        max_pages=4,
    )

    out = baseline.fetch_paginated_ohlcv(opts, fetcher=fake_fetcher)

    assert calls == [start, start + baseline.MS_PER_DAY + 1, start + (2 * baseline.MS_PER_DAY) + 1]
    assert fetched_symbols == ["BTC/USD", "BTC/USD", "BTC/USD"]
    assert [row[4] for row in out] == [1, 2, 3]


def test_build_baseline_report_marks_non_closing_sample_not_ready() -> None:
    rows = _candles([100.0] * 12)
    opts = baseline.BaselineOptions(
        source_label="unit:no_exit",
        sma_period=5,
        atr_period=2,
        warmup_bars=6,
        min_closed_trades=1,
    )

    out = baseline.build_baseline_report(rows, opts)

    assert out["baseline_ready"] is False
    assert "insufficient_closed_trades" in out["blocking_reasons"]
    assert "no_exit_signals" in out["blocking_reasons"]
    assert out["candidate_backtest_metrics"]["source"] == "unit:no_exit"
    assert out["candidate_backtest_metrics"]["metric_basis"] == "net_return_pct"
    assert out["source"]["symbol"] == "BTC/USDT"
    assert out["source"]["data_symbol"] == "BTC/USDT"
    assert out["dataset"]["source_label"] == "unit:no_exit"
    assert out["dataset"]["row_count"] == len(rows)
    assert len(out["dataset"]["sha256"]) == 64
    assert out["backtest_expectations"]["source"] is None
    assert out["backtest_expectations"]["win_rate"] is None
    assert out["backtest_expectations"]["avg_win_return_pct"] is None
    assert out["backtest_expectations"]["avg_loss_return_pct"] is None
    assert out["counts"]["closed_trades"] == 0


def test_main_reads_input_and_writes_report(tmp_path: Path, capsys) -> None:
    fixture = tmp_path / "ohlcv.json"
    closes = (
        [100.0] * 62
        + [100.2, 100.4, 100.6, 100.8, 101.0, 101.2, 101.4, 101.6]
        + [99.0, 98.8, 98.6, 98.4, 98.2, 98.0]
    )
    fixture.write_text(json.dumps(_candles(closes)), encoding="utf-8")
    report_path = tmp_path / "report.json"

    code = baseline.main(
        [
            "--input",
            str(fixture),
            "--sma-period",
            "5",
            "--atr-period",
            "2",
            "--warmup-bars",
            "62",
            "--min-closed-trades",
            "1",
            "--source-label",
            "unit:fixture",
            "--output",
            str(report_path),
        ]
    )

    assert code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert report["baseline_ready"] is True
    assert printed["baseline_ready"] is True
    assert report["counts"]["closed_trades"] >= 1
    assert report["candidate_backtest_metrics"]["source"] == "unit:fixture"
    assert report["backtest_expectations"]["source"] == "unit:fixture"
    assert report["backtest_expectations"]["metric_basis"] == "net_return_pct"
    assert report["backtest_expectations"]["avg_loss_return_pct"] < 0.0
    assert report["dataset"]["source_label"] == "unit:fixture"
    assert report["dataset"]["row_count"] == len(closes)
    assert report["dataset"]["sha256"] == printed["dataset"]["sha256"]


def test_closed_trade_return_pcts_uses_entry_notional_and_net_pnl() -> None:
    out = baseline.closed_trade_return_pcts(
        [
            {"action": "buy", "notional": 100.0},
            {"action": "sell", "realized_pnl": 5.0},
            {"action": "buy", "notional": 200.0},
            {"action": "sell", "realized_pnl": -10.0},
        ]
    )

    assert out == [5.0, -5.0]
