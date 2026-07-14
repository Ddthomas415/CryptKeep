from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Any


def decimal_value(value: Any, *, name: str = "value") -> Decimal:
    try:
        out = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name}_invalid") from exc
    if not out.is_finite():
        raise ValueError(f"{name}_non_finite")
    return out


def decimal_product(left: Any, right: Any) -> Decimal:
    return decimal_value(left, name="left") * decimal_value(right, name="right")


def decimal_step_ok(qty: Any, step: Any) -> bool:
    step_d = decimal_value(step, name="step")
    if step_d <= 0:
        return True
    qty_d = decimal_value(qty, name="qty")
    return qty_d % step_d == 0


def step_ok(qty: float, step: float, eps: float = 1e-12) -> bool:
    del eps  # retained for backward-compatible call sites; Decimal is exact.
    try:
        return decimal_step_ok(qty, step)
    except ValueError:
        return False
