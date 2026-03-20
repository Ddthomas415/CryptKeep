from __future__ import annotations

import pytest

from dashboard import auth_gate


class _StopCalled(RuntimeError):
    pass


class _FakeContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeColumn:
    def metric(self, *args, **kwargs):
        return None

    def caption(self, *args, **kwargs):
        return None


class _FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.infos: list[str] = []
        self.successes: list[str] = []
        self.captions: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(str(message))

    def warning(self, message: str) -> None:
        self.warnings.append(str(message))

    def info(self, message: str) -> None:
        self.infos.append(str(message))

    def success(self, message: str) -> None:
        self.successes.append(str(message))

    def caption(self, message: str) -> None:
        self.captions.append(str(message))

    def metric(self, *args, **kwargs) -> None:
        return None

    def columns(self, spec):
        return [_FakeColumn() for _ in range(len(spec))]

    def expander(self, *args, **kwargs):
        return _FakeContext()

    def form(self, *args, **kwargs):
        return _FakeContext()

    def text_input(self, *args, **kwargs) -> str:
        return ""

    def form_submit_button(self, *args, **kwargs) -> bool:
        return False

    def button(self, *args, **kwargs) -> bool:
        return False

    def rerun(self) -> None:
        raise AssertionError("rerun should not be called in this test")

    def stop(self) -> None:
        raise _StopCalled()


def test_get_security_timeout_minutes_reads_settings_view(monkeypatch) -> None:
    import dashboard.services.view_data as view_data

    monkeypatch.setattr(view_data, "get_settings_view", lambda: {"security": {"session_timeout_minutes": 90}})

    assert auth_gate._get_security_timeout_minutes() == 90


def test_auth_session_expires_based_on_last_activity(monkeypatch) -> None:
    fake = _FakeStreamlit()
    fake.session_state[auth_gate.SESSION_KEY] = {
        "ok": True,
        "username": "admin",
        "role": "ADMIN",
        "source": "keychain",
        "error": "",
        "login_at": 100,
        "last_activity_at": 100,
    }
    monkeypatch.setattr(auth_gate, "st", fake)
    monkeypatch.setattr(auth_gate, "_get_security_timeout_minutes", lambda: 1)
    monkeypatch.setattr(auth_gate, "_now_ts", lambda: 161)

    assert auth_gate._auth_session_expired() is True


def test_failed_logins_trigger_lockout_and_success_resets(monkeypatch) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(auth_gate, "st", fake)
    monkeypatch.setattr(auth_gate, "_now_ts", lambda: 1_000)

    for _ in range(auth_gate.DEFAULT_LOCKOUT_THRESHOLD):
        auth_gate._register_failed_login()

    assert fake.session_state[auth_gate.FAILED_LOGIN_COUNT_KEY] == auth_gate.DEFAULT_LOCKOUT_THRESHOLD
    assert fake.session_state[auth_gate.FAILED_LOGIN_LOCKOUT_UNTIL_KEY] == 1_000 + auth_gate.DEFAULT_LOCKOUT_SECONDS
    assert auth_gate._current_lockout_remaining() == auth_gate.DEFAULT_LOCKOUT_SECONDS

    auth_gate._mark_login_success(username="admin", role="ADMIN", source="keychain")

    assert fake.session_state[auth_gate.FAILED_LOGIN_COUNT_KEY] == 0
    assert fake.session_state[auth_gate.FAILED_LOGIN_LOCKOUT_UNTIL_KEY] == 0
    assert fake.session_state[auth_gate.SESSION_KEY]["ok"] is True


def test_require_authenticated_role_allows_dev_bypass(monkeypatch) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(auth_gate, "st", fake)
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("BYPASS_DASHBOARD_AUTH", "1")

    out = auth_gate.require_authenticated_role("VIEWER")

    assert out["ok"] is True
    assert out["source"] == "bypass"
    assert any("bypass is active" in msg.lower() for msg in fake.warnings)


def test_require_authenticated_role_refuses_bypass_outside_dev(monkeypatch) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(auth_gate, "st", fake)
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("BYPASS_DASHBOARD_AUTH", "1")
    monkeypatch.setattr(
        auth_gate,
        "auth_capabilities",
        lambda: {
            "os_keychain": True,
            "env_credentials": False,
            "recommended": "os_keychain",
            "detail": None,
            "auth_scope_label": "Local/private only",
            "scope_detail": "Configured for local/private use.",
            "mfa_detail": "Built-in MFA/TOTP is not available in the app.",
            "runtime_guard_violations": ["BYPASS_DASHBOARD_AUTH is set outside APP_ENV=dev"],
            "runtime_guard_warnings": [],
        },
    )
    monkeypatch.setattr(auth_gate, "ensure_bootstrap_user_from_env", lambda: {"ok": True, "skipped": True})

    with pytest.raises(_StopCalled):
        auth_gate.require_authenticated_role("VIEWER")

    assert any("auth bypass is refused" in msg.lower() for msg in fake.errors)


def test_require_authenticated_role_warns_when_remote_scope_is_not_hardened(monkeypatch) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(auth_gate, "st", fake)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("BYPASS_DASHBOARD_AUTH", raising=False)
    monkeypatch.setattr(
        auth_gate,
        "auth_capabilities",
        lambda: {
            "os_keychain": True,
            "env_credentials": False,
            "recommended": "os_keychain",
            "detail": None,
            "auth_scope": "remote_public_candidate",
            "auth_scope_label": "Remote/public candidate",
            "scope_detail": "Remote/public use requires stronger controls.",
            "built_in_mfa": True,
            "mfa_detail": "Built-in TOTP MFA is available.",
            "outer_access_control": "",
            "remote_access_hardened": False,
            "runtime_guard_violations": [],
            "runtime_guard_warnings": [],
        },
    )
    monkeypatch.setattr(auth_gate, "ensure_bootstrap_user_from_env", lambda: {"ok": True, "skipped": True})

    with pytest.raises(_StopCalled):
        auth_gate.require_authenticated_role("VIEWER")

    assert any("outer access-control layer" in msg.lower() for msg in fake.warnings)
