# HS1: Strategy config validator (Phase 228)
from __future__ import annotations

from typing import Any, Dict, List


SUPPORTED = {"ema_cross", "mean_reversion_rsi", "breakout_donchian"}


def _num(v: Any) -> bool:
    return isinstance(v, (int, float))


def validate_strategy_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    c = dict(cfg or {})
    errors: List[str] = []
    warnings: List[str] = []
    st = c.get("strategy") if isinstance(c.get("strategy"), dict) else {}
    name = str(st.get("name") or "ema_cross").strip()
    if name not in SUPPORTED:
        errors.append(f"unsupported_strategy:{name}")
    if "trade_enabled" in st and not isinstance(st.get("trade_enabled"), bool):
        errors.append("strategy.trade_enabled must be bool")

    if name == "ema_cross":
        if "ema_fast" in st and not _num(st.get("ema_fast")):
            errors.append("strategy.ema_fast must be number")
        if "ema_slow" in st and not _num(st.get("ema_slow")):
            errors.append("strategy.ema_slow must be number")
        if _num(st.get("ema_fast")) and _num(st.get("ema_slow")):
            if int(st["ema_fast"]) >= int(st["ema_slow"]):
                warnings.append("ema_fast is >= ema_slow")
    elif name == "mean_reversion_rsi":
        for k in ("rsi_len", "rsi_buy", "rsi_sell", "sma_len"):
            if k in st and not _num(st.get(k)):
                errors.append(f"strategy.{k} must be number")
    elif name == "breakout_donchian":
        if "donchian_len" in st and not _num(st.get("donchian_len")):
            errors.append("strategy.donchian_len must be number")

    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings, "strategy": name}
