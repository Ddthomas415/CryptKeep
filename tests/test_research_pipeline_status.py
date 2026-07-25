from __future__ import annotations

import json


def test_research_pipeline_status_reports_wiring_and_missing_artifacts(tmp_path) -> None:
    from services.analytics.research_pipeline_status import build_research_pipeline_status

    (tmp_path / "scripts" / "research").mkdir(parents=True)
    (tmp_path / "scripts" / "SCRIPTS.md").write_text(
        "\n".join(
            [
                "research/run_price_action_research_pipeline.py — use make price-action-research-pipeline",
                "research/run_funding_threshold_research_pipeline.py — use make funding-threshold-research-pipeline",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "scripts" / "research" / "run_price_action_research_pipeline.py").write_text("", encoding="utf-8")
    (tmp_path / "scripts" / "research" / "run_funding_threshold_research_pipeline.py").write_text("", encoding="utf-8")
    (tmp_path / "Makefile").write_text(
        "price-action-research-pipeline:\n\ttrue\nfunding-threshold-research-pipeline:\n\ttrue\n",
        encoding="utf-8",
    )

    out = build_research_pipeline_status(repo_root=tmp_path)

    assert out["ok"] is True
    assert out["summary"]["wired"] == 2
    assert out["summary"]["not_run"] == 2
    assert all(row["latest_status"] == "not_run" for row in out["pipelines"])


def test_research_pipeline_status_reads_latest_summary(tmp_path) -> None:
    from services.analytics.research_pipeline_status import build_research_pipeline_status

    (tmp_path / "scripts" / "research").mkdir(parents=True)
    (tmp_path / "scripts" / "SCRIPTS.md").write_text(
        "\n".join(
            [
                "research/run_price_action_research_pipeline.py make price-action-research-pipeline",
                "research/run_funding_threshold_research_pipeline.py make funding-threshold-research-pipeline",
            ]
        ),
        encoding="utf-8",
    )
    for name in (
        "run_price_action_research_pipeline.py",
        "run_funding_threshold_research_pipeline.py",
    ):
        (tmp_path / "scripts" / "research" / name).write_text("", encoding="utf-8")
    (tmp_path / "Makefile").write_text(
        "price-action-research-pipeline:\n\ttrue\nfunding-threshold-research-pipeline:\n\ttrue\n",
        encoding="utf-8",
    )
    summary_dir = tmp_path / ".cbp_state" / "data" / "research" / "price_action_pipeline" / "run1"
    summary_dir.mkdir(parents=True)
    (summary_dir / "pipeline_summary.json").write_text(
        json.dumps(
            {
                "ok": True,
                "read_only": True,
                "report_type": "price_action_research_pipeline",
                "generated_at": "2026-07-25T00:00:00+00:00",
                "steps": [
                    {"name": "context_labels"},
                    {"name": "forward_returns"},
                    {"name": "window_stability"},
                    {"name": "candidate_triage"},
                ],
            }
        ),
        encoding="utf-8",
    )

    out = build_research_pipeline_status(repo_root=tmp_path)
    rows = {row["pipeline_id"]: row for row in out["pipelines"]}

    assert rows["price_action"]["latest_status"] == "latest_ok"
    assert rows["price_action"]["latest_summary_sha256"]
    assert rows["funding_threshold"]["latest_status"] == "not_run"


def test_research_pipeline_status_fails_on_wiring_drift(tmp_path) -> None:
    from services.analytics.research_pipeline_status import build_research_pipeline_status

    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "SCRIPTS.md").write_text("", encoding="utf-8")
    (tmp_path / "Makefile").write_text("", encoding="utf-8")

    out = build_research_pipeline_status(repo_root=tmp_path)

    assert out["ok"] is False
    assert out["summary"]["wired"] == 0
    assert any("script_missing" in row["reasons"] for row in out["pipelines"])
