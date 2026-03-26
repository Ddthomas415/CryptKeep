from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_service_ctl_uses_simple_service_manager() -> None:
    txt = (ROOT / "scripts" / "service_ctl.py").read_text(encoding="utf-8", errors="replace")
    assert "from services.desktop.simple_service_manager import (" in txt


def test_compat_service_manager_describes_legacy_role() -> None:
    txt = (ROOT / "services" / "desktop" / "service_manager.py").read_text(encoding="utf-8", errors="replace")
    assert "Legacy compatibility shim" in txt
    assert "scripts/service_ctl.py -> services.desktop.simple_service_manager" in txt
