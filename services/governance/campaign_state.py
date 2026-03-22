from __future__ import annotations

VALID_CAMPAIGN_STATES = {
    "running",
    "completed",
    "stopped",
    "failed",
    "INVALID",
}


def is_valid_campaign_state(value: str) -> bool:
    return str(value) in VALID_CAMPAIGN_STATES
