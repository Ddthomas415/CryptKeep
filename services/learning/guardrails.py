# Phase 178: learning foundation + guardrails
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class LearningGuardrailConfig:
    min_train_rows: int = 200
    min_valid_rows: int = 100
    min_metric: float = 0.52
    max_drawdown_pct: float = 0.25


def evaluate_learning_guardrails(
    metrics: Dict[str, Any],
    *,
    cfg: LearningGuardrailConfig | None = None,
) -> Dict[str, Any]:
    c = cfg or LearningGuardrailConfig()
    train_rows = int(metrics.get("train_rows") or 0)
    valid_rows = int(metrics.get("valid_rows") or 0)
    metric = float(metrics.get("metric") or 0.0)
    drawdown = float(metrics.get("max_drawdown_pct") or 0.0)
    reasons: list[str] = []
    if train_rows < c.min_train_rows:
        reasons.append("insufficient_train_rows")
    if valid_rows < c.min_valid_rows:
        reasons.append("insufficient_valid_rows")
    if metric < c.min_metric:
        reasons.append("metric_below_threshold")
    if drawdown > c.max_drawdown_pct:
        reasons.append("drawdown_above_limit")
    return {
        "ok": len(reasons) == 0,
        "reasons": reasons,
        "metrics": {"train_rows": train_rows, "valid_rows": valid_rows, "metric": metric, "max_drawdown_pct": drawdown},
        "limits": {
            "min_train_rows": c.min_train_rows,
            "min_valid_rows": c.min_valid_rows,
            "min_metric": c.min_metric,
            "max_drawdown_pct": c.max_drawdown_pct,
        },
    }
