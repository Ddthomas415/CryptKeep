from __future__ import annotations

import json
from pathlib import Path

from services.ai_copilot.oversight_watch import (
    answer_repo_question,
    build_oversight_snapshot,
    quick_repo_watch,
    write_oversight_report,
)


def test_build_oversight_snapshot_collects_repo_and_runtime(monkeypatch):
    monkeypatch.setattr(
        "services.ai_copilot.oversight_watch._repo_state",
        lambda: {"head": "abc1234", "branch": "main", "dirty": False},
    )
    monkeypatch.setattr(
        "services.ai_copilot.oversight_watch._runtime_state",
        lambda: {
            "system_health": {"state": "HEALTHY", "reasons": []},
            "running_services": ["pipeline", "executor"],
            "stopped_services": ["reconciler"],
        },
    )
    monkeypatch.setattr(
        "services.ai_copilot.oversight_watch._core_doc_entries",
        lambda: [{"path": "REMAINING_TASKS.md", "excerpt": "Current state"}],
    )
    monkeypatch.setattr(
        "services.ai_copilot.oversight_watch._repo_hits",
        lambda question, limit=8: [{"path": "services/execution/live_reconciler.py", "line": 42, "snippet": "def run_forever"}],
    )

    snapshot = build_oversight_snapshot(question="why is reconciler down", extra_notes="operator note")

    assert snapshot["question"] == "why is reconciler down"
    assert snapshot["extra_notes"] == "operator note"
    assert snapshot["repo"]["head"] == "abc1234"
    assert snapshot["runtime"]["system_health"]["state"] == "HEALTHY"
    assert snapshot["relevant_files"][0]["path"] == "services/execution/live_reconciler.py"
    assert "services" in snapshot["watch_scope"]


def test_answer_repo_question_uses_provider_layer(monkeypatch):
    monkeypatch.setattr(
        "services.ai_copilot.oversight_watch.build_oversight_snapshot",
        lambda question, extra_notes="": {
            "generated_at": "2026-05-06T00:00:00+00:00",
            "question": question,
            "repo": {"head": "abc1234", "branch": "main"},
            "runtime": {"system_health": {"state": "HEALTHY"}, "running_services": ["pipeline"], "stopped_services": []},
            "relevant_files": [],
        },
    )
    monkeypatch.setattr(
        "services.ai_copilot.oversight_watch.render_oversight_context",
        lambda snapshot: "ctx-block",
    )
    monkeypatch.setattr(
        "services.ai_copilot.oversight_watch.call_llm",
        lambda **_: {
            "ok": True,
            "text": "Repo looks healthy.",
            "provider": "openai",
            "model": "gpt-test",
        },
    )

    result = answer_repo_question(question="what is the current health?")

    assert result["ok"] is True
    assert result["mode"] == "llm"
    assert result["analysis"] == "Repo looks healthy."
    assert result["provider"] == "openai"
    assert result["model"] == "gpt-test"
    assert result["context_chars"] == len("ctx-block")


def test_answer_repo_question_falls_back_without_provider(monkeypatch):
    monkeypatch.setattr(
        "services.ai_copilot.oversight_watch.build_oversight_snapshot",
        lambda question, extra_notes="": {
            "generated_at": "2026-05-06T00:00:00+00:00",
            "question": question,
            "repo": {"head": "abc1234", "branch": "main"},
            "runtime": {
                "system_health": {"state": "DEGRADED", "reasons": ["example"]},
                "running_services": ["pipeline"],
                "stopped_services": ["reconciler"],
            },
            "relevant_files": [{"path": "services/runtime/process_supervisor.py", "line": 66, "snippet": "stdout=subprocess.DEVNULL"}],
        },
    )
    monkeypatch.setattr(
        "services.ai_copilot.oversight_watch.render_oversight_context",
        lambda snapshot: "ctx-block",
    )
    monkeypatch.setattr(
        "services.ai_copilot.oversight_watch.call_llm",
        lambda **_: {"ok": False, "error": "Missing API key", "provider": "openai", "model": "gpt-test"},
    )

    result = answer_repo_question(question="why is crash evidence missing?")

    assert result["ok"] is True
    assert result["mode"] == "heuristic_fallback"
    assert "Missing API key" in result["warning"]
    assert "process_supervisor.py:66" in result["analysis"]
    assert "DEGRADED" in result["analysis"]


def test_quick_repo_watch_uses_standard_prompt(monkeypatch):
    captured: dict[str, str] = {}

    def _fake(*, question: str, extra_notes: str = ""):
        captured["question"] = question
        captured["extra_notes"] = extra_notes
        return {"ok": True}

    monkeypatch.setattr("services.ai_copilot.oversight_watch.answer_repo_question", _fake)

    result = quick_repo_watch()

    assert result == {"ok": True}
    assert "repo-wide oversight summary" in captured["question"]
    assert captured["extra_notes"] == ""


def test_write_oversight_report_writes_files(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    payload = {
        "ok": True,
        "mode": "heuristic_fallback",
        "analysis": "Status Summary\nhealthy enough",
        "snapshot": {
            "generated_at": "2026-05-06T00:00:00+00:00",
            "question": "what is watched?",
            "repo": {"head": "abc1234", "branch": "main"},
            "runtime": {"system_health": {"state": "HEALTHY"}},
            "relevant_files": [{"path": "AGENTS.md", "line": 1, "snippet": "# AGENTS"}],
        },
    }

    paths = write_oversight_report(payload, stem="oversight_watch_test")

    json_path = Path(paths["json_path"])
    markdown_path = Path(paths["markdown_path"])

    assert json_path.exists()
    assert markdown_path.exists()
    stored = json.loads(json_path.read_text(encoding="utf-8"))
    assert stored["mode"] == "heuristic_fallback"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# CryptKeep Repo Oversight Watch" in markdown
    assert "AGENTS.md" in markdown
