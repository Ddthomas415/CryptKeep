from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from dashboard.role_guard import Role, has_role
from services.security.auth_capabilities import auth_capabilities
from services.security.user_auth_store import ensure_bootstrap_user_from_env, verify_login


SESSION_KEY = "cbp_auth_session"
BOOTSTRAP_KEY = "cbp_auth_bootstrap_done"


def _session_default() -> Dict[str, Any]:
    return {"ok": False, "username": "", "role": "VIEWER", "source": "", "error": ""}


def _session_get() -> Dict[str, Any]:
    cur = st.session_state.get(SESSION_KEY)
    if not isinstance(cur, dict):
        cur = _session_default()
        st.session_state[SESSION_KEY] = cur
    return cur


def logout() -> None:
    st.session_state[SESSION_KEY] = _session_default()


def require_authenticated_role(required_role: Role = "VIEWER") -> Dict[str, Any]:
    state = _session_get()
    caps = auth_capabilities()

    if not bool(st.session_state.get(BOOTSTRAP_KEY)):
        st.session_state[BOOTSTRAP_KEY] = True
        try:
            ensure_bootstrap_user_from_env()
        except Exception:
            pass

    with st.expander("Authentication", expanded=not bool(state.get("ok"))):
        st.caption(
            "Sign in with keychain-backed credentials. "
            "Optional fallback: env `CBP_AUTH_USERNAME/CBP_AUTH_PASSWORD`."
        )

        c0, c1, c2 = st.columns([1, 1, 2])
        c0.metric("Keychain", "OK" if bool(caps.get("os_keychain")) else "Unavailable")
        c1.metric("Env fallback", "ON" if bool(caps.get("env_credentials")) else "OFF")
        c2.caption(f"Recommended: {caps.get('recommended')}")
        if caps.get("detail"):
            st.caption(f"Detail: {caps.get('detail')}")

        if bool(state.get("ok")):
            st.success(f"Signed in as `{state.get('username')}` ({state.get('role')}) via `{state.get('source')}`")
            if st.button("Sign out", key="auth_sign_out"):
                logout()
                st.rerun()
        else:
            with st.form("auth_sign_in_form"):
                username = st.text_input("Username", value="", key="auth_username")
                password = st.text_input("Password", value="", type="password", key="auth_password")
                submitted = st.form_submit_button("Sign in")
                if submitted:
                    out = verify_login(username=str(username), password=str(password))
                    if bool(out.get("ok")):
                        st.session_state[SESSION_KEY] = {
                            "ok": True,
                            "username": str(out.get("username") or ""),
                            "role": str(out.get("role") or "VIEWER"),
                            "source": str(out.get("source") or ""),
                            "error": "",
                        }
                        st.rerun()
                    else:
                        state["error"] = str(out.get("reason") or "login_failed")
            if state.get("error"):
                st.error(f"Sign-in failed: {state.get('error')}")

    state = _session_get()
    if not bool(state.get("ok")):
        st.info("Sign in is required to access this page.")
        st.stop()

    current_role = str(state.get("role") or "VIEWER")
    if not has_role(current_role, required_role):
        st.error(f"Access denied. Required role: `{required_role}`. Current role: `{current_role}`.")
        st.stop()

    return state
