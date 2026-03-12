from __future__ import annotations

from typing import Any


def _clip(value: Any, *, low: float = 0.0, high: float = 1.0, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = default
    return max(low, min(high, numeric))


def _normalize_regime_label(value: Any) -> str:
    label = str(value or "").strip().lower()
    if not label:
        return "unknown"
    if label in {"safe", "trend_up", "risk_on", "allow_trading"}:
        return "trend_up"
    if label in {"caution", "volatile", "event_driven", "macro_risk_off"}:
        return "event_driven"
    if label in {"danger", "degraded", "halt_new_positions", "full_stop", "panic"}:
        return "risk_off"
    return label


def _regime_fit(signal: str, regime: str) -> float:
    normalized_signal = str(signal or "hold").strip().lower()
    normalized_regime = _normalize_regime_label(regime)
    if normalized_signal in {"buy", "research"}:
        if normalized_regime == "trend_up":
            return 0.82
        if normalized_regime == "event_driven":
            return 0.64
        if normalized_regime == "risk_off":
            return 0.38
    if normalized_signal in {"sell", "reduce"}:
        if normalized_regime == "risk_off":
            return 0.8
        if normalized_regime == "event_driven":
            return 0.66
        if normalized_regime == "trend_up":
            return 0.44
    return 0.52


def _tradeability(price: Any, spread: Any, volume_24h: Any) -> float:
    price_value = _clip(price, low=0.0, high=10_000_000.0, default=0.0)
    spread_value = _clip(spread, low=0.0, high=10_000_000.0, default=0.0)
    volume_value = _clip(volume_24h, low=0.0, high=10_000_000_000.0, default=0.0)

    spread_ratio = (spread_value / price_value) if price_value > 0 else 0.0
    spread_score = 1.0 - _clip(spread_ratio / 0.02, default=0.0)
    volume_score = _clip(volume_value / 25_000_000.0, default=0.0)
    return round((spread_score * 0.55) + (volume_score * 0.45), 3)


def _setup_quality(reliability: dict[str, Any] | None) -> float:
    payload = reliability if isinstance(reliability, dict) else {}
    hit_rate = _clip(payload.get("hit_rate"), default=0.5)
    scored = _clip(payload.get("n_scored"), low=0.0, high=200.0, default=0.0) / 200.0
    avg_return = _clip(payload.get("avg_return_bps"), low=-5000.0, high=5000.0, default=0.0)
    avg_return_score = _clip((avg_return + 500.0) / 1000.0, default=0.5)
    return round((hit_rate * 0.55) + (scored * 0.15) + (avg_return_score * 0.30), 3)


def build_opportunity_snapshot(
    *,
    signal_row: dict[str, Any] | None,
    market_row: dict[str, Any] | None,
    reliability: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    signal_payload = signal_row if isinstance(signal_row, dict) else {}
    market_payload = market_row if isinstance(market_row, dict) else {}
    summary_payload = summary if isinstance(summary, dict) else {}

    signal = str(signal_payload.get("signal") or "hold")
    confidence = _clip(signal_payload.get("confidence"), default=0.0)
    move_24h = _clip(market_payload.get("change_24h_pct"), low=-1000.0, high=1000.0, default=0.0)
    regime = _normalize_regime_label(
        signal_payload.get("regime")
        or summary_payload.get("current_regime")
        or summary_payload.get("risk_status")
    )
    regime_fit = _regime_fit(signal, regime)
    tradeability = _tradeability(
        market_payload.get("price"),
        market_payload.get("spread"),
        market_payload.get("volume_24h"),
    )
    setup_quality = _setup_quality(reliability)

    expected_return = round((move_24h / 100.0) * (0.4 + (confidence * 0.9)), 4)
    risk_penalty = round((1.0 - regime_fit) * 0.28 + (1.0 - tradeability) * 0.22, 3)
    opportunity_score = round(
        max(
            0.0,
            min(
                1.0,
                (confidence * 0.34)
                + (regime_fit * 0.24)
                + (tradeability * 0.18)
                + (setup_quality * 0.16)
                + (_clip(abs(move_24h) / 10.0, default=0.0) * 0.08)
                - risk_penalty,
            ),
        ),
        3,
    )

    if opportunity_score >= 0.72:
        category = "top_opportunity"
    elif opportunity_score >= 0.56:
        category = "watch_closely"
    elif opportunity_score >= 0.42:
        category = "needs_confirmation"
    else:
        category = "avoid_for_now"

    return {
        "regime": regime,
        "regime_fit": regime_fit,
        "tradeability": tradeability,
        "setup_quality": setup_quality,
        "expected_return": expected_return,
        "risk_penalty": risk_penalty,
        "opportunity_score": opportunity_score,
        "category": category,
    }
