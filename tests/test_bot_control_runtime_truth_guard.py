from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT_CONTROL = ROOT / "docs" / "BOT_CONTROL.md"
CURRENT_RUNTIME_TRUTH = ROOT / "docs" / "CURRENT_RUNTIME_TRUTH.md"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8", errors="replace").split())


def test_bot_control_defers_to_current_runtime_truth() -> None:
    bot_control = _flat(BOT_CONTROL)

    assert "docs/CURRENT_RUNTIME_TRUTH.md" in bot_control
    assert "authoritative operator-facing runtime truth" in bot_control
    assert "must stay aligned with that document" in bot_control
    assert "tests/test_bot_control_runtime_truth_guard.py" in bot_control


def test_bot_control_and_runtime_truth_share_canonical_control_plane() -> None:
    bot_control = _flat(BOT_CONTROL)
    runtime_truth = _flat(CURRENT_RUNTIME_TRUTH)

    for command in (
        "scripts/start_bot.py",
        "scripts/stop_bot.py",
        "scripts/bot_status.py",
    ):
        assert command in bot_control
        assert command in runtime_truth

    assert "managed-service startup through supervisor / `service_ctl`" in bot_control
    assert "managed startup through supervisor / `service_ctl`" in runtime_truth


def test_bot_control_keeps_legacy_plane_compatibility_only() -> None:
    bot_control = _flat(BOT_CONTROL)

    assert "Compatibility-only legacy plane" in bot_control
    for surface in (
        "scripts/bot_ctl.py",
        "services.process.bot_process",
        "scripts/run_bot_safe.py",
        "data/bot_process.json",
        "data/bot_heartbeat.json",
    ):
        assert surface in bot_control

    assert "not the canonical startup or stop path" in bot_control
    assert "scripts/bot_ctl.py` -> `scripts/run_bot_safe.py" not in bot_control
    assert "scripts/bot_ctl.py` → `scripts/run_bot_safe.py" not in bot_control


def test_bot_control_pins_decision_only_boundary() -> None:
    bot_control = _flat(BOT_CONTROL)

    assert "Decision-only compatibility surface" in bot_control
    assert "services.bot.start_manager.decide_start(...)" in bot_control
    assert "not the runtime process owner" in bot_control


def test_bot_control_pins_live_confirmation_requirements() -> None:
    bot_control = _flat(BOT_CONTROL)

    assert "Live confirmations" in bot_control
    assert "ENABLE_LIVE_TRADING=YES" in bot_control
    assert "CONFIRM_LIVE=YES" in bot_control
