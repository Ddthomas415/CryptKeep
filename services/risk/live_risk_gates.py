from __future__ import annotations

# CBP_LIVE_RISK_GATES_CANONICAL
#
# Import chain (fully documented):
#
#   services/execution/risk_gates.py       → imports from THIS shim
#   services/risk/killswitch.py            → imports LiveGateDB from THIS shim
#   services/execution/_executor_submit.py → imports DIRECTLY from phase82
#   services/execution/_executor_shared.py → imports DIRECTLY from phase82
#   services/execution/_executor_reconcile.py → imports DIRECTLY from phase82
#
# Canonical implementation: live_risk_gates_phase82.py
# This shim is a re-export layer ONLY — no logic lives here.
# All new code must import from live_risk_gates_phase82 directly.
#
# To collapse this shim:
#   1. Update services/execution/risk_gates.py and services/risk/killswitch.py
#      to import from live_risk_gates_phase82 directly.
#   2. Delete this file.
#   3. Add "live_risk_gates.py must not exist" to a structural test.

from services.risk.live_risk_gates_phase82 import (  # noqa: F401
    LiveRiskLimits,
    LiveGateDB,
    LiveRiskGates,
    _utc_day_key,
    _killswitch_file_on,
    phase83_incr_trade_counter,
)
