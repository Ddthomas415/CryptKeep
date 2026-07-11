from __future__ import annotations

import json

from scripts.research import run_archive_walk_forward as runner
from storage.market_store_sqlite import MarketStore


def _seed_archive(db_path, *, count: int = 50) -> None:
    store = MarketStore(db_path)
    base_ms = 1_700_000_000_000
    for idx in range(count):
        ts_ms = base_ms + (idx * 60_000)
        close = 100.0 + ((idx % 14) - 7) * 0.5
        store.upsert_ohlcv(
            ts_ms=ts_ms,
            exchange="coinbase",
            symbol="BTC/USD",
            timeframe="1h",
            o=close - 0.1,
            h=close + 0.5,
            l=close - 0.5,
            cl=close,
            v=10.0 + idx,
        )


def test_runner_writes_archive_backed_walk_forward_artifact(tmp_path, capsys) -> None:
    db = tmp_path / "market_raw.sqlite"
    cfg = tmp_path / "strategy.json"
    out_path = tmp_path / "walk_forward.json"
    _seed_archive(db)
    cfg.write_text(json.dumps({"strategy": {"name": "ema_cross", "ema_fast": 3, "ema_slow": 5}}), encoding="utf-8")

    rc = runner.main(
        [
            "--config",
            str(cfg),
            "--archive-db",
            str(db),
            "--venue",
            "coinbase",
            "--symbol",
            "BTC/USD",
            "--timeframe",
            "1h",
            "--limit",
            "50",
            "--warmup-bars",
            "5",
            "--min-train-bars",
            "20",
            "--test-bars",
            "10",
            "--step-bars",
            "10",
            "--output",
            str(out_path),
        ]
    )

    printed = json.loads(capsys.readouterr().out)
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload == printed
    assert payload["ok"] is True
    assert payload["archive_backed"] is True
    assert payload["artifact_type"] == "archive_backed_walk_forward_v1"
    assert payload["config_path"] == str(cfg)
    assert payload["dataset"]["source"] == "market_ohlcv_archive"
    assert payload["dataset_hash"] == payload["dataset"]["dataset_hash"]
    assert len(payload["dataset_hash"]) == 64
    assert payload["window_count"] >= 1


def test_runner_fail_if_not_ok_returns_2_for_missing_archive(tmp_path, capsys) -> None:
    cfg = tmp_path / "strategy.json"
    cfg.write_text(json.dumps({"strategy": {"name": "ema_cross", "ema_fast": 3, "ema_slow": 5}}), encoding="utf-8")

    rc = runner.main(
        [
            "--config",
            str(cfg),
            "--archive-db",
            str(tmp_path / "missing.sqlite"),
            "--venue",
            "coinbase",
            "--symbol",
            "BTC/USD",
            "--limit",
            "50",
            "--fail-if-not-ok",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert payload["reason"] == "archive_missing"
