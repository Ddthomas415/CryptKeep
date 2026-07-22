from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_TRUTH = ROOT / "docs" / "CURRENT_RUNTIME_TRUTH.md"


def _flat() -> str:
    return " ".join(RUNTIME_TRUTH.read_text(encoding="utf-8", errors="replace").split())


def _doc_path(*parts: str) -> str:
    return "/".join(parts)


def test_runtime_truth_declares_executable_guard() -> None:
    truth = _flat()

    assert "Executable guard:" in truth
    assert "tests/test_current_runtime_truth_guard.py" in truth
    assert "If startup/status authority changes" in truth
    assert "update that test and this document together" in truth


def test_runtime_truth_pins_canonical_operator_control_plane() -> None:
    truth = _flat()

    assert "Canonical operator control plane" in truth
    assert "python scripts/start_bot.py [--with_reconcile]" in truth
    assert (
        "python scripts/stop_bot.py "
        "[--all|--pipeline|--executor|--intent_consumer|--ops_signal_adapter|--ops_risk_gate|--reconciler]"
    ) in truth
    assert "python scripts/bot_status.py" in truth
    assert "managed startup through supervisor / `service_ctl`" in truth


def test_runtime_truth_pins_canonical_truth_sources() -> None:
    truth = _flat()

    assert "Canonical runtime truth sources" in truth
    assert "services.runtime.process_supervisor.status(...)" in truth
    assert _doc_path("runtime", "flags", "*.status.json") in truth
    assert _doc_path("runtime", "health", "*.json") in truth
    assert _doc_path("runtime", "flags", "bot_runner.status.json") in truth
    assert "services/process/bot_runtime_truth.py" in truth


def test_runtime_truth_pins_managed_service_set() -> None:
    truth = _flat()

    for service in (
        "market_ws",
        "pipeline",
        "executor",
        "intent_consumer",
        "ops_signal_adapter",
        "ops_risk_gate",
        "reconciler",
    ):
        assert service in truth


def test_runtime_truth_pins_source_shown_startup_behavior() -> None:
    truth = _flat()

    assert "scripts/start_bot.py` starts supervised services" in truth
    assert "not a wrapper around `bot_ctl.py`" in truth
    assert "runtime_trading_config_available()" in truth
    assert "IDLE / SAFE-IDLE" in truth
    assert _doc_path("runtime", "flags", "bot_runner.status.json") in truth
    assert "CBP_ALLOW_LEGACY_BOT_RUNTIME_FALLBACK=YES" in truth


def test_runtime_truth_pins_compatibility_only_legacy_surfaces() -> None:
    truth = _flat()

    assert "Compatibility-only legacy surfaces" in truth
    for surface in (
        "scripts/bot_ctl.py",
        "scripts/run_bot_safe.py",
        "services.process.bot_process",
        "services.bot.start_manager.start(...)",
        "services.bot.start_manager.stop()",
        "services.bot.process_manager",
        _doc_path("data", "bot_process.json"),
        _doc_path("data", "bot_heartbeat.json"),
    ):
        assert surface in truth
    assert "not the canonical operator startup or runtime truth path" in truth


def test_runtime_truth_pins_startup_reconciliation_boundary() -> None:
    truth = _flat()

    assert "Startup reconciliation status" in truth
    assert _doc_path("data", "startup_status.json") in truth
    assert "services/execution/startup_status.py" in truth
    assert "services/execution/startup_reconcile.py" in truth
    assert "No current in-repo caller was shown enforcing startup-status freshness" in truth
    assert "recorded reconciliation evidence, not as a current canonical launch gate" in truth


def test_runtime_truth_pins_read_only_startup_audit_boundary() -> None:
    truth = _flat()

    assert "python scripts/audit_startup_hardening.py" in truth
    assert ".cbp_state/runtime/startup_audits/" in truth
    assert "does not start services, stop services, mutate process-supervisor state" in truth
    assert "enable live execution, or route orders" in truth
