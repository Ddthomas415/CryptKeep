from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from services.admin.master_read_only import is_master_read_only
from services.config_loader import load_user_config
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


def _truthy(v: Any) -> bool:
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


async def decide_order(
    venue: str,
    symbol_norm: str,
    delta_qty: float,
    overrides: Dict[str, Any] | None = None,
) -> RouterDecision:
    scope = f"{venue}:{symbol_norm}"
    _cfg = load_user_config()
    ov = overrides or {}
    ov_router = ov.get("router") or {}

    side = "buy" if delta_qty > 0 else "sell" if delta_qty < 0 else "none"
    qty = abs(float(delta_qty))
    limit_price: Optional[float] = None

    meta: Dict[str, Any] = {"scope": scope}

    ro_state = is_master_read_only()
    ro_on = bool(ro_state[0]) if isinstance(ro_state, tuple) else bool(ro_state)
    if ro_on:
        return RouterDecision(False, "master_read_only", "none", 0.0, "none", None, meta)

    # Safety gates (deterministic). Executors also enforce.
    try:
        gates = load_gates()
        store = ExecutionGuardStoreSQLite()
        ok_s, why_s = should_allow_order(venue, symbol_norm, side, float(qty), float(limit_price or 0.0), gates, store)
    except Exception:
        ok_s, why_s = True, "safety_check_error_ignored"

    meta["safety_ok"] = bool(ok_s)
    meta["safety_reason"] = str(why_s)
    if not ok_s:
        return RouterDecision(False, f"safety:{why_s}", "none", 0.0, "none", None, meta)

    # Optional AI gate (decision-support first, strict only if explicitly enabled).
    ai_cfg = _cfg.get("ai_engine") if isinstance(_cfg.get("ai_engine"), dict) else {}
    ai_enabled = bool(
        _truthy(os.environ.get("CBP_AI_ENGINE_ENABLED"))
        or bool(ai_cfg.get("enabled", False))
        or bool(ov_router.get("use_ai_engine", False))
    )
    ai_strict = bool(
        _truthy(os.environ.get("CBP_AI_ENGINE_STRICT"))
        or bool(ai_cfg.get("strict", False))
        or bool(ov_router.get("ai_strict", False))
    )
    if ai_enabled and side in ("buy", "sell"):
        try:
            from services.ai_engine.signal_service import AISignalService

            model_path = str(os.environ.get("CBP_AI_MODEL_PATH") or ai_cfg.get("model_path") or "")
            buy_th = float(
                os.environ.get("CBP_AI_BUY_THRESHOLD")
                or ov_router.get("ai_buy_th", ai_cfg.get("buy_threshold", 0.55))
            )
            sell_th = float(
                os.environ.get("CBP_AI_SELL_THRESHOLD")
                or ov_router.get("ai_sell_th", ai_cfg.get("sell_threshold", 0.45))
            )
            ai_context = dict(ov.get("ai_context") or {})
            ai_context.setdefault("side", side)
            ai_context.setdefault("venue", venue)
            ai_context.setdefault("symbol", symbol_norm)
            ai_context.setdefault("qty", float(qty))
            ai = AISignalService(model_path=model_path).evaluate(
                side=side,
                context=ai_context,
                buy_threshold=buy_th,
                sell_threshold=sell_th,
            )
            meta["ai"] = ai.to_dict()
            if not ai.ok:
                return RouterDecision(False, f"ai_gate:{ai.reason}", "none", 0.0, "none", None, meta)
        except Exception as e:
            meta["ai"] = {"ok": True, "reason": f"ai_error_ignored:{type(e).__name__}"}
            if ai_strict:
                return RouterDecision(False, f"ai_gate:error:{type(e).__name__}", "none", 0.0, "none", None, meta)

    # Optional proba gate (explicit toggle)
    try:
        from services.feature_gate import proba_gate

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
            meta["proba"] = {"name": gv.feature_name, "val": gv.feature_value}
            if not gv.ok:
                return RouterDecision(False, f"proba_gate:{gv.reason}", "none", 0.0, "none", None, meta)
    except Exception:
        pass

    # Simulated decision (in real app, compute price, qty, etc.)
    limit_price = 60000.0  # placeholder

    return RouterDecision(True, "ok", side, qty, "limit", limit_price, meta)


if __name__ == "__main__":
    print("Live router loaded")
