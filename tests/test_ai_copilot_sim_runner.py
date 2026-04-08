from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from services.ai_copilot.sim_runner import (
    build_simulation_command,
    run_simulation_job,
    write_simulation_report,
)


def test_build_simulation_command_rejects_unknown_job():
    with pytest.raises(ValueError, match="unsupported simulation job"):
        build_simulation_command("live_submit")


def test_build_simulation_command_requires_strategy_id_for_loss_replay():
    with pytest.raises(ValueError, match="requires strategy_id"):
        build_simulation_command("paper_loss_replay")


def test_run_simulation_job_parses_structured_replay_output(monkeypatch):
    def _fake_run(cmd, **kwargs):
        assert "replay_paper_losses.py" in cmd[1]
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout=json.dumps({"ok": True, "rows": [{"trade_id": "loss-1"}]}),
            stderr="",
        )

    monkeypatch.setattr("services.ai_copilot.sim_runner.subprocess.run", _fake_run)

    report = run_simulation_job(
        "paper_loss_replay",
        strategy_id="mean_reversion_rsi",
        symbol="ETH/USD",
        limit=2,
        timeframe="5m",
        context_bars=2,
    )

    assert report["ok"] is True
    assert report["severity"] == "ok"
    assert report["parsed_output"]["rows"][0]["trade_id"] == "loss-1"
    assert report["params"]["strategy_id"] == "mean_reversion_rsi"


def test_write_simulation_report_writes_json_and_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    report = {
        "generated_at": "2026-04-08T00:00:00+00:00",
        "job": "paper_diagnostics",
        "severity": "ok",
        "ok": True,
        "summary": "Paper diagnostics completed.",
        "command": ["python", "scripts/report_paper_run_diagnostics.py"],
        "stdout": "=== runner_status ===\n{}",
        "stderr": "",
        "recommendations": ["Keep this runner paper-only."],
    }

    paths = write_simulation_report(report, stem="simulation_test")

    json_path = Path(paths["json_path"])
    markdown_path = Path(paths["markdown_path"])
    assert json_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["job"] == "paper_diagnostics"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# CryptKeep Simulation Run" in markdown
    assert "paper_diagnostics" in markdown
