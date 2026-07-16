from __future__ import annotations

import json
import threading

import pytest

from services.security import user_auth_store as uas


class _FakeKeyring:
    def __init__(self):
        self._db: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, account: str):
        return self._db.get((str(service), str(account)))

    def set_password(self, service: str, account: str, password: str):
        self._db[(str(service), str(account))] = str(password)


@pytest.fixture(autouse=True)
def _no_real_operator_event_writes(monkeypatch):
    monkeypatch.setattr(
        uas,
        "append_operator_event",
        lambda **_kwargs: {"event_id": "evt-test", "path": "/tmp/operator_events.jsonl"},
    )


def test_lockout_store_round_trip_does_not_deadlock(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(uas, "_LOCKOUT_TABLE_INIT", False, raising=False)

    result: dict[str, object] = {}
    errors: list[BaseException] = []

    def _run() -> None:
        try:
            result["first"] = uas.record_failed_login("admin", threshold=2, lockout_seconds=300)
            result["second"] = uas.record_failed_login("admin", threshold=2, lockout_seconds=300)
            result["status_before_clear"] = uas.get_lockout_status("admin")
            result["cleared"] = uas.clear_failed_logins("admin")
            result["status_after_clear"] = uas.get_lockout_status("admin")
        except BaseException as exc:  # pragma: no cover - assertion uses captured list
            errors.append(exc)

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    worker.join(2.0)

    assert not worker.is_alive(), "lockout store operations deadlocked"
    assert errors == []
    assert result["first"]["ok"] is True
    assert result["second"]["ok"] is True
    assert result["second"]["fail_count"] == 2
    assert result["status_before_clear"]["locked"] is True
    assert result["cleared"]["ok"] is True
    assert result["status_after_clear"]["locked"] is False
    assert result["status_after_clear"]["fail_count"] == 0


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

    row = uas.get_user("admin")
    assert row is not None
    assert row["password_algo"] == uas.PASSWORD_ALGO_ARGON2ID
    assert str(row.get("password_hash") or "").startswith("$argon2")
    assert "password_hash_hex" not in row

    bad = uas.verify_login(username="admin", password="wrong")
    assert bad["ok"] is False
    assert bad["reason"] == "invalid_credentials"


def test_user_auth_store_events_are_metadata_only(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)
    monkeypatch.setattr(uas.time, "time", lambda: 1_700_000_000)
    calls: list[dict[str, object]] = []

    def _append_operator_event(**kwargs):
        calls.append(kwargs)
        return {"event_id": f"evt-{len(calls)}", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setattr(uas, "append_operator_event", _append_operator_event)

    password = "pw-SUPER-SECRET-123"
    upsert = uas.upsert_user(username="Admin", password=password, role="admin", enabled=True)
    assert upsert["ok"] is True
    enrollment = uas.begin_mfa_enrollment(username="admin")
    assert enrollment["ok"] is True
    secret = str(enrollment["secret_b32"])
    backup = str(enrollment["backup_codes"][0])
    code = uas._current_totp_code(secret, for_time=1_700_000_000)
    assert uas.confirm_mfa_enrollment(username="admin", code=code)["ok"] is True
    assert uas.verify_mfa_code(username="admin", code=backup)["ok"] is True
    assert uas.disable_mfa_for_user(username="admin")["ok"] is True

    reasons = [str(call["reason"]) for call in calls]
    assert reasons == [
        "upsert_user",
        "begin_mfa_enrollment",
        "confirm_mfa_enrollment",
        "consume_mfa_backup_code",
        "disable_mfa_for_user",
    ]
    assert all(call["action"] == "dashboard_user_auth_store_change" for call in calls)
    assert all(call["target"] == "dashboard_user:admin" for call in calls)
    assert calls[0]["pre_state"]["present"] is False
    assert calls[0]["post_state"]["role"] == "ADMIN"
    assert calls[1]["post_state"]["mfa_enrollment_pending"] is True
    assert calls[2]["post_state"]["mfa_enabled"] is True
    assert calls[3]["post_state"]["backup_code_count"] == len(enrollment["backup_codes"]) - 1
    assert calls[4]["post_state"]["mfa_configured"] is False

    serialized = json.dumps(calls, sort_keys=True)
    assert password not in serialized
    assert secret not in serialized
    assert backup not in serialized
    assert code not in serialized
    assert "otpauth://" not in serialized
    assert "password_hash" not in serialized
    assert "password_salt" not in serialized
    assert "mfa_secret_b32" not in serialized
    assert "mfa_backup_code_hashes" not in serialized


def test_user_auth_store_event_failure_is_best_effort(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)

    def _append_operator_event(**_kwargs):
        raise PermissionError("journal denied")

    monkeypatch.setattr(uas, "append_operator_event", _append_operator_event)

    out = uas.upsert_user(username="Admin", password="pw-123", role="admin", enabled=True)
    assert out["ok"] is True
    assert uas.verify_login(username="admin", password="pw-123")["ok"] is True


def test_verify_login_upgrades_legacy_pbkdf2_user(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)

    legacy = uas._build_pbkdf2_password_record("pw-123")
    legacy_record = {
        "username": "admin",
        "role": "ADMIN",
        "enabled": True,
        "created_ts": "2026-01-01T00:00:00+00:00",
        "updated_ts": "2026-01-01T00:00:00+00:00",
        **legacy,
    }
    uas._save_user_record("admin", legacy_record)
    uas._save_users_index(["admin"])
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        uas,
        "append_operator_event",
        lambda **kwargs: calls.append(kwargs)
        or {"event_id": "evt-rehash", "path": "/tmp/operator_events.jsonl"},
    )

    ok = uas.verify_login(username="admin", password="pw-123")
    assert ok["ok"] is True
    row = uas.get_user("admin")
    assert row is not None
    assert row["password_algo"] == uas.PASSWORD_ALGO_ARGON2ID
    assert str(row.get("password_hash") or "").startswith("$argon2")
    assert "password_hash_hex" not in row
    assert "password_salt_b64" not in row
    assert "iterations" not in row
    assert calls[0]["actor"] == "system"
    assert calls[0]["reason"] == "login_hash_upgrade"
    assert calls[0]["pre_state"]["present"] is True
    assert calls[0]["post_state"]["present"] is True
    serialized = json.dumps(calls, sort_keys=True)
    assert "pw-123" not in serialized
    assert "password_hash" not in serialized
    assert "password_salt" not in serialized


def test_bootstrap_user_from_env(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        uas,
        "append_operator_event",
        lambda **kwargs: calls.append(kwargs)
        or {"event_id": "evt-bootstrap", "path": "/tmp/operator_events.jsonl"},
    )
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("CBP_ALLOW_BOOTSTRAP_USER", "1")
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
    assert calls[0]["actor"] == "system"
    assert calls[0]["reason"] == "bootstrap_user_from_env"
    assert calls[0]["post_state"]["role"] == "OPERATOR"


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
    assert out["reason"] == "invalid_credentials"


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
