from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import yaml

from services.execution.exchange_client import ExchangeClient
from services.risk.live_risk_gates_phase82 import LiveRiskLimits, LiveGateDB, LiveRiskGates  # PHASE82_LIVE_GATES
from storage.execution_store_sqlite import ExecutionStore
from storage.order_dedupe_store_sqlite import OrderDedupeStore

def _now_ms() -> int:
    return int(time.time() * 1000)


def _remote_id_from_reason(reason: str) -> Optional[str]:
    s = (reason or "").strip()
    if "remote_id=" in s:
        return s.split("remote_id=", 1)[-1].split()[0].strip() or None
    return None


@dataclass
class LiveCfg:
    enabled: bool = False
    sandbox: bool = False
    exchange_id: str = "coinbase"
    exec_db: str = "data/execution.sqlite"
    symbol: str = "BTC/USDT"
    max_submit_per_tick: int = 1
    reconcile_limit: int = 25

def cfg_from_yaml(path: str = "config/trading.yaml") -> LiveCfg:
    cfg = yaml.safe_load(open(path, "r", encoding="utf-8").read()) or {}
    live = cfg.get("live") or {}
    ex_cfg = cfg.get("execution") or {}
    return LiveCfg(
        enabled=bool(live.get("enabled", False)),
        sandbox=bool(live.get("sandbox", False)),
        exchange_id=str(live.get("exchange_id") or "coinbase").lower(),
        exec_db=str(ex_cfg.get("db_path") or "data/execution.sqlite"),
        symbol=str((cfg.get("symbols") or ["BTC/USDT"])[0]),
        max_submit_per_tick=int(live.get("max_submit_per_tick") or 1),
        reconcile_limit=int(live.get("reconcile_limit") or 25),
    )

def _hard_off_guard(cfg: LiveCfg) -> tuple[bool, str]:
    if not cfg.enabled:
        return False, "live.enabled is false"
    if os.environ.get("LIVE_TRADING") != "YES":
        return False, "LIVE_TRADING env var is not YES"
    return True, "ok"

def _list_intents_any(store: ExecutionStore, *, mode: str, exchange: str, symbol: str, statuses: list[str], limit: int) -> list[dict[str, Any]]:
    # ExecutionStore.list_intents only supports one status; do multiple queries
    out: list[dict[str, Any]] = []
    for st in statuses:
        out.extend(store.list_intents(mode=mode, exchange=exchange, symbol=symbol, status=st, limit=limit))
    # sort by ts desc
    out.sort(key=lambda r: int(r.get("ts_ms") or 0), reverse=True)
    return out[:limit]

def submit_pending_live(cfg: LiveCfg) -> Dict[str, Any]:
    ok, why = _hard_off_guard(cfg)
    if not ok:
        return {"ok": False, "note": why, "submitted": 0}

    # PHASE82_LIVE_GATES init
    limits = LiveRiskLimits.from_trading_yaml('config/trading.yaml')
    gate_db = LiveGateDB(exec_db=cfg.exec_db)
    gates = LiveRiskGates(limits=limits, db=gate_db) if limits else None
    if not gates:
        return {'ok': False, 'note': 'LIVE blocked: risk limits missing/invalid', 'submitted': 0}
    if gate_db.killswitch_on():
        return {'ok': False, 'note': 'LIVE blocked: kill switch ON', 'submitted': 0}

    store = ExecutionStore(path=cfg.exec_db)
    store_dedupe = OrderDedupeStore(exec_db=cfg.exec_db)
    client = ExchangeClient(exchange_id=cfg.exchange_id, sandbox=cfg.sandbox)

    pending = _list_intents_any(store, mode="live", exchange=cfg.exchange_id, symbol=cfg.symbol, statuses=["pending"], limit=200)
    submitted = 0
    errors = 0

    for it in pending:
        if submitted >= int(cfg.max_submit_per_tick):
            break

        intent_id = str(it["intent_id"])
        meta = dict(it.get("meta") or {})
        reason0 = str(it.get("reason") or "")
        rid0 = _remote_id_from_reason(reason0)
        if rid0:
            store.set_intent_status(intent_id=intent_id, status="submitted", reason=f"remote_id={rid0}")
            continue
        cid = None
        try:
            # PHASE82_LIVE_GATES enforce
            row = gate_db.day_row()
            rpnl = float(row.get('realized_pnl_usd') or 0.0)
            lp = (float(it['limit_price']) if it.get('limit_price') is not None else None)
            ok2, reason2, meta2 = gates.check_live(it={'qty': float(it.get('qty') or 0.0), 'price': lp}, realized_pnl_usd=rpnl)
            if not ok2:
                store.set_intent_status(intent_id=intent_id, status='pending', reason=f'live_gate_block:{reason2}')
                continue

            order = client.submit_order(
                symbol=str(it["symbol"]),
                side=str(it["side"]),
                order_type=str(it["order_type"]),
                amount=float(it["qty"]),
                price=(float(it["limit_price"]) if it.get("limit_price") is not None else None),
                client_id=cid,
                extra_params=None,
                intent_id=intent_id,
                exec_db=cfg.exec_db,
            )
            meta["client_id"] = cid
            meta["remote_order_id"] = order.get("id")
            meta["sent_ts_ms"] = _now_ms()
            # store meta back: simplest is to re-submit a no-op? we don't have meta update method; encode into reason for now
            # We'll store remote id in reason field and keep full meta in fills later.
            row_d = store_dedupe.get_by_intent(cfg.exchange_id, intent_id)
            cid2 = (row_d or {}).get("client_order_id") or cid
            rid2 = (row_d or {}).get("remote_order_id") or order.get("id")
            store.set_intent_status(intent_id=intent_id, status="submitted", reason=f"remote_id={rid2} client_id={cid2}")

            # EXEC_GUARD_TRADE_ATTEMPT
            try:
                from storage.execution_guard_store_sqlite import ExecutionGuardStoreSQLite
                ExecutionGuardStoreSQLite()._record_trade_attempt_sync()
            except Exception:
                pass
            submitted += 1
        except Exception as e:
            errors += 1
            store.set_intent_status(intent_id=intent_id, status="pending", reason=f"submit_error:{type(e).__name__}:{e}")

    return {"ok": True, "note": "submitted tick complete", "submitted": submitted, "errors": errors}

