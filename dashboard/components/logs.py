from __future__ import annotations

from html import escape

import streamlit as st


def render_action_result(*, action: str | None, rc: int | None, output: str | None) -> None:
    if not action:
        return

    st.markdown(
        """
        <div class="ck-section-head">
          <div class="ck-section-title">Action Result</div>
          <div class="ck-section-meta">latest command output</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.markdown(
            f"<div class='ck-log-shell'><div class='ck-log-meta'>{escape(str(action))} (rc={rc if rc is not None else '-'})</div></div>",
            unsafe_allow_html=True,
        )
        st.code(str(output or "(no output)"))
