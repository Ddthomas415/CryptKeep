from __future__ import annotations
from typing import Any, Dict


def normalize_order(order: dict | None) -> Dict[str, Any]:
    if isinstance(order, dict):
        return order
    return {}
