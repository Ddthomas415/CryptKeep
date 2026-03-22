from __future__ import annotations


TERMINAL_INVALIDATION_REASONS = {
    "fingerprint_mismatch",
    "drift",
    "contamination",
}


def should_invalidate(reason: str) -> bool:
    return str(reason).strip().lower() in TERMINAL_INVALIDATION_REASONS
