from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Literal

import streamlit as st

from services.security.auth_capabilities import auth_capabilities
from services.security.user_auth_store import (
    begin_mfa_enrollment,
    confirm_mfa_enrollment,
    disable_mfa_for_user,
    ensure_bootstrap_user_from_env,
    get_user_mfa_status,
    verify_login,
    verify_mfa_code,
)

logger = logging.getLogger(__name__)

Role = Literal["VIEWER", "OPERATOR", "ADMIN"]

SESSION_KEY = "cbp_auth_session"
BOOTSTRAP_KEY = "cbp_auth_bootstrap_done"
MFA_PENDING_KEY = "cbp_auth_mfa_pending"
MFA_ENROLLMENT_KEY = "cbp_auth_mfa_enrollment"

FAILED_LOGIN_COUNT_KEY = "cbp_auth_failed_count"
FAILED_LOGIN_LOCKOUT_UNTIL_KEY = "cbp_auth_lockout_until"

DEFAULT_SESSION_TIMEOUT_MINUTES = 30
DEFAULT_LOCKOUT_THRESHOLD = 5
DEFAULT_LOCKOUT_SECONDS = 300  # 5 minutes


def has_role(current_role: str, required_role: Role) -> bool:
    order = {"VIEWER": 0, "OPERATOR": 1, "ADMIN": 2}
    cur = str(current_role or "VIEWER").strip().upper()
    req = str(required_role or "VIEWER").strip().upper()
    return order.get(cur, 0) >= order.get(req, 0)


def _now_ts() -> int:
    return int(time.time())


def _app_env() -> str:
    return str(os.getenv("APP_ENV", "")).strip().lower()


