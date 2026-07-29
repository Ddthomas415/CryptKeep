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
    assert all(row["action_required"] is True for row in out["pipelines"])
    assert {row["blocking_reason"] for row in out["pipelines"]} == {"latest_summary_missing"}
    assert all(f"make {row['make_target']}" in row["next_action"] for row in out["pipelines"])


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
    assert rows["price_action"]["action_required"] is False
    assert rows["price_action"]["blocking_reason"] is None
    assert rows["price_action"]["next_action"] == "none"
    assert rows["funding_threshold"]["latest_status"] == "not_run"
    assert rows["funding_threshold"]["action_required"] is True
    assert rows["funding_threshold"]["blocking_reason"] == "latest_summary_missing"


def test_research_pipeline_status_filters_by_pipeline(tmp_path) -> None:
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

    out = build_research_pipeline_status(repo_root=tmp_path, pipeline="funding_threshold")

    assert out["pipeline_filter"] == "funding_threshold"
    assert out["pipeline_count"] == 1
    assert out["source_pipeline_count"] == 2
    assert out["summary"]["not_run"] == 1
    assert out["summary"]["source_wired"] == 2
    assert [row["pipeline_id"] for row in out["pipelines"]] == ["funding_threshold"]


def test_research_pipeline_status_fails_closed_on_unknown_pipeline(tmp_path) -> None:
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

    out = build_research_pipeline_status(repo_root=tmp_path, pipeline="missing_pipeline")

    assert out["ok"] is False
    assert out["reason"] == "invalid_pipeline"
    assert out["pipeline_filter"] == "missing_pipeline"
    assert out["available_pipeline_ids"] == ["funding_threshold", "price_action"]
    assert out["pipeline_count"] == 0
    assert out["source_pipeline_count"] == 2
    assert out["pipelines"] == []


def test_research_pipeline_status_fails_on_wiring_drift(tmp_path) -> None:
    from services.analytics.research_pipeline_status import build_research_pipeline_status

    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "SCRIPTS.md").write_text("", encoding="utf-8")
    (tmp_path / "Makefile").write_text("", encoding="utf-8")

    out = build_research_pipeline_status(repo_root=tmp_path)

    assert out["ok"] is False
    assert out["summary"]["wired"] == 0
    assert any("script_missing" in row["reasons"] for row in out["pipelines"])
    assert all(row["action_required"] is True for row in out["pipelines"])
    assert {row["blocking_reason"] for row in out["pipelines"]} == {"wiring_drift"}


def test_report_research_pipeline_status_cli_prints_next_action(monkeypatch, capsys) -> None:
    from scripts.research import report_research_pipeline_status as script

    monkeypatch.setattr(
        script,
        "build_research_pipeline_status",
        lambda repo_root=None, pipeline=None: {
            "ok": True,
            "pipeline_filter": pipeline,
            "pipeline_count": 1,
            "summary": {"wired": 1, "latest_ok": 0, "not_run": 1, "latest_not_ok": 0},
            "pipelines": [
                {
                    "pipeline_id": "price_action",
                    "wiring_ok": True,
                    "latest_status": "not_run",
                    "make_target": "price-action-research-pipeline",
                    "latest_summary_path": None,
                    "reasons": ["latest_summary_missing"],
                    "action_required": True,
                    "next_action": "run make price-action-research-pipeline with the required research inputs",
                }
            ],
        },
    )

    assert script.main(["--pipeline", "price_action"]) == 0
    out = capsys.readouterr().out
    assert "Research Pipeline Status" in out
    assert "pipeline_filter=price_action" in out
    assert "reasons=latest_summary_missing" in out
    assert "next_action=run make price-action-research-pipeline" in out


def test_report_research_pipeline_status_cli_fails_on_unknown_pipeline(monkeypatch, capsys) -> None:
    from scripts.research import report_research_pipeline_status as script

    monkeypatch.setattr(
        script,
        "build_research_pipeline_status",
        lambda repo_root=None, pipeline=None: {
            "ok": False,
            "reason": "invalid_pipeline",
            "pipeline_filter": pipeline,
            "available_pipeline_ids": ["funding_threshold", "price_action"],
            "pipeline_count": 0,
            "summary": {"wired": 0, "latest_ok": 0, "not_run": 0, "latest_not_ok": 0},
            "pipelines": [],
        },
    )

    assert script.main(["--pipeline", "missing_pipeline"]) == 2
    out = capsys.readouterr().out
    assert "reason=invalid_pipeline" in out
    assert "pipeline_filter=missing_pipeline" in out
    assert "available_pipeline_ids=funding_threshold,price_action" in out
