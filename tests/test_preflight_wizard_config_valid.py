from __future__ import annotations

from services.admin import config_editor
from services.app import preflight_wizard as pw



def test_config_valid_handles_tuple_result(monkeypatch):
    monkeypatch.setattr(config_editor, "validate_user_yaml", lambda cfg: (False, ["risk.enable_live:must_be_bool"], []))
    monkeypatch.setattr(pw, "load_user_yaml", lambda: {"risk": {"enable_live": "yes"}})

    ok, err = pw._config_valid()

    assert ok is False
    assert "risk.enable_live:must_be_bool" in str(err)



def test_config_valid_returns_true_for_valid_config(monkeypatch):
    monkeypatch.setattr(config_editor, "validate_user_yaml", lambda cfg: (True, [], []))
    monkeypatch.setattr(pw, "load_user_yaml", lambda: {"risk": {"enable_live": False}})

    ok, err = pw._config_valid()

    assert ok is True
    assert err is None
