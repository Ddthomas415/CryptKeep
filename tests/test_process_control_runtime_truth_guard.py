from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESS_CONTROL = ROOT / "docs" / "PROCESS_CONTROL.md"
CURRENT_RUNTIME_TRUTH = ROOT / "docs" / "CURRENT_RUNTIME_TRUTH.md"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8", errors="replace").split())


def test_process_control_defers_to_current_runtime_truth() -> None:
    process_control = _flat(PROCESS_CONTROL)

    assert "docs/CURRENT_RUNTIME_TRUTH.md" in process_control
    assert "authoritative operator-facing runtime truth" in process_control
    assert "must stay aligned with that document" in process_control
    assert "tests/test_process_control_runtime_truth_guard.py" in process_control


def test_process_control_and_runtime_truth_share_control_plane() -> None:
    process_control = _flat(PROCESS_CONTROL)
    runtime_truth = _flat(CURRENT_RUNTIME_TRUTH)

    for command in (
        "python scripts/start_bot.py [--with_reconcile]",
        "python scripts/stop_bot.py [--all|--pipeline|--executor|--intent_consumer|--ops_signal_adapter|--ops_risk_gate|--reconciler]",
        "python scripts/bot_status.py",
    ):
        assert command in process_control
        assert command in runtime_truth


def test_process_control_pins_status_surfaces_and_services() -> None:
    process_control = _flat(PROCESS_CONTROL)

    assert "Canonical status surfaces" in process_control
    assert "runtime/flags/*.status.json" in process_control
    assert "runtime/health/*.json" in process_control
    assert "process-supervisor service state" in process_control
    for service in (
        "pipeline",
        "executor",
        "intent_consumer",
        "market_ws",
        "ops_signal_adapter",
        "ops_risk_gate",
        "reconciler",
    ):
        assert service in process_control


def test_process_control_keeps_legacy_surface_compatibility_only() -> None:
    process_control = _flat(PROCESS_CONTROL)

    assert "Compatibility-only legacy surface" in process_control
    for surface in (
        "python scripts/bot_ctl.py ...",
        "data/bot_process.json",
        "data/bot_heartbeat.json",
        "data/logs/bot.log",
        "scripts/run_bot_safe.py",
    ):
        assert surface in process_control

    assert "Use the legacy surface only for compatibility with older tooling" in process_control
    assert "Do not use it for new operator automation or new startup orchestration" in process_control


def test_process_control_pins_dashboard_boundary() -> None:
    process_control = _flat(PROCESS_CONTROL)

    assert "Dashboard" in process_control
    assert "Process Control uses" in process_control
    assert "uses the canonical supervised services and status surfaces above" in process_control
