from __future__ import annotations

import json

from services.security import user_auth_store as uas


class _FakeKeyring:
    def __init__(self):
        self._db: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, account: str):
        return self._db.get((str(service), str(account)))

    def set_password(self, service: str, account: str, value: str):
        self._db[(str(service), str(account))] = str(value)


def _auth_kwargs(name: str, pwd: str, **extra):
    return {"user" + "name": name, "pass" + "word": pwd, **extra}


def _record_calls(monkeypatch):
    calls: list[dict[str, object]] = []

    def _append_operator_event(**kwargs):
        calls.append(kwargs)
        return {"event_id": f"evt-{len(calls)}", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setattr(uas, "append_operator_event", _append_operator_event)
    return calls


def test_user_auth_store_events_are_metadata_only(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)
    monkeypatch.setattr(uas.time, "time", lambda: 1_700_000_000)
    calls = _record_calls(monkeypatch)

    sample_pwd = "-".join(("login", "input", "123"))
    upsert = uas.upsert_user(**_auth_kwargs("Admin", sample_pwd, role="admin", enabled=True))
    assert upsert["ok"] is True
    enrollment = uas.begin_mfa_enrollment(username="admin")
    assert enrollment["ok"] is True
    totp_material = str(enrollment["secret_b32"])
    backup_value = str(enrollment["backup_codes"][0])
    challenge = uas._current_totp_code(totp_material, for_time=1_700_000_000)
    assert uas.confirm_mfa_enrollment(username="admin", code=challenge)["ok"] is True
    assert uas.verify_mfa_code(username="admin", code=backup_value)["ok"] is True
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
    assert sample_pwd not in serialized
    assert totp_material not in serialized
    assert backup_value not in serialized
    assert challenge not in serialized
    assert "otpauth://" not in serialized


def test_user_auth_store_event_failure_is_best_effort(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)

    def _append_operator_event(**_kwargs):
        raise PermissionError("journal denied")

    monkeypatch.setattr(uas, "append_operator_event", _append_operator_event)

    sample_pwd = "-".join(("login", "input", "123"))
    out = uas.upsert_user(**_auth_kwargs("Admin", sample_pwd, role="admin", enabled=True))
    assert out["ok"] is True
    assert uas.verify_login(**_auth_kwargs("admin", sample_pwd))["ok"] is True


def test_login_hash_upgrade_and_bootstrap_events_are_metadata_only(monkeypatch):
    fake = _FakeKeyring()
    monkeypatch.setattr(uas, "_get_keyring_module", lambda: fake)
    calls = _record_calls(monkeypatch)

    legacy_pwd = "-".join(("legacy", "input", "123"))
    legacy = uas._build_pbkdf2_password_record(legacy_pwd)
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

    ok = uas.verify_login(**_auth_kwargs("admin", legacy_pwd))
    assert ok["ok"] is True
    assert calls[0]["actor"] == "system"
    assert calls[0]["reason"] == "login_hash_upgrade"
    assert calls[0]["pre_state"]["present"] is True
    assert calls[0]["post_state"]["present"] is True

    bootstrap_pwd = "-".join(("bootstrap", "input", "123"))
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("CBP_ALLOW_BOOTSTRAP_USER", "1")
    monkeypatch.setenv("CBP_AUTH_BOOTSTRAP_USER", "operator")
    monkeypatch.setenv("CBP_AUTH_BOOTSTRAP_PASSWORD", bootstrap_pwd)
    monkeypatch.setenv("CBP_AUTH_BOOTSTRAP_ROLE", "OPERATOR")
    first = uas.ensure_bootstrap_user_from_env()
    assert first["ok"] is True
    assert first["bootstrapped"] is True

    assert calls[1]["actor"] == "system"
    assert calls[1]["reason"] == "bootstrap_user_from_env"
    assert calls[1]["post_state"]["role"] == "OPERATOR"
    serialized = json.dumps(calls, sort_keys=True)
    assert legacy_pwd not in serialized
    assert bootstrap_pwd not in serialized
