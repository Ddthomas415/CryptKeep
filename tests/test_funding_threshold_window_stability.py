from __future__ import annotations

import json

from services.analytics.funding_threshold_window_stability import (
    run_funding_threshold_window_stability,
)


def _price_join_artifact(path, *, include_costs: bool = True) -> None:
    payload = {
        "ok": True,
        "artifact_type": "funding_context_price_join_v1",
        "dataset_hash": "price-join-hash",
        "rows": [
            {"capture_ts": "2026-07-20T00:00:00Z", "funding_rate_pct": -0.02, "entry_close": 100.0, "exit_close": 110.0},
            {"capture_ts": "2026-07-20T00:05:00Z", "funding_rate_pct": 0.06, "entry_close": 100.0, "exit_close": 90.0},
            {"capture_ts": "2026-07-20T00:10:00Z", "funding_rate_pct": 0.0, "entry_close": 100.0, "exit_close": 100.0},
            {"capture_ts": "2026-07-20T00:15:00Z", "funding_rate_pct": -0.02, "entry_close": 100.0, "exit_close": 90.0},
            {"capture_ts": "2026-07-20T00:20:00Z", "funding_rate_pct": 0.06, "entry_close": 100.0, "exit_close": 110.0},
            {"capture_ts": "2026-07-20T00:25:00Z", "funding_rate_pct": 0.0, "entry_close": 100.0, "exit_close": 100.0},
        ],
    }
    if include_costs:
        payload["fee_bps"] = 0.0
        payload["slippage_bps"] = 0.0
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_funding_threshold_window_stability_summarizes_threshold_pairs(tmp_path):
    src = tmp_path / "price_join.json"
    _price_join_artifact(src)

    out = run_funding_threshold_window_stability(
        input_path=src,
        long_thresholds_pct=[0.05],
        short_thresholds_pct=[-0.01],
        window_rows=3,
        min_windows=2,
    )

    assert out["ok"] is True
    assert out["artifact_type"] == "funding_threshold_window_stability_v1"
    assert out["research_only"] is True
    assert out["source_dataset_hash"] == "price-join-hash"
    assert out["window_count"] == 2
    assert out["fee_bps"] == 0.0
    row = out["threshold_stability"][0]
    assert row["long_threshold_pct"] == 0.05
    assert row["short_threshold_pct"] == -0.01
    assert row["windows_with_actionable_rows"] == 2
    assert row["positive_actionable_window_ratio"] == 0.5
    assert row["avg_net_forward_return_pct_across_actionable_windows"] == 0.0
    assert row["worst_window_avg_net_forward_return_pct"] == -10.0
    assert row["window_rows"][0]["avg_net_forward_return_pct"] == 10.0
    assert row["window_rows"][1]["avg_net_forward_return_pct"] == -10.0
    assert "not_promotion_evidence" in out["limitations"]


def test_funding_threshold_window_stability_requires_enough_complete_windows(tmp_path):
    src = tmp_path / "price_join.json"
    _price_join_artifact(src)

    out = run_funding_threshold_window_stability(
        input_path=src,
        long_thresholds_pct=[0.05],
        short_thresholds_pct=[-0.01],
        window_rows=4,
        min_windows=2,
    )

    assert out["ok"] is False
    assert out["reason"] == "insufficient_windows"
    assert out["window_count"] == 1


def test_funding_threshold_window_stability_requires_source_cost_assumptions(tmp_path):
    src = tmp_path / "price_join.json"
    _price_join_artifact(src, include_costs=False)

    out = run_funding_threshold_window_stability(input_path=src, window_rows=3)

    assert out["ok"] is False
    assert out["reason"] == "source_cost_assumptions_missing"


def test_funding_threshold_window_stability_rejects_wrong_input_artifact(tmp_path):
    src = tmp_path / "wrong.json"
    src.write_text(json.dumps({"artifact_type": "other", "rows": []}), encoding="utf-8")

    out = run_funding_threshold_window_stability(input_path=src)

    assert out["ok"] is False
    assert out["reason"] == "unsupported_input_artifact_type"


def test_funding_threshold_window_stability_cli_writes_artifact(tmp_path, capsys):
    from scripts.research import run_funding_threshold_window_stability as cli

    src = tmp_path / "price_join.json"
    out_path = tmp_path / "stability.json"
    _price_join_artifact(src)

    rc = cli.main(
        [
            "--input",
            str(src),
            "--output",
            str(out_path),
            "--long-thresholds-pct",
            "0.05",
            "--short-thresholds-pct",
            "-0.01",
            "--window-rows",
            "3",
            "--fail-if-not-ok",
        ]
    )

    assert rc == 0
    written = json.loads(out_path.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert written["dataset_hash"] == printed["dataset_hash"]
    assert written["script"] == "scripts/research/run_funding_threshold_window_stability.py"
    assert written["window_count"] == 2


def test_funding_threshold_window_stability_cli_returns_2_when_requested_and_not_ok(tmp_path):
    from scripts.research import run_funding_threshold_window_stability as cli

    rc = cli.main(["--input", str(tmp_path / "missing.json"), "--fail-if-not-ok"])

    assert rc == 2
