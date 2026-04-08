from __future__ import annotations

import json
from pathlib import Path

from services.ai_copilot.pr_reviewer import build_review_packet, write_review_report


def test_build_review_packet_marks_protected_paths_red():
    packet = build_review_packet(
        changed_files=[
            "services/execution/live_executor.py",
            "dashboard/app.py",
        ],
        verification=["./.venv/bin/python -m pytest -q tests/test_live_executor_latency_safety_integration.py"],
        extra_notes="narrow execution slice",
    )

    assert packet["risk_tier"] == "red"
    assert packet["approval_required"] is True
    assert "services/execution/live_executor.py" in packet["protected_files"]
    assert packet["verification"]
    assert packet["extra_notes"] == "narrow execution slice"


def test_write_review_report_writes_json_and_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    packet = build_review_packet(
        changed_files=["services/ai_copilot/policy.py", "docs/AI_COPILOT_BOUNDARY.md"],
        verification=["policy import ok"],
    )

    paths = write_review_report(packet, stem="repo_review_test")

    json_path = Path(paths["json_path"])
    markdown_path = Path(paths["markdown_path"])

    assert json_path.exists()
    assert markdown_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["risk_tier"] == "yellow"
    assert "services/ai_copilot/policy.py" in payload["changed_files"]

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# CryptKeep Repo Review" in markdown
    assert "Approval required" in markdown
