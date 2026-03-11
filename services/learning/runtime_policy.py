# Phase 179: canary/live enforcement + auto-rollback
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class RuntimePolicy:
    canary_enabled: bool = True
    canary_min_samples: int = 30
    promote_min_metric_delta: float = 0.0
    rollback_max_metric_drop: float = 0.03
    fail_open: bool = False


def read_runtime_policy(cfg: Dict[str, Any] | None = None) -> RuntimePolicy:
    c = dict(cfg or {})
    s = c.get("runtime_policy") if isinstance(c.get("runtime_policy"), dict) else c
    return RuntimePolicy(
        canary_enabled=bool(s.get("canary_enabled", True)),
        canary_min_samples=int(s.get("canary_min_samples", 30) or 30),
        promote_min_metric_delta=float(s.get("promote_min_metric_delta", 0.0) or 0.0),
        rollback_max_metric_drop=float(s.get("rollback_max_metric_drop", 0.03) or 0.03),
        fail_open=bool(s.get("fail_open", False)),
    )
