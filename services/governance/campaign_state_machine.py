from __future__ import annotations


def can_transition(current_state: str, next_state: str) -> bool:
    if str(current_state) == "INVALID" and str(next_state) != "INVALID":
        return False
    return True
