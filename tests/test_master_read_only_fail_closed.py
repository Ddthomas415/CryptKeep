from __future__ import annotations

import services.admin.master_read_only as mro
from services.config_loader import ConfigLoadError


def test_absent_config_remains_not_read_only(monkeypatch):
    calls: list[bool] = []

    def fake_load_user_config(*, strict: bool = False):
        calls.append(strict)
        return {}

    monkeypatch.setattr(mro, "load_user_config", fake_load_user_config)

    read_only, details = mro.is_master_read_only()

    assert read_only is False
    assert calls == [True]
    assert details["read_only_mode"] is False
    assert details["reason"] == "not_read_only"


def test_explicit_true_config_sets_read_only(monkeypatch):
    monkeypatch.setattr(
        mro,
        "load_user_config",
        lambda *, strict=False: {"safety": {"read_only_mode": True}},
    )

    read_only, details = mro.is_master_read_only()

    assert read_only is True
    assert details["read_only_mode"] is True
    assert details["reason"] == "config"


def test_explicit_false_config_is_not_read_only(monkeypatch):
    monkeypatch.setattr(
        mro,
        "load_user_config",
        lambda *, strict=False: {"safety": {"read_only_mode": False}},
    )

    read_only, details = mro.is_master_read_only()

    assert read_only is False
    assert details["read_only_mode"] is False
    assert details["reason"] == "not_read_only"


def test_missing_safety_block_is_not_read_only(monkeypatch):
    monkeypatch.setattr(mro, "load_user_config", lambda *, strict=False: {"other": True})

    read_only, details = mro.is_master_read_only()

    assert read_only is False
    assert details["reason"] == "not_read_only"


def test_corrupt_config_fails_closed(monkeypatch):
    def fake_load_user_config(*, strict: bool = False):
        raise ConfigLoadError("config_load_failed:/tmp/user.yaml:ScannerError")

    monkeypatch.setattr(mro, "load_user_config", fake_load_user_config)

    read_only, details = mro.is_master_read_only()

    assert read_only is True
    assert details["read_only_mode"] is True
    assert details["reason"] == "config_unreadable"
    assert "config_load_failed" in details["error"]


def test_unexpected_config_exception_fails_closed(monkeypatch):
    def fake_load_user_config(*, strict: bool = False):
        raise OSError("disk unavailable")

    monkeypatch.setattr(mro, "load_user_config", fake_load_user_config)

    read_only, details = mro.is_master_read_only()

    assert read_only is True
    assert details["read_only_mode"] is True
    assert details["reason"] == "config_unreadable"
    assert details["error"] == "OSError: disk unavailable"


def test_details_surfaces_fail_closed_reason(monkeypatch):
    def fake_load_user_config(*, strict: bool = False):
        raise ConfigLoadError("config_load_failed:/tmp/user.yaml:not_mapping")

    monkeypatch.setattr(mro, "load_user_config", fake_load_user_config)

    details = mro.details()

    assert details["read_only_mode"] is True
    assert details["reason"] == "config_unreadable"
