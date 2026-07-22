from __future__ import annotations

import json

from services.analytics.price_action_research_pipeline import run_price_action_research_pipeline
from storage.market_store_sqlite import MarketStore


BASE_TS = 1_700_000_000_000


def _row(idx: int, close: float) -> list[float]:
    return [BASE_TS + idx * 60_000, close - 0.2, close + 0.5, close - 0.5, close, 10.0]


def _stable_rows() -> list[list[float]]:
    closes = [
        100.0,
        99.0,
        101.0,
        102.0,
        102.0,
        101.0,
        103.0,
        104.0,
        104.0,
        103.0,
        105.0,
        106.0,
    ]
    rows = [_row(idx, close) for idx, close in enumerate(closes)]
    rows[2] = [BASE_TS + 2 * 60_000, 98.5, 102.0, 98.0, 101.0, 10.0]
    rows[6] = [BASE_TS + 6 * 60_000, 100.5, 104.0, 100.0, 103.0, 10.0]
    rows[10] = [BASE_TS + 10 * 60_000, 102.5, 106.0, 102.0, 105.0, 10.0]
    return rows


def _seed_archive(db_path) -> None:
    store = MarketStore(db_path)
    for row in _stable_rows():
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


def test_price_action_research_pipeline_writes_all_artifacts(tmp_path) -> None:
    db = tmp_path / "market_raw.sqlite"
    out_dir = tmp_path / "artifacts"
    _seed_archive(db)

    report = run_price_action_research_pipeline(
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1m",
        limit=len(_stable_rows()),
        db_path=db,
        output_dir=out_dir,
        swing_lookback=2,
        range_lookback=2,
        horizon_bars=1,
        fee_bps=0.0,
        slippage_bps=0.0,
        forward_min_label_count=1,
        window_size_rows=4,
        stability_min_windows=3,
        stability_min_label_count=1,
    )

    assert report["artifact_type"] == "price_action_research_pipeline_v1"
    assert report["ok"] is True
    assert report["research_only"] is True
    assert report["not_strategy_config"] is True
    assert report["not_campaign_evidence"] is True
    assert report["not_promotion_evidence"] is True
    assert report["not_profitability_evidence"] is True
    assert report["stages"]["labels"]["ok"] is True
    assert report["stages"]["forward_returns"]["ok"] is True
    assert report["stages"]["stability"]["ok"] is True
    assert report["stages"]["stability"]["stable_label_count"] >= 1
    for key in ("labels", "forward_returns", "stability", "pipeline"):
        path = out_dir / f"price_action_{key}.json"
        if key == "forward_returns":
            path = out_dir / "price_action_forward_returns.json"
        assert path.exists(), key


def test_price_action_research_pipeline_reports_archive_failure(tmp_path) -> None:
    report = run_price_action_research_pipeline(
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1m",
        limit=10,
        db_path=tmp_path / "missing.sqlite",
        output_dir=tmp_path / "out",
    )

    assert report["ok"] is False
    assert report["stages"]["labels"]["ok"] is False
    assert report["stages"]["labels"]["reason"] == "archive_missing"
    assert report["stages"]["forward_returns"]["ok"] is False
    assert report["stages"]["stability"]["ok"] is False


def test_price_action_research_pipeline_cli_writes_summary(tmp_path, capsys) -> None:
    from scripts.research import run_price_action_research_pipeline as cli

    db = tmp_path / "market_raw.sqlite"
    out_dir = tmp_path / "artifacts"
    _seed_archive(db)

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
            str(len(_stable_rows())),
            "--output-dir",
            str(out_dir),
            "--swing-lookback",
            "2",
            "--range-lookback",
            "2",
            "--horizon-bars",
            "1",
            "--fee-bps",
            "0",
            "--slippage-bps",
            "0",
            "--forward-min-label-count",
            "1",
            "--window-size-rows",
            "4",
            "--stability-min-windows",
            "3",
            "--stability-min-label-count",
            "1",
            "--fail-if-not-ok",
        ]
    )

    printed = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert printed["ok"] is True
    assert json.loads((out_dir / "price_action_pipeline.json").read_text(encoding="utf-8"))["ok"] is True


def test_price_action_research_pipeline_cli_returns_2_when_requested_and_not_ok(tmp_path, capsys) -> None:
    from scripts.research import run_price_action_research_pipeline as cli

    rc = cli.main(
        [
            "--archive-db",
            str(tmp_path / "missing.sqlite"),
            "--output-dir",
            str(tmp_path / "artifacts"),
            "--fail-if-not-ok",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
