from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts.research import run_funding_threshold_research_pipeline as pipeline


ROOT = Path(__file__).resolve().parents[1]


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _flat(rel: str) -> str:
    return " ".join(_text(rel).split())


def _fake_completed(returncode: int, payload: dict) -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=json.dumps(payload), stderr="")


def test_funding_threshold_pipeline_runs_reports_in_dependency_order(monkeypatch, tmp_path, capsys):
    calls: list[list[str]] = []

    def fake_run(cmd: list[str]):
        calls.append(cmd)
        output = Path(cmd[cmd.index("--output") + 1])
        payload = {"ok": True, "artifact_type": output.stem}
        output.write_text(json.dumps(payload), encoding="utf-8")
        return _fake_completed(0, payload)

    monkeypatch.setattr(pipeline, "_run_command", fake_run)

    rc = pipeline.main(
        [
            "--output-dir",
            str(tmp_path),
            "--edge-db",
            str(tmp_path / "edge.sqlite"),
            "--archive-db",
            str(tmp_path / "archive.sqlite"),
            "--fee-bps",
            "11.0",
            "--slippage-bps",
            "3.5",
        ]
    )

    assert rc == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["ok"] is True
    assert summary["read_only"] is True
    assert summary["not_strategy_config"] is True
    assert summary["not_campaign_evidence"] is True
    assert summary["not_promotion_evidence"] is True
    assert summary["not_execution_input"] is True
    assert [step["name"] for step in summary["steps"]] == [
        "price_join",
        "threshold_sensitivity",
        "candidate_triage",
        "window_stability",
        "stability_triage",
    ]
    assert [Path(cmd[1]).name for cmd in calls] == [
        "run_funding_context_price_join.py",
        "run_funding_threshold_sensitivity.py",
        "run_funding_threshold_candidate_triage.py",
        "run_funding_threshold_window_stability.py",
        "run_funding_threshold_stability_triage.py",
    ]
    assert all("--fail-if-not-ok" in cmd for cmd in calls)
    assert calls[1][calls[1].index("--input") + 1].endswith("funding_context_price_join.json")
    assert calls[2][calls[2].index("--input") + 1].endswith("funding_threshold_sensitivity.json")
    assert calls[4][calls[4].index("--input") + 1].endswith("funding_threshold_window_stability.json")
    assert "--short-thresholds-pct=-0.005,-0.01,-0.02,-0.05" in calls[1]
    assert "--short-thresholds-pct=-0.005,-0.01,-0.02,-0.05" in calls[3]
    assert calls[1][calls[1].index("--fee-bps") + 1] == "11.0"
    assert calls[1][calls[1].index("--slippage-bps") + 1] == "3.5"
    assert Path(summary["summary_path"]).is_file()


def test_funding_threshold_pipeline_stops_on_first_non_ok_step(monkeypatch, tmp_path, capsys):
    calls: list[list[str]] = []

    def fake_run(cmd: list[str]):
        calls.append(cmd)
        output = Path(cmd[cmd.index("--output") + 1])
        payload = {"ok": len(calls) < 2, "reason": "insufficient_joined_rows"}
        output.write_text(json.dumps(payload), encoding="utf-8")
        return _fake_completed(0 if payload["ok"] else 2, payload)

    monkeypatch.setattr(pipeline, "_run_command", fake_run)

    rc = pipeline.main(["--output-dir", str(tmp_path)])

    assert rc == 2
    assert len(calls) == 2
    summary = json.loads(capsys.readouterr().out)
    assert summary["ok"] is False
    assert [step["name"] for step in summary["steps"]] == ["price_join", "threshold_sensitivity"]
    assert summary["steps"][1]["returncode"] == 2
    assert summary["steps"][1]["ok"] is False


def test_funding_threshold_pipeline_is_registered_as_research_only() -> None:
    makefile = _text("Makefile")
    scripts = _text("scripts/SCRIPTS.md")
    source_decision = _flat("docs/research/crypto_edge_source_decision.md")
    remaining = _text("REMAINING_TASKS.md")

    assert "FUNDING_THRESHOLD_RESEARCH_PIPELINE_ARGS ?=" in makefile
    assert "funding-threshold-research-pipeline:" in makefile
    assert "scripts/research/run_funding_threshold_research_pipeline.py" in makefile
    assert "research/run_funding_threshold_research_pipeline.py" in scripts
    assert "make funding-threshold-research-pipeline" in scripts
    assert "read-only funding-threshold research pipeline wrapper" in source_decision
    assert "does not change collectors, strategy config, campaigns, gates" in source_decision
    assert "run_funding_threshold_research_pipeline.py" in remaining
