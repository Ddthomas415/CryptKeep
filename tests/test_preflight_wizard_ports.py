from __future__ import annotations

from services.app import preflight_wizard as pw
from services.os.ports import PortResolution


def test_run_preflight_reports_auto_switched_ui_port(monkeypatch) -> None:
    monkeypatch.setattr(pw, "ensure_dirs", lambda: None)
    monkeypatch.setattr(pw, "dashboard_default_port", lambda: 8502)
    monkeypatch.setattr(pw, "_in_venv", lambda: True)
    monkeypatch.setattr(pw, "_import_ok", lambda mod: (True, None))
    monkeypatch.setattr(pw, "_config_valid", lambda: (True, None))
    monkeypatch.setattr(pw, "_cfg", lambda: {"venues": ["coinbase"], "symbols": ["BTC/USD"]})
    monkeypatch.setattr(pw, "_market_checks", lambda venues, symbols: [{"ok": True}])
    monkeypatch.setattr(pw, "_db_presence", lambda: {})
    monkeypatch.setattr(pw, "_supervisor_state", lambda: {})
    monkeypatch.setattr(pw, "_live_arming_state", lambda: {"armed": False})
    monkeypatch.setattr(
        pw,
        "resolve_preferred_port",
        lambda host, port, max_offset=50: PortResolution(
            host=str(host),
            requested_port=int(port),
            resolved_port=8503,
            requested_available=False,
            auto_switched=True,
        ),
    )
    monkeypatch.setattr(pw, "_port_can_bind", lambda host, port: int(port) == 8503)
    monkeypatch.setattr(pw, "_port_open", lambda host, port, timeout=0.25: False)

    out = pw.run_preflight()

    assert out["ready"] is True
    assert "ui_port_unavailable" not in out["problems"]
    assert out["dashboard_port"]["requested_port"] == 8502
    assert out["dashboard_port"]["resolved_port"] == 8503
    assert out["dashboard_port"]["auto_switched"] is True
    assert out["port_8501"]["requested_port"] == 8502
