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
    assert ok["mfa_required"] is False

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


def test_verify_login_env_fallback_blocked_by_default(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)

    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("CBP_ALLOW_ENV_LOGIN", raising=False)
    monkeypatch.setenv("CBP_AUTH_USERNAME", "viewer")
    monkeypatch.setenv("CBP_AUTH_PASSWORD", "view-pass")
    monkeypatch.setenv("CBP_AUTH_ROLE", "VIEWER")

    out = uas.verify_login(username="viewer", password="view-pass")
    assert out["ok"] is False
    assert out["reason"] == "unknown_user"


def test_verify_login_env_fallback_allowed_only_in_explicit_dev(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)

    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("CBP_ALLOW_ENV_LOGIN", "1")
    monkeypatch.setenv("CBP_AUTH_USERNAME", "viewer")
    monkeypatch.setenv("CBP_AUTH_PASSWORD", "view-pass")
    monkeypatch.setenv("CBP_AUTH_ROLE", "VIEWER")

    out = uas.verify_login(username="viewer", password="view-pass")
    assert out["ok"] is True
    assert out["source"] == "env"
    assert out["role"] == "VIEWER"


def test_mfa_enrollment_and_verification(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)
    monkeypatch.setattr(uas.time, "time", lambda: 1_700_000_000)

    uas.upsert_user(username="Admin", password="pw-123", role="admin", enabled=True)

    enrollment = uas.begin_mfa_enrollment(username="admin")
    assert enrollment["ok"] is True
    assert enrollment["secret_b32"]
    assert enrollment["backup_codes"]
    assert enrollment["otpauth_uri"].startswith("otpauth://totp/")

    code = uas._current_totp_code(str(enrollment["secret_b32"]), for_time=1_700_000_000)
    confirmed = uas.confirm_mfa_enrollment(username="admin", code=code)
    assert confirmed["ok"] is True
    assert confirmed["backup_codes_remaining"] == len(enrollment["backup_codes"])

    login = uas.verify_login(username="admin", password="pw-123")
    assert login["ok"] is True
    assert login["mfa_required"] is True

    mfa_ok = uas.verify_mfa_code(username="admin", code=code)
    assert mfa_ok["ok"] is True
    assert mfa_ok["method"] == "totp"

    status = uas.get_user_mfa_status("admin")
    assert status["ok"] is True
    assert status["enabled"] is True
    assert status["backup_codes_remaining"] == len(enrollment["backup_codes"])


def test_backup_code_is_one_time(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)
    monkeypatch.setattr(uas.time, "time", lambda: 1_700_000_000)

    uas.upsert_user(username="Admin", password="pw-123", role="admin", enabled=True)
    enrollment = uas.begin_mfa_enrollment(username="admin")
    code = uas._current_totp_code(str(enrollment["secret_b32"]), for_time=1_700_000_000)
    uas.confirm_mfa_enrollment(username="admin", code=code)

    backup = str(enrollment["backup_codes"][0])
    first = uas.verify_mfa_code(username="admin", code=backup)
    assert first["ok"] is True
    assert first["method"] == "backup_code"

    second = uas.verify_mfa_code(username="admin", code=backup)
    assert second["ok"] is False
    assert second["reason"] == "invalid_mfa_code"


def test_disable_mfa_clears_requirement(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)
    monkeypatch.setattr(uas.time, "time", lambda: 1_700_000_000)

    uas.upsert_user(username="Admin", password="pw-123", role="admin", enabled=True)
    enrollment = uas.begin_mfa_enrollment(username="admin")
    code = uas._current_totp_code(str(enrollment["secret_b32"]), for_time=1_700_000_000)
    uas.confirm_mfa_enrollment(username="admin", code=code)

    out = uas.disable_mfa_for_user(username="admin")
    assert out["ok"] is True

    login = uas.verify_login(username="admin", password="pw-123")
    assert login["ok"] is True
    assert login["mfa_required"] is False
