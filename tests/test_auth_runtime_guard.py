from __future__ import annotations

from services.security.auth_runtime_guard import auth_runtime_guard_status


def test_runtime_guard_ok_in_normal_mode(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("BYPASS_DASHBOARD_AUTH", raising=False)
    monkeypatch.delenv("CBP_ALLOW_ENV_LOGIN", raising=False)
    monkeypatch.delenv("CBP_AUTH_BOOTSTRAP_USER", raising=False)
    monkeypatch.delenv("CBP_AUTH_BOOTSTRAP_PASSWORD", raising=False)

    out = auth_runtime_guard_status()
    assert out["ok"] is True
    assert out["violations"] == []


def test_runtime_guard_blocks_bypass_outside_dev(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("BYPASS_DASHBOARD_AUTH", "1")

    out = auth_runtime_guard_status()
    assert out["ok"] is False
    assert any("BYPASS_DASHBOARD_AUTH" in msg for msg in out["violations"])


def test_runtime_guard_blocks_env_login_outside_dev(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("CBP_ALLOW_ENV_LOGIN", "1")

    out = auth_runtime_guard_status()
    assert out["ok"] is False
    assert any("CBP_ALLOW_ENV_LOGIN" in msg for msg in out["violations"])


def test_runtime_guard_warns_on_partial_bootstrap(monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("CBP_AUTH_BOOTSTRAP_USER", "admin")
    monkeypatch.delenv("CBP_AUTH_BOOTSTRAP_PASSWORD", raising=False)

    out = auth_runtime_guard_status()
    assert out["ok"] is True
    assert any("partially configured" in msg for msg in out["warnings"])


def test_runtime_guard_warns_when_remote_scope_lacks_outer_control(monkeypatch):
    import services.security.auth_runtime_guard as arg

    monkeypatch.setattr(
        arg,
        "get_settings_view",
        lambda: {"security": {"auth_scope": "remote_public_candidate", "outer_access_control": ""}},
        raising=False,
    )

    out = auth_runtime_guard_status()
    assert out["ok"] is True
    assert any("outer access-control layer" in msg for msg in out["warnings"])
