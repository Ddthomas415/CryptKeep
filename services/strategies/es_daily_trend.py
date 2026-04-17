"""
services/strategies/es_daily_trend.py

ES Daily Trend v1 — 200-day SMA long/flat strategy.

Signal logic only. All execution, sizing, and halting decisions
are handled by the control kernel (services/control/kernel.py).

Spec: docs/strategies/es_daily_trend_v1.md
Config: configs/strategies/es_daily_trend_v1.yaml
"""
from __future__ import annotations

import math
from typing import Any

from services.logging.app_logger import get_logger
from services.strategies.evidence_logger import EvidenceLogger

_LOG = get_logger("strategy.es_daily_trend")

STRATEGY_ID = "es_daily_trend_v1"
SMA_PERIOD_DEFAULT = 200
ATR_PERIOD_DEFAULT = 20
ATR_STOP_MULT_DEFAULT = 2.0


# ---------------------------------------------------------------------------
# Signal
# ---------------------------------------------------------------------------

def compute_signal(closes: list[float], *, period: int = SMA_PERIOD_DEFAULT) -> str:
    """Return 'long' or 'flat' based on 200-SMA crossover rule.

    Returns 'flat' when history is insufficient.
    """
    if len(closes) < period:
        return "flat"
    sma = sum(closes[-period:]) / period
    return "long" if closes[-1] > sma else "flat"


def compute_sma(closes: list[float], period: int) -> float | None:
    """Return the SMA for the last `period` closes, or None if insufficient data."""
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


# ---------------------------------------------------------------------------
# Regime
# ---------------------------------------------------------------------------

def compute_atr(highs: list[float], lows: list[float], closes: list[float],
                period: int = ATR_PERIOD_DEFAULT) -> float | None:
    """Compute Average True Range over `period` bars."""
    n = min(len(highs), len(lows), len(closes))
    if n < period + 1:
        return None
    trs = []
    for i in range(n - period, n):
        prev_close = closes[i - 1]
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - prev_close),
                 abs(lows[i] - prev_close))
        trs.append(tr)
    return sum(trs) / len(trs) if trs else None


def regime_stability(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    *,
    atr_period: int = ATR_PERIOD_DEFAULT,
    lookback_days: int = 60,
    trending_floor: float = 0.80,
    chop_ceiling: float = 0.60,
    chop_days: int = 5,
    high_vol_ceiling: float = 2.50,
) -> dict[str, Any]:
    """Evaluate regime using ATR ratio.

    ATR ratio = current_ATR / rolling_avg_ATR(lookback_days)

    Returns:
        {
          "regime":       trending | chop | high_vol | insufficient_data
          "atr_ratio":    float or None
          "current_atr":  float or None
          "entry_allowed": bool
          "size_factor":  float (1.0 = full, 0.5 = half, 0.0 = blocked)
          "note":         str
        }
    """
    current_atr = compute_atr(highs, lows, closes, period=atr_period)
    if current_atr is None:
        return {
            "regime": "insufficient_data", "atr_ratio": None, "current_atr": None,
            "entry_allowed": False, "size_factor": 0.0,
            "note": f"insufficient history (need {atr_period + 1} bars minimum)"
        }

    # Compute ATR over the lookback period to get a rolling average
    n = min(len(highs), len(lows), len(closes))
    required = atr_period + lookback_days
    if n < required:
        return {
            "regime": "insufficient_data", "atr_ratio": None, "current_atr": current_atr,
            "entry_allowed": False, "size_factor": 0.0,
            "note": f"need {required} bars for regime detection, have {n}"
        }

    # Rolling ATR values over the lookback window
    atr_values = []
    for offset in range(lookback_days):
        end = n - offset
        h = highs[:end]; l = lows[:end]; c = closes[:end]
        a = compute_atr(h, l, c, period=atr_period)
        if a is not None:
            atr_values.append(a)

    if not atr_values:
        return {
            "regime": "insufficient_data", "atr_ratio": None, "current_atr": current_atr,
            "entry_allowed": False, "size_factor": 0.0,
            "note": "could not compute rolling ATR"
        }

    rolling_avg = sum(atr_values) / len(atr_values)
    atr_ratio = current_atr / rolling_avg if rolling_avg > 0 else 1.0

    # Classify regime
    if atr_ratio > high_vol_ceiling:
        return {
            "regime": "high_vol", "atr_ratio": atr_ratio, "current_atr": current_atr,
            "entry_allowed": False, "size_factor": 0.5,
            "note": f"ATR ratio {atr_ratio:.2f} > high_vol ceiling {high_vol_ceiling}"
        }
    if atr_ratio >= trending_floor:
        return {
            "regime": "trending", "atr_ratio": atr_ratio, "current_atr": current_atr,
            "entry_allowed": True, "size_factor": 1.0,
            "note": f"ATR ratio {atr_ratio:.2f} ≥ trending floor {trending_floor}"
        }
    # Check consecutive chop days — simplified: if current ratio < chop_ceiling, flag
    if atr_ratio < chop_ceiling:
        return {
            "regime": "chop", "atr_ratio": atr_ratio, "current_atr": current_atr,
            "entry_allowed": False, "size_factor": 0.0,
            "note": f"ATR ratio {atr_ratio:.2f} < chop ceiling {chop_ceiling}"
        }
    # In between: allow entries but note borderline
    return {
        "regime": "borderline", "atr_ratio": atr_ratio, "current_atr": current_atr,
        "entry_allowed": True, "size_factor": 0.75,
        "note": f"ATR ratio {atr_ratio:.2f} between chop and trending thresholds"
    }


