from __future__ import annotations

from services.security import auth_capabilities as ac


def test_security_policy_uses_module_level_settings_reader(monkeypatch):
    monkeypatch.setattr(
        ac,
        "get_settings_view",
        lambda: {
            "security": {
                "auth_scope": "remote_public_candidate",
                "remote_access_requires_mfa": True,
                "outer_access_control": "vpn",
            }
        },
        raising=False,
    )

    out = ac._security_policy()

    assert out["auth_scope"] == "remote_public_candidate"
    assert out["remote_access_requires_mfa"] is True
    assert out["outer_access_control"] == "vpn"


def test_security_policy_fails_closed_when_settings_reader_raises(monkeypatch):
    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(ac, "get_settings_view", _boom, raising=False)

    out = ac._security_policy()

    assert out["auth_scope"] == "local_private_only"
    assert out["remote_access_requires_mfa"] is True
    assert out["outer_access_control"] == ""


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


def test_auth_capabilities_surfaces_runtime_guard_violation_for_unhardened_remote_scope(monkeypatch):
    import services.security.auth_runtime_guard as arg

    # Verify the monkeypatch hits the right call site.
    # auth_runtime_guard.py binds get_settings_view at module level:
    #   try: from services.market_data.local_data_reader import get_settings_view
    # Patching arg.get_settings_view replaces that module-level binding,
    # which is what auth_runtime_guard_status() calls. This is correct.
    calls = []
    def _fake_settings():
        calls.append(1)
        return {"security": {"auth_scope": "remote_public_candidate", "outer_access_control": ""}}

    monkeypatch.setattr(ac, "_keychain_available", lambda: (True, None))
    monkeypatch.setattr(
        ac,
        "_security_policy",
        lambda: {
            "auth_scope": "remote_public_candidate",
            "auth_scope_label": "Remote/public candidate",
            "remote_access_requires_mfa": True,
            "scope_detail": "Remote/public use requires an external MFA layer.",
            "mfa_detail": "Built-in TOTP MFA is available for keychain-backed users.",
            "outer_access_control": "",
        },
    )
    monkeypatch.setattr(arg, "get_settings_view", _fake_settings, raising=False)

    out = ac.auth_capabilities()

    # Confirm the patch actually fired — the call site was reached
    assert calls, "monkeypatch did not reach get_settings_view — patch target is wrong"
    assert out["runtime_guard_ok"] is False
    assert any("outer access-control layer" in msg for msg in out["runtime_guard_violations"])


def test_auth_capabilities_fails_closed_when_auth_store_import_fails(monkeypatch):
    monkeypatch.setattr(ac, "_load_user_auth_store", lambda: (None, "user_auth_store unavailable: ImportError: bad arch"))
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("CBP_ALLOW_ENV_LOGIN", raising=False)
    monkeypatch.delenv("CBP_AUTH_USERNAME", raising=False)
    monkeypatch.delenv("CBP_AUTH_PASSWORD", raising=False)

    out = ac.auth_capabilities()

    assert out["os_keychain"] is False
    assert out["env_credentials"] is False
    assert out["recommended"] == "unavailable"
    assert out["detail"] == "user_auth_store unavailable: ImportError: bad arch"
