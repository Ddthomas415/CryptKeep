from __future__ import annotations

from typing import Any, Dict, Iterable, List

from services.execution.reconciliation import reconcile_spot_position


def reconcile_once(*, venue: str, symbol: str) -> Dict[str, Any]:
    """Compatibility wrapper used by legacy callers."""
    return reconcile_spot_position(venue=str(venue), symbol=str(symbol))


def run_startup_reconciliation(
    *,
    venue: str,
    symbols: Iterable[str],
    fail_fast: bool = False,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    ok_count = 0
    fail_count = 0
    for sym in symbols:
        out = reconcile_once(venue=venue, symbol=str(sym))
        rows.append(out)
        if bool(out.get("ok")):
            ok_count += 1
        else:
            fail_count += 1
            if fail_fast:
                break
    return {
        "ok": fail_count == 0,
        "venue": str(venue),
        "count": len(rows),
        "ok_count": ok_count,
        "fail_count": fail_count,
        "rows": rows,
    }
