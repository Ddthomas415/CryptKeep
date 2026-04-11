from __future__ import annotations

from typing import Any

from services.market_data.regime_detector import detect_regime
from services.market_data.volume_surge_detector import detect_volume_surge


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def select_strategy(
    *,
    default_strategy: str,
    ohlcv: list,
) -> dict[str, Any]:
    regime_info = detect_regime(ohlcv) if ohlcv else {"regime": "unknown"}
    volume_info = detect_volume_surge(ohlcv) if ohlcv else {"surge": False, "ratio": 1.0}

    regime = str(regime_info.get("regime") or "unknown")
    vol_surge = bool(volume_info.get("surge"))
    vol_ratio = _safe_float(volume_info.get("ratio"), 1.0)

    ranked: list[str]
    reason: str

    if regime == "trending_up":
        ranked = ["momentum", "breakout_volume", "breakout_donchian", default_strategy, "ema_cross"]
        reason = "regime_trending_up"
    elif regime == "ranging":
        ranked = ["mean_reversion_rsi", "gap_fill", "volatility_reversal", default_strategy, "ema_cross"]
        reason = "regime_ranging"
    elif regime == "high_volatility":
        ranked = ["volatility_reversal", "gap_fill", "momentum", default_strategy, "ema_cross"]
        reason = "regime_high_volatility"
    elif regime == "low_volatility":
        ranked = ["mean_reversion_rsi", "breakout_donchian", default_strategy, "ema_cross"]
        reason = "regime_low_volatility"
    else:
        ranked = [default_strategy, "ema_cross"]
        reason = "regime_unknown"

    if vol_surge and "breakout_volume" in ranked:
        ranked = ["breakout_volume"] + [x for x in ranked if x != "breakout_volume"]
        reason += "|volume_surge"

    chosen = next((x for x in ranked if x), default_strategy or "ema_cross")

    return {
        "selected_strategy": chosen,
        "selected_strategy_reason": reason,
        "regime": regime,
        "regime_info": regime_info,
        "volume_surge": vol_surge,
        "volume_ratio": round(vol_ratio, 2),
        "volume_info": volume_info,
        "ranked_candidates": ranked,
    }
