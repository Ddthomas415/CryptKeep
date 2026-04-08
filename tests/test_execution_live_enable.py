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
    arm_calls: list[tuple[bool, str, str]] = []

    def _save(cfg):
        saved["cfg"] = cfg
        return True, "Saved"

    monkeypatch.setattr(le, "run_preflight", lambda: SimpleNamespace(ok=True, checks=[{"name": "ok", "ok": True}]))
    monkeypatch.setattr(le, "verify_and_consume", lambda token: {"ok": True, "token": token})
    monkeypatch.setattr(le, "load_user_yaml", lambda: {"risk": {"live": {"max_trades_per_day": 3}}})
    monkeypatch.setattr(le, "save_user_yaml", _save)
    monkeypatch.setattr(
        le,
        "set_live_armed_state",
        lambda armed, *, writer, reason: arm_calls.append((bool(armed), writer, reason)) or {"armed": armed, "writer": writer, "reason": reason},
    )

    out = le.enable_live(token="abc123", checklist=CHECKLIST)

    assert out["ok"] is True
    assert out["preflight"]["ok"] is True
    assert saved["cfg"]["live"]["enabled"] is True
    assert saved["cfg"]["live_trading"]["enabled"] is True
    assert saved["cfg"]["risk"]["enable_live"] is True
    assert saved["cfg"]["execution"]["live_enabled"] is True
    assert out["armed_state"]["armed"] is True
    assert arm_calls == [(True, "execution_live_enable", "token_enable_live")]

def test_enable_live_rejects_incomplete_checklist(monkeypatch):
    from services.execution import live_enable as le

    monkeypatch.setattr(le, "run_preflight", lambda: (_ for _ in ()).throw(AssertionError("should not run preflight")))
    monkeypatch.setattr(le, "verify_and_consume", lambda token: (_ for _ in ()).throw(AssertionError("should not verify token")))

    out = le.enable_live(
        token="abc123",
        checklist={
            "i_understand_live_risk": True,
            "api_keys_configured": False,
            "risk_limits_set": True,
            "dry_run_tested": True,
            "i_accept_no_guarantees": True,
        },
    )

    assert out["ok"] is False
    assert out["reason"] == "checklist_incomplete"
    assert "api_keys_configured" in out["missing"]


def test_enable_live_returns_token_failed_when_verification_fails(monkeypatch):
    from types import SimpleNamespace
    from services.execution import live_enable as le

    monkeypatch.setattr(le, "run_preflight", lambda: SimpleNamespace(ok=True, checks=[]))
    monkeypatch.setattr(le, "verify_and_consume", lambda token: {"ok": False, "reason": "token_mismatch"})
    monkeypatch.setattr(le, "load_user_yaml", lambda: {"live": {"enabled": False}})
    monkeypatch.setattr(le, "save_user_yaml", lambda cfg: (_ for _ in ()).throw(AssertionError("should not save")))

    out = le.enable_live(token="bad-token", checklist=CHECKLIST)

    assert out["ok"] is False
    assert out["reason"] == "token_failed"
    assert out["token"]["reason"] == "token_mismatch"
    assert out["preflight"]["ok"] is True
