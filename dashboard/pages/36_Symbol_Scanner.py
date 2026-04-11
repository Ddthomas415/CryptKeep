from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from dashboard.services.symbol_scanner import run_symbol_scan
from dashboard.services.view_data import _repo_default_watchlist_assets


AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Market Scanner")
st.caption("Read-only scanner powered by Coinbase market-wide movers data.")

col0, col1 = st.columns([1, 1])
with col0:
    venue = st.selectbox("Venue", ["coinbase"], index=0, key="scanner_venue")
with col1:
    run_now = st.button("Scan Coinbase Market", width="stretch", key="scanner_run")

if "scanner_result" not in st.session_state:
    st.session_state["scanner_result"] = None

if run_now:
    with st.spinner("Scanning symbols..."):
        st.session_state["scanner_result"] = run_symbol_scan(
            venue=venue,
            symbols=_repo_default_watchlist_assets(),
        )

result = st.session_state.get("scanner_result")

if result is None:
    st.info("Run the scanner to load ranked symbols.")
    st.stop()

if not result.get("ok"):
    st.error(result.get("error") or "Scanner failed")
    st.stop()

c0, c1, c2, c3 = st.columns(4)
c0.metric("Scanned", int(result.get("scanned", 0)))
c1.metric("Pumps", len(result.get("pumps", [])))
c2.metric("Dumps", len(result.get("dumps", [])))
c3.metric("Errors", len(result.get("errors", [])))

st.caption(f"Timestamp: {result.get('ts')}")

def _show_table(title: str, rows: list[dict]) -> None:
    st.subheader(title)
    if not rows:
        st.caption("None")
        return
    st.dataframe(rows, width="stretch")

_show_table("Pumps", result.get("pumps", []))
_show_table("Dumps", result.get("dumps", []))
_show_table("Volume Surges", result.get("volume_surges", []))
_show_table("Oversold", result.get("oversold", []))

with st.expander("All Ranked Symbols"):
    st.dataframe(result.get("all", []), width="stretch")

with st.expander("Scanner Errors"):
    errs = result.get("errors", [])
    if errs:
        st.dataframe(errs, width="stretch")
    else:
        st.caption("No scanner errors.")
