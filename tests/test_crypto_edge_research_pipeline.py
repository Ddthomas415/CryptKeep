from __future__ import annotations

import json

from services.analytics.crypto_edge_research_pipeline import run_crypto_edge_research_pipeline
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite
from storage.market_store_sqlite import MarketStore


BASE_TS = 1_700_000_000_000
STEP_MS = 300_000


def _seed_edge(db_path) -> None:
    store = CryptoEdgeStoreSQLite(path=str(db_path))
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "okx", "funding_rate": -0.0002, "interval_hours": 8.0}],
        source="live_public",
        capture_ts="2023-11-14T22:13:20+00:00",
        snapshot_id="funding-buy",
    )
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "okx", "funding_rate": 0.0008, "interval_hours": 8.0}],
        source="live_public",
        capture_ts="2023-11-14T22:23:20+00:00",
        snapshot_id="funding-sell",
    )


def _seed_archive(db_path) -> None:
    store = MarketStore(db_path)
    closes = [100.0, 110.0, 100.0, 90.0, 91.0]
    for idx, close in enumerate(closes):
        store.upsert_ohlcv(
            ts_ms=BASE_TS + (idx * STEP_MS),
            exchange="okx",
            symbol="BTC/USDT",
            timeframe="5m",
            o=close,
            h=close + 1.0,
            l=close - 1.0,
            cl=close,
            v=10.0,
        )


def test_crypto_edge_research_pipeline_writes_all_artifacts(tmp_path) -> None:
    edge_db = tmp_path / "crypto_edges.sqlite"
    archive_db = tmp_path / "market_raw.sqlite"
    out_dir = tmp_path / "artifacts"
    _seed_edge(edge_db)
    _seed_archive(archive_db)

    out = run_crypto_edge_research_pipeline(
        edge_db_path=edge_db,
        archive_db_path=archive_db,
        output_dir=out_dir,
        funding_limit=5,
        ohlcv_limit=5,
        min_rows=2,
        min_joined_rows=2,
        fee_bps=0.0,
        slippage_bps=0.0,
        long_thresholds_pct=[0.05],
        short_thresholds_pct=[-0.01],
    )

    assert out["artifact_type"] == "crypto_edge_research_pipeline_v1"
    assert out["ok"] is True
    assert out["research_only"] is True
    assert out["not_strategy_config"] is True
    assert out["not_campaign_evidence"] is True
    assert out["not_promotion_evidence"] is True
    assert out["not_profitability_evidence"] is True
    assert out["stages"]["replay"]["action_counts"] == {"buy": 1, "sell": 1}
    assert out["stages"]["price_join"]["joined_rows"] == 2
    assert out["stages"]["threshold_sensitivity"]["max_actionable_rows"] == 2
    for name in (
        "funding_context_replay.json",
        "funding_context_price_join.json",
        "funding_threshold_sensitivity.json",
        "crypto_edge_research_pipeline.json",
    ):
        assert (out_dir / name).exists(), name


def test_crypto_edge_research_pipeline_reports_archive_failure(tmp_path) -> None:
    edge_db = tmp_path / "crypto_edges.sqlite"
    _seed_edge(edge_db)

    out = run_crypto_edge_research_pipeline(
        edge_db_path=edge_db,
        archive_db_path=tmp_path / "missing.sqlite",
        output_dir=tmp_path / "artifacts",
        funding_limit=5,
        min_rows=2,
        min_joined_rows=2,
    )

    assert out["ok"] is False
    assert out["stages"]["replay"]["ok"] is True
    assert out["stages"]["price_join"]["ok"] is False
    assert out["stages"]["price_join"]["reason"] == "archive_missing"
    assert out["stages"]["threshold_sensitivity"]["ok"] is False


def test_crypto_edge_research_pipeline_cli_writes_summary(tmp_path, capsys) -> None:
    from scripts.research import run_crypto_edge_research_pipeline as cli

    edge_db = tmp_path / "crypto_edges.sqlite"
    archive_db = tmp_path / "market_raw.sqlite"
    out_dir = tmp_path / "artifacts"
    _seed_edge(edge_db)
    _seed_archive(archive_db)

    rc = cli.main(
        [
            "--edge-db",
            str(edge_db),
            "--archive-db",
            str(archive_db),
            "--output-dir",
            str(out_dir),
            "--funding-limit",
            "5",
            "--ohlcv-limit",
            "5",
            "--min-rows",
            "2",
            "--min-joined-rows",
            "2",
            "--fee-bps",
            "0",
            "--slippage-bps",
            "0",
            "--long-thresholds-pct",
            "0.05",
            "--short-thresholds-pct",
            "-0.01",
            "--fail-if-not-ok",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["ok"] is True
    assert json.loads((out_dir / "crypto_edge_research_pipeline.json").read_text(encoding="utf-8"))["ok"] is True


def test_crypto_edge_research_pipeline_cli_returns_2_when_requested_and_not_ok(tmp_path, capsys) -> None:
    from scripts.research import run_crypto_edge_research_pipeline as cli

    rc = cli.main(
        [
            "--edge-db",
            str(tmp_path / "missing-edge.sqlite"),
            "--archive-db",
            str(tmp_path / "missing-archive.sqlite"),
            "--output-dir",
            str(tmp_path / "artifacts"),
            "--fail-if-not-ok",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
