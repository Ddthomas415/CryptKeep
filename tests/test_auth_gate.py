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


class _FakeColumn(_FakeContext):
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
        self.markdowns: list[str] = []
        self.expanders: list[str] = []
        self.sidebar = _FakeContext()

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

    def markdown(self, message: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append(str(message))

    def metric(self, *args, **kwargs) -> None:
        return None

    def columns(self, spec):
        return [_FakeColumn() for _ in range(len(spec))]

    def expander(self, label: str, *args, **kwargs):
        self.expanders.append(str(label))
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


def test_require_authenticated_role_hides_sidebar_when_signed_out(monkeypatch) -> None:
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
            "auth_scope_label": "Remote/public candidate",
            "scope_detail": "Remote/public use requires stronger controls.",
            "built_in_mfa": True,
            "mfa_detail": "Built-in TOTP MFA is available.",
            "outer_access_control": "cloudflare_access",
            "remote_access_hardened": True,
            "runtime_guard_violations": [],
            "runtime_guard_warnings": [],
        },
    )
    monkeypatch.setattr(auth_gate, "ensure_bootstrap_user_from_env", lambda: {"ok": True, "skipped": True})

    with pytest.raises(_StopCalled):
        auth_gate.require_authenticated_role("VIEWER")

    assert any('[data-testid="stSidebar"]' in text for text in fake.markdowns)


def test_require_authenticated_role_moves_signed_in_account_controls_to_sidebar(monkeypatch) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(auth_gate, "_now_ts", lambda: 100)
    fake.session_state[auth_gate.SESSION_KEY] = {
        "ok": True,
        "username": "auditor",
        "role": "ADMIN",
        "source": "keychain",
        "error": "",
        "login_at": 100,
        "last_activity_at": 100,
    }

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
            "auth_scope_label": "Local/private only",
            "scope_detail": "Configured for local/private use.",
            "built_in_mfa": True,
            "mfa_detail": "Built-in TOTP MFA is available.",
            "outer_access_control": "",
            "remote_access_hardened": False,
            "runtime_guard_violations": [],
            "runtime_guard_warnings": [],
        },
    )
    monkeypatch.setattr(auth_gate, "ensure_bootstrap_user_from_env", lambda: {"ok": True, "skipped": True})
    monkeypatch.setattr(auth_gate, "get_user_mfa_status", lambda **kwargs: {"ok": False})

    out = auth_gate.require_authenticated_role("VIEWER")

    assert out["ok"] is True
    assert "Authentication" not in fake.expanders
    assert "Account Security" in fake.expanders
    assert any("Signed in as `auditor`" in text for text in fake.captions)


def test_require_authenticated_role_surfaces_runtime_guard_violation_for_remote_scope(monkeypatch) -> None:
    import services.security.auth_capabilities as ac
    import services.security.auth_runtime_guard as arg

    fake = _FakeStreamlit()
    monkeypatch.setattr(auth_gate, "st", fake)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("BYPASS_DASHBOARD_AUTH", raising=False)
    monkeypatch.setattr(ac, "_keychain_available", lambda: (True, None))
    monkeypatch.setattr(
        ac,
        "_security_policy",
        lambda: {
            "auth_scope": "remote_public_candidate",
            "auth_scope_label": "Remote/public candidate",
            "remote_access_requires_mfa": True,
            "scope_detail": "Remote/public use requires stronger controls.",
            "mfa_detail": "Built-in TOTP MFA is available.",
            "outer_access_control": "",
        },
    )
    monkeypatch.setattr(
        arg,
        "get_settings_view",
        lambda: {"security": {"auth_scope": "remote_public_candidate", "outer_access_control": ""}},
        raising=False,
    )
    monkeypatch.setattr(auth_gate, "auth_capabilities", ac.auth_capabilities)
    monkeypatch.setattr(auth_gate, "ensure_bootstrap_user_from_env", lambda: {"ok": True, "skipped": True})

    with pytest.raises(_StopCalled):
        auth_gate.require_authenticated_role("VIEWER")

    assert any("outer access-control layer" in msg.lower() for msg in fake.warnings)
    assert any(
        "runtime guard: remote/public candidate mode is set without an outer access-control layer" in msg.lower()
        for msg in fake.errors
    )

def test_login_requires_mfa_when_user_has_mfa_enabled(monkeypatch):
    from dashboard import auth_gate

    monkeypatch.setattr(
        auth_gate,
        "verify_login",
        lambda *args, **kwargs: {"ok": True, "mfa_required": True},
    )

    out = auth_gate.verify_login("user", "pass")
    assert out["ok"] is True
    assert out["mfa_required"] is True


def test_verify_login_fails_closed_when_auth_store_is_unavailable(monkeypatch):
    monkeypatch.setattr(auth_gate, "_load_user_auth_store", lambda: (None, "auth_store_unavailable:ImportError"))

    out = auth_gate.verify_login("user", "pass")

    assert out == {"ok": False, "reason": "auth_store_unavailable:ImportError"}


def test_bootstrap_user_fails_closed_when_auth_store_is_unavailable(monkeypatch):
    monkeypatch.setattr(auth_gate, "_load_user_auth_store", lambda: (None, "auth_store_unavailable:ImportError"))

    out = auth_gate.ensure_bootstrap_user_from_env()

    assert out == {"ok": False, "reason": "auth_store_unavailable:ImportError"}

def test_logout_clears_session_state(monkeypatch):
    from dashboard import auth_gate

    fake_state = {"authenticated": True}
    monkeypatch.setattr(auth_gate.st, "session_state", fake_state, raising=False)

    auth_gate.logout()
    assert fake_state["cbp_auth_session"]["ok"] is False
    assert "user" not in fake_state["cbp_auth_session"]

def test_login_requires_mfa_when_user_has_mfa_enabled(monkeypatch):
    from dashboard import auth_gate

    monkeypatch.setattr(
        auth_gate,
        "verify_login",
        lambda *args, **kwargs: {"ok": True, "mfa_required": True},
    )

    out = auth_gate.verify_login("user", "pass")
    assert out["ok"] is True
    assert out["mfa_required"] is True
