
from __future__ import annotations

import math
from typing import Any

from services.market_data.local_data_reader import _load_local_ohlcv
from services.market_data.composite_ranker import build_ranker_config
from services.market_data.regime_detector import detect_regime


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _closes(rows: list[list[Any]]) -> list[float]:
    return [_safe_float(r[4], 0.0) for r in rows if isinstance(r, (list, tuple)) and len(r) >= 5]


def _volumes(rows: list[list[Any]]) -> list[float]:
    return [_safe_float(r[5], 0.0) for r in rows if isinstance(r, (list, tuple)) and len(r) >= 6]


def _window_return_pct(closes: list[float], entry_idx: int, forward_bars: int) -> float:
    if entry_idx < 0 or entry_idx + forward_bars >= len(closes):
        return 0.0
    entry = _safe_float(closes[entry_idx], 0.0)
    exit_ = _safe_float(closes[entry_idx + forward_bars], 0.0)
    if entry <= 0 or exit_ <= 0:
        return 0.0
    return ((exit_ - entry) / entry) * 100.0


def _rsi_from_window(closes: list[float], anchor_idx: int, period: int = 14) -> float:
    start = anchor_idx - period
    if start < 1 or anchor_idx >= len(closes):
        return 50.0
    gains = 0.0
    losses = 0.0
    for i in range(start + 1, anchor_idx + 1):
        delta = closes[i] - closes[i - 1]
        if delta > 0:
            gains += delta
        else:
            losses += abs(delta)
    if losses <= 1e-12:
        return 100.0
    rs = gains / max(losses, 1e-12)
    return 100.0 - (100.0 / (1.0 + rs))


def _realized_vol_pct(closes: list[float], anchor_idx: int, window: int = 20) -> float:
    start = anchor_idx - window + 1
    if start < 1:
        return 0.0
    rets = []
    for i in range(start, anchor_idx + 1):
        prev = closes[i - 1]
        cur = closes[i]
        if prev > 0 and cur > 0:
            rets.append((cur - prev) / prev)
    if len(rets) < 2:
        return 0.0
    mu = sum(rets) / len(rets)
    var = sum((r - mu) ** 2 for r in rets) / max(len(rets) - 1, 1)
    return math.sqrt(max(var, 0.0)) * 100.0


def _volume_surge_ratio(volumes: list[float], anchor_idx: int, short_window: int = 4, long_window: int = 24) -> float:
    if anchor_idx < long_window or anchor_idx >= len(volumes):
        return 1.0
    short_vals = volumes[max(0, anchor_idx - short_window + 1):anchor_idx + 1]
    long_vals = volumes[max(0, anchor_idx - long_window + 1):anchor_idx + 1]
    short_avg = sum(short_vals) / max(len(short_vals), 1)
    long_avg = sum(long_vals) / max(len(long_vals), 1)
    if long_avg <= 1e-12:
        return 1.0
    return short_avg / long_avg


def _historical_features(
    *,
    closes: list[float],
    volumes: list[float],
    anchor_idx: int,
) -> dict[str, float]:
    ret_1 = _window_return_pct(closes, anchor_idx - 1, 1) if anchor_idx >= 1 else 0.0
    ret_4 = _window_return_pct(closes, anchor_idx - 4, 4) if anchor_idx >= 4 else 0.0
    ret_24 = _window_return_pct(closes, anchor_idx - 24, 24) if anchor_idx >= 24 else 0.0
    rsi = _rsi_from_window(closes, anchor_idx, 14)
    vol_pct = _realized_vol_pct(closes, anchor_idx, 20)
    volume_ratio = _volume_surge_ratio(volumes, anchor_idx, 4, 24)
    return {
        "ret_1": round(ret_1, 4),
        "ret_4": round(ret_4, 4),
        "ret_24": round(ret_24, 4),
        "rsi": round(rsi, 4),
        "volatility_pct": round(vol_pct, 4),
        "volume_ratio": round(volume_ratio, 4),
    }


