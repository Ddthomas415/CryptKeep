from __future__ import annotations

from typing import Any

import streamlit as st

OPS_LAST_RESULT_KEY = "ops_last_result"


def set_operator_result(*, action: str, rc: int, output: str) -> None:
    st.session_state[OPS_LAST_RESULT_KEY] = {
        "action": str(action),
        "rc": int(rc),
        "output": str(output or "(no output)"),
    }


def get_operator_result() -> dict[str, Any]:
    result = st.session_state.get(OPS_LAST_RESULT_KEY)
    if isinstance(result, dict):
        return result
    return {}


def clear_operator_result() -> None:
    st.session_state.pop(OPS_LAST_RESULT_KEY, None)
