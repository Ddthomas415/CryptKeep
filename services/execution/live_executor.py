from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import yaml

from services.execution.exchange_client import ExchangeClient
from services.os.app_paths import data_dir, ensure_dirs
from services.preflight.preflight import run_preflight
from services.risk.live_risk_gates_phase82 import (
    LiveRiskLimits,
    LiveGateDB,
    LiveRiskGates,
    phase83_incr_trade_counter,
)  # PHASE82_LIVE_GATES
from services.risk.journal_introspection_phase83 import JournalSignals
from storage.execution_store_sqlite import ExecutionStore
from storage.order_dedupe_store_sqlite import OrderDedupeStore
from storage.pnl_store_sqlite import PnLStoreSQLite

# ---- runtime defaults (override by env set from scripts/bot_ctl.py) ----
DEFAULT_SYMBOL = ([x.strip() for x in (os.environ.get("CBP_SYMBOLS") or "").split(",") if x.strip()] or ["BTC/USD"])[0]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _remote_id_from_reason(reason: str) -> Optional[str]:
    s = (reason or "").strip()
    if "remote_id=" in s:
        return s.split("remote_id=", 1)[-1].split()[0].strip() or None
    return None


def _truthy(v: str | None, *, default: bool = False) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on", "y"}


def _first_preflight_error(checks: list[dict[str, Any]]) -> str:
    for item in checks:
        if not bool(item.get("ok", False)) and str(item.get("severity") or "").upper() == "ERROR":
            detail = str(item.get("detail") or "").strip()
            if detail:
                return detail
            name = str(item.get("name") or "").strip()
            if name:
                return name
    return "preflight_failed"


@dataclass
class _PreflightCircuitState:
    consecutive_failures: int = 0
    pause_until_ts: float = 0.0
    last_reason: str = ""


_PREFLIGHT_CIRCUIT = _PreflightCircuitState()


