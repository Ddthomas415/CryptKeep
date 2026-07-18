from __future__ import annotations

import json

from services.analytics.funding_context_replay import run_funding_context_replay
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite


def _seed_funding(db_path, *, source: str = "live_public") -> None:
    store = CryptoEdgeStoreSQLite(path=str(db_path))
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "okx", "funding_rate": 0.0008, "interval_hours": 8.0}],
        source=source,
        capture_ts="2026-07-18T02:00:00+00:00",
        snapshot_id="funding-sell",
    )
    store.append_funding_rows(
        [{"symbol": "BTC/USDT:USDT", "venue": "okx", "funding_rate": -0.0002, "interval_hours": 8.0}],
        source=source,
        capture_ts="2026-07-18T01:00:00+00:00",
        snapshot_id="funding-buy",
    )
    store.append_funding_rows(
        [{"symbol": "ETH/USDT:USDT", "venue": "okx", "funding_rate": 0.001, "interval_hours": 8.0}],
        source=source,
        capture_ts="2026-07-18T03:00:00+00:00",
        snapshot_id="funding-other-symbol",
    )


def test_funding_context_replay_counts_actions_and_hashes_dataset(tmp_path):
    db_path = tmp_path / "crypto_edges.sqlite"
    _seed_funding(db_path)

    out = run_funding_context_replay(db_path=db_path, min_rows=2)
    again = run_funding_context_replay(db_path=db_path, min_rows=2)

    assert out["ok"] is True
    assert out["research_only"] is True
    assert out["artifact_type"] == "funding_context_signal_replay_v1"
    assert out["row_count"] == 2
    assert out["action_counts"] == {"buy": 1, "sell": 1}
    assert out["reason_counts"] == {"funding_extreme_longs": 1, "funding_extreme_shorts": 1}
    assert out["dataset_hash"] == again["dataset_hash"]
    assert out["signals"][0]["snapshot_id"] == "funding-buy"
    assert out["signals"][1]["snapshot_id"] == "funding-sell"
    assert "no_pnl_or_expectancy" in out["limitations"]
    assert "not_promotion_evidence" in out["limitations"]


def test_funding_context_replay_reports_insufficient_rows(tmp_path):
    db_path = tmp_path / "crypto_edges.sqlite"
    _seed_funding(db_path)

    out = run_funding_context_replay(db_path=db_path, min_rows=3)

    assert out["ok"] is False
    assert out["reason"] == "insufficient_funding_rows"
    assert out["row_count"] == 2


def test_funding_context_replay_rejects_non_funding_strategy(tmp_path):
    db_path = tmp_path / "crypto_edges.sqlite"
    _seed_funding(db_path)

    out = run_funding_context_replay(cfg={"strategy": {"name": "ema_cross"}}, db_path=db_path)

    assert out["ok"] is False
    assert out["reason"] == "unsupported_strategy"
    assert out["strategy"] == "ema_cross"
    assert out["signals"] == []


def test_funding_context_replay_cli_writes_artifact(tmp_path, capsys):
    from scripts.research import run_funding_context_replay as cli

    db_path = tmp_path / "crypto_edges.sqlite"
    out_path = tmp_path / "replay.json"
    _seed_funding(db_path)

    rc = cli.main(["--edge-db", str(db_path), "--min-rows", "2", "--output", str(out_path), "--fail-if-not-ok"])

    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert payload["dataset_hash"] == printed["dataset_hash"]
    assert payload["action_counts"] == {"buy": 1, "sell": 1}


def test_funding_context_replay_cli_returns_2_when_requested_and_not_ok(tmp_path):
    from scripts.research import run_funding_context_replay as cli

    db_path = tmp_path / "crypto_edges.sqlite"

    rc = cli.main(["--edge-db", str(db_path), "--min-rows", "1", "--fail-if-not-ok"])

    assert rc == 2
