from __future__ import annotations

import streamlit as st

from dashboard.auth_gate import require_authenticated_role
from services.backtest.selector_run_store import load_selector_runs, summarize_selector_runs_by_preset
from services.backtest.backtest_run_store import load_historical_selector_runs, summarize_historical_runs_by_preset

AUTH_STATE = require_authenticated_role("VIEWER")
CURRENT_ROLE = str(AUTH_STATE.get("role") or "VIEWER")

st.title("Preset Comparison")
st.caption("Compare current selector winners versus historical selector winners side by side.")

current_rows = summarize_selector_runs_by_preset(load_selector_runs(limit=200))
historical_rows = summarize_historical_runs_by_preset(load_historical_selector_runs(limit=200))

hist_map = {str(r.get("preset_name") or ""): r for r in historical_rows}
all_presets = sorted(set([str(r.get("preset_name") or "") for r in current_rows] + [str(r.get("preset_name") or "") for r in historical_rows]))

joined = []
for preset in all_presets:
    c = next((r for r in current_rows if str(r.get("preset_name") or "") == preset), {})
    h = hist_map.get(preset, {})
    joined.append({
        "preset_name": preset,
        "current_runs": c.get("runs"),
        "current_avg_delta_avg_return_pct": c.get("avg_delta_avg_return_pct"),
        "current_avg_delta_hit_rate": c.get("avg_delta_hit_rate"),
        "current_avg_delta_total_return_pct": c.get("avg_delta_total_return_pct"),
        "historical_runs": h.get("runs"),
        "historical_avg_delta_avg_return_pct": h.get("avg_delta_avg_return_pct"),
        "historical_avg_delta_hit_rate": h.get("avg_delta_hit_rate"),
        "historical_avg_delta_total_return_pct": h.get("avg_delta_total_return_pct"),
    })

joined.sort(
    key=lambda r: (
        float(r.get("historical_avg_delta_avg_return_pct") or 0.0),
        float(r.get("current_avg_delta_avg_return_pct") or 0.0),
    ),
    reverse=True,
)

c0, c1 = st.columns(2)
c0.metric("Current Presets", len(current_rows))
c1.metric("Historical Presets", len(historical_rows))

st.subheader("Side-by-Side Preset Comparison")
st.dataframe(joined, use_container_width=True)

st.subheader("Current Snapshot Summary")
st.dataframe(current_rows, use_container_width=True)

st.subheader("Historical Summary")
st.dataframe(historical_rows, use_container_width=True)
