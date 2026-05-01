from __future__ import annotations

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)


def _data_dir() -> Path:
    from services.os.app_paths import data_dir
    return data_dir()


def _exec_db() -> str:
    from services.os.app_paths import data_dir, ensure_dirs
    ensure_dirs()
    return str(
        os.environ.get("EXEC_DB_PATH")
        or os.environ.get("CBP_DB_PATH")
        or (data_dir() / "execution.sqlite")
    )


def _check_halt_flag() -> str | None:
    flag = _data_dir() / "system_halted.flag"
    if not flag.exists():
        return None
    try:
        raw = flag.read_text(encoding="utf-8").strip()
        reason = raw if raw else "system_halted_flag_present"
    except Exception as err:
        reason = f"system_halted_flag_unreadable:{type(err).__name__}"
    return f"halted:{reason}"


def _check_risk_sink_flag() -> str | None:
    flag = _data_dir() / "risk_sink_failed.flag"
    if not flag.exists():
        return None
    try:
        payload = json.loads(flag.read_text(encoding="utf-8"))
        venue = str(payload.get("venue") or "unknown")
        fill_id = str(payload.get("fill_id") or "unknown")
        error = str(payload.get("error") or payload.get("reason") or "unknown")
        return f"risk_sink_failed:venue={venue} fill_id={fill_id} error={error}"
    except Exception as err:
        return f"risk_sink_flag_unreadable:{type(err).__name__}:{err}"


def _check_accounting_invariant() -> str | None:
    db_path = _exec_db()
    try:
        con = sqlite3.connect(db_path, timeout=5)
        try:
            row = con.execute("""
                SELECT COUNT(*)
                FROM canonical_fills cf
                LEFT JOIN risk_daily_fills rdf
                    ON cf.venue = rdf.venue
                    AND cf.fill_id = rdf.fill_id
                WHERE rdf.fill_id IS NULL
            """).fetchone()
            missing = int(row[0]) if row else 0
        finally:
            con.close()
    except sqlite3.OperationalError:
        return None
    except Exception as err:
        _LOG.warning("system_health.accounting_invariant_check_failed: %s", err)
        return f"accounting_invariant_check_failed:{type(err).__name__}:{err}"

    if missing > 0:
        return (
            "accounting_invariant_violated:"
            f"{missing}_canonical_fills_missing_from_risk_daily_fills"
        )
    return None


def get_system_health() -> dict[str, Any]:
    halt_reason = _check_halt_flag()
    if halt_reason is not None:
        return {"state": "HALTED", "reasons": [halt_reason]}

    reasons: list[str] = []

    sink_reason = _check_risk_sink_flag()
    if sink_reason is not None:
        reasons.append(sink_reason)

    invariant_reason = _check_accounting_invariant()
    if invariant_reason is not None:
        reasons.append(invariant_reason)

    if reasons:
        return {"state": "DEGRADED", "reasons": reasons}

    return {"state": "HEALTHY", "reasons": []}