# ---------------------------------------------------------------------------
# Stop calculation
# ---------------------------------------------------------------------------

def compute_stop(
    entry_price: float,
    current_atr: float,
    *,
    atr_multiplier: float = ATR_STOP_MULT_DEFAULT,
    side: str = "long",
) -> float:
    """Compute hard stop price.

    For long: stop = entry_price − (atr_multiplier × ATR)
    """
    if side == "long":
        return entry_price - (atr_multiplier * current_atr)
    raise ValueError(f"Side '{side}' not supported in v1 (long/flat only)")


# ---------------------------------------------------------------------------
# Sizing
# ---------------------------------------------------------------------------

def compute_position_size(
    total_capital: float,
    entry_price: float,
    stop_price: float,
    *,
    capital_at_risk_pct: float = 0.50,
    max_notional_pct: float = 10.0,
) -> dict[str, Any]:
    """Compute position size from capital at risk and stop distance.

    capital_at_risk_pct: % of total capital to risk at stop (default 0.5%)
    max_notional_pct:    hard cap on notional as % of total capital (default 10%)

    Returns {contracts, notional, capital_at_risk_usd, capped}
    """
    stop_distance = abs(entry_price - stop_price)
    if stop_distance <= 0:
        return {"contracts": 0, "notional": 0.0, "capital_at_risk_usd": 0.0, "capped": False,
                "note": "stop_distance is zero or negative"}

    capital_at_risk_usd = total_capital * (capital_at_risk_pct / 100.0)
    # Number of units where loss at stop = capital_at_risk_usd
    units = capital_at_risk_usd / stop_distance
    notional = units * entry_price
    max_notional = total_capital * (max_notional_pct / 100.0)

    capped = notional > max_notional
    if capped:
        units = max_notional / entry_price
        notional = max_notional
        capital_at_risk_usd = units * stop_distance

    return {
        "contracts": math.floor(units),
        "notional": round(notional, 2),
        "capital_at_risk_usd": round(capital_at_risk_usd, 2),
        "capped": capped,
        "note": "capped at max_notional_pct" if capped else "sized from risk"
    }


# ---------------------------------------------------------------------------
# Full decision
# ---------------------------------------------------------------------------