def _truthy_env(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def _dashboard_auth_bypassed() -> bool:
    # Explicit dev-only bypass. If BYPASS_DASHBOARD_AUTH is set outside dev,
    # it must not silently bypass auth.
    return _app_env() == "dev" and _truthy_env("BYPASS_DASHBOARD_AUTH")


def _bypass_requested_outside_dev() -> bool:
    return _app_env() != "dev" and _truthy_env("BYPASS_DASHBOARD_AUTH")


def _session_default() -> Dict[str, Any]:
    return {
        "ok": False,
        "username": "",
        "role": "VIEWER",
        "source": "",
        "error": "",
        "login_at": None,
        "last_activity_at": None,
    }


def _session_get() -> Dict[str, Any]:
    cur = st.session_state.get(SESSION_KEY)
    if not isinstance(cur, dict):
        cur = _session_default()
        st.session_state[SESSION_KEY] = cur
    else:
        cur.setdefault("ok", False)
        cur.setdefault("username", "")
        cur.setdefault("role", "VIEWER")
        cur.setdefault("source", "")
        cur.setdefault("error", "")
        cur.setdefault("login_at", None)
        cur.setdefault("last_activity_at", None)
    return cur


def _clear_auth_session() -> None:
    st.session_state[SESSION_KEY] = _session_default()


def logout() -> None:
    _clear_auth_session()
    st.session_state[MFA_PENDING_KEY] = {}
    st.session_state.pop(MFA_ENROLLMENT_KEY, None)


def _mark_login_success(username: str, role: str, source: str) -> None:
    now = _now_ts()
    st.session_state[SESSION_KEY] = {
        "ok": True,
        "username": str(username or ""),
        "role": str(role or "VIEWER"),
        "source": str(source or ""),
        "error": "",
        "login_at": now,
        "last_activity_at": now,
    }
    st.session_state[FAILED_LOGIN_COUNT_KEY] = 0
    st.session_state[FAILED_LOGIN_LOCKOUT_UNTIL_KEY] = 0


def _register_failed_login() -> None:
    count = int(st.session_state.get(FAILED_LOGIN_COUNT_KEY, 0) or 0) + 1
    st.session_state[FAILED_LOGIN_COUNT_KEY] = count
    if count >= DEFAULT_LOCKOUT_THRESHOLD:
        st.session_state[FAILED_LOGIN_LOCKOUT_UNTIL_KEY] = _now_ts() + DEFAULT_LOCKOUT_SECONDS


def _current_lockout_remaining() -> int:
    until = int(st.session_state.get(FAILED_LOGIN_LOCKOUT_UNTIL_KEY, 0) or 0)
    return max(0, until - _now_ts())


def _get_security_timeout_minutes() -> int:
    try:
        from dashboard.services.view_data import get_settings_view

        data = get_settings_view() or {}
        security = data.get("security") or {}
        raw = security.get("session_timeout_minutes", DEFAULT_SESSION_TIMEOUT_MINUTES)
        value = int(raw)
        return max(1, value)
    except Exception:
        return DEFAULT_SESSION_TIMEOUT_MINUTES


def _auth_session_expired() -> bool:
    session = _session_get()
    if not bool(session.get("ok")):
        return False
    timeout_minutes = _get_security_timeout_minutes()
    last_activity = session.get("last_activity_at")
    if not isinstance(last_activity, int):
        return True
    return (_now_ts() - last_activity) > (timeout_minutes * 60)


def _touch_auth_session() -> None:
    session = _session_get()
    if bool(session.get("ok")):
        session["last_activity_at"] = _now_ts()
        st.session_state[SESSION_KEY] = session


def _mfa_pending_default() -> Dict[str, Any]:
    return {"active": False, "username": "", "role": "VIEWER", "source": ""}


def _mfa_pending_get() -> Dict[str, Any]:
    cur = st.session_state.get(MFA_PENDING_KEY)
    if not isinstance(cur, dict):
        cur = _mfa_pending_default()
        st.session_state[MFA_PENDING_KEY] = cur
    else:
        cur.setdefault("active", False)
        cur.setdefault("username", "")
        cur.setdefault("role", "VIEWER")
        cur.setdefault("source", "")
    return cur


def _set_mfa_pending(*, username: str, role: str, source: str) -> None:
    st.session_state[MFA_PENDING_KEY] = {
        "active": True,
        "username": str(username or ""),
        "role": str(role or "VIEWER"),
        "source": str(source or "keychain"),
    }


def _clear_mfa_pending() -> None:
    st.session_state[MFA_PENDING_KEY] = _mfa_pending_default()


def _clear_mfa_enrollment_if_user(username: str) -> None:
    cur = st.session_state.get(MFA_ENROLLMENT_KEY)
    if isinstance(cur, dict) and str(cur.get("username") or "") == str(username or ""):
        st.session_state.pop(MFA_ENROLLMENT_KEY, None)


def _render_signed_in_mfa_controls(username: str) -> None:
    mfa = get_user_mfa_status(username=str(username or ""))
    if not bool(mfa.get("ok")):
        return

    st.caption(
        "Built-in TOTP MFA is available for keychain-backed users. "
        "Remote/public deployment still requires stronger outer access controls."
    )
    remaining = int(mfa.get("backup_codes_remaining") or 0)
    if bool(mfa.get("enabled")):
        st.success(f"MFA is enabled for `{username}` with {remaining} backup code(s) remaining.")
        if st.button("Disable MFA", key="auth_disable_mfa"):
            out = disable_mfa_for_user(username=str(username or ""))
            if bool(out.get("ok")):
                _clear_mfa_enrollment_if_user(str(username or ""))
                st.rerun()
            st.error(f"Failed to disable MFA: {out.get('reason') or 'unknown_error'}")
        return

    enrollment = st.session_state.get(MFA_ENROLLMENT_KEY)
    if not isinstance(enrollment, dict) or str(enrollment.get("username") or "") != str(username or ""):
        enrollment = {}

    if not enrollment:
        if st.button("Prepare Built-in MFA", key="auth_prepare_mfa"):
            out = begin_mfa_enrollment(username=str(username or ""))
            if bool(out.get("ok")):
                st.session_state[MFA_ENROLLMENT_KEY] = out
                st.rerun()
            st.error(f"Failed to prepare MFA enrollment: {out.get('reason') or 'unknown_error'}")
        return

    st.warning("Save these MFA enrollment details before confirming. Backup codes are one-time recovery codes.")
    st.caption(f"Secret: {str(enrollment.get('secret_b32') or '')}")
    st.caption(f"OTP URI: {str(enrollment.get('otpauth_uri') or '')}")
    st.caption(f"Backup codes: {', '.join(str(item) for item in list(enrollment.get('backup_codes') or []))}")

    with st.form("auth_mfa_enrollment_form"):
        code = st.text_input("Authenticator code", value="", key="auth_mfa_enrollment_code")
        submitted = st.form_submit_button("Enable MFA")
        if submitted:
            out = confirm_mfa_enrollment(username=str(username or ""), code=str(code or ""))
            if bool(out.get("ok")):
                st.session_state.pop(MFA_ENROLLMENT_KEY, None)
                st.rerun()
            st.error(f"MFA confirmation failed: {out.get('reason') or 'unknown_error'}")

    if st.button("Cancel MFA setup", key="auth_cancel_mfa_setup"):
        disable_mfa_for_user(username=str(username or ""))
        st.session_state.pop(MFA_ENROLLMENT_KEY, None)
        st.rerun()


def require_authenticated_role(required_role: Role = "VIEWER") -> Dict[str, Any]:
    if _bypass_requested_outside_dev():
        st.error("BYPASS_DASHBOARD_AUTH is set outside APP_ENV=dev. Auth bypass is refused.")

    if _dashboard_auth_bypassed():
        st.warning("Dashboard auth bypass is active (APP_ENV=dev only).")
        return {
            "ok": True,
            "username": "local-dev",
            "role": "OPERATOR",
            "source": "bypass",
            "error": "",
            "login_at": _now_ts(),
            "last_activity_at": _now_ts(),
        }

    state = _session_get()
    pending_mfa = _mfa_pending_get()
    caps = auth_capabilities()

    # Bootstrap once per app session, but do not fail silently.
    if not bool(st.session_state.get(BOOTSTRAP_KEY)):
        st.session_state[BOOTSTRAP_KEY] = True
        try:
            ensure_bootstrap_user_from_env()
        except Exception as exc:
            logger.warning("Bootstrap user initialization failed: %s", exc)
            st.warning("Auth bootstrap initialization failed. Bootstrap env user may be unavailable.")

    # Enforce real session expiry.
    if _auth_session_expired():
        _clear_auth_session()
        state = _session_get()
        state["error"] = "session_expired"

    with st.expander("Authentication", expanded=not bool(state.get("ok"))):
        st.caption(
            "Sign in with keychain-backed credentials. "
            "Env fallback is development-only and must be explicitly enabled."
        )

        c0, c1, c2, c3 = st.columns([1, 1, 1.2, 1.1])
        c0.metric("Keychain", "OK" if bool(caps.get("os_keychain")) else "Unavailable")
        c1.metric("Env fallback", "ON" if bool(caps.get("env_credentials")) else "OFF")
        c2.metric("Scope", str(caps.get("auth_scope_label") or "Local/private only"))
        c3.metric("Built-in MFA", "Yes" if bool(caps.get("built_in_mfa")) else "No")
        st.caption(f"Recommended: {caps.get('recommended')}")
        if caps.get("detail"):
            st.caption(f"Credential store: {caps.get('detail')}")
        if caps.get("scope_detail"):
            st.caption(f"Scope: {caps.get('scope_detail')}")
        if caps.get("mfa_detail"):
            st.caption(f"MFA: {caps.get('mfa_detail')}")
        if str(caps.get("outer_access_control") or "").strip():
            st.caption(f"Outer access control: {caps.get('outer_access_control')}")
        if str(caps.get("auth_scope") or "") == "remote_public_candidate":
            if bool(caps.get("remote_access_hardened")):
                st.success("Remote/public candidate mode has MFA plus outer access control configured.")
            else:
                st.warning(
                    "Remote/public candidate mode still requires an enforced outer access-control layer "
                    "before exposure."
                )
        for violation in list(caps.get("runtime_guard_violations") or []):
            st.error(f"Runtime guard: {violation}")
        for warning in list(caps.get("runtime_guard_warnings") or []):
            st.warning(f"Runtime guard: {warning}")

        timeout_minutes = _get_security_timeout_minutes()
        st.caption(f"Session timeout: {timeout_minutes} minute(s)")

        if bool(state.get("ok")):
            _touch_auth_session()
            st.success(
                f"Signed in as `{state.get('username')}` "
                f"({state.get('role')}) via `{state.get('source')}`"
            )
            _render_signed_in_mfa_controls(str(state.get("username") or ""))
            if st.button("Sign out", key="auth_sign_out"):
                logout()
                st.rerun()
        else:
            if bool(pending_mfa.get("active")):
                st.caption(f"MFA required for `{pending_mfa.get('username')}`.")
                with st.form("auth_mfa_form"):
                    code = st.text_input(
                        "Authenticator or backup code",
                        value="",
                        type="password",
                        key="auth_mfa_code",
                    )
                    submitted = st.form_submit_button("Verify MFA")
                    if submitted:
                        out = verify_mfa_code(
                            username=str(pending_mfa.get("username") or ""),
                            code=str(code or ""),
                        )
                        if bool(out.get("ok")):
                            method = str(out.get("method") or "totp")
                            _mark_login_success(
                                username=str(pending_mfa.get("username") or ""),
                                role=str(pending_mfa.get("role") or "VIEWER"),
                                source=f"{str(pending_mfa.get('source') or 'keychain')}+{method}",
                            )
                            _clear_mfa_pending()
                            st.rerun()
                        else:
                            state = _session_get()
                            state["error"] = str(out.get("reason") or "invalid_mfa_code")
                            st.session_state[SESSION_KEY] = state
            else:
                remaining = _current_lockout_remaining()
                if remaining > 0:
                    st.error(f"Too many failed login attempts. Try again in {remaining} seconds.")
                else:
                    with st.form("auth_sign_in_form"):
                        username = st.text_input("Username", value="", key="auth_username")
                        password = st.text_input("Password", value="", type="password", key="auth_password")
                        submitted = st.form_submit_button("Sign in")
                        if submitted:
                            out = verify_login(username=str(username), password=str(password))
                            if bool(out.get("ok")):
                                if bool(out.get("mfa_required")):
                                    _set_mfa_pending(
                                        username=str(out.get("username") or ""),
                                        role=str(out.get("role") or "VIEWER"),
                                        source=str(out.get("source") or "keychain"),
                                    )
                                    state = _session_get()
                                    state["error"] = ""
                                    st.session_state[SESSION_KEY] = state
                                    st.rerun()
                                _mark_login_success(
                                    username=str(out.get("username") or ""),
                                    role=str(out.get("role") or "VIEWER"),
                                    source=str(out.get("source") or ""),
                                )
                                _clear_mfa_pending()
                                st.rerun()
                            else:
                                _register_failed_login()
                                state = _session_get()
                                state["error"] = str(out.get("reason") or "login_failed")
                                st.session_state[SESSION_KEY] = state

            if state.get("error"):
                msg = str(state.get("error"))
                if msg == "session_expired":
                    st.warning("Your session expired. Please sign in again.")
                elif msg == "invalid_mfa_code":
                    st.error("MFA verification failed. Use a current authenticator code or an unused backup code.")
                else:
                    st.error("Sign-in failed. Check your credentials and try again.")

    state = _session_get()
    if not bool(state.get("ok")):
        st.info("Sign in is required to access this page.")
        st.stop()

    current_role = str(state.get("role") or "VIEWER")
    if not has_role(current_role, required_role):
        st.error(f"Access denied. Required role: `{required_role}`. Current role: `{current_role}`.")
        st.stop()

    return state
