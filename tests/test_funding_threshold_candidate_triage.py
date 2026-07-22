from __future__ import annotations

import json

from services.analytics.funding_threshold_candidate_triage import (
    build_funding_threshold_candidate_triage,
    run_funding_threshold_candidate_triage,
)


def _sensitivity_artifact(path) -> None:
    payload = {
        "ok": True,
        "artifact_type": "funding_threshold_sensitivity_v1",
        "dataset_hash": "sensitivity-hash",
        "fee_bps": 10.0,
        "slippage_bps": 5.0,
        "input_rows": 500,
        "funding_rate_pct_range": {"min": -0.02, "max": 0.06},
        "grid_rows": [
            {
                "long_threshold_pct": 0.05,
                "short_threshold_pct": -0.01,
                "total_rows": 500,
                "actionable_rows": 12,
                "actionable_share": 0.024,
                "positive_actionable_ratio": 0.75,
                "avg_net_forward_return_pct": 0.8,
            },
            {
                "long_threshold_pct": 0.005,
                "short_threshold_pct": -0.005,
                "total_rows": 500,
                "actionable_rows": 60,
                "actionable_share": 0.12,
                "positive_actionable_ratio": 0.45,
                "avg_net_forward_return_pct": -0.1,
            },
            {
                "long_threshold_pct": 0.02,
                "short_threshold_pct": -0.02,
                "total_rows": 500,
                "actionable_rows": 2,
                "actionable_share": 0.004,
                "positive_actionable_ratio": 1.0,
                "avg_net_forward_return_pct": 2.0,
            },
        ],
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_funding_threshold_candidate_triage_ranks_manual_review_candidates(tmp_path):
    src = tmp_path / "sensitivity.json"
    _sensitivity_artifact(src)

    out = run_funding_threshold_candidate_triage(
        input_path=src,
        min_input_rows=100,
        min_actionable_rows=5,
        min_actionable_share=0.01,
        min_positive_ratio=0.50,
        min_avg_net_forward_return_pct=0.0,
    )

    assert out["ok"] is True
    assert out["artifact_type"] == "funding_threshold_candidate_triage_v1"
    assert out["research_only"] is True
    assert out["source_dataset_hash"] == "sensitivity-hash"
    assert out["candidate_count"] == 1
    assert out["review_candidates"][0]["long_threshold_pct"] == 0.05
    assert out["review_candidates"][0]["short_threshold_pct"] == -0.01
    assert out["review_candidates"][0]["status"] == "candidate_for_manual_review"
    assert out["candidates"][0]["false_positive_proxy"]["metric"] == "non_positive_actionable_ratio"
    assert "not_promotion_evidence" in out["limitations"]


def test_funding_threshold_candidate_triage_rejects_low_frequency_pairs(tmp_path):
    src = tmp_path / "sensitivity.json"
    _sensitivity_artifact(src)

    out = run_funding_threshold_candidate_triage(
        input_path=src,
        min_input_rows=100,
        min_actionable_rows=20,
        min_actionable_share=0.05,
        min_positive_ratio=0.60,
        min_avg_net_forward_return_pct=0.0,
    )

    assert out["ok"] is True
    assert out["candidate_count"] == 0
    reasons = {reason for row in out["candidates"] for reason in row["reasons"]}
    assert "insufficient_actionable_rows" in reasons
    assert "positive_ratio_below_threshold" in reasons


def test_funding_threshold_candidate_triage_fails_closed_for_bad_artifact(tmp_path):
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"artifact_type": "other", "grid_rows": []}), encoding="utf-8")

    out = run_funding_threshold_candidate_triage(input_path=wrong)

    assert out["ok"] is False
    assert out["reason"] == "unsupported_input_artifact_type"
    assert out["candidate_count"] == 0


def test_funding_threshold_candidate_triage_fails_closed_for_bad_thresholds(tmp_path):
    src = tmp_path / "sensitivity.json"
    _sensitivity_artifact(src)

    out = run_funding_threshold_candidate_triage(input_path=src, min_positive_ratio=1.5)

    assert out["ok"] is False
    assert out["reason"] == "invalid_ratio:min_positive_actionable_ratio"


def test_funding_threshold_candidate_triage_propagates_not_ok_source():
    out = build_funding_threshold_candidate_triage(
        sensitivity_report={
            "ok": False,
            "reason": "no_input_rows",
            "artifact_type": "funding_threshold_sensitivity_v1",
            "dataset_hash": "empty",
            "grid_rows": [],
        }
    )

    assert out["ok"] is False
    assert out["reason"] == "no_input_rows"
    assert out["candidate_count"] == 0


def test_funding_threshold_candidate_triage_cli_writes_artifact(tmp_path, capsys):
    from scripts.research import run_funding_threshold_candidate_triage as cli

    src = tmp_path / "sensitivity.json"
    out_path = tmp_path / "triage.json"
    _sensitivity_artifact(src)

    rc = cli.main(
        [
            "--input",
            str(src),
            "--output",
            str(out_path),
            "--min-input-rows",
            "100",
            "--min-actionable-rows",
            "5",
            "--fail-if-not-ok",
        ]
    )

    assert rc == 0
    written = json.loads(out_path.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert written["dataset_hash"] == printed["dataset_hash"]
    assert written["script"] == "scripts/research/run_funding_threshold_candidate_triage.py"
    assert written["candidate_count"] == 1


def test_funding_threshold_candidate_triage_cli_returns_2_when_requested_and_not_ok(tmp_path):
    from scripts.research import run_funding_threshold_candidate_triage as cli

    rc = cli.main(["--input", str(tmp_path / "missing.json"), "--fail-if-not-ok"])

    assert rc == 2