def _score_from_history(
    *,
    closes: list[float],
    volumes: list[float],
    anchor_idx: int,
    ranking_config: dict[str, Any],
) -> dict[str, Any]:
    cfg = build_ranker_config({"ranking": dict(ranking_config or {})})

    if anchor_idx < 24:
        return {"score": -999.0, "features": {}, "breakdown": {}, "regime": "unknown"}

    feats = _historical_features(
        closes=closes,
        volumes=volumes,
        anchor_idx=anchor_idx,
    )

    ohlcv_stub = []
    start = max(0, anchor_idx - 30)
    for i in range(start, anchor_idx + 1):
        c = closes[i]
        v = volumes[i] if i < len(volumes) else 0.0
        ohlcv_stub.append([i, c, c, c, c, v])

    regime_info = detect_regime(ohlcv_stub, period=14)
    regime = str(regime_info.get("regime") or "unknown")

    momentum_mult = cfg["momentum_mult"]
    hot_mult = cfg["hot_mult"]
    volume_mult = cfg["volume_z_mult"]
    rsi_bonus = cfg["rsi_bonus_healthy"]
    overbought_penalty = cfg["rsi_penalty_overbought"]
    oversold_penalty = cfg["rsi_penalty_oversold"]
    vol_bonus = cfg["volatility_bonus_mid"]
    vol_penalty = cfg["volatility_penalty_high"]

    if regime == "trending_up":
        momentum_mult *= 1.4
        hot_mult *= 1.25
        volume_mult *= 1.15
    elif regime == "trending_down":
        momentum_mult *= 0.6
        hot_mult *= 0.5
        overbought_penalty *= 1.25
    elif regime == "ranging":
        momentum_mult *= 0.65
        hot_mult *= 0.6
        rsi_bonus *= 1.4
        oversold_penalty = 0.0
    elif regime == "high_volatility":
        momentum_mult *= 0.8
        volume_mult *= 1.25
        vol_penalty *= 1.35

    score_momentum = _clamp(
        feats["ret_4"] * momentum_mult,
        cfg["momentum_min"],
        cfg["momentum_max"],
    )
    score_hot = _clamp(
        feats["ret_24"] * hot_mult,
        cfg["hot_min"],
        cfg["hot_max"],
    )
    score_volume = _clamp(
        max(feats["volume_ratio"] - 1.0, 0.0) * volume_mult,
        cfg["volume_min"],
        cfg["volume_max"],
    )

    score_rsi = 0.0
    if 45.0 <= feats["rsi"] <= 70.0:
        score_rsi = rsi_bonus
    elif feats["rsi"] > 80.0:
        score_rsi = overbought_penalty
    elif feats["rsi"] < 25.0:
        score_rsi = oversold_penalty

    score_volatility = 0.0
    if feats["volatility_pct"] >= 10.0:
        score_volatility = vol_penalty
    elif 2.0 <= feats["volatility_pct"] <= 8.0:
        score_volatility = vol_bonus

    total = score_momentum + score_hot + score_volume + score_rsi + score_volatility

    return {
        "score": round(total, 4),
        "regime": regime,
        "features": feats,
        "breakdown": {
            "momentum": round(score_momentum, 4),
            "hot": round(score_hot, 4),
            "volume": round(score_volume, 4),
            "rsi": round(score_rsi, 4),
            "volatility": round(score_volatility, 4),
        },
    }


