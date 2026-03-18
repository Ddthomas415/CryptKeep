# HS1: Strategy config validator (Phase 228)
from __future__ import annotations

from typing import Any, Dict, List


SUPPORTED = {"ema_cross", "mean_reversion_rsi", "breakout_donchian"}


def _num(v: Any) -> bool:
    return isinstance(v, (int, float))


def _bool(v: Any) -> bool:
    return isinstance(v, bool)


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
        for k in ("ema_fast", "ema_slow", "filter_window", "min_volatility_pct", "min_volume_ratio", "min_trend_efficiency", "min_cross_gap_pct"):
            if k in st and not _num(st.get(k)):
                errors.append(f"strategy.{k} must be number")
        if _num(st.get("ema_fast")) and _num(st.get("ema_slow")):
            if int(st["ema_fast"]) >= int(st["ema_slow"]):
                warnings.append("ema_fast is >= ema_slow")
    elif name == "mean_reversion_rsi":
        for k in ("rsi_len", "rsi_buy", "rsi_sell", "sma_len", "filter_window", "max_volatility_pct", "min_volume_ratio", "max_trend_efficiency", "max_sma_distance_pct"):
            if k in st and not _num(st.get(k)):
                errors.append(f"strategy.{k} must be number")
        if "require_reversal_confirmation" in st and not _bool(st.get("require_reversal_confirmation")):
            errors.append("strategy.require_reversal_confirmation must be bool")
    elif name == "breakout_donchian":
        for k in ("donchian_len", "filter_window", "min_volatility_pct", "min_volume_ratio", "min_trend_efficiency", "min_channel_width_pct", "breakout_buffer_pct"):
            if k in st and not _num(st.get(k)):
                errors.append(f"strategy.{k} must be number")
        if "require_directional_confirmation" in st and not _bool(st.get("require_directional_confirmation")):
            errors.append("strategy.require_directional_confirmation must be bool")

    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings, "strategy": name}
