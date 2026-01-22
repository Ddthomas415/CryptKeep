from services.admin.master_read_only import is_master_read_only
from services.risk.risk_block_logger import record_block
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
from services.config_loader import load_user_config
from services.feature_gate import proba_gate
from services.execution.safety import load_gates, should_allow_order
from storage.execution_guard_store_sqlite import ExecutionGuardStoreSQLite

@dataclass(frozen=True)
class RouterDecision:
    allowed: bool
    reason: str
    side: str
    qty: float
    order_type: str
    limit_price: Optional[float]
    meta: Dict[str, Any]

async def decide_order(
    venue: str,
    symbol_norm: str,
    delta_qty: float,
    overrides: Dict[str, Any] | None = None,
) -> RouterDecision:
    scope = f"{venue}:{symbol_norm}"
    cfg = load_user_config()
    ov = overrides or {}
    ov_router = ov.get("router") or {}
    side = "buy" if delta_qty > 0 else "sell" if delta_qty < 0 else "none"
    qty = abs(float(delta_qty))

    # Safety gates (deterministic). Executors also enforce.
try:
    gates = load_gates()
    store = ExecutionGuardStoreSQLite()
    ok_s, why_s = should_allow_order(venue, symbol_norm, side, float(qty), float(limit_price), gates, store)
except Exception:
    ok_s, why_s = True, "safety_check_error_ignored"
# attach safety info to meta
try:
    if isinstance(meta, dict):
        meta["safety_ok"] = bool(ok_s)
        meta["safety_reason"] = str(why_s)
except Exception:
    pass
    try:
        gates = load_gates()
        store = ExecutionGuardStoreSQLite()
        ok_s, why_s = should_allow_order(venue, symbol_norm, side, qty, 0.0, gates, store)  # price placeholder
        if not ok_s:
            return RouterDecision(False, f"safety:{why_s}", "none", 0.0, "none", None, {"safety_ok": False, "safety_reason": why_s})
    except Exception:
        ok_s, why_s = True, "safety_check_error_ignored"

    # Optional proba gate (explicit toggle)
    try:
        env_use = (os.environ.get("CBP_USE_FUSED_PROBA", "") or "").strip().lower() in ("1", "true", "yes", "on")
        use_fused = bool(env_use or ov_router.get("use_fused_proba", False))
        if use_fused:
            gv = proba_gate(
                scope=scope,
                side=side,
                use_fused=use_fused,
                buy_th=float(ov_router.get("proba_buy_th", 0.55)),
                sell_th=float(ov_router.get("proba_sell_th", 0.45)),
                strict=bool(int(os.environ.get("CBP_PROBA_STRICT", "0") or "0")),
            )
            if not gv.ok:
                return RouterDecision(False, f"proba_gate:{gv.reason}", "none", 0.0, "none", None, {"safety_ok": ok_s, "safety_reason": why_s, "proba": {"name": gv.feature_name, "val": gv.feature_value}})
    except Exception:
        pass

    # Simulated decision (in real app, compute price, qty, etc.)
    limit_price = 60000.0  # placeholder

    meta = {
        "scope": scope,
        "safety_ok": bool(ok_s),
        "safety_reason": str(why_s),
    }

    return RouterDecision(True, "ok", side, qty, "limit", limit_price, meta)

if __name__ == "__main__":
    print("Live router loaded")
