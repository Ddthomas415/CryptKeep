from __future__ import annotations

import streamlit as st


def render_action_result(*, action: str | None, rc: int | None, output: str | None) -> None:
    if not action:
        return

    st.markdown("### Action Result")
    st.caption(f"{action} (rc={rc if rc is not None else '-'})")
    st.code(str(output or "(no output)"))
