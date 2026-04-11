from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.backtest.selector_backtest import backtest_selector_comparison
from services.market_data.ranking_presets import RANKING_PRESETS, merge_ranking_config
from services.backtest.selector_run_store import append_selector_run, load_selector_runs, summarize_selector_runs

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Selector Backtest")
st.caption("Compare old hot-score selection against the new composite ranker.")

col0, col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1, 1])
with col0:
    top_n = st.slider("Top N", min_value=3, max_value=15, value=8, step=1)
with col1:
    max_abs_corr = st.slider("Max abs correlation", min_value=0.30, max_value=0.95, value=0.85, step=0.05)
with col2:
    preset_name = st.selectbox("Ranking preset", list(RANKING_PRESETS.keys()), index=0)
with col3:
    momentum_mult = st.slider("Momentum weight", min_value=0.5, max_value=4.0, value=2.0, step=0.5)
with col4:
    timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d"], index=0)
with col5:
    forward_bars = st.slider("Forward bars", min_value=1, max_value=24, value=1, step=1)
with col6:
    run_now = st.button("Run Selector Backtest", width="stretch")

run_label = st.text_input("Run label", value="")

if "selector_backtest_result" not in st.session_state:
    st.session_state["selector_backtest_result"] = None
if "selector_run_saved" not in st.session_state:
    st.session_state["selector_run_saved"] = None

if run_now:
    with st.spinner("Comparing selectors..."):
        ranking_config = merge_ranking_config(
            preset_name,
            {"momentum_mult": momentum_mult},
        )
        st.session_state["selector_backtest_result"] = backtest_selector_comparison(
            top_n=top_n,
            max_abs_corr=max_abs_corr,
            ranking_config=ranking_config,
            timeframe=timeframe,
            forward_bars=forward_bars,
        )
        st.session_state["selector_run_saved"] = append_selector_run(
            result=st.session_state["selector_backtest_result"],
            label=(run_label or preset_name),
            ranking_config=ranking_config,
            preset_name=preset_name,
        )

result = st.session_state.get("selector_backtest_result")

if result is None:
    st.info("Click 'Run Selector Backtest' to compare selection logic.")
    st.stop()

baseline = (result.get("baseline") or {})
composite = (result.get("composite") or {})
delta = result.get("delta") or {}

st.caption(f"Forward window: {result.get('forward_bars')} bar(s) on {result.get('timeframe')}")

with st.expander("Active Ranking Config"):
    st.json({
        "preset_name": preset_name,
        **merge_ranking_config(preset_name, {"momentum_mult": momentum_mult}),
    })

c0, c1, c2 = st.columns(3)
c0.metric("Δ Avg Return %", float(delta.get("avg_return_pct", 0.0)))
c1.metric("Δ Hit Rate", float(delta.get("hit_rate", 0.0)))
c2.metric("Δ Total Return %", float(delta.get("total_return_pct", 0.0)))

st.subheader("Baseline Summary")
st.json(baseline.get("summary") or {})

st.subheader("Composite Summary")
st.json(composite.get("summary") or {})

st.subheader("Baseline Symbols")
st.write(baseline.get("symbols") or [])

st.subheader("Composite Symbols")
st.write(composite.get("symbols") or [])

st.subheader("Baseline Rows")
st.dataframe(baseline.get("rows", []), use_container_width=True)

st.subheader("Composite Rows")
st.dataframe(composite.get("rows", []), use_container_width=True)

st.subheader("Multi-Window Comparison")
mw_rows = []
for w in (result.get("multi_window") or []):
    b = dict(w.get("baseline_summary") or {})
    c = dict(w.get("composite_summary") or {})
    d = dict(w.get("delta") or {})
    mw_rows.append({
        "timeframe": w.get("timeframe"),
        "forward_bars": w.get("forward_bars"),
        "baseline_avg_return_pct": b.get("avg_return_pct"),
        "composite_avg_return_pct": c.get("avg_return_pct"),
        "delta_avg_return_pct": d.get("avg_return_pct"),
        "baseline_hit_rate": b.get("hit_rate"),
        "composite_hit_rate": c.get("hit_rate"),
        "delta_hit_rate": d.get("hit_rate"),
        "baseline_total_return_pct": b.get("total_return_pct"),
        "composite_total_return_pct": c.get("total_return_pct"),
        "delta_total_return_pct": d.get("total_return_pct"),
    })
st.dataframe(mw_rows, use_container_width=True)


st.subheader("Saved Selector Runs")
saved_runs = load_selector_runs(limit=100)
st.dataframe(summarize_selector_runs(saved_runs), use_container_width=True)
