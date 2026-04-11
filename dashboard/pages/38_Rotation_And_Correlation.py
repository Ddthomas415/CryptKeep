from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.market_data.rotation_engine import build_rotation_candidates
from services.market_data.ranking_presets import RANKING_PRESETS, merge_ranking_config

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Rotation & Correlation")
st.caption("Rotation candidates from market scanner hot list with correlation-aware diversification.")

col0, col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1, 1])
with col0:
    top_n = st.slider("Top candidates", min_value=5, max_value=20, value=10, step=1)
with col1:
    max_abs_corr = st.slider("Max abs correlation", min_value=0.30, max_value=0.95, value=0.85, step=0.05)
with col2:
    preset_name = st.selectbox("Ranking preset", list(RANKING_PRESETS.keys()), index=0)
with col3:
    momentum_mult = st.slider("Momentum weight", min_value=0.5, max_value=4.0, value=2.0, step=0.5)
with col4:
    volume_mult = st.slider("Volume weight", min_value=1.0, max_value=8.0, value=4.0, step=0.5)
with col5:
    run_now = st.button("Build Rotation List", width="stretch")

if "rotation_result" not in st.session_state:
    st.session_state["rotation_result"] = None

if run_now:
    with st.spinner("Building rotation candidates..."):
        ranking_config = merge_ranking_config(
            preset_name,
            {
                "momentum_mult": momentum_mult,
                "volume_z_mult": volume_mult,
                "correlation_penalty_threshold": max_abs_corr,
            },
        )
        st.session_state["rotation_result"] = build_rotation_candidates(
            top_n=top_n,
            diversify=True,
            max_abs_corr=max_abs_corr,
            ranking_config=ranking_config,
        )

result = st.session_state.get("rotation_result")

if result is None:
    st.info("Click 'Build Rotation List' to build the current rotation list from scanner intelligence.")
    st.stop()

if not result.get("ok"):
    st.error("Rotation build failed.")
    st.stop()

c0, c1, c2, c3 = st.columns(4)
c0.metric("Scanned", int(result.get("scanned", 0)))
c1.metric("Selected", len(result.get("selected", [])))
c2.metric("Diversified", "Yes" if result.get("diversified") else "No")
c3.metric("Timestamp", str(result.get("ts", "")))

mr = result.get("market_regime") or {}
if mr:
    m0, m1, m2 = st.columns(3)
    m0.metric("Market Regime", str(mr.get("regime", "unknown")))
    m1.metric("Fear & Greed", str(mr.get("fg_value", mr.get("fear_greed", {}).get("value", ""))))
    m2.metric("Market Signal", str(mr.get("signal", "neutral")))

st.subheader("Selected Symbols")
st.write(result.get("selected", []))

with st.expander("Active Ranking Config"):
    st.json(result.get("ranking_config") or {})

st.subheader("Selected Rows")
st.dataframe(result.get("selected_rows", []), use_container_width=True)

st.subheader("Score Breakdown")
score_rows = []
for r in (result.get("selected_rows") or []):
    b = dict(r.get("score_breakdown") or {})
    score_rows.append({
        "symbol": r.get("symbol"),
        "composite_score": r.get("composite_score"),
        "composite_score_penalized": r.get("composite_score_penalized"),
        "correlation_penalty": r.get("correlation_penalty"),
        "momentum": b.get("momentum"),
        "hot": b.get("hot"),
        "volume": b.get("volume"),
        "regime": b.get("regime"),
        "funding": b.get("funding"),
        "open_interest": b.get("open_interest"),
        "order_book": b.get("order_book"),
        "order_book_imbalance": r.get("order_book_imbalance"),
        "rsi": b.get("rsi"),
        "volatility": b.get("volatility"),
    })
st.dataframe(score_rows, use_container_width=True)

st.subheader("Top Rotation Candidates")
st.dataframe(result.get("rows", []), use_container_width=True)

corr = result.get("correlation") or {}
with st.expander("Correlation Pairs"):
    st.write("Most Positive")
    st.dataframe(corr.get("most_positive", []), use_container_width=True)
    st.write("Most Negative")
    st.dataframe(corr.get("most_negative", []), use_container_width=True)
