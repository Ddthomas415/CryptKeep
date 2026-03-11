from __future__ import annotations

import os
import sqlite3
import statistics
import time
from dataclasses import dataclass

from services.os.app_paths import data_dir


@dataclass(frozen=True)
class LiveStartGateResult:
    ok: bool
    status: str
    reasons: list[str]
    details: dict


def check_ws_gate(cfg: dict) -> LiveStartGateResult:
    cb = cfg.get("circuit_breaker") if isinstance(cfg.get("circuit_breaker"), dict) else {}
    ws_db = str(cb.get("latency_db_path") or (data_dir() / "market_ws.sqlite"))
    warn_ms = float(cb.get("ws_warn_ms") or os.environ.get("CBP_WS_WARN_MS", "1200"))
    block_ms = float(cb.get("ws_block_ms") or cb.get("max_ws_latency_ms") or os.environ.get("CBP_WS_BLOCK_MS", "2500"))
    lookback_sec = int(cb.get("ws_lookback_sec") or 30)

    try:
        con = sqlite3.connect(ws_db)
        cutoff = int((time.time() - lookback_sec) * 1000)
        rows = con.execute(
            "SELECT value_ms FROM market_ws_latency WHERE ts_ms >= ? ORDER BY ts_ms DESC LIMIT 500",
            (cutoff,),
        ).fetchall()
        con.close()
    except Exception as e:
        return LiveStartGateResult(
            ok=True,
            status="WARN",
            reasons=["ws_latency_unavailable"],
            details={"db_path": ws_db, "error": f"{type(e).__name__}: {e}"},
        )

    vals = [float(r[0]) for r in rows if r and r[0] is not None]
    if not vals:
        return LiveStartGateResult(
            ok=True,
            status="WARN",
            reasons=["ws_latency_missing"],
            details={"db_path": ws_db, "lookback_sec": lookback_sec, "samples": 0},
        )

    peak = max(vals)
    med = float(statistics.median(vals))
    details = {"db_path": ws_db, "samples": len(vals), "peak_ms": peak, "median_ms": med, "warn_ms": warn_ms, "block_ms": block_ms}
    if peak > block_ms:
        return LiveStartGateResult(ok=False, status="BLOCK", reasons=["ws_latency_block"], details=details)
    if peak > warn_ms:
        return LiveStartGateResult(ok=True, status="WARN", reasons=["ws_latency_warn"], details=details)
    return LiveStartGateResult(ok=True, status="OK", reasons=[], details=details)

