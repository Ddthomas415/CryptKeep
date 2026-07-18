from __future__ import annotations

import json

from services.analytics.funding_context_price_join import run_funding_context_price_join
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


def test_funding_context_price_join_reports_forward_returns_and_hashes(tmp_path):
    edge_db = tmp_path / "crypto_edges.sqlite"
    archive_db = tmp_path / "market_raw.sqlite"
    _seed_edge(edge_db)
    _seed_archive(archive_db)

    out = run_funding_context_price_join(
        edge_db_path=edge_db,
        archive_db_path=archive_db,
        ohlcv_limit=5,
        min_joined_rows=2,
        fee_bps=0.0,
        slippage_bps=0.0,
    )
    again = run_funding_context_price_join(
        edge_db_path=edge_db,
        archive_db_path=archive_db,
        ohlcv_limit=5,
        min_joined_rows=2,
        fee_bps=0.0,
        slippage_bps=0.0,
    )

    assert out["ok"] is True
    assert out["artifact_type"] == "funding_context_price_join_v1"
    assert out["research_only"] is True
    assert out["joined_rows"] == 2
    assert out["action_counts"] == {"buy": 1, "sell": 1}
    assert out["reason_counts"] == {"funding_extreme_longs": 1, "funding_extreme_shorts": 1}
    assert out["dataset_hash"] == again["dataset_hash"]
    assert out["summary"]["actionable_rows"] == 2
    assert out["summary"]["positive_actionable_rows"] == 2
    assert out["rows"][0]["action"] == "buy"
    assert out["rows"][0]["net_forward_return_pct"] == 10.0
    assert out["rows"][1]["action"] == "sell"
    assert out["rows"][1]["net_forward_return_pct"] == 10.0
    assert "not_promotion_evidence" in out["limitations"]
    assert "no_portfolio_pnl" in out["limitations"]


def test_funding_context_price_join_applies_costs(tmp_path):
    edge_db = tmp_path / "crypto_edges.sqlite"
    archive_db = tmp_path / "market_raw.sqlite"
    _seed_edge(edge_db)
    _seed_archive(archive_db)

    out = run_funding_context_price_join(
        edge_db_path=edge_db,
        archive_db_path=archive_db,
        ohlcv_limit=5,
        min_joined_rows=2,
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    assert out["ok"] is True
    assert out["rows"][0]["net_forward_return_pct"] < 10.0
    assert out["rows"][1]["net_forward_return_pct"] < 10.0


def test_funding_context_price_join_requires_complete_archive(tmp_path):
    edge_db = tmp_path / "crypto_edges.sqlite"
    _seed_edge(edge_db)

    out = run_funding_context_price_join(edge_db_path=edge_db, archive_db_path=tmp_path / "missing.sqlite")

    assert out["ok"] is False
    assert out["reason"] == "archive_missing"
    assert out["joined_rows"] == 0
    assert "archive_required" in out["limitations"]


def test_funding_context_price_join_rejects_non_funding_strategy(tmp_path):
    edge_db = tmp_path / "crypto_edges.sqlite"
    archive_db = tmp_path / "market_raw.sqlite"
    _seed_edge(edge_db)
    _seed_archive(archive_db)

    out = run_funding_context_price_join(
        cfg={"strategy": {"name": "ema_cross"}},
        edge_db_path=edge_db,
        archive_db_path=archive_db,
    )

    assert out["ok"] is False
    assert out["reason"] == "unsupported_strategy"
    assert out["strategy"] == "ema_cross"


def test_funding_context_price_join_cli_writes_artifact(tmp_path, capsys):
    from scripts.research import run_funding_context_price_join as cli

    edge_db = tmp_path / "crypto_edges.sqlite"
    archive_db = tmp_path / "market_raw.sqlite"
    out_path = tmp_path / "joined.json"
    _seed_edge(edge_db)
    _seed_archive(archive_db)

    rc = cli.main(
        [
            "--edge-db",
            str(edge_db),
            "--archive-db",
            str(archive_db),
            "--ohlcv-limit",
            "5",
            "--min-joined-rows",
            "2",
            "--fee-bps",
            "0",
            "--slippage-bps",
            "0",
            "--output",
            str(out_path),
            "--fail-if-not-ok",
        ]
    )

    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert payload["dataset_hash"] == printed["dataset_hash"]
    assert payload["joined_rows"] == 2


def test_funding_context_price_join_cli_keeps_stdout_json_only(monkeypatch, tmp_path, capsys):
    from scripts.research import run_funding_context_price_join as cli

    def _noisy_report(**_kwargs):
        print("diagnostic emitted by a dependency")
        return {"ok": True, "dataset_hash": "abc123", "joined_rows": 0}

    monkeypatch.setattr(cli, "run_funding_context_price_join", _noisy_report)

    rc = cli.main(["--output", str(tmp_path / "joined.json")])

    captured = capsys.readouterr()
    assert rc == 0
    assert json.loads(captured.out)["dataset_hash"] == "abc123"
    assert "diagnostic emitted by a dependency" in captured.err


def test_funding_context_price_join_cli_returns_2_when_requested_and_not_ok(tmp_path):
    from scripts.research import run_funding_context_price_join as cli

    rc = cli.main(["--edge-db", str(tmp_path / "edge.sqlite"), "--archive-db", str(tmp_path / "missing.sqlite"), "--fail-if-not-ok"])

    assert rc == 2
