from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from services.ai_engine.features import FEATURE_ORDER, build_feature_map
from services.ai_engine.model import LinearSignalModel


@dataclass(frozen=True)
class TrainingRow:
    context: Dict[str, Any]
    label: int  # 1=good outcome for long/up; 0=bad


def _mean(rows: List[TrainingRow], feature_name: str) -> float:
    if not rows:
        return 0.0
    acc = 0.0
    for row in rows:
        m = build_feature_map(row.context)
        acc += float(m.get(feature_name, 0.0))
    return acc / float(len(rows))


def train_linear_signal_model(
    rows: Iterable[TrainingRow], feature_order: Iterable[str] | None = None
) -> LinearSignalModel:
    data = [r for r in rows]
    order = list(feature_order or FEATURE_ORDER)
    if not data:
        return LinearSignalModel.default()

    pos = [r for r in data if int(r.label) == 1]
    neg = [r for r in data if int(r.label) == 0]
    if not pos or not neg:
        return LinearSignalModel.default()

    weights: Dict[str, float] = {}
    pos_center: Dict[str, float] = {}
    neg_center: Dict[str, float] = {}
    for name in order:
        p = _mean(pos, name)
        n = _mean(neg, name)
        pos_center[name] = p
        neg_center[name] = n
        weights[name] = p - n

    # LDA-like midpoint bias keeps separation centered between class means.
    bias = 0.0
    for name in order:
        mid = 0.5 * (pos_center[name] + neg_center[name])
        bias -= float(weights[name]) * float(mid)

    # Scale weights to keep logits numerically stable with raw features.
    max_abs = max(abs(v) for v in weights.values()) if weights else 0.0
    if max_abs > 0:
        scale = 1.0 / max_abs
        weights = {k: float(v) * scale for k, v in weights.items()}
        bias = float(bias) * scale

    return LinearSignalModel(feature_order=order, weights=weights, bias=bias, version=1)

