from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.backtest.historical_selector_backtest import backtest_historical_selector
from services.backtest.backtest_run_store import append_historical_selector_run, load_historical_selector_runs, summarize_saved_runs, summarize_historical_runs_by_preset
from services.market_data.ranking_presets import RANKING_PRESETS, merge_ranking_config

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Historical Selector Backtest")
st.caption("Walk-forward style selector comparison using historical anchor bars.")

col0, col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1, 1])
with col0:
    top_n = st.slider("Top N", min_value=2, max_value=10, value=5, step=1)
with col1:
    timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d"], index=0)
with col2:
    forward_bars = st.slider("Forward bars", min_value=1, max_value=24, value=4, step=1)
with col3:
    anchor_stride = st.slider("Anchor stride", min_value=1, max_value=24, value=12, step=1)
with col4:
    preset_name = st.selectbox("Ranking preset", list(RANKING_PRESETS.keys()), index=0)
with col5:
    momentum_mult = st.slider("Momentum weight", min_value=0.5, max_value=4.0, value=2.0, step=0.5)
with col6:
    run_now = st.button("Run Historical Backtest", width="stretch")

run_label = st.text_input("Run label", value="")

if "historical_selector_result" not in st.session_state:
    st.session_state["historical_selector_result"] = None

if run_now:
    with st.spinner("Running historical selector comparison..."):
        ranking_config = merge_ranking_config(
            preset_name,
            {"momentum_mult": momentum_mult},
        )
        st.session_state["historical_selector_result"] = backtest_historical_selector(
            top_n=top_n,
            timeframe=timeframe,
            forward_bars=forward_bars,
            anchor_stride=anchor_stride,
            ranking_config=ranking_config,
        )
        st.session_state["historical_selector_run_saved"] = append_historical_selector_run(
            result=st.session_state["historical_selector_result"],
            label=(run_label or preset_name),
            ranking_config={"preset_name": preset_name, **ranking_config},
        )

result = st.session_state.get("historical_selector_result")

if result is None:
    st.info("Click 'Run Historical Backtest' to compare selectors across past anchor points.")
    st.stop()

if not result.get("ok"):
    st.error(f"Historical selector backtest failed: {result.get('reason')}")
    st.stop()

baseline = result.get("baseline") or {}
composite = result.get("composite") or {}
delta = result.get("delta") or {}

c0, c1, c2, c3 = st.columns(4)
c0.metric("Anchors", int(result.get("anchors_tested", 0)))
c1.metric("Δ Avg Return %", float(delta.get("avg_return_pct", 0.0)))
c2.metric("Δ Hit Rate", float(delta.get("hit_rate", 0.0)))
c3.metric("Δ Total Return %", float(delta.get("total_return_pct", 0.0)))

st.subheader("Baseline Summary")
st.json(baseline)

st.subheader("Composite Summary")
st.json(composite)

st.subheader("Anchor Results")
st.dataframe(result.get("anchors", []), use_container_width=True)

st.subheader("Composite Feature Samples")
feature_rows = []
for anchor in (result.get("anchors") or [])[:10]:
    for item in (anchor.get("composite_top_features") or []):
        feature_rows.append({
            "anchor_idx": anchor.get("anchor_idx"),
            "symbol": item.get("symbol"),
            "score": item.get("score"),
            "regime": item.get("regime"),
            "ret_1": (item.get("features") or {}).get("ret_1"),
            "ret_4": (item.get("features") or {}).get("ret_4"),
            "ret_24": (item.get("features") or {}).get("ret_24"),
            "rsi": (item.get("features") or {}).get("rsi"),
            "volatility_pct": (item.get("features") or {}).get("volatility_pct"),
            "volume_ratio": (item.get("features") or {}).get("volume_ratio"),
            "score_momentum": (item.get("breakdown") or {}).get("momentum"),
            "score_hot": (item.get("breakdown") or {}).get("hot"),
            "score_volume": (item.get("breakdown") or {}).get("volume"),
            "score_rsi": (item.get("breakdown") or {}).get("rsi"),
            "score_volatility": (item.get("breakdown") or {}).get("volatility"),
        })
st.dataframe(feature_rows, use_container_width=True)


st.subheader("Preset Summary")
saved_runs = load_historical_selector_runs(limit=100)
st.dataframe(summarize_historical_runs_by_preset(saved_runs), use_container_width=True)

st.subheader("Saved Run Comparison")
st.dataframe(summarize_saved_runs(saved_runs), use_container_width=True)
