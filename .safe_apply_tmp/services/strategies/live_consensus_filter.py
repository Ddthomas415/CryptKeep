from __future__ import annotations
from services.learning.consensus_signal_engine import compute_consensus

class ConsensusCache:
    def __init__(self):
        self._last_epoch = 0.0
        self._ttl = 0.0
        self._last = {}

    def get(self, *, symbol: str, ttl_sec: int, compute_fn):
        import time
        now = time.time()
        if (now - self._last_epoch) < float(ttl_sec) and symbol in self._last:
            return self._last[symbol]
        val = compute_fn()
        self._last_epoch = now
        self._ttl = float(ttl_sec)
        self._last[symbol] = val
        return val

def live_consensus_score(*, symbol: str, cfg_signal_blend: dict) -> float:
    sb = cfg_signal_blend or {}
    cons = compute_consensus(
        symbols=[symbol],
        lookback_signals=int(sb.get("lookback_signals", 500) or 500),
        max_signal_age_sec=int(sb.get("max_signal_age_sec", 21600) or 21600),
        min_weight=float(sb.get("min_trader_weight", 0.0) or 0.0),
        lookback_evals=int((sb.get("weights", {}) or {}).get("lookback_evals", 500) or 500),
        min_evals=int((sb.get("weights", {}) or {}).get("min_evals", 5) or 5),
    )
    return float((cons.get("consensus", {}).get(symbol, {}) or {}).get("score") or 0.0)

def allows_action(*, action: str, score: float, threshold: float) -> bool:
    if action == "enter":
        return float(score) >= float(threshold)
    return True
