from __future__ import annotations

import logging
_LOG = logging.getLogger(__name__)

from typing import Any, Dict, List

from services.admin.journal_exchange_reconcile import reconcile_journal_vs_exchange
from services.admin.position_reconcile import reconcile_positions
from services.admin import wizard_state


def _normalize_symbols(symbols: List[str] | None) -> List[str]:
    out: List[str] = []
    for s in symbols or []:
        t = str(s).strip().upper().replace("-", "/")
        if t:
            out.append(t)
    return out


def run_all_safe_steps(
    *,
    venue: str,
    symbols: List[str] | None = None,
    mode: str = "spot",
    require_exchange_ok: bool = False,
) -> Dict[str, Any]:
    """
    Non-destructive reconciliation helper for KJ6.
    Runs read-only journal and position reconciliations and records wizard progress.
    """
    v = str(venue or "").strip().lower()
    syms = _normalize_symbols(symbols)
    if not v:
        return {"ok": False, "reason": "missing_venue", "steps": []}

    steps: List[Dict[str, Any]] = []

    # Step 1: journal vs exchange reconcile snapshot (read-only).
    journal_symbol = syms[0] if syms else None
    jrep = reconcile_journal_vs_exchange(v, journal_symbol)
    steps.append(
        {
            "step": "journal_reconcile",
            "ok": bool(jrep.get("ok", False)),
            "snapshot_path": jrep.get("snapshot_path"),
            "counts": dict(jrep.get("counts") or {}),
            "signals": dict(jrep.get("signals") or {}),
        }
    )

    # Step 2: position reconcile snapshot (read-only).
    prep = reconcile_positions(
        v,
        syms if syms else None,
        mode=str(mode or "spot"),
        require_exchange_ok=bool(require_exchange_ok),
    )
    steps.append(
        {
            "step": "position_reconcile",
            "ok": bool(prep.get("ok", False)),
            "snapshot_path": prep.get("snapshot_path"),
            "mismatch_count": int(prep.get("mismatch_count", 0) or 0),
            "reason": prep.get("reason"),
        }
    )

    # Best-effort wizard progress update.
    try:
        st = wizard_state.load()
        st["last_reconcile"] = jrep.get("snapshot_path")
        st["last_reconcile_after_cancel"] = prep.get("snapshot_path")
        st["step"] = max(int(st.get("step", 1) or 1), 3)
        wizard_state.save(st)
    except Exception as _err:
        pass  # suppressed: see _LOG.debug below

    ok = all(bool(s.get("ok")) for s in steps)
    return {
        "ok": ok,
        "non_destructive": True,
        "venue": v,
        "symbols": syms,
        "mode": str(mode or "spot"),
        "require_exchange_ok": bool(require_exchange_ok),
        "steps": steps,
    }
