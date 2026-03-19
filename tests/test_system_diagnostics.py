from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from services.admin import system_diagnostics as sd


def test_run_full_diagnostics_detects_stale_runtime_files(monkeypatch, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    data = tmp_path / "data"
    (runtime / "locks").mkdir(parents=True)
    (runtime / "pids").mkdir(parents=True)
    (runtime / "flags").mkdir(parents=True)
    (runtime / "snapshots").mkdir(parents=True)
    (runtime / "supervisor").mkdir(parents=True)
    (data / "strategy_evidence").mkdir(parents=True)

    (runtime / "locks" / "tick_publisher.lock").write_text('{"pid": 111, "ts": "2026-03-19T00:00:00Z"}\n', encoding="utf-8")
    (runtime / "pids" / "paper_engine.pid").write_text("222\n", encoding="utf-8")
    (runtime / "flags" / "strategy_runner.stop").write_text("2026-03-19T00:00:00Z\n", encoding="utf-8")

    monkeypatch.setattr(sd, "runtime_dir", lambda: runtime)
    monkeypatch.setattr(sd, "data_dir", lambda: data)
    monkeypatch.setattr(sd, "ensure_dirs", lambda: None)
    monkeypatch.setattr(
        sd,
        "run_core_preflight",
        lambda: SimpleNamespace(ok=True, checks=[]),
    )
    monkeypatch.setattr(sd, "run_app_preflight", lambda: {"ready": True, "problems": []})
    monkeypatch.setattr(sd, "collect_process_files", lambda: {"flags": [], "locks": [], "supervisor": [], "snapshots": [], "pids": None})
    monkeypatch.setattr(
        sd,
        "list_health",
        lambda: [{"service": "tick_publisher", "status": "RUNNING", "pid": 111, "ts": "2026-03-19T00:00:00Z"}],
    )
    monkeypatch.setattr(sd, "_pid_alive", lambda pid: False)
    monkeypatch.setattr(
        "services.analytics.crypto_edge_collector_service.load_runtime_status",
        lambda: {"ok": True, "status": "running", "pid": 333, "ts": "2026-03-19T00:00:00Z"},
    )
    monkeypatch.setattr(
        "services.analytics.paper_strategy_evidence_service.load_runtime_status",
        lambda: {"ok": True, "status": "completed", "pid": None, "ts": "2026-03-19T00:00:00Z"},
    )

    out = sd.run_full_diagnostics(export_bundle=False)

    assert out["ok"] is True
    assert out["status"] == "warn"
    actions = {(item["action"], Path(item["path"]).name) for item in out["repair_plan"]}
    assert ("remove_stale_lock", "tick_publisher.lock") in actions
    assert ("remove_stale_pid_file", "paper_engine.pid") in actions
    assert ("remove_stale_stop_file", "strategy_runner.stop") in actions


def test_apply_safe_self_repair_removes_paths_and_exports(monkeypatch, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir(parents=True)
    stale_lock = runtime / "tick_publisher.lock"
    stale_pid = runtime / "paper_engine.pid"
    stale_lock.write_text("{}", encoding="utf-8")
    stale_pid.write_text("123", encoding="utf-8")
    export_path = tmp_path / "diagnostics.zip"

    monkeypatch.setattr(
        sd,
        "preview_safe_self_repair",
        lambda: {
            "ok": True,
            "repair_plan": [
                {"action": "remove_stale_lock", "path": str(stale_lock)},
                {"action": "remove_stale_pid_file", "path": str(stale_pid)},
            ],
        },
    )
    monkeypatch.setattr(sd, "runtime_dir", lambda: runtime.parent)
    monkeypatch.setattr(sd, "export_zip_to_runtime", lambda: export_path)
    monkeypatch.setattr(sd, "run_full_diagnostics", lambda export_bundle=False: {"ok": True, "status": "ok", "summary": {}})

    out = sd.apply_safe_self_repair(export_bundle=True)

    assert out["ok"] is True
    assert out["removed_count"] == 2
    assert str(export_path) == out["export_path"]
    assert stale_lock.exists() is False
    assert stale_pid.exists() is False
