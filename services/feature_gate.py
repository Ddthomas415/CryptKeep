from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GateValue:
    ok: bool
    reason: str
    feature_name: str
    feature_value: float


def proba_gate(
    *,
    scope: str,
    side: str,
    use_fused: bool,
    buy_th: float = 0.55,
    sell_th: float = 0.45,
    strict: bool = False,
) -> GateValue:
    _ = scope
    if not bool(use_fused):
        return GateValue(ok=True, reason="disabled", feature_name="fused_proba", feature_value=0.5)

    raw = (os.environ.get("CBP_FUSED_PROBA", "") or "").strip()
    if not raw:
        if strict:
            return GateValue(ok=False, reason="missing_fused_proba", feature_name="fused_proba", feature_value=0.0)
        prob = 0.5
    else:
        try:
            prob = float(raw)
        except Exception:
            if strict:
                return GateValue(ok=False, reason="invalid_fused_proba", feature_name="fused_proba", feature_value=0.0)
            prob = 0.5

    prob = max(0.0, min(1.0, float(prob)))
    action = str(side or "").strip().lower()
    if action == "buy":
        ok = prob >= float(buy_th)
        return GateValue(ok=ok, reason=("ok" if ok else "below_buy_threshold"), feature_name="fused_proba", feature_value=prob)
    if action == "sell":
        ok = prob <= float(sell_th)
        return GateValue(ok=ok, reason=("ok" if ok else "above_sell_threshold"), feature_name="fused_proba", feature_value=prob)
    return GateValue(ok=True, reason="non_entry_action", feature_name="fused_proba", feature_value=prob)

