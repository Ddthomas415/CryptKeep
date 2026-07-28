from __future__ import annotations

import json
from pathlib import Path

from services.analytics.price_action_candidate_triage import (
    run_price_action_candidate_triage,
)
from storage.market_store_sqlite import MarketStore


BASE_TS = 1_700_000_000_000


def _row(idx: int, o: float, h: float, l: float, c: float, v: float = 10.0) -> list[float]:
    return [BASE_TS + idx * 60_000, o, h, l, c, v]


def _rows() -> list[list[float]]:
    return [
        _row(0, 100.0, 101.0, 97.0, 98.0),
        _row(1, 97.0, 102.0, 96.0, 101.0),
        _row(2, 102.0, 104.0, 101.5, 103.0),
        _row(3, 103.0, 105.0, 102.0, 104.0),
        _row(4, 104.0, 105.0, 101.0, 102.0),
        _row(5, 101.0, 106.0, 100.0, 105.0),
        _row(6, 106.0, 108.0, 105.5, 107.0),
        _row(7, 107.0, 109.0, 106.0, 108.0),
    ]


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


def test_price_action_candidate_triage_promotes_only_manual_review_candidates(tmp_path: Path) -> None:
    db_path = tmp_path / "market.sqlite"
    _write_archive(db_path, _rows())

    out = run_price_action_candidate_triage(
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1h",
        limit=8,
        db_path=str(db_path),
        window_bars=4,
        step_bars=2,
        min_windows=2,
        horizon_bars=1,
        fee_bps=0.0,
        slippage_bps=0.0,
        min_sample_size=2,
        min_avg_delta_pct=-10.0,
        min_outperform_ratio=0.50,
        max_underperform_ratio=0.50,
        label_config={"opening_range_bars": 2},
    )

    assert out["ok"] is True
    assert out["research_only"] is True
    assert out["not_strategy_config"] is True
    assert out["not_campaign_evidence"] is True
    assert out["not_promotion_evidence"] is True
    assert out["not_profitability_evidence"] is True
    assert out["review_required_before_use"] is True
    assert len(out["dataset_hash"]) == 64
    assert out["candidate_count"] >= 1
    assert out["review_candidates"]
    assert all(candidate["status"] == "candidate_for_manual_review" for candidate in out["review_candidates"])
    assert all("false_positive_proxy" in candidate for candidate in out["candidates"])


def test_price_action_candidate_triage_thresholds_can_reject_all_candidates(tmp_path: Path) -> None:
    db_path = tmp_path / "market.sqlite"
    _write_archive(db_path, _rows())

    out = run_price_action_candidate_triage(
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1h",
        limit=8,
        db_path=str(db_path),
        window_bars=4,
        step_bars=2,
        min_windows=2,
        horizon_bars=1,
        fee_bps=0.0,
        slippage_bps=0.0,
        min_sample_size=999,
        label_config={"opening_range_bars": 2},
    )

    assert out["ok"] is True
    assert out["candidate_count"] == 0
    assert out["review_candidates"] == []
    assert out["candidates"]
    assert all(candidate["status"] == "not_candidate" for candidate in out["candidates"])
    assert all("insufficient_sample_size" in candidate["reasons"] for candidate in out["candidates"])


def test_price_action_candidate_triage_refuses_missing_archive(tmp_path: Path) -> None:
    out = run_price_action_candidate_triage(
        venue="coinbase",
        symbol="BTC/USDT",
        timeframe="1h",
        limit=8,
        db_path=str(tmp_path / "missing.sqlite"),
    )

    assert out["ok"] is False
    assert out["reason"] == "archive_missing"
    assert out["candidate_count"] == 0
    assert out["candidates"] == []
    assert out["review_required_before_use"] is True


def test_price_action_candidate_triage_cli_writes_artifact_and_exit_2(tmp_path: Path) -> None:
    from scripts.research.run_price_action_candidate_triage import main

    missing_rc = main(
        [
            "--archive-db",
            str(tmp_path / "missing.sqlite"),
            "--limit",
            "8",
            "--fail-if-not-ok",
        ]
    )
    assert missing_rc == 2

    db_path = tmp_path / "market.sqlite"
    out_path = tmp_path / "candidate_triage.json"
    _write_archive(db_path, _rows())

    rc = main(
        [
            "--archive-db",
            str(db_path),
            "--limit",
            "8",
            "--window-bars",
            "4",
            "--step-bars",
            "2",
            "--min-windows",
            "2",
            "--fee-bps",
            "0",
            "--slippage-bps",
            "0",
            "--min-sample-size",
            "2",
            "--min-avg-delta-pct",
            "-10",
            "--output",
            str(out_path),
            "--fail-if-not-ok",
        ]
    )

    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["script"] == "scripts/research/run_price_action_candidate_triage.py"
    assert payload["candidates"]
