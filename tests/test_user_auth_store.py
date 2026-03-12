from __future__ import annotations

from services.security import user_auth_store as uas


class _FakeKeyring:
    def __init__(self):
        self._db: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, account: str):
        return self._db.get((str(service), str(account)))

    def set_password(self, service: str, account: str, password: str):
        self._db[(str(service), str(account))] = str(password)


def test_upsert_and_verify_keychain_user(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)

    out = uas.upsert_user(username="Admin", password="pw-123", role="admin", enabled=True)
    assert out["ok"] is True
    assert out["username"] == "admin"
    assert out["role"] == "ADMIN"

    ok = uas.verify_login(username="admin", password="pw-123")
    assert ok["ok"] is True
    assert ok["source"] == "keychain"
    assert ok["role"] == "ADMIN"

    bad = uas.verify_login(username="admin", password="wrong")
    assert bad["ok"] is False
    assert bad["reason"] == "invalid_credentials"


def test_bootstrap_user_from_env(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)
    monkeypatch.setenv("CBP_AUTH_BOOTSTRAP_USER", "operator")
    monkeypatch.setenv("CBP_AUTH_BOOTSTRAP_PASSWORD", "op-pass")
    monkeypatch.setenv("CBP_AUTH_BOOTSTRAP_ROLE", "OPERATOR")

    first = uas.ensure_bootstrap_user_from_env()
    assert first["ok"] is True
    assert first["bootstrapped"] is True

    second = uas.ensure_bootstrap_user_from_env()
    assert second["ok"] is True
    assert second["skipped"] is True
    assert second["reason"] == "bootstrap_user_exists"

    users = uas.list_users()
    assert len(users) == 1
    assert users[0]["username"] == "operator"
    assert users[0]["role"] == "OPERATOR"


def test_verify_login_env_fallback_without_keyring(monkeypatch):
    monkeypatch.setenv("CBP_AUTH_USERNAME", "viewer")
    monkeypatch.setenv("CBP_AUTH_PASSWORD", "view-pass")
    monkeypatch.setenv("CBP_AUTH_ROLE", "VIEWER")

    out = uas.verify_login(username="viewer", password="view-pass")
    assert out["ok"] is True
    assert out["source"] == "env"
    assert out["role"] == "VIEWER"
