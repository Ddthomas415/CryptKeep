from services.security import auth_capabilities as ac


def test_auth_capabilities_prefers_keychain_when_available(monkeypatch):
    monkeypatch.setattr(ac, "_keychain_available", lambda: (True, None))
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


def test_auth_capabilities_falls_back_when_keychain_unavailable(monkeypatch):
    monkeypatch.setattr(ac, "_keychain_available", lambda: (False, None))
    monkeypatch.delenv("CBP_AUTH_USERNAME", raising=False)
    monkeypatch.delenv("CBP_AUTH_PASSWORD", raising=False)

    out = ac.auth_capabilities()

    assert out["local_role_selector"] is False
    assert out["os_keychain"] is False
    assert out["env_credentials"] is False
    assert out["recommended"] == "unavailable"


def test_auth_capabilities_reports_store_error(monkeypatch):
    monkeypatch.setattr(ac, "_keychain_available", lambda: (False, "keychain unavailable"))
    monkeypatch.setenv("CBP_AUTH_USERNAME", "admin")
    monkeypatch.setenv("CBP_AUTH_PASSWORD", "secret")

    out = ac.auth_capabilities()

    assert out["local_role_selector"] is False
    assert out["os_keychain"] is False
    assert out["env_credentials"] is True
    assert out["recommended"] == "env_credentials"
    assert "keychain unavailable" in (out["detail"] or "")
