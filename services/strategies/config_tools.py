from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Tuple

from services.strategies.presets import apply_preset
from services.strategies.validation import validate_strategy_config


_SUPPORTED = {"ema_cross", "mean_reversion_rsi", "breakout_donchian"}
_INT_FIELDS = {
    "ema_cross": ("ema_fast", "ema_slow"),
    "mean_reversion_rsi": ("rsi_len", "sma_len"),
    "breakout_donchian": ("donchian_len",),
}
_FLOAT_FIELDS = {
    "ema_cross": (),
    "mean_reversion_rsi": ("rsi_buy", "rsi_sell"),
    "breakout_donchian": (),
}


def _name(name: str) -> str:
    return str(name or "").strip()


def supported_strategies() -> list[str]:
    return sorted(_SUPPORTED)


def build_strategy_block(
    *,
    name: str,
    trade_enabled: bool = True,
    params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    n = _name(name)
    if n not in _SUPPORTED:
        raise ValueError(f"unsupported_strategy:{n}")
    p = dict(params or {})
    out: Dict[str, Any] = {"name": n, "trade_enabled": bool(trade_enabled)}

    for k in _INT_FIELDS.get(n, ()):
        if k in p and p.get(k) is not None:
            out[k] = int(p[k])
    for k in _FLOAT_FIELDS.get(n, ()):
        if k in p and p.get(k) is not None:
            out[k] = float(p[k])
    return out


def apply_strategy_block(cfg: Dict[str, Any], strategy_block: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(dict(cfg or {}))
    out["strategy"] = deepcopy(dict(strategy_block or {}))
    return out


def validate_cfg(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return validate_strategy_config(dict(cfg or {}))


def apply_preset_and_validate(cfg: Dict[str, Any], preset_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = apply_preset(dict(cfg or {}), str(preset_name))
    vr = validate_cfg(out)
    return out, vr