def reconcile_live(cfg: LiveCfg) -> Dict[str, Any]:
    ok, why = _hard_off_guard(cfg)
    if not ok:
        return {"ok": False, "note": why, "fills_added": 0}

    store = ExecutionStore(path=cfg.exec_db)
    store_dedupe = OrderDedupeStore(exec_db=cfg.exec_db)
    client = ExchangeClient(exchange_id=cfg.exchange_id, sandbox=cfg.sandbox)

    # track intents that are "submitted" (and sometimes pending with remote_id in reason)
    intents = _list_intents_any(store, mode="live", exchange=cfg.exchange_id, symbol=cfg.symbol, statuses=["submitted", "pending"], limit=200)

    fills_added = 0
    checked = 0

    for it in intents:
        if checked >= int(cfg.reconcile_limit):
            break
        checked += 1

        intent_id = str(it["intent_id"])
        reason = str(it.get("reason") or "")
        remote_id = _remote_id_from_reason(reason)
        if not remote_id:
            row_d = store_dedupe.get_by_intent(cfg.exchange_id, intent_id)
            remote_id = (row_d or {}).get("remote_order_id")
        if not remote_id:
            continue

        try:
            o = client.fetch_order(order_id=remote_id, symbol=str(it["symbol"]))
        except Exception as e:
            # keep tracking; don't spam submits
            continue

        status = str(o.get("status") or "").lower()
        filled = float(o.get("filled") or 0.0)
        avg = float(o.get("average") or (o.get("price") or 0.0) or 0.0)
        fee = o.get("fee") or {}
        fee_cost = float(fee.get("cost") or 0.0)
        fee_ccy = str(fee.get("currency") or "").upper() or "USD"

        # we store a single synthetic fill when order is closed and filled>0.
        # For partials: if filled>0 and status is open, we do not add fills yet (safe + simple).
        if status in ("closed", "filled") and filled > 0 and avg > 0:
            store.add_fill(
                intent_id=intent_id,
                ts_ms=_now_ms(),
                price=avg,
                qty=filled,
                fee=fee_cost,
                fee_ccy=fee_ccy,
                meta={"remote_order_id": remote_id, "status": status, "raw_order": {"id": o.get("id"), "filled": filled, "average": avg, "fee": fee}},
            )
            store.set_intent_status(intent_id=intent_id, status="filled", reason=f"remote_id={remote_id}")
            try:
                store_dedupe.mark_terminal(exchange_id=cfg.exchange_id, intent_id=intent_id, terminal_status=status)
            except Exception:
                pass
            fills_added += 1
        elif status in ("canceled", "cancelled", "rejected", "expired"):
            store.set_intent_status(intent_id=intent_id, status="canceled", reason=f"remote_id={remote_id}:{status}")
            try:
                store_dedupe.mark_terminal(exchange_id=cfg.exchange_id, intent_id=intent_id, terminal_status=status)
            except Exception:
                pass

    return {"ok": True, "note": "reconcile complete", "checked": checked, "fills_added": fills_added}
# PHASE82_LIVE_GATES
