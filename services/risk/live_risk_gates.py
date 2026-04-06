from __future__ import annotations

# CBP_LIVE_RISK_GATES_CANONICAL
# This module is a compatibility shim. The canonical implementation is
# live_risk_gates_phase82.py. All new code should import from there directly.
# This shim exists so legacy importers (killswitch.py, live_safety_state.py)
# continue to work without a mass import refactor.

from services.risk.live_risk_gates_phase82 import (  # noqa: F401
    LiveRiskLimits,
    LiveGateDB,
    LiveRiskGates,
    _utc_day_key,
    _killswitch_file_on,
    phase83_incr_trade_counter,
)
