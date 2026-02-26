from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Crypto Bot Pro", layout="wide")

_st_button = st.button


def _disabled_button(label: str, *args, **kwargs):
    if isinstance(label, str) and "Start Live Bot" in label:
        kwargs["disabled"] = True
        return False
    return _st_button(label, *args, **kwargs)


st.button = _disabled_button

st.title("Crypto Bot Pro")
st.caption("Use the pages sidebar to navigate. Operator controls are in the Operator page.")
