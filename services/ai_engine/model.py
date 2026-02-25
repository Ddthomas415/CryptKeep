from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

from services.ai_engine.features import FEATURE_ORDER


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


@dataclass(frozen=True)
class LinearSignalModel:
    feature_order: List[str]
    weights: Dict[str, float]
    bias: float
    version: int = 1

    @staticmethod
    def default() -> "LinearSignalModel":
        return LinearSignalModel(
            feature_order=list(FEATURE_ORDER),
            weights={k: 0.0 for k in FEATURE_ORDER},
            bias=0.0,
            version=1,
        )

    @staticmethod
    def from_dict(payload: Dict[str, Any]) -> "LinearSignalModel":
        p = dict(payload or {})
        order = [str(v) for v in (p.get("feature_order") or FEATURE_ORDER)]
        weights_raw = dict(p.get("weights") or {})
        weights = {k: float(weights_raw.get(k, 0.0) or 0.0) for k in order}
        return LinearSignalModel(
            feature_order=order,
            weights=weights,
            bias=float(p.get("bias", 0.0) or 0.0),
            version=int(p.get("version", 1) or 1),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_order": list(self.feature_order),
            "weights": {k: float(self.weights.get(k, 0.0)) for k in self.feature_order},
            "bias": float(self.bias),
            "version": int(self.version),
        }

    def score(self, features: Dict[str, float]) -> float:
        s = float(self.bias)
        for name in self.feature_order:
            s += float(self.weights.get(name, 0.0)) * float(features.get(name, 0.0))
        return s

    def predict_proba_up(self, features: Dict[str, float]) -> float:
        z = _clamp(self.score(features), -60.0, 60.0)
        return float(1.0 / (1.0 + math.exp(-z)))

    def evaluate_side(
        self,
        *,
        side: str,
        features: Dict[str, float],
        buy_threshold: float = 0.55,
        sell_threshold: float = 0.45,
    ) -> Tuple[bool, str, float]:
        p_up = self.predict_proba_up(features)
        s = str(side or "").strip().lower()
        if s == "buy":
            if p_up < float(buy_threshold):
                return False, "buy_below_threshold", p_up
            return True, "ok", p_up
        if s == "sell":
            if p_up > float(sell_threshold):
                return False, "sell_above_threshold", p_up
            return True, "ok", p_up
        return True, "side_not_trade", p_up

