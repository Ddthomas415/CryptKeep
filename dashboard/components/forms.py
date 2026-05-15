from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st


def render_save_action(
    *,
    button_label: str,
    session_key: str,
    payload: dict[str, Any],
    save_fn: Callable[[dict[str, Any]], dict[str, Any]],
    success_message: str,
    error_message: str,
    button_key: str | None = None,
    required_role: str | None = None,
    current_role: str | None = None,
) -> None:
    if st.button(button_label, type="primary", key=button_key):
        if required_role is not None:
            from dashboard.auth_gate import has_role as _has_role
            if not _has_role(str(current_role or "VIEWER"), required_role):
                st.error(
                    f"{required_role} role required for this action. "
                    f"Current role: {str(current_role or 'VIEWER').upper()}"
                )
                return
        st.session_state[session_key] = save_fn(payload)

    result = st.session_state.get(session_key)
    if not isinstance(result, dict):
        return
    if bool(result.get("ok")):
        st.success(str(result.get("message") or success_message))
        return
    st.error(str(result.get("message") or error_message))
