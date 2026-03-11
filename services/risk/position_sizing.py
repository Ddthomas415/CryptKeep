from __future__ import annotations

import math
from typing import Iterable


def estimate_volatility(closes: Iterable[float]) -> float:
    xs = [float(x) for x in closes]
    if len(xs) < 3:
        return 0.0
    rets: list[float] = []
    for i in range(1, len(xs)):
        prev = xs[i - 1]
        cur = xs[i]
        if prev <= 0:
            continue
        rets.append((cur - prev) / prev)
    if len(rets) < 2:
        return 0.0
    mu = sum(rets) / len(rets)
    var = sum((r - mu) ** 2 for r in rets) / max(1, (len(rets) - 1))
    return float(math.sqrt(max(0.0, var)))


def size_from_stop(
    *,
    risk_budget_usd: float,
    entry_price: float,
    stop_price: float,
    min_qty: float = 0.0,
    max_qty: float = 0.0,
    qty_step: float = 0.0,
) -> float:
    e = float(entry_price)
    s = float(stop_price)
    if e <= 0:
        return 0.0
    stop_dist = abs(e - s)
    if stop_dist <= 0:
        return 0.0
    qty = float(risk_budget_usd) / stop_dist
    if max_qty > 0:
        qty = min(qty, float(max_qty))
    if qty_step > 0:
        qty = math.floor(qty / float(qty_step)) * float(qty_step)
    if min_qty > 0 and qty < float(min_qty):
        return 0.0
    return float(max(0.0, qty))


def size_by_volatility(
    *,
    equity_usd: float,
    risk_pct: float,
    price: float,
    volatility: float,
    vol_scale: float = 2.0,
    max_notional_usd: float = 0.0,
) -> float:
    e = float(equity_usd)
    p = float(price)
    v = max(0.0, float(volatility))
    if e <= 0 or p <= 0 or risk_pct <= 0:
        return 0.0
    risk_budget = e * float(risk_pct)
    stop_dist = max(p * v * float(vol_scale), p * 0.001)
    qty = risk_budget / stop_dist
    if max_notional_usd > 0:
        qty = min(qty, float(max_notional_usd) / p)
    return float(max(0.0, qty))
