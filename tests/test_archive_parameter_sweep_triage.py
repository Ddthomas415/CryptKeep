from __future__ import annotations

import json

from services.analytics.archive_parameter_sweep_triage import (
    build_archive_parameter_sweep_triage,
    run_archive_parameter_sweep_triage,
)


def _sweep_artifact(path) -> None:
    payload = {
        "ok": True,
        "artifact_type": "archive_backed_parameter_sweep_v1",
        "venue": "coinbase",
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "variant_count": 3,
        "successful_variant_count": 3,
        "dataset_summary": {"dataset_hashes": ["archive-hash"]},
        "ranked_variants": [
            {
                "variant_id": "variant_001",
                "rank": 1,
                "ok": True,
                "strategy": "ema_cross",
                "parameters": {"strategy.ema_fast": 3},
                "config_hash": "cfg-a",
                "dataset_hash": "archive-hash",
                "window_count": 3,
                "score": {
                    "research_score": 0.8,
                    "avg_test_return_pct": 1.2,
                    "avg_test_max_drawdown_pct": 0.4,
                    "non_negative_test_window_ratio": 1.0,
                    "total_test_closed_trades": 12,
                    "window_count": 3,
                },
            },
            {
                "variant_id": "variant_002",
                "rank": 2,
                "ok": True,
                "strategy": "ema_cross",
                "parameters": {"strategy.ema_fast": 5},
                "config_hash": "cfg-b",
                "dataset_hash": "archive-hash",
                "window_count": 3,
                "score": {
                    "research_score": -0.2,
                    "avg_test_return_pct": -0.1,
                    "avg_test_max_drawdown_pct": 0.1,
                    "non_negative_test_window_ratio": 0.33,
                    "total_test_closed_trades": 9,
                    "window_count": 3,
                },
            },
            {
                "variant_id": "variant_003",
                "rank": 3,
                "ok": False,
                "reason": "archive_missing",
                "strategy": "ema_cross",
                "parameters": {"strategy.ema_fast": 8},
                "config_hash": "cfg-c",
                "dataset_hash": "",
                "window_count": 0,
                "score": {
                    "research_score": 0.0,
                    "avg_test_return_pct": 0.0,
                    "avg_test_max_drawdown_pct": 0.0,
                    "non_negative_test_window_ratio": 0.0,
                    "total_test_closed_trades": 0,
                    "window_count": 0,
                },
            },
        ],
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_archive_parameter_sweep_triage_ranks_manual_review_candidates(tmp_path):
    src = tmp_path / "sweep.json"
    _sweep_artifact(src)

    out = run_archive_parameter_sweep_triage(
        input_path=src,
        min_successful_variants=1,
        min_window_count=2,
        min_closed_trades=5,
        min_non_negative_window_ratio=0.5,
        min_avg_test_return_pct=0.0,
        max_avg_test_drawdown_pct=2.0,
    )

    assert out["ok"] is True
    assert out["artifact_type"] == "archive_parameter_sweep_triage_v1"
    assert out["research_only"] is True
    assert out["source_dataset_hashes"] == ["archive-hash"]
    assert out["candidate_count"] == 1
    assert out["review_candidates"][0]["variant_id"] == "variant_001"
    assert out["review_candidates"][0]["status"] == "candidate_for_manual_review"
    assert out["candidates"][0]["false_positive_proxy"]["metric"] == "negative_test_window_ratio"
    assert out["source_cost_assumptions_present"] is False
    assert "not_promotion_evidence" in out["limitations"]


def test_archive_parameter_sweep_triage_rejects_weak_variants(tmp_path):
    src = tmp_path / "sweep.json"
    _sweep_artifact(src)

    out = run_archive_parameter_sweep_triage(
        input_path=src,
        min_successful_variants=2,
        min_window_count=3,
        min_closed_trades=10,
        min_non_negative_window_ratio=0.9,
        min_avg_test_return_pct=1.5,
        max_avg_test_drawdown_pct=0.2,
    )

    assert out["ok"] is False
    assert out["reason"] == "insufficient_review_candidates"
    reasons = {reason for row in out["candidates"] for reason in row["reasons"]}
    assert "avg_test_return_below_threshold" in reasons
    assert "avg_test_drawdown_above_threshold" in reasons
    assert "variant_not_ok" in reasons


def test_archive_parameter_sweep_triage_fails_closed_for_bad_artifact(tmp_path):
    src = tmp_path / "wrong.json"
    src.write_text(json.dumps({"artifact_type": "other", "ranked_variants": []}), encoding="utf-8")

    out = run_archive_parameter_sweep_triage(input_path=src)

    assert out["ok"] is False
    assert out["reason"] == "unsupported_input_artifact_type"
    assert out["candidate_count"] == 0


def test_archive_parameter_sweep_triage_fails_closed_for_bad_threshold():
    out = build_archive_parameter_sweep_triage(
        sweep_report={
            "ok": True,
            "artifact_type": "archive_backed_parameter_sweep_v1",
            "ranked_variants": [],
        },
        min_non_negative_window_ratio=1.5,
    )

    assert out["ok"] is False
    assert out["reason"] == "invalid_ratio:min_non_negative_test_window_ratio"


def test_archive_parameter_sweep_triage_propagates_not_ok_source():
    out = build_archive_parameter_sweep_triage(
        sweep_report={
            "ok": False,
            "reason": "no_successful_variants",
            "artifact_type": "archive_backed_parameter_sweep_v1",
            "dataset_summary": {"dataset_hashes": ["archive-hash"]},
            "ranked_variants": [],
        }
    )

    assert out["ok"] is False
    assert out["reason"] == "no_successful_variants"
    assert out["source_dataset_hashes"] == ["archive-hash"]


def test_archive_parameter_sweep_triage_cli_writes_artifact(tmp_path, capsys):
    from scripts.research import run_archive_parameter_sweep_triage as cli

    src = tmp_path / "sweep.json"
    out_path = tmp_path / "triage.json"
    _sweep_artifact(src)

    rc = cli.main(
        [
            "--input",
            str(src),
            "--output",
            str(out_path),
            "--min-closed-trades",
            "5",
            "--fail-if-not-ok",
        ]
    )

    assert rc == 0
    written = json.loads(out_path.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert written["dataset_hash"] == printed["dataset_hash"]
    assert written["script"] == "scripts/research/run_archive_parameter_sweep_triage.py"
    assert written["candidate_count"] == 1


def test_archive_parameter_sweep_triage_cli_returns_2_when_requested_and_not_ok(tmp_path):
    from scripts.research import run_archive_parameter_sweep_triage as cli

    rc = cli.main(["--input", str(tmp_path / "missing.json"), "--fail-if-not-ok"])

    assert rc == 2
