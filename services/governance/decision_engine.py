from __future__ import annotations


def decide(state: str) -> str:
    if str(state) == "INVALID":
        return "BLOCK"
    return "ALLOW"
