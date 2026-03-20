from __future__ import annotations

from services.security import auth_capabilities as ac


def test_auth_capabilities_prefers_keychain(monkeypatch):
    monkeypatch.setattr(ac, "_keychain_available", lambda: (True, None))
    monkeypatch.setattr(
        ac,
        "_security_policy",
        lambda: {
            "auth_scope": "local_private_only",
            "auth_scope_label": "Local/private only",
            "remote_access_requires_mfa": True,
            "scope_detail": "Configured for local/private use.",
            "mfa_detail": "Built-in TOTP MFA is available for keychain-backed users.",
            "outer_access_control": "",
        },
    )
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("CBP_ALLOW_ENV_LOGIN", raising=False)
    monkeypatch.delenv("CBP_AUTH_USERNAME", raising=False)
    monkeypatch.delenv("CBP_AUTH_PASSWORD", raising=False)

    out = ac.auth_capabilities()

    assert out["local_role_selector"] is False
    assert out["os_keychain"] is True
    assert out["env_credentials"] is False
    assert out["oauth"] is False
    assert out["sso"] is False
    assert out["recommended"] == "os_keychain"
    assert out["detail"] is None
    assert out["auth_scope"] == "local_private_only"
    assert out["built_in_mfa"] is True
    assert out["remote_access_requires_mfa"] is True
    assert out["outer_access_control"] == ""
    assert out["remote_access_hardened"] is False


def test_auth_capabilities_env_credentials_only_in_explicit_dev(monkeypatch):
    monkeypatch.setattr(ac, "_keychain_available", lambda: (False, "keychain unavailable"))
    monkeypatch.setattr(
        ac,
        "_security_policy",
        lambda: {
            "auth_scope": "remote_public_candidate",
            "auth_scope_label": "Remote/public candidate",
            "remote_access_requires_mfa": True,
            "scope_detail": "Remote/public use requires an external MFA layer.",
            "mfa_detail": "Built-in TOTP MFA is available for keychain-backed users.",
            "outer_access_control": "vpn",
        },
    )
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("CBP_ALLOW_ENV_LOGIN", "1")
    monkeypatch.setenv("CBP_AUTH_USERNAME", "admin")
    monkeypatch.setenv("CBP_AUTH_PASSWORD", "secret")

    out = ac.auth_capabilities()

    assert out["local_role_selector"] is False
    assert out["os_keychain"] is False
    assert out["env_credentials"] is True
    assert out["oauth"] is False
    assert out["sso"] is False
    assert out["recommended"] == "env_credentials"
    assert out["detail"] == "keychain unavailable"
    assert out["auth_scope_label"] == "Remote/public candidate"
    assert out["scope_detail"] == "Remote/public use requires an external MFA layer."
    assert out["outer_access_control"] == "vpn"
    assert out["remote_access_hardened"] is True


def test_auth_capabilities_reports_store_error_without_dev_env_login(monkeypatch):
    monkeypatch.setattr(ac, "_keychain_available", lambda: (False, "keychain unavailable"))
    monkeypatch.setattr(
        ac,
        "_security_policy",
        lambda: {
            "auth_scope": "local_private_only",
            "auth_scope_label": "Local/private only",
            "remote_access_requires_mfa": True,
            "scope_detail": "Configured for local/private use.",
            "mfa_detail": "Built-in TOTP MFA is available for keychain-backed users.",
            "outer_access_control": "",
        },
    )
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("CBP_ALLOW_ENV_LOGIN", raising=False)
    monkeypatch.setenv("CBP_AUTH_USERNAME", "admin")
    monkeypatch.setenv("CBP_AUTH_PASSWORD", "secret")

    out = ac.auth_capabilities()

    assert out["local_role_selector"] is False
    assert out["os_keychain"] is False
    assert out["env_credentials"] is False
    assert out["oauth"] is False
    assert out["sso"] is False
    assert out["recommended"] == "unavailable"
    assert out["detail"] == "keychain unavailable"
    assert out["remote_access_hardened"] is False
