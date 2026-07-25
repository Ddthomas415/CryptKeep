from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts.research import run_price_action_research_pipeline as pipeline


ROOT = Path(__file__).resolve().parents[1]


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _fake_completed(returncode: int, payload: dict) -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=json.dumps(payload), stderr="")


def test_price_action_pipeline_runs_accepted_reports_in_order(monkeypatch, tmp_path, capsys):
    calls: list[list[str]] = []

    def fake_run(cmd: list[str]):
        calls.append(cmd)
        output = Path(cmd[cmd.index("--output") + 1])
        payload = {"ok": True, "report_type": output.stem}
        output.write_text(json.dumps(payload), encoding="utf-8")
        return _fake_completed(0, payload)

    monkeypatch.setattr(pipeline, "_run_command", fake_run)

    rc = pipeline.main(
        [
            "--venue",
            "coinbase",
            "--symbol",
            "BTC/USDT",
            "--timeframe",
            "1h",
            "--limit",
            "240",
            "--output-dir",
            str(tmp_path),
            "--fee-bps",
            "12.5",
            "--slippage-bps",
            "4.0",
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
        "context_labels",
        "forward_returns",
        "window_stability",
        "candidate_triage",
    ]
    assert [Path(cmd[1]).name for cmd in calls] == [
        "run_price_action_context_labels.py",
        "run_price_action_forward_returns.py",
        "run_price_action_window_stability.py",
        "run_price_action_candidate_triage.py",
    ]
    assert all("--fail-if-not-ok" in cmd for cmd in calls)
    assert "--fee-bps" not in calls[0]
    assert calls[1][calls[1].index("--fee-bps") + 1] == "12.5"
    assert calls[3][calls[3].index("--slippage-bps") + 1] == "4.0"
    assert Path(summary["summary_path"]).is_file()


def test_price_action_pipeline_stops_fail_closed_on_first_failed_report(
    monkeypatch,
    tmp_path,
    capsys,
):
    calls: list[list[str]] = []

    def fake_run(cmd: list[str]):
        calls.append(cmd)
        output = Path(cmd[cmd.index("--output") + 1])
        payload = {"ok": False, "reason": "archive_missing"}
        output.write_text(json.dumps(payload), encoding="utf-8")
        return _fake_completed(2, payload)

    monkeypatch.setattr(pipeline, "_run_command", fake_run)

    rc = pipeline.main(["--output-dir", str(tmp_path)])

    assert rc == 2
    assert len(calls) == 1
    summary = json.loads(capsys.readouterr().out)
    assert summary["ok"] is False
    assert summary["steps"][0]["name"] == "context_labels"
    assert summary["steps"][0]["returncode"] == 2
    assert summary["steps"][0]["ok"] is False


def test_price_action_pipeline_is_registered_as_research_only() -> None:
    makefile = _text("Makefile")
    scripts = _text("scripts/SCRIPTS.md")
    backlog = _text("docs/research/pattern_strategy_backlog.md")
    remaining = _text("REMAINING_TASKS.md")

    assert "PRICE_ACTION_RESEARCH_PIPELINE_ARGS ?=" in makefile
    assert "price-action-research-pipeline:" in makefile
    assert "scripts/research/run_price_action_research_pipeline.py" in makefile
    assert "research/run_price_action_research_pipeline.py" in scripts
    assert "make price-action-research-pipeline" in scripts
    assert "read-only pipeline wrapper" in backlog
    assert "not strategy config, campaign evidence, promotion evidence, or execution" in backlog
    assert "run_price_action_research_pipeline.py" in remaining
