"""services/control/retirement_checker.py

Retirement threshold evaluation for strategy evidence logs.

Extracted from check_promotion_gates.py to eliminate the illegal
services → scripts import in kernel.py.

Called by: services/control/kernel.py (runtime enforcement)
           scripts/check_promotion_gates.py (operator reporting)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_all_evidence(ev_dir: Path) -> dict[str, list[dict]]:
    """Load all JSONL evidence files from a strategy evidence directory."""
    result: dict[str, list[dict]] = {
        "signal": [], "order": [], "fill": [], "session": [], "drawdown": []
    }
    if not ev_dir.exists():
        return result
    for fpath in sorted(ev_dir.glob("*.jsonl")):
        stem = fpath.stem
        for key in result:
            if key in stem:
                records = []
                for line in fpath.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
                result[key].extend(records)
                break
    for fpath in sorted(ev_dir.glob("session_*.json")):
        try:
            result["session"].append(json.loads(fpath.read_text()))
        except Exception:
            pass
    return result


def check_retirement_triggers(
    fills: list[dict],
    sessions: list[dict],
    *,
    max_drawdown_pct: float = 12.0,
    rolling_window: int = 60,
) -> dict[str, Any]:
    """Evaluate retirement conditions from fill and session evidence.

    Returns:
        triggers_fired:       list of triggered condition strings
        retirement_required:  True if 2+ triggers active simultaneously
        single_trigger_review: True if exactly 1 trigger active
        note:                 summary string
    """
    triggers = []

    # Negative rolling expectancy
    pnls = [float(f.get("pnl_usd") or 0) for f in fills if "pnl_usd" in f]
    if len(pnls) >= 10:
        avg = sum(pnls) / len(pnls)
        if avg < 0:
            triggers.append(f"rolling_expectancy_negative:avg={avg:.2f}")

    # Drawdown exceeded
    actual_dd = max(
        (float(s.get("drawdown_from_peak") or 0) for s in sessions),
        default=0.0,
    )
    if actual_dd > max_drawdown_pct:
        triggers.append(f"drawdown_exceeded:{actual_dd:.1f}%>{max_drawdown_pct:.1f}%")

    return {
        "triggers_fired":        triggers,
        "retirement_required":   len(triggers) >= 2,
        "single_trigger_review": len(triggers) == 1,
        "note": f"{len(triggers)} retirement trigger(s) active",
    }
