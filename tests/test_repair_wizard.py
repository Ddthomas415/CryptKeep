from __future__ import annotations

from types import SimpleNamespace

from services.admin import repair_wizard as rw


def test_preflight_self_check_shape(monkeypatch):
    monkeypatch.setattr(
        rw,
        "run_preflight",
        lambda cfg_path="config/trading.yaml": SimpleNamespace(ok=True, dry_run=False, checks=[{"name": "x", "ok": True}]),
    )
    out = rw.preflight_self_check()
    assert out["ok"] is True
    assert out["dry_run"] is False
    assert isinstance(out["checks"], list)


def test_preview_reset_is_non_destructive(monkeypatch):
    monkeypatch.setattr(
        rw,
        "reset_runtime_state",
        lambda include_locks=False, dry_run=False: {"ok": True, "include_locks": include_locks, "dry_run": dry_run},
    )
    out = rw.preview_reset(include_locks=True)
    assert out["ok"] is True
    assert out["non_destructive"] is True
    assert out["dry_run"] is True
    assert out["include_locks"] is True


def test_execute_reset_requires_confirmation(monkeypatch):
    monkeypatch.setattr(
        rw,
        "reset_runtime_state",
        lambda include_locks=False, dry_run=False: {"ok": True, "include_locks": include_locks, "dry_run": dry_run},
    )
    bad = rw.execute_reset(confirm_text="WRONG", include_locks=False)
    assert bad["ok"] is False
    assert bad["reason"] == "confirmation_mismatch"

    good = rw.execute_reset(confirm_text=rw.CONFIRM_TEXT, include_locks=True)
    assert good["ok"] is True
    assert good["non_destructive"] is False
    assert good["dry_run"] is False
    assert good["include_locks"] is True

def test_preflight_self_check_uses_default_config_path(monkeypatch):
    captured = {}

    def _run_preflight(cfg_path="config/trading.yaml"):
        captured["cfg_path"] = cfg_path
        return SimpleNamespace(ok=True, dry_run=False, checks=[])

    monkeypatch.setattr(rw, "run_preflight", _run_preflight)

    out = rw.preflight_self_check()

    assert out["ok"] is True
    assert captured["cfg_path"] == "config/trading.yaml"


def test_preview_reset_defaults_to_excluding_locks(monkeypatch):
    captured = {}

    def _reset_runtime_state(include_locks=False, dry_run=False):
        captured["include_locks"] = include_locks
        captured["dry_run"] = dry_run
        return {"ok": True, "include_locks": include_locks, "dry_run": dry_run}

    monkeypatch.setattr(rw, "reset_runtime_state", _reset_runtime_state)

    out = rw.preview_reset()

    assert out["ok"] is True
    assert out["non_destructive"] is True
    assert captured == {"include_locks": False, "dry_run": True}


def test_execute_reset_passes_confirmed_arguments(monkeypatch):
    captured = {}

    def _reset_runtime_state(include_locks=False, dry_run=False):
        captured["include_locks"] = include_locks
        captured["dry_run"] = dry_run
        return {"ok": True, "include_locks": include_locks, "dry_run": dry_run}

    monkeypatch.setattr(rw, "reset_runtime_state", _reset_runtime_state)

    out = rw.execute_reset(confirm_text=rw.CONFIRM_TEXT, include_locks=False)

    assert out["ok"] is True
    assert out["non_destructive"] is False
    assert captured == {"include_locks": False, "dry_run": False}


def test_execute_reset_confirmation_is_exact(monkeypatch):
    monkeypatch.setattr(
        rw,
        "reset_runtime_state",
        lambda include_locks=False, dry_run=False: {"ok": True, "include_locks": include_locks, "dry_run": dry_run},
    )

    out = rw.execute_reset(confirm_text=rw.CONFIRM_TEXT.lower(), include_locks=True)

    assert out["ok"] is False
    assert out["reason"] == "confirmation_mismatch"


def test_preview_reset_can_include_locks(monkeypatch):
    captured = {}

    def _reset_runtime_state(include_locks=False, dry_run=False):
        captured["include_locks"] = include_locks
        captured["dry_run"] = dry_run
        return {"ok": True, "include_locks": include_locks, "dry_run": dry_run}

    monkeypatch.setattr(rw, "reset_runtime_state", _reset_runtime_state)

    out = rw.preview_reset(include_locks=True)

    assert out["ok"] is True
    assert out["non_destructive"] is True
    assert captured == {"include_locks": True, "dry_run": True}


def test_execute_reset_can_include_locks_when_confirmed(monkeypatch):
    captured = {}

    def _reset_runtime_state(include_locks=False, dry_run=False):
        captured["include_locks"] = include_locks
        captured["dry_run"] = dry_run
        return {"ok": True, "include_locks": include_locks, "dry_run": dry_run}

    monkeypatch.setattr(rw, "reset_runtime_state", _reset_runtime_state)

    out = rw.execute_reset(confirm_text=rw.CONFIRM_TEXT, include_locks=True)

    assert out["ok"] is True
    assert out["non_destructive"] is False
    assert captured == {"include_locks": True, "dry_run": False}

