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
    monkeypatch.setattr(le, "load_user_yaml", lambda **_kwargs: {"risk": {"live": {"max_trades_per_day": 3}}})
    monkeypatch.setattr(le, "save_user_yaml", _save)
    monkeypatch.setattr(
        le,
        "set_live_armed_state",
        lambda armed, *, writer, reason: arm_calls.append((bool(armed), writer, reason)) or {"armed": armed, "writer": writer, "reason": reason},
    )
    monkeypatch.setattr(
        le,
        "record_live_enable_event",
        lambda **kwargs: {"ok": True, "event_id": "evt-enable", "path": "test://operator_events", "payload": kwargs},
    )

    out = le.enable_live(token="abc123", checklist=CHECKLIST)

    assert out["ok"] is True
    assert out["preflight"]["ok"] is True
    assert saved["cfg"]["execution"]["live_enabled"] is True
    assert out["armed_state"]["armed"] is True
    assert out["operator_event"]["ok"] is True
    assert arm_calls == [(True, "execution_live_enable", "token_enable_live")]


def test_enable_live_rolls_back_when_operator_event_write_fails(monkeypatch):
    save_calls: list[dict] = []
    arm_calls: list[tuple[bool, str, str]] = []
    raw_cfg = {"execution": {"live_enabled": False}, "risk": {"live": {"max_trades_per_day": 3}}}

    def _save(cfg):
        save_calls.append(cfg)
        return True, "Saved"

    monkeypatch.setattr(le, "run_preflight", lambda: SimpleNamespace(ok=True, checks=[{"name": "ok", "ok": True}]))
    monkeypatch.setattr(le, "verify_and_consume", lambda token: {"ok": True, "token": token})
    monkeypatch.setattr(le, "load_user_yaml", lambda **_kwargs: dict(raw_cfg))
    monkeypatch.setattr(le, "save_user_yaml", _save)
    monkeypatch.setattr(
        le,
        "set_live_armed_state",
        lambda armed, *, writer, reason: arm_calls.append((bool(armed), writer, reason)) or {"armed": armed, "writer": writer, "reason": reason},
    )
    monkeypatch.setattr(
        le,
        "record_live_enable_event",
        lambda **_kwargs: {"ok": False, "reason": "operator_event_write_failed:PermissionError"},
    )

    out = le.enable_live(token="abc123", checklist=CHECKLIST)

    assert out["ok"] is False
    assert out["reason"] == "operator_event_write_failed_live_enable_rolled_back"
    assert out["operator_event"] == {"ok": False, "reason": "operator_event_write_failed:PermissionError"}
    assert save_calls[0]["execution"]["live_enabled"] is True
    assert save_calls[1] == raw_cfg
    assert out["rollback"]["save"] == {"ok": True, "message": "Saved"}
    assert out["rollback"]["armed_state"]["armed"] is False
    assert arm_calls == [
        (True, "execution_live_enable", "token_enable_live"),
        (False, "execution_live_enable", "token_enable_live:rollback_operator_event_failed"),
    ]


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


def test_enable_live_fails_closed_on_unreadable_config(monkeypatch):
    save_calls: list[dict] = []
    arm_calls: list[tuple[bool, str, str]] = []
    load_kwargs: list[dict] = []

    def _load_user_yaml(**kwargs):
        load_kwargs.append(dict(kwargs))
        raise le.ConfigLoadError("config_load_failed:/tmp/user.yaml:ScannerError:bad")

    monkeypatch.setattr(le, "run_preflight", lambda: SimpleNamespace(ok=True, checks=[{"name": "ok", "ok": True}]))
    monkeypatch.setattr(le, "verify_and_consume", lambda token: {"ok": True, "token": token})
    monkeypatch.setattr(le, "load_user_yaml", _load_user_yaml)
    monkeypatch.setattr(le, "save_user_yaml", lambda cfg: save_calls.append(cfg) or (True, "Saved"))
    monkeypatch.setattr(
        le,
        "set_live_armed_state",
        lambda armed, *, writer, reason: arm_calls.append((bool(armed), writer, reason)) or {"armed": armed, "writer": writer, "reason": reason},
    )

    out = le.enable_live(token="abc123", checklist=CHECKLIST)

    assert out["ok"] is False
    assert out["reason"] == "config_load_failed"
    assert "config_load_failed" in out["error"]
    assert out["preflight"]["ok"] is True
    assert load_kwargs == [{"strict": True}]
    assert save_calls == []
    assert arm_calls == []