def _check_preflight_gate(
    cfg: "LiveCfg",
    *,
    cfg_path: str = "config/trading.yaml",
    state: _PreflightCircuitState = _PREFLIGHT_CIRCUIT,
    now_ts: float | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    enforce = _truthy(os.environ.get("CBP_LIVE_PREFLIGHT_ENFORCE"), default=True)
    if not enforce:
        return True, "PREFLIGHT_GATE_DISABLED", {"enforced": False}

    now = float(now_ts) if now_ts is not None else time.time()
    if state.pause_until_ts > now:
        return False, "CIRCUIT_BREAKER_PAUSED", {
            "pause_until_ts": state.pause_until_ts,
            "pause_remaining_s": round(max(0.0, state.pause_until_ts - now), 3),
            "last_reason": state.last_reason,
        }

    pf = run_preflight(cfg_path=cfg_path)
    checks = list(getattr(pf, "checks", []) or [])
    if bool(getattr(pf, "ok", False)):
        state.consecutive_failures = 0
        state.last_reason = ""
        return True, "OK", {"checks": checks}

    state.consecutive_failures += 1
    threshold = max(1, int(os.environ.get("CBP_LIVE_PREFLIGHT_FAIL_THRESHOLD") or 3))
    pause_s = max(1.0, float(os.environ.get("CBP_LIVE_PREFLIGHT_PAUSE_SECONDS") or 30.0))
    detail = _first_preflight_error(checks)
    state.last_reason = detail

    meta: dict[str, Any] = {
        "checks": checks,
        "error": detail,
        "consecutive_failures": state.consecutive_failures,
        "threshold": threshold,
    }

    if state.consecutive_failures >= threshold:
        state.pause_until_ts = now + pause_s
        state.consecutive_failures = 0
        meta["pause_seconds"] = pause_s
        meta["pause_until_ts"] = state.pause_until_ts
        return False, "CIRCUIT_BREAKER_TRIPPED", meta

    return False, "PREFLIGHT_FAILED", meta


@dataclass
class LiveCfg:
    enabled: bool = False
    sandbox: bool = False
    exchange_id: str = "coinbase"
    exec_db: str = ""
    symbol: str = DEFAULT_SYMBOL
    max_submit_per_tick: int = 1
    reconcile_limit: int = 25

def cfg_from_yaml(path: str = "config/trading.yaml") -> LiveCfg:
    ensure_dirs()
    cfg = yaml.safe_load(open(path, "r", encoding="utf-8").read()) or {}
    live = cfg.get("live") or {}
    ex_cfg = cfg.get("execution") or {}
    return LiveCfg(
        enabled=bool(live.get("enabled", False)),
        sandbox=bool(live.get("sandbox", False)),
        exchange_id=str(live.get("exchange_id") or "coinbase").lower(),
        exec_db=str(ex_cfg.get("db_path") or (data_dir() / "execution.sqlite")),
        symbol=str((cfg.get("symbols") or [DEFAULT_SYMBOL])[0]),
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
    preflight_blocked = 0

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
            pnl_store = PnLStoreSQLite()
            pnl_today = pnl_store.get_today_realized() or {}
            rpnl = float((pnl_today.get('realized_pnl') or 0.0))
            if pnl_today.get("updated_ts") is None:
                fallback = JournalSignals(exec_db=cfg.exec_db).realized_pnl_today_usd()
                if fallback is not None:
                    rpnl = float(fallback)
            lp = (float(it['limit_price']) if it.get('limit_price') is not None else None)
            if lp is None:
                try:
                    ex = client.build()
                    t = ex.fetch_ticker(str(it['symbol']))
                    side0 = str(it.get('side') or '').lower()
                    if side0 == 'buy':
                        lp = float(t.get('ask') or t.get('last') or t.get('close') or 0.0) or None
                    else:
                        lp = float(t.get('bid') or t.get('last') or t.get('close') or 0.0) or None
                except Exception:
                    lp = None
            ok2, reason2, meta2 = gates.check_live(it={'qty': float(it.get('qty') or 0.0), 'price': lp, 'symbol': str(it.get('symbol') or '')}, realized_pnl_usd=rpnl)
            if not ok2:
                store.set_intent_status(intent_id=intent_id, status='pending', reason=f'live_gate_block:{reason2}')
                continue

            pf_ok, pf_reason, pf_meta = _check_preflight_gate(cfg)
            if not pf_ok:
                preflight_blocked += 1
                detail = str(pf_meta.get("error") or pf_reason)
                store.set_intent_status(intent_id=intent_id, status="pending", reason=f"preflight_gate_block:{pf_reason}:{detail}")
                # Pause state applies to all live submits this tick.
                if pf_reason in {"CIRCUIT_BREAKER_TRIPPED", "CIRCUIT_BREAKER_PAUSED"}:
                    break
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

            # LIVE_SUBMIT_SUCCESS_ANCHOR
            try:
                phase83_incr_trade_counter(cfg.exec_db, gate_db=gate_db)
            except Exception:
                pass

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

    return {"ok": True, "note": "submitted tick complete", "submitted": submitted, "errors": errors, "preflight_blocked": preflight_blocked}

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


# ---------------- PHASE 85: open-orders reconcile helpers ----------------
def _extract_client_id(o: dict) -> str:
    for k in ("clientOrderId", "client_order_id", "text"):
        v = o.get(k)
        if v:
            return str(v)
    info = o.get("info")
    if isinstance(info, dict):
        for k in ("clientOrderId", "client_order_id", "text", "client_id"):
            v = info.get(k)
            if v:
                return str(v)
    return ""

def reconcile_open_orders(exec_db: str, exchange_id: str, *, limit: int = 200) -> dict:
    ex_id = (exchange_id or "").lower().strip()
    store = OrderDedupeStore(exec_db=exec_db)
    client = ExchangeClient(exchange_id=ex_id, sandbox=False)
    rows = store.list_needs_reconcile(exchange_id=ex_id, limit=int(limit))
    by_sym = {}
    for r in rows:
        sym = str(r.get("symbol") or "")
        if sym:
            by_sym.setdefault(sym, []).append(r)
    matched = 0
    for sym, rs in by_sym.items():
        want = {str(r.get("client_order_id") or ""): str(r.get("intent_id") or "") for r in rs}
        want = {k:v for k,v in want.items() if k}
        if not want:
            continue
        try:
            oo = client.fetch_open_orders(symbol=sym) or []
        except Exception:
            oo = []
        for o in oo:
            cid = _extract_client_id(o)
            if cid and cid in want:
                intent_id = want[cid]
                rid = o.get("id")
                if rid:
                    store.set_remote_id_if_empty(exchange_id=ex_id, intent_id=intent_id, remote_order_id=str(rid))
                    store.mark_submitted(exchange_id=ex_id, intent_id=intent_id, remote_order_id=str(rid))
                    matched += 1
    return {"ok": True, "rows": len(rows), "matched_open": matched}

def _env_symbol(default: str = "BTC/USD") -> str:
    s = (os.environ.get("CBP_SYMBOLS") or "").split(",")[0].strip()
    return s or default

def _env_venue(default: str = "coinbase") -> str:
    v = (os.environ.get("CBP_VENUE") or "").strip()
    return (v or default).lower().strip()
