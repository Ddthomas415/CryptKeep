from __future__ import annotations

from typing import Any, Dict, Iterable, List


FEATURE_ORDER: List[str] = [
    "order_reject_rate",
    "ws_lag_ms",
    "venue_latency_ms",
    "realized_volatility",
    "drawdown_pct",
    "pnl_usd",
    "exposure_usd",
    "leverage",
    "side_buy",
    "side_sell",
]


def _f(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return float(default)
        return float(v)
    except Exception:
        return float(default)


def build_feature_map(context: Dict[str, Any] | None) -> Dict[str, float]:
    ctx = dict(context or {})
    telemetry = dict(ctx.get("telemetry") or {})
    side = str(ctx.get("side") or telemetry.get("side") or "").strip().lower()

    out: Dict[str, float] = {
        "order_reject_rate": _f(
            telemetry.get("order_reject_rate", ctx.get("order_reject_rate", 0.0)), 0.0
        ),
        "ws_lag_ms": _f(telemetry.get("ws_lag_ms", ctx.get("ws_lag_ms", 0.0)), 0.0),
        "venue_latency_ms": _f(
            telemetry.get("venue_latency_ms", ctx.get("venue_latency_ms", 0.0)), 0.0
        ),
        "realized_volatility": _f(
            telemetry.get("realized_volatility", ctx.get("realized_volatility", 0.0)), 0.0
        ),
        "drawdown_pct": _f(telemetry.get("drawdown_pct", ctx.get("drawdown_pct", 0.0)), 0.0),
        "pnl_usd": _f(telemetry.get("pnl_usd", ctx.get("pnl_usd", 0.0)), 0.0),
        "exposure_usd": _f(telemetry.get("exposure_usd", ctx.get("exposure_usd", 0.0)), 0.0),
        "leverage": _f(telemetry.get("leverage", ctx.get("leverage", 0.0)), 0.0),
        "side_buy": 1.0 if side == "buy" else 0.0,
        "side_sell": 1.0 if side == "sell" else 0.0,
    }
    return out


def vectorize_features(
    feature_map: Dict[str, float], feature_order: Iterable[str] | None = None
) -> List[float]:
    order = list(feature_order or FEATURE_ORDER)
    return [float(feature_map.get(name, 0.0)) for name in order]

