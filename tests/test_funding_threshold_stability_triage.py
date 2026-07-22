from __future__ import annotations

import json

from services.analytics.funding_threshold_stability_triage import (
    build_funding_threshold_stability_triage,
    run_funding_threshold_stability_triage,
)


def _stability_artifact(path) -> None:
    payload = {
        "ok": True,
        "artifact_type": "funding_threshold_window_stability_v1",
        "dataset_hash": "stability-hash",
        "fee_bps": 0.0,
        "slippage_bps": 0.0,
        "input_rows": 600,
        "window_count": 3,
        "threshold_stability": [
            {
                "long_threshold_pct": 0.05,
                "short_threshold_pct": -0.01,
                "window_count": 3,
                "actionable_window_ratio": 1.0,
                "positive_actionable_window_ratio": 1.0,
                "avg_net_forward_return_pct_across_actionable_windows": 0.4,
                "worst_window_avg_net_forward_return_pct": 0.1,
            },
            {
                "long_threshold_pct": 0.005,
                "short_threshold_pct": -0.005,
                "window_count": 3,
                "actionable_window_ratio": 1.0,
                "positive_actionable_window_ratio": 0.33,
                "avg_net_forward_return_pct_across_actionable_windows": -0.2,
                "worst_window_avg_net_forward_return_pct": -1.0,
            },
            {
                "long_threshold_pct": 0.02,
                "short_threshold_pct": -0.02,
                "window_count": 1,
                "actionable_window_ratio": 1.0,
                "positive_actionable_window_ratio": 1.0,
                "avg_net_forward_return_pct_across_actionable_windows": 2.0,
                "worst_window_avg_net_forward_return_pct": 2.0,
            },
        ],
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_funding_threshold_stability_triage_ranks_stable_candidates(tmp_path):
    src = tmp_path / "stability.json"
    _stability_artifact(src)

    out = run_funding_threshold_stability_triage(
        input_path=src,
        min_window_count=2,
        min_actionable_window_ratio=0.5,
        min_positive_actionable_window_ratio=0.5,
        min_avg_net_forward_return_pct=0.0,
        min_worst_window_avg_net_forward_return_pct=0.0,
    )

    assert out["ok"] is True
    assert out["artifact_type"] == "funding_threshold_stability_triage_v1"
    assert out["research_only"] is True
    assert out["source_dataset_hash"] == "stability-hash"
    assert out["candidate_count"] == 1
    assert out["review_candidates"][0]["long_threshold_pct"] == 0.05
    assert out["review_candidates"][0]["short_threshold_pct"] == -0.01
    assert out["review_candidates"][0]["status"] == "candidate_for_manual_review"
    assert out["candidates"][0]["false_positive_proxy"]["metric"] == "non_positive_actionable_window_ratio"
    assert "not_activation_decision" in out["limitations"]


def test_funding_threshold_stability_triage_rejects_unstable_pairs(tmp_path):
    src = tmp_path / "stability.json"
    _stability_artifact(src)

    out = run_funding_threshold_stability_triage(
        input_path=src,
        min_window_count=3,
        min_positive_actionable_window_ratio=0.9,
        min_worst_window_avg_net_forward_return_pct=0.5,
    )

    assert out["ok"] is True
    assert out["candidate_count"] == 0
    reasons = {reason for row in out["candidates"] for reason in row["reasons"]}
    assert "worst_window_return_below_threshold" in reasons
    assert "positive_window_ratio_below_threshold" in reasons
    assert "insufficient_windows" in reasons


def test_funding_threshold_stability_triage_fails_closed_for_bad_artifact(tmp_path):
    src = tmp_path / "wrong.json"
    src.write_text(json.dumps({"artifact_type": "other", "threshold_stability": []}), encoding="utf-8")

    out = run_funding_threshold_stability_triage(input_path=src)

    assert out["ok"] is False
    assert out["reason"] == "unsupported_input_artifact_type"


def test_funding_threshold_stability_triage_fails_closed_for_bad_threshold():
    out = build_funding_threshold_stability_triage(
        stability_report={
            "ok": True,
            "artifact_type": "funding_threshold_window_stability_v1",
            "threshold_stability": [],
        },
        min_actionable_window_ratio=1.5,
    )

    assert out["ok"] is False
    assert out["reason"] == "invalid_ratio:min_actionable_window_ratio"


def test_funding_threshold_stability_triage_propagates_not_ok_source():
    out = build_funding_threshold_stability_triage(
        stability_report={
            "ok": False,
            "reason": "insufficient_windows",
            "artifact_type": "funding_threshold_window_stability_v1",
            "dataset_hash": "short",
            "threshold_stability": [],
        }
    )

    assert out["ok"] is False
    assert out["reason"] == "insufficient_windows"
    assert out["candidate_count"] == 0


def test_funding_threshold_stability_triage_cli_writes_artifact(tmp_path, capsys):
    from scripts.research import run_funding_threshold_stability_triage as cli

    src = tmp_path / "stability.json"
    out_path = tmp_path / "triage.json"
    _stability_artifact(src)

    rc = cli.main(
        [
            "--input",
            str(src),
            "--output",
            str(out_path),
            "--fail-if-not-ok",
        ]
    )

    assert rc == 0
    written = json.loads(out_path.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert written["dataset_hash"] == printed["dataset_hash"]
    assert written["script"] == "scripts/research/run_funding_threshold_stability_triage.py"
    assert written["candidate_count"] == 1


def test_funding_threshold_stability_triage_cli_returns_2_when_requested_and_not_ok(tmp_path):
    from scripts.research import run_funding_threshold_stability_triage as cli

    rc = cli.main(["--input", str(tmp_path / "missing.json"), "--fail-if-not-ok"])

    assert rc == 2
