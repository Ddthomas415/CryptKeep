from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(dict(out.get(k) or {}), v)
        else:
            out[k] = deepcopy(v)
    return out


BUNDLES: Dict[str, Dict[str, Any]] = {
    "PAPER_SAFE_DEFAULTS": {
        "runtime": {"mode": "paper"},
        "marketdata": {
            "timeframe": "1m",
            "ohlcv_limit": 400,
            "loop_sleep_sec": 15.0,
            "ws_enabled": False,
            "ws_use_for_trading": False,
            "ws_block_on_stale": True,
        },
        "ws_health": {
            "enabled": False,
            "auto_switch_enabled": False,
            "min_score": 0.7,
            "bad_for_sec": 20.0,
            "good_for_sec": 30.0,
            "require_ticker": True,
        },
        "risk": {
            "enabled": True,
            "max_risk_per_trade_quote": 10.0,
            "min_order_quote": 10.0,
            "max_order_quote": 100.0,
            "max_portfolio_exposure_quote": 800.0,
        },
        "paper_execution": {"fee_bps": 10.0, "slippage_bps": 5.0},
    },
    "STRAT_MEAN_REVERSION_5M": {
        "runtime": {"mode": "paper"},
        "marketdata": {
            "timeframe": "5m",
            "ohlcv_limit": 500,
            "loop_sleep_sec": 10.0,
            "ws_enabled": True,
            "ws_use_for_trading": True,
            "ws_block_on_stale": False,
        },
        "ws_health": {
            "enabled": True,
            "auto_switch_enabled": True,
            "min_score": 0.70,
            "bad_for_sec": 15.0,
            "good_for_sec": 30.0,
            "require_ticker": True,
        },
        "strategy": {
            "name": "mean_reversion_rsi",
            "trade_enabled": True,
            "rsi_len": 14,
            "rsi_buy": 30.0,
            "rsi_sell": 70.0,
            "sma_len": 50,
        },
        "risk": {
            "enabled": True,
            "max_risk_per_trade_quote": 20.0,
            "min_order_quote": 10.0,
            "max_order_quote": 250.0,
            "max_portfolio_exposure_quote": 1500.0,
        },
        "paper_execution": {"fee_bps": 10.0, "slippage_bps": 5.0},
    },
    "STRAT_BREAKOUT_5M": {
        "runtime": {"mode": "paper"},
        "marketdata": {
            "timeframe": "5m",
            "ohlcv_limit": 700,
            "loop_sleep_sec": 10.0,
            "ws_enabled": True,
            "ws_use_for_trading": True,
            "ws_block_on_stale": False,
        },
        "ws_health": {
            "enabled": True,
            "auto_switch_enabled": True,
            "min_score": 0.70,
            "bad_for_sec": 15.0,
            "good_for_sec": 30.0,
            "require_ticker": True,
        },
        "strategy": {"name": "breakout_donchian", "trade_enabled": True, "donchian_len": 20},
        "risk": {
            "enabled": True,
            "max_risk_per_trade_quote": 20.0,
            "min_order_quote": 10.0,
            "max_order_quote": 250.0,
            "max_portfolio_exposure_quote": 1500.0,
        },
        "paper_execution": {"fee_bps": 10.0, "slippage_bps": 5.0},
    },
}


def list_bundles() -> list[str]:
    return sorted(BUNDLES.keys())


def get_bundle(name: str) -> Dict[str, Any] | None:
    v = BUNDLES.get(str(name))
    if v is None:
        return None
    return deepcopy(v)


def register_bundle(name: str, bundle: Dict[str, Any], *, replace: bool = False) -> Dict[str, Any]:
    key = str(name).strip()
    if not key:
        raise ValueError("bundle name is required")
    if key in BUNDLES and not replace:
        raise ValueError(f"bundle already exists: {key}")
    BUNDLES[key] = deepcopy(dict(bundle or {}))
    return deepcopy(BUNDLES[key])


def merge_bundle(base_cfg: Dict[str, Any], bundle_name: str, *, overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    b = get_bundle(bundle_name)
    if b is None:
        raise KeyError(f"unknown bundle: {bundle_name}")
    merged = _deep_merge(dict(base_cfg or {}), b)
    if isinstance(overrides, dict) and overrides:
        merged = _deep_merge(merged, overrides)
    return merged


def apply_bundle(config: Dict[str, Any], bundle_name: str, *, overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Compatibility alias for callers that use apply-style naming."""
    return merge_bundle(config, bundle_name, overrides=overrides)


__all__ = [
    "BUNDLES",
    "list_bundles",
    "get_bundle",
    "register_bundle",
    "merge_bundle",
    "apply_bundle",
]
