from __future__ import annotations

import json
from pathlib import Path

from services.ai_copilot.safety_auditor import build_safety_report, write_safety_report


def test_build_safety_report_runtime_shape(monkeypatch):
    monkeypatch.setattr(
        "services.ai_copilot.safety_auditor.get_kill_switch_state",
        lambda: {"armed": False, "note": "ok"},
    )
    monkeypatch.setattr(
        "services.ai_copilot.safety_auditor.get_system_guard_state",
        lambda fail_closed=False: {"state": "RUNNING", "reason": "ok", "epoch": 3},
    )
    monkeypatch.setattr(
        "services.ai_copilot.safety_auditor.live_allowed",
        lambda: (True, "ok", {"kill_switch": {"armed": False}, "system_guard": {"state": "RUNNING"}}),
    )
    monkeypatch.setattr(
        "services.ai_copilot.safety_auditor.get_live_armed_state",
        lambda: {"armed": False, "writer": "test", "reason": "default"},
    )
    monkeypatch.setattr(
        "services.ai_copilot.safety_auditor.live_enabled_and_armed",
        lambda: (False, "live_not_armed"),
    )
    monkeypatch.setattr("services.ai_copilot.safety_auditor.is_live_enabled", lambda cfg=None: False)

    report = build_safety_report()

    assert report["severity"] == "ok"
    assert report["runtime"]["live_allowed"] is True
    assert report["runtime"]["live_reason"] == "ok"
    assert report["place_order_contract"]["has_enforce_fail_closed"] is True
    assert report["recommendations"]


def test_write_safety_report_writes_files(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(
        "services.ai_copilot.safety_auditor.get_kill_switch_state",
        lambda: {"armed": True, "note": "manual"},
    )
    monkeypatch.setattr(
        "services.ai_copilot.safety_auditor.get_system_guard_state",
        lambda fail_closed=False: {"state": "HALTED", "reason": "manual", "epoch": 7},
    )
    monkeypatch.setattr(
        "services.ai_copilot.safety_auditor.live_allowed",
        lambda: (False, "system_guard_halted", {"kill_switch": {"armed": True}, "system_guard": {"state": "HALTED"}}),
    )
    monkeypatch.setattr(
        "services.ai_copilot.safety_auditor.get_live_armed_state",
        lambda: {"armed": False, "writer": "test", "reason": "halted"},
    )
    monkeypatch.setattr(
        "services.ai_copilot.safety_auditor.live_enabled_and_armed",
        lambda: (False, "live_not_armed"),
    )
    monkeypatch.setattr("services.ai_copilot.safety_auditor.is_live_enabled", lambda cfg=None: False)

    report = build_safety_report()
    paths = write_safety_report(report, stem="safety_audit_test")

    json_path = Path(paths["json_path"])
    markdown_path = Path(paths["markdown_path"])

    assert json_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["severity"] == "warn"
    assert payload["runtime"]["live_reason"] == "system_guard_halted"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# CryptKeep Safety Audit" in markdown
    assert "system_guard_halted" in markdown
