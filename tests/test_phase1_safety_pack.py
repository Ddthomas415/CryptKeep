from __future__ import annotations

from pathlib import Path

from scripts import run_phase1_safety as phase1


def test_build_steps_contains_verifier_and_phase1_pytest():
    steps = phase1.build_steps("/tmp/python")

    assert [label for label, _cmd in steps] == [
        "verify_no_direct_create_order",
        "phase1_pytest",
    ]
    assert steps[0][1] == ["/tmp/python", "scripts/verify_no_direct_create_order.py", "--root", "."]
    assert steps[1][1][:3] == ["/tmp/python", "-m", "pytest"]
    for test_path in phase1.PHASE1_TESTS:
        assert test_path in steps[1][1]


def test_default_python_prefers_repo_venv(monkeypatch, tmp_path):
    venv_python = tmp_path / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")

    monkeypatch.setattr(phase1, "VENV_PYTHON", venv_python)

    assert phase1._default_python_executable() == str(venv_python)


def test_default_python_falls_back_to_sys_executable(monkeypatch):
    monkeypatch.setattr(phase1, "VENV_PYTHON", Path("/nonexistent/phase1-safety-python"))
    monkeypatch.setattr(phase1.sys, "executable", "/tmp/system-python")

    assert phase1._default_python_executable() == "/tmp/system-python"


def test_main_runs_all_steps_and_returns_zero(monkeypatch):
    seen: list[tuple[str, list[str]]] = []

    def _fake_run(label: str, cmd: list[str]) -> int:
        seen.append((label, cmd))
        return 0

    monkeypatch.setattr(phase1, "_run_step", _fake_run)

    assert phase1.main() == 0
    assert [label for label, _cmd in seen] == [
        "verify_no_direct_create_order",
        "phase1_pytest",
    ]


def test_main_stops_on_first_failed_step(monkeypatch):
    seen: list[str] = []

    def _fake_run(label: str, cmd: list[str]) -> int:
        seen.append(label)
        return 7 if label == "verify_no_direct_create_order" else 0

    monkeypatch.setattr(phase1, "_run_step", _fake_run)

    assert phase1.main() == 7
    assert seen == ["verify_no_direct_create_order"]
