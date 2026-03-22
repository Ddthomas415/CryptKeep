from __future__ import annotations

from typing import Any


def validate_campaign_payload(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    # Minimal canonical validation: strategy-bearing campaign payload.
    return bool(payload.get("strategy") or payload.get("strategies"))
