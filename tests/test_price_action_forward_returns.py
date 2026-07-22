from __future__ import annotations

import json
from pathlib import Path

from services.analytics.price_action_forward_returns import run_price_action_forward_returns
from storage.market_store_sqlite import MarketStore


BASE_TS = 1_700_000_000_000


def _row(idx: int, o: float, h: float, l: float, c: float, v: float = 10.0) -> list[float]:
    return [BASE_TS + idx * 60_000, o, h, l, c, v]


def _write_archive(db_path: Path, rows: list[list[float]]) -> None:
    store = MarketStore(db_path)
    for row in rows:
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


def test_price_action_forward_returns_groups_label_buckets_after_costs(tmp_path: Path) -> None:
    db_path = tmp_path / "market.sqlite"
    _write_archive(
        db_path,
        [
            _row(0, 100.0, 101.0, 97.0, 98.0),
            _row(1, 97.0, 102.0, 96.0, 101.0),
            _row(2, 102.0, 104.0, 101.5, 103.0),
            _row(3, 103.0, 105.0, 102.0, 104.0),
        ],
    )

    out = run_price_action_forward_returns(
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1h",
        limit=4,
        db_path=str(db_path),
        horizon_bars=1,
        fee_bps=0.0,
        slippage_bps=0.0,
        label_config={"opening_range_bars": 2},
    )

    assert out["ok"] is True
    assert out["research_only"] is True
    assert out["not_strategy_config"] is True
    assert out["not_campaign_evidence"] is True
    assert out["not_promotion_evidence"] is True
    assert out["not_profitability_evidence"] is True
    assert out["summary"]["label_bucket_count"] >= 2
    engulfing = out["label_summaries"]["engulfing_candle:bullish"]
    assert engulfing["long"]["sample_size"] == 1
    assert engulfing["long"]["avg_net_forward_return_pct"] > 0.0
    assert engulfing["short"]["avg_net_forward_return_pct"] < 0.0
    fvg = out["label_summaries"]["fair_value_gap:bullish"]
    assert fvg["long"]["sample_size"] == 1
    assert fvg["long"]["avg_net_forward_return_pct"] > 0.0


def test_price_action_forward_returns_include_cost_assumptions_in_hash(tmp_path: Path) -> None:
    db_path = tmp_path / "market.sqlite"
    _write_archive(
        db_path,
        [
            _row(0, 100.0, 101.0, 97.0, 98.0),
            _row(1, 97.0, 102.0, 96.0, 101.0),
            _row(2, 102.0, 104.0, 101.5, 103.0),
        ],
    )

    no_cost = run_price_action_forward_returns(
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1h",
        limit=3,
        db_path=str(db_path),
        fee_bps=0.0,
        slippage_bps=0.0,
    )
    with_cost = run_price_action_forward_returns(
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1h",
        limit=3,
        db_path=str(db_path),
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    assert no_cost["ok"] is True
    assert with_cost["ok"] is True
    assert no_cost["dataset_hash"] != with_cost["dataset_hash"]
    assert with_cost["fee_bps"] == 10.0
    assert with_cost["slippage_bps"] == 5.0


def test_price_action_forward_returns_refuse_missing_archive_without_live_fallback(
    tmp_path: Path,
) -> None:
    out = run_price_action_forward_returns(
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1h",
        limit=3,
        db_path=str(tmp_path / "missing.sqlite"),
        horizon_bars=1,
    )

    assert out["ok"] is False
    assert out["reason"] == "archive_missing"
    assert out["rows"] == []
    assert out["label_summaries"] == {}
    assert out["research_only"] is True


def test_price_action_forward_returns_cli_writes_artifact_and_returns_exit_2(
    tmp_path: Path,
) -> None:
    from scripts.research.run_price_action_forward_returns import main

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
    out_path = tmp_path / "forward_returns.json"
    _write_archive(
        db_path,
        [
            _row(0, 100.0, 101.0, 97.0, 98.0),
            _row(1, 97.0, 102.0, 96.0, 101.0),
            _row(2, 102.0, 104.0, 101.5, 103.0),
        ],
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
    assert payload["script"] == "scripts/research/run_price_action_forward_returns.py"
    assert payload["rows"]
