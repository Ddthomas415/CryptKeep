from services.security import auth_capabilities as ac


def test_auth_capabilities_prefers_keychain_when_available(monkeypatch):
    monkeypatch.setattr(ac, "_keychain_available", lambda: (True, None))

    out = ac.auth_capabilities()

    assert out["local_role_selector"] is True
    assert out["os_keychain"] is True
    assert out["oauth"] is False
    assert out["sso"] is False
    assert out["recommended"] == "os_keychain"
    assert out["detail"] is None


def test_auth_capabilities_falls_back_when_keychain_unavailable(monkeypatch):
    monkeypatch.setattr(ac, "_keychain_available", lambda: (False, None))

    out = ac.auth_capabilities()

    assert out["local_role_selector"] is True
    assert out["os_keychain"] is False
    assert out["recommended"] == "local_role_selector"


def test_auth_capabilities_reports_store_error(monkeypatch):
    monkeypatch.setattr(ac, "_keychain_available", lambda: (False, "keychain unavailable"))

    out = ac.auth_capabilities()

    assert out["local_role_selector"] is True
    assert out["os_keychain"] is False
    assert out["recommended"] == "local_role_selector"
    assert "keychain unavailable" in (out["detail"] or "")
