from __future__ import annotations

import json

from scripts import run_system_diagnostics as script


def test_run_system_diagnostics_default(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "run_full_diagnostics", lambda export_bundle=False: {"ok": True, "status": "warn", "export_bundle": export_bundle})
    monkeypatch.setattr(script.sys, "argv", ["run_system_diagnostics.py"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "warn"
    assert out["export_bundle"] is False


def test_run_system_diagnostics_preview_repair(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "preview_safe_self_repair", lambda: {"ok": True, "repair_plan": [{"action": "remove_stale_lock"}]})
    monkeypatch.setattr(script.sys, "argv", ["run_system_diagnostics.py", "--preview-repair"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["repair_plan"][0]["action"] == "remove_stale_lock"


def test_run_system_diagnostics_apply_safe_repair(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "apply_safe_self_repair", lambda export_bundle=False: {"ok": True, "export_bundle": export_bundle, "removed_count": 1})
    monkeypatch.setattr(script.sys, "argv", ["run_system_diagnostics.py", "--repair-safe", "--export"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["export_bundle"] is True
    assert out["removed_count"] == 1


def test_run_system_diagnostics_dashboard_mode(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "run_dashboard_diagnostics",
        lambda startup_smoke=True, timeout_sec=15.0: {
            "ok": True,
            "status": "ok",
            "startup_smoke": startup_smoke,
            "timeout_sec": timeout_sec,
        },
    )
    monkeypatch.setattr(
        script.sys,
        "argv",
        ["run_system_diagnostics.py", "--dashboard", "--dashboard-no-smoke", "--dashboard-timeout-sec", "7.5"],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    assert out["startup_smoke"] is False
    assert out["timeout_sec"] == 7.5
