"""Position-truth confirmation and halt binding (operator decision 2026-10-09).

Decision record: docs/decisions/position_truth_resolution_authority.md (section "Decision 2026-10-09").
- Authority: HALT AND ADJUDICATE. Confirmed drift arms the canonical kill switch; nothing is auto-corrected and
  this module never disarms the kill switch (the operator decides).
- Trust policy: a drift key counts only when its |drift| > 3x tolerance (exchange_reconciler CRITICAL rule).
  Confirmed when the same key is observed >= min_obs times AND its first observation is >= min_persist_ms old.
  Venue lookup/reconcile errors are NOT observations (they neither count nor clear), and neither is a venue balance
  snapshot whose own timestamp is older than max_snapshot_age_ms (default 2 minutes). A completed observation where
  the key is not CRITICAL clears that key.
Not wired to any scheduler here; run_position_truth_once() is the single entry point for a future loop.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

MIN_OBS_ENV, MIN_PERSIST_MS_ENV = "CBP_POSITION_DRIFT_MIN_OBS", "CBP_POSITION_DRIFT_MIN_PERSIST_MS"
MIN_OBS_DEFAULT, MIN_PERSIST_MS_DEFAULT = 3, 900_000
MAX_SNAPSHOT_AGE_ENV, MAX_SNAPSHOT_AGE_MS_DEFAULT = "CBP_POSITION_DRIFT_MAX_SNAPSHOT_AGE_MS", 120_000


def _env_int(name: str, default: int, floor: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= floor else default  # never loosen below the floor via a bad env value


@dataclass(frozen=True)
class PositionTruthPolicy:
    min_obs: int = MIN_OBS_DEFAULT
    min_persist_ms: int = MIN_PERSIST_MS_DEFAULT
    max_snapshot_age_ms: int = MAX_SNAPSHOT_AGE_MS_DEFAULT

    def __post_init__(self):
        if (type(self.min_obs) is not int or self.min_obs < MIN_OBS_DEFAULT
                or type(self.min_persist_ms) is not int or self.min_persist_ms < MIN_PERSIST_MS_DEFAULT
                or type(self.max_snapshot_age_ms) is not int or self.max_snapshot_age_ms < 1):
            raise ValueError("position_truth_policy_below_accepted_minimum_or_invalid")

    @classmethod
    def from_env(cls) -> "PositionTruthPolicy":
        return cls(_env_int(MIN_OBS_ENV, MIN_OBS_DEFAULT, MIN_OBS_DEFAULT),
                   _env_int(MIN_PERSIST_MS_ENV, MIN_PERSIST_MS_DEFAULT, MIN_PERSIST_MS_DEFAULT),
                   _env_int(MAX_SNAPSHOT_AGE_ENV, MAX_SNAPSHOT_AGE_MS_DEFAULT, 1))


def critical_keys(drift: Dict[str, Any], cash_tol: float, qty_tol: float) -> Dict[str, float]:
    """Keys whose drift exceeds 3x tolerance, matching exchange_reconciler.severity_from's CRITICAL rule."""
    out: Dict[str, float] = {}
    exchange = str(drift.get("exchange") or "")
    cash = drift.get("cash") or {}
    for row in [cash.get("primary") or {}, *(cash.get("others") or [])]:
        if row and abs(float(row.get("abs_drift", 0.0) or 0.0)) > 3 * float(cash_tol):
            out[f"{exchange}:cash:{row.get('quote_ccy')}"] = float(row["abs_drift"])
    for p in drift.get("positions") or []:
        if abs(float(p.get("abs_drift", 0.0) or 0.0)) > 3 * float(qty_tol):
            out[f"{exchange}:position:{p.get('base')}"] = float(p["abs_drift"])
    return out


class DriftConfirmationStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        with sqlite3.connect(self.path) as con:
            con.execute("CREATE TABLE IF NOT EXISTS position_drift_obs (key TEXT PRIMARY KEY, exchange TEXT NOT NULL,"
                        " first_ts_ms INTEGER NOT NULL, last_ts_ms INTEGER NOT NULL, count INTEGER NOT NULL,"
                        " last_drift REAL NOT NULL)")

    def record_observation(self, exchange: str, keys: Dict[str, float], ts_ms: int) -> None:
        """One completed venue observation: upsert CRITICAL keys, clear this exchange's other keys."""
        with sqlite3.connect(self.path) as con:
            con.execute("BEGIN IMMEDIATE")
            existing = {r[0] for r in con.execute("SELECT key FROM position_drift_obs WHERE exchange=?", (exchange,))}
            for key in existing - set(keys):
                con.execute("DELETE FROM position_drift_obs WHERE key=?", (key,))
            for key, drift in keys.items():
                con.execute("INSERT INTO position_drift_obs(key,exchange,first_ts_ms,last_ts_ms,count,last_drift) "
                            "VALUES(?,?,?,?,1,?) ON CONFLICT(key) DO UPDATE SET last_ts_ms=excluded.last_ts_ms, "
                            "count=count+1, last_drift=excluded.last_drift", (key, exchange, ts_ms, ts_ms, drift))

    def rows(self, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.path) as con:
            con.row_factory = sqlite3.Row
            q = "SELECT * FROM position_drift_obs" + (" WHERE exchange=?" if exchange else "") + " ORDER BY key"
            return [dict(r) for r in con.execute(q, (exchange,) if exchange else ())]


def confirmed(rows: List[Dict[str, Any]], policy: PositionTruthPolicy, now_ms: int) -> List[Dict[str, Any]]:
    return [r for r in rows if r["count"] >= policy.min_obs and now_ms - r["first_ts_ms"] >= policy.min_persist_ms]


def _default_halt(reason: str) -> dict:
    from services.execution.kill_switch import set_kill_switch
    return set_kill_switch(True, reason=reason)


async def run_position_truth_once(*, exchange_id: str, ex_obj, cfg, trading_cfg: Dict[str, Any],
                                  store: DriftConfirmationStore, policy: Optional[PositionTruthPolicy] = None,
                                  halt: Callable[[str], Any] = _default_halt,
                                  now_ms: Callable[[], int] = lambda: int(time.time() * 1000)) -> Dict[str, Any]:
    """Reconcile once, update confirmation state, arm the kill switch on confirmed drift. Never disarms."""
    from services.reconciliation.exchange_reconciler import reconcile_once
    from storage.reconciliation_store_sqlite import SQLiteReconciliationStore
    policy = policy or PositionTruthPolicy.from_env()
    seen: Dict[str, Any] = {}

    class _Recording:  # capture the venue snapshot so its age can be checked before it is trusted
        async def fetch_balance(self):
            seen["balance"] = await ex_obj.fetch_balance()
            return seen["balance"]

        def __getattr__(self, name):
            return getattr(ex_obj, name)

    observed_at = now_ms()
    try:
        result = await reconcile_once(exchange_id=exchange_id, ex_obj=_Recording(), cfg=cfg, trading_cfg=trading_cfg)
        reports = SQLiteReconciliationStore(path=cfg.recon_db_path).list_drift_reports(exchange=exchange_id, limit=1)
        drift = reports[0]["payload"]
    except Exception as exc:  # lookup errors are not observations: no count, no clear, no halt
        return {"ok": False, "observation": "error_not_counted", "error_type": type(exc).__name__,
                "confirmed": [], "halted": False}
    venue_ts = (seen.get("balance") or {}).get("timestamp")
    if isinstance(venue_ts, (int, float)) and observed_at - int(venue_ts) > policy.max_snapshot_age_ms:
        return {"ok": False, "observation": "stale_snapshot_not_counted", "snapshot_age_ms": observed_at - int(venue_ts),
                "confirmed": [], "halted": False}
    ts = observed_at  # one clock for first/last observation and the persistence check
    keys = critical_keys(drift, cfg.cash_tolerance, cfg.asset_qty_tolerance)
    store.record_observation(exchange_id, keys, ts)
    hits = confirmed(store.rows(exchange_id), policy, ts)
    halted = False
    if hits:
        reason = "position_truth_drift_confirmed:" + ",".join(sorted(r["key"] for r in hits))
        halt(reason)
        halted = True
    return {"ok": True, "observation": "counted", "severity": result.get("severity"), "critical_keys": keys,
            "confirmed": hits, "halted": halted, "policy": {"min_obs": policy.min_obs,
                                                              "min_persist_ms": policy.min_persist_ms,
                                                              "max_snapshot_age_ms": policy.max_snapshot_age_ms},
            "authority": "halt_and_adjudicate_no_auto_correction"}