def backtest_historical_selector(
    *,
    venue: str = "coinbase",
    symbols: list[str] | None = None,
    timeframe: str = "1h",
    top_n: int = 5,
    lookback_limit: int = 300,
    anchor_stride: int = 12,
    min_history_bars: int = 48,
    forward_bars: int = 4,
    ranking_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target = symbols or ["BTC/USD", "ETH/USD", "SOL/USD", "AVAX/USD", "LINK/USD", "DOGE/USD"]
    series: dict[str, dict[str, list[float]]] = {}

    for sym in target:
        rows = _load_local_ohlcv(venue, sym, timeframe=timeframe, limit=lookback_limit) or []
        closes = _closes(rows)
        volumes = _volumes(rows)
        if len(closes) >= (min_history_bars + forward_bars + 1):
            series[sym] = {"closes": closes, "volumes": volumes}

    if not series:
        return {"ok": False, "reason": "no_series"}

    max_len = min(len(v["closes"]) for v in series.values())
    start_idx = min_history_bars
    end_idx = max_len - forward_bars - 1

    baseline_anchor_returns: list[float] = []
    composite_anchor_returns: list[float] = []
    anchors: list[dict[str, Any]] = []

    for anchor_idx in range(start_idx, end_idx + 1, anchor_stride):
        baseline_ranked = []
        composite_ranked = []

        for sym, pack in series.items():
            closes = pack["closes"]
            volumes = pack["volumes"]

            r24 = _window_return_pct(closes, anchor_idx - 24, 24) if anchor_idx >= 24 else -999.0
            baseline_ranked.append({"symbol": sym, "score": r24})

            scored = _score_from_history(
                closes=closes,
                volumes=volumes,
                anchor_idx=anchor_idx,
                ranking_config=ranking_config or {},
            )
            composite_ranked.append({
                "symbol": sym,
                "score": scored["score"],
                "regime": scored.get("regime"),
                "features": scored["features"],
                "breakdown": scored["breakdown"],
            })

        baseline_ranked.sort(key=lambda r: r["score"], reverse=True)
        composite_ranked.sort(key=lambda r: r["score"], reverse=True)

        baseline_selected = baseline_ranked[:top_n]
        composite_selected = composite_ranked[:top_n]

        baseline_returns = [
            _window_return_pct(series[row["symbol"]]["closes"], anchor_idx, forward_bars)
            for row in baseline_selected
        ]
        composite_returns = [
            _window_return_pct(series[row["symbol"]]["closes"], anchor_idx, forward_bars)
            for row in composite_selected
        ]

        baseline_avg = sum(baseline_returns) / len(baseline_returns) if baseline_returns else 0.0
        composite_avg = sum(composite_returns) / len(composite_returns) if composite_returns else 0.0

        baseline_anchor_returns.append(baseline_avg)
        composite_anchor_returns.append(composite_avg)

        anchors.append({
            "anchor_idx": anchor_idx,
            "baseline_symbols": [r["symbol"] for r in baseline_selected],
            "composite_symbols": [r["symbol"] for r in composite_selected],
            "baseline_avg_return_pct": round(baseline_avg, 4),
            "composite_avg_return_pct": round(composite_avg, 4),
            "delta_avg_return_pct": round(composite_avg - baseline_avg, 4),
            "composite_top_features": [
                {
                    "symbol": r["symbol"],
                    "score": r["score"],
                    "regime": r.get("regime"),
                    "features": r.get("features", {}),
                    "breakdown": r.get("breakdown", {}),
                }
                for r in composite_selected[:3]
            ],
        })

    def _summary(vals: list[float]) -> dict[str, Any]:
        if not vals:
            return {"count": 0, "avg_return_pct": 0.0, "hit_rate": 0.0, "total_return_pct": 0.0}
        hits = sum(1 for v in vals if v > 0)
        return {
            "count": len(vals),
            "avg_return_pct": round(sum(vals) / len(vals), 4),
            "hit_rate": round(hits / len(vals), 4),
            "total_return_pct": round(sum(vals), 4),
        }

    baseline_summary = _summary(baseline_anchor_returns)
    composite_summary = _summary(composite_anchor_returns)

    return {
        "ok": True,
        "venue": venue,
        "timeframe": timeframe,
        "forward_bars": forward_bars,
        "top_n": top_n,
        "anchors_tested": len(anchors),
        "baseline": baseline_summary,
        "composite": composite_summary,
        "delta": {
            "avg_return_pct": round(
                _safe_float(composite_summary.get("avg_return_pct")) - _safe_float(baseline_summary.get("avg_return_pct")),
                4,
            ),
            "hit_rate": round(
                _safe_float(composite_summary.get("hit_rate")) - _safe_float(baseline_summary.get("hit_rate")),
                4,
            ),
            "total_return_pct": round(
                _safe_float(composite_summary.get("total_return_pct")) - _safe_float(baseline_summary.get("total_return_pct")),
                4,
            ),
        },
        "anchors": anchors,
    }