def decide(
    closes: list[float],
    highs: list[float],
    lows: list[float],
    *,
    total_capital: float = 100_000.0,
    entry_price: float | None = None,
    kernel_metrics: dict[str, float] | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full decision: signal + regime + kernel gate + sizing.

    All execution is logged. All decisions are traceable.
    """
    from services.control.kernel import ControlKernel

    c = cfg or {}
    sma_period = int(c.get("sma_period") or SMA_PERIOD_DEFAULT)
    atr_period = int(c.get("atr_period") or ATR_PERIOD_DEFAULT)
    atr_mult = float(c.get("atr_multiplier") or ATR_STOP_MULT_DEFAULT)
    risk_pct = float(c.get("capital_at_risk_per_trade_pct") or 0.50)
    max_notional_pct = float(c.get("max_position_notional_pct") or 10.0)

    signal = compute_signal(closes, period=sma_period)
    sma_val = compute_sma(closes, sma_period)
    reg = regime_stability(highs, lows, closes, atr_period=atr_period)

    # Kernel gate
    m = dict(kernel_metrics or {})
    if "regime_stability" not in m:
        m["regime_stability"] = reg.get("atr_ratio") or 0.5
    kernel = ControlKernel(STRATEGY_ID)
    kd = kernel.evaluate(m)

    # Sizing (only if signal=long AND regime allows AND kernel allows)
    size = {"contracts": 0, "notional": 0.0, "capital_at_risk_usd": 0.0, "capped": False}
    stop_price = None

    ep = entry_price or (closes[-1] if closes else 0.0)
    current_atr = reg.get("current_atr")

    if (signal == "long"
            and reg["entry_allowed"]
            and kd["new_risk_allowed"]
            and current_atr is not None
            and ep > 0):
        stop_price = compute_stop(ep, current_atr, atr_multiplier=atr_mult)
        size = compute_position_size(
            total_capital, ep, stop_price,
            capital_at_risk_pct=risk_pct,
            max_notional_pct=max_notional_pct,
        )
        # Apply stage cap: capped_live is limited to 1 contract (spec §6 / §7)
        from services.control.deployment_stage import get_current_stage, Stage
        if get_current_stage(STRATEGY_ID) == Stage.CAPPED_LIVE:
            size = dict(size)
            size["contracts"] = min(size["contracts"], 1)
            size["note"] = "capped_live:max_1_contract" 

    result = {
        "strategy_id": STRATEGY_ID,
        "signal": signal,
        "sma_200": sma_val,
        "regime": reg,
        "kernel_action": kd["action"],
        "kernel_stage": kd["stage"],
        "new_risk_allowed": kd["new_risk_allowed"] and reg["entry_allowed"],
        "stop_price": stop_price,
        "sizing": size,
        "reasons": kd["reasons"],
    }

    _LOG.info(
        "es_daily_trend signal=%s regime=%s kernel=%s contracts=%s stage=%s",
        signal, reg["regime"], kd["action"], size["contracts"], kd["stage"],
    )

    # Log signal evidence record
    try:
        ev_logger = EvidenceLogger(STRATEGY_ID)
        from datetime import datetime, timezone
        ev_logger.log_signal(
            timestamp=datetime.now(timezone.utc).isoformat(),
            price=ep,
            sma_200=sma_val,
            atr_ratio=reg.get("atr_ratio"),
            signal_direction=signal,
            regime_flag=reg.get("regime", "unknown"),
            kernel_action=kd["action"],
            entry_allowed=result["new_risk_allowed"],
        )
    except Exception as _ev_err:
        _LOG.warning("evidence_logger failed: %s", _ev_err)

    return result


# ---------------------------------------------------------------------------
# Registry adapter
# ---------------------------------------------------------------------------

def signal_from_ohlcv(
    ohlcv: list[list],
    *,
    sma_period: int = SMA_PERIOD_DEFAULT,
    atr_period: int = ATR_PERIOD_DEFAULT,
) -> dict[str, Any]:
    """Adapter for strategy_registry. Accepts ohlcv rows [ts,o,h,l,c,vol].

    Returns the standard registry signal envelope:
      {ok, action, reason, signal, regime, sma_200, atr_ratio}
    """
    if not ohlcv or len(ohlcv) < sma_period:
        return {"ok": True, "action": "hold", "reason": "insufficient_history",
                "signal": "flat", "regime": "insufficient_data"}

    closes = [float(row[4]) for row in ohlcv]
    highs  = [float(row[2]) for row in ohlcv]
    lows   = [float(row[3]) for row in ohlcv]

    signal = compute_signal(closes, period=sma_period)
    reg    = regime_stability(highs, lows, closes, atr_period=atr_period)
    sma    = compute_sma(closes, sma_period)

    action = "buy" if (signal == "long" and reg["entry_allowed"]) else "hold"
    reason = f"sma200:{signal}:regime:{reg['regime']}"

    # Log every signal call to evidence — this is the production signal path
    # (signal_from_ohlcv is called by strategy_registry from ema_crossover_runner)
    try:
        from datetime import datetime, timezone as _tz
        EvidenceLogger(STRATEGY_ID).log_signal(
            timestamp=datetime.now(_tz.utc).isoformat(),
            price=float(ohlcv[-1][4]) if ohlcv else 0.0,
            sma_200=sma,
            atr_ratio=reg.get("atr_ratio"),
            signal_direction=signal,
            regime_flag=reg.get("regime", "unknown"),
            entry_allowed=reg["entry_allowed"],
        )
    except Exception as _ev_err:
        pass  # evidence logging never blocks signal production

    return {
        "ok":      True,
        "action":  action,
        "reason":  reason,
        "signal":  signal,
        "regime":  reg["regime"],
        "sma_200": sma,
        "atr_ratio": reg.get("atr_ratio"),
        "entry_allowed": reg["entry_allowed"],
    }
