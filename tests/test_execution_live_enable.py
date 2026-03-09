from __future__ import annotations

from types import SimpleNamespace

from services.execution import live_enable as le


CHECKLIST = {
    "i_understand_live_risk": True,
    "api_keys_configured": True,
    "risk_limits_set": True,
    "dry_run_tested": True,
    "i_accept_no_guarantees": True,
}



def test_enable_live_uses_normalized_live_contract(monkeypatch):
    saved: dict[str, object] = {}

    def _save(cfg):
        saved["cfg"] = cfg
        return True, "Saved"

    monkeypatch.setattr(le, "run_preflight", lambda: SimpleNamespace(ok=True, checks=[{"name": "ok", "ok": True}]))
    monkeypatch.setattr(le, "verify_and_consume", lambda token: {"ok": True, "token": token})
    monkeypatch.setattr(le, "load_user_yaml", lambda: {"risk": {"live": {"max_trades_per_day": 3}}})
    monkeypatch.setattr(le, "save_user_yaml", _save)

    out = le.enable_live(token="abc123", checklist=CHECKLIST)

    assert out["ok"] is True
    assert out["preflight"]["ok"] is True
    assert saved["cfg"]["live"]["enabled"] is True
    assert saved["cfg"]["live_trading"]["enabled"] is True
    assert saved["cfg"]["risk"]["enable_live"] is True
    assert saved["cfg"]["execution"]["live_enabled"] is True
