
from __future__ import annotations

import os

from typing import Any

from services.market_data.regime_detector import detect_regime
from services.market_data.volume_surge_detector import detect_volume_surge
from services.execution.outcome_summary import recent_strategy_regime_score
from services.signals.candidate_advisor import get_top_candidate


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

    if regime == "trending_up":
        ranked = ["pullback_recovery", "momentum", "breakout_volume", "breakout_donchian", default_strategy, "ema_cross"]
        reason = "regime_trending_up"
    elif regime == "ranging":
        ranked = ["mean_reversion_rsi", "gap_fill", "volatility_reversal", default_strategy, "ema_cross"]
        reason = "regime_ranging"
    elif regime == "high_volatility":
        ranked = ["volatility_reversal", "gap_fill", "momentum", default_strategy, "ema_cross"]
        reason = "regime_high_volatility"
    elif regime == "low_volatility":
        try_pullback = False
        closes = [_safe_float(r[4], 0.0) for r in (ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 5]
        if len(closes) >= 50:
            current = closes[-1]
            prev = closes[-2] if len(closes) >= 2 else current
            trend_sma = sum(closes[-50:]) / 50.0 if len(closes) >= 50 else 0.0
            recent_high = max(closes[-50:]) if len(closes) >= 50 else current
            pullback_pct = ((recent_high - current) / recent_high * 100.0) if recent_high > 0 else 0.0
            rebound_pct = ((current - prev) / prev * 100.0) if prev > 0 else 0.0
            trend_gap_pct = ((trend_sma - current) / trend_sma * 100.0) if trend_sma > 0 else 999.0

            try_pullback = (
                2.0 <= pullback_pct <= 12.0
                and rebound_pct >= 0.0
                and trend_gap_pct <= 1.5
            )

        if try_pullback:
            ranked = ["pullback_recovery", "mean_reversion_rsi", "breakout_donchian", default_strategy, "ema_cross"]
            reason = "regime_low_volatility_pullback_recovery"
        else:
            ranked = ["mean_reversion_rsi", "breakout_donchian", default_strategy, "ema_cross"]
            reason = "regime_low_volatility"
    else:
        ranked = [default_strategy, "ema_cross"]
        reason = "regime_unknown"

    ranked = [x for i, x in enumerate(ranked) if x and x not in ranked[:i]]

    scored = []
    total_reasons = {}
    n = len(ranked)

    for i, name in enumerate(ranked):
        base_score = float((n - i) * 10)

        if vol_surge and name == "breakout_volume":
            base_score += 8.0
        elif vol_surge and name == "momentum":
            base_score += 4.0

        evidence = recent_strategy_regime_score(name, regime, limit=200, min_count=3)
        evidence_score = _safe_float(evidence.get("score"), 0.0)

        total = base_score + evidence_score
        scored.append((name, total, base_score, evidence_score, evidence))
        total_reasons[name] = f"{reason}|base={base_score:.1f}|evidence={evidence_score:.2f}"

    use_candidate_advisor = str(os.environ.get("CBP_USE_CANDIDATE_ADVISOR", "")).strip().lower() in ("1", "true", "yes", "on")
    if use_candidate_advisor:
        try:
            top = get_top_candidate(min_score=35.0)
            if (
                isinstance(top, dict)
                and str(top.get("symbol") or "") == str(os.environ.get("CBP_SYMBOLS") or "")
                and str(top.get("preferred_strategy") or "")
            ):
                preferred = str(top.get("preferred_strategy"))
                advisor_reason = f"candidate_advisor:{top.get('trade_type')}:{top.get('mapping_reason')}"
                scored_names = {name for name, *_ in scored}
                if preferred not in scored_names:
                    # Preferred strategy was not in this regime's ranked list —
                    # inject it with a base score of 0 so the +100 boost can win.
                    scored.append((preferred, 0.0, 0.0, 0.0, {}))
                    total_reasons[preferred] = advisor_reason
                patched = []
                for name, total, base, ev_score, ev in scored:
                    if name == preferred:
                        total = round(float(total) + 100.0, 4)
                        total_reasons[name] = advisor_reason
                    patched.append((name, total, base, ev_score, ev))
                scored = patched
        except Exception:
            pass

    scored.sort(key=lambda x: x[1], reverse=True)
    chosen, chosen_total, _, _, _ = scored[0]

    return {
        "selected_strategy": chosen,
        "selected_strategy_reason": total_reasons.get(chosen),
        "regime": regime,
        "regime_info": regime_info,
        "volume_surge": vol_surge,
        "volume_ratio": round(vol_ratio, 2),
        "volume_info": volume_info,
        "ranked_candidates": [x[0] for x in scored],
        "candidate_scores": [
            {
                "strategy": name,
                "score": round(total, 4),
                "base_score": round(base, 4),
                "evidence_score": round(ev_score, 4),
                "evidence_count": int((ev or {}).get("count", 0)),
            }
            for name, total, base, ev_score, ev in scored
        ],
    }
