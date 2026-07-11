from __future__ import annotations

import json

from scripts.research import run_archive_parameter_sweep as runner
from services.backtest.parameter_sweep import expand_parameter_grid, run_archive_parameter_sweep
from storage.market_store_sqlite import MarketStore


def _seed_archive(db_path, *, count: int = 64) -> None:
    store = MarketStore(db_path)
    base_ms = 1_700_000_000_000
    for idx in range(count):
        ts_ms = base_ms + (idx * 60_000)
        drift = 0.08 * idx
        cycle = ((idx % 12) - 6) * 0.35
        close = 100.0 + drift + cycle
        store.upsert_ohlcv(
            ts_ms=ts_ms,
            exchange="coinbase",
            symbol="BTC/USD",
            timeframe="1h",
            o=close - 0.2,
            h=close + 0.6,
            l=close - 0.6,
            cl=close,
            v=10.0 + idx,
        )


def test_expand_parameter_grid_sets_dot_paths_deterministically() -> None:
    variants = expand_parameter_grid(
        base_cfg={"strategy": {"name": "ema_cross", "ema_fast": 3, "ema_slow": 8}},
        grid={"strategy.ema_fast": [3, 5], "strategy.ema_slow": [8, 13]},
    )

    assert [row["variant_id"] for row in variants] == ["variant_001", "variant_002", "variant_003", "variant_004"]
    assert variants[0]["parameters"] == {"strategy.ema_fast": 3, "strategy.ema_slow": 8}
    assert variants[-1]["config"]["strategy"]["ema_fast"] == 5
    assert variants[-1]["config"]["strategy"]["ema_slow"] == 13


def test_run_archive_parameter_sweep_returns_ranked_research_artifact(tmp_path) -> None:
    db = tmp_path / "market_raw.sqlite"
    _seed_archive(db)

    out = run_archive_parameter_sweep(
        base_cfg={"strategy": {"name": "ema_cross", "ema_fast": 3, "ema_slow": 8}},
        grid={"strategy.ema_fast": [3, 5], "strategy.ema_slow": [8, 13]},
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1h",
        limit=64,
        db_path=str(db),
        warmup_bars=5,
        min_train_bars=20,
        test_bars=10,
        step_bars=10,
        initial_cash=1_000.0,
    )

    assert out["ok"] is True
    assert out["research_only"] is True
    assert out["archive_backed"] is True
    assert out["artifact_type"] == "archive_backed_parameter_sweep_v1"
    assert out["variant_count"] == 4
    assert out["successful_variant_count"] == 4
    assert out["ranking_policy"]["promotion_decision"] is False
    assert [row["rank"] for row in out["ranked_variants"]] == [1, 2, 3, 4]
    assert out["top_variant"]["rank"] == 1
    assert len(out["dataset_summary"]["dataset_hashes"]) == 1
    assert {row["dataset_hash"] for row in out["ranked_variants"]} == set(out["dataset_summary"]["dataset_hashes"])
    assert {"research_score", "avg_test_return_pct", "avg_test_max_drawdown_pct"} <= set(out["top_variant"]["score"])


def test_run_archive_parameter_sweep_refuses_oversized_grid() -> None:
    out = run_archive_parameter_sweep(
        base_cfg={"strategy": {"name": "ema_cross", "ema_fast": 3, "ema_slow": 8}},
        grid={"strategy.ema_fast": [1, 2, 3], "strategy.ema_slow": [4, 5, 6]},
        venue="coinbase",
        symbol="BTC/USD",
        max_variants=4,
    )

    assert out["ok"] is False
    assert out["reason"] == "invalid_grid"
    assert "above max_variants=4" in out["detail"]
    assert out["ranked_variants"] == []


def test_runner_writes_ranked_sweep_artifact(tmp_path, capsys) -> None:
    db = tmp_path / "market_raw.sqlite"
    cfg = tmp_path / "strategy.json"
    grid = tmp_path / "grid.json"
    out_path = tmp_path / "sweep.json"
    _seed_archive(db)
    cfg.write_text(json.dumps({"strategy": {"name": "ema_cross", "ema_fast": 3, "ema_slow": 8}}), encoding="utf-8")
    grid.write_text(json.dumps({"strategy.ema_fast": [3, 5], "strategy.ema_slow": [8, 13]}), encoding="utf-8")

    rc = runner.main(
        [
            "--config",
            str(cfg),
            "--grid",
            str(grid),
            "--archive-db",
            str(db),
            "--venue",
            "coinbase",
            "--symbol",
            "BTC/USD",
            "--timeframe",
            "1h",
            "--limit",
            "64",
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
    assert payload["config_path"] == str(cfg)
    assert payload["grid_path"] == str(grid)
    assert payload["variant_count"] == 4
    assert payload["top_variant"]["rank"] == 1
