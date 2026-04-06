from __future__ import annotations

# CBP_KILLSWITCH_CANONICAL
# Compatibility shim — canonical implementation is killswitch.py.
# killswitch.py now imports from live_risk_gates.py which itself
# re-exports from live_risk_gates_phase82.py.

from services.risk.killswitch import KillSwitch, is_on, snapshot  # noqa: F401
