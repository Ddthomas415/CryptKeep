from __future__ import annotations
import math

def step_ok(qty: float, step: float, eps: float = 1e-12) -> bool:
    if step <= 0:
        return True
    q = float(qty); s = float(step)
    k = round(q / s)
    return abs(q - (k * s)) <= eps
