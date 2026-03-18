from __future__ import annotations

import logging
import math
import os
from services.security.binance_guard import require_binance_allowed
import time
from typing import Any, Dict, Optional, Tuple
from services.os.app_paths import data_dir, ensure_dirs

# The ONLY file allowed to call `.create_order(` directly.
# Everything else must call place_order/place_order_async.
#
# CBP_PHASE3_PLACE_ORDER_FAIL_CLOSED
# CBP_PHASE4_CHOKEPOINT_RISK_MARKET_V1

_LOG = logging.getLogger(__name__)

def _truthy(v: Optional[str]) -> bool:
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")

def _exec_db_path() -> str:
    ensure_dirs()
    return str(os.environ.get("EXEC_DB_PATH") or os.environ.get("CBP_DB_PATH") or (data_dir() / "execution.sqlite"))

def _venue_norm_for_market_rules(ex: Any) -> str:
    # ccxt exchange id (best effort)
    try:
        v = getattr(ex, "id", None)
        v = str(v).strip().lower() if v else "unknown"
    except Exception:
        v = "unknown"

    # normalize to services.markets.rules expected venue IDs
    if v in ("gateio", "gate.io", "gate"):
        return "gate"
    require_binance_allowed(v)
    if v.startswith("binance"):
        return "binance"
    if v in ("coinbase", "coinbasepro", "coinbase_adv"):
        return "coinbase"
    return v


def _load_killswitch_module() -> Any:
    from services.risk import killswitch as ks  # type: ignore

    return ks


def _killswitch_fail_closed() -> bool:
    raw = os.environ.get("CBP_KILLSWITCH_FAIL_CLOSED")
    if raw is None or str(raw).strip() == "":
        return True
    return _truthy(raw)


def _log_killswitch_probe_failure(*, stage: str, exc: Exception, fail_closed: bool) -> None:
    _LOG.warning(
        "place_order_killswitch_probe_failed",
        extra={
            "source": "services.risk.killswitch",
            "stage": stage,
            "failure_type": type(exc).__name__,
            "reason": str(exc),
            "fallback": "fail_closed_block" if fail_closed else "best_effort_allow",
        },
    )


def _killswitch_state() -> Tuple[bool, str]:
    if _truthy(os.environ.get("CBP_KILL_SWITCH")):
        return True, "env:CBP_KILL_SWITCH"

    fail_closed = _killswitch_fail_closed()

    try:
        ks = _load_killswitch_module()
    except Exception as exc:
        _log_killswitch_probe_failure(stage="import", exc=exc, fail_closed=fail_closed)
        if fail_closed:
            return True, f"services.risk.killswitch.import_failed:{type(exc).__name__}"
        return False, ""

    probe_available = False
    if hasattr(ks, "is_on") and callable(getattr(ks, "is_on")):
        probe_available = True
        try:
            if bool(ks.is_on()):
                return True, "services.risk.killswitch.is_on"
        except Exception as exc:
            _log_killswitch_probe_failure(stage="is_on", exc=exc, fail_closed=fail_closed)
            if fail_closed:
                return True, f"services.risk.killswitch.is_on_failed:{type(exc).__name__}"
            return False, ""

    if hasattr(ks, "snapshot") and callable(getattr(ks, "snapshot")):
        probe_available = True
        try:
            snap = ks.snapshot()
        except Exception as exc:
            _log_killswitch_probe_failure(stage="snapshot", exc=exc, fail_closed=fail_closed)
            if fail_closed:
                return True, f"services.risk.killswitch.snapshot_failed:{type(exc).__name__}"
            return False, ""

        if not isinstance(snap, dict):
            exc = TypeError("snapshot_not_dict")
            _log_killswitch_probe_failure(stage="snapshot", exc=exc, fail_closed=fail_closed)
            if fail_closed:
                return True, "services.risk.killswitch.snapshot_failed:TypeError"
            return False, ""

        if bool(snap.get("kill_switch", False)):
            return True, "services.risk.killswitch.snapshot.kill_switch"

        try:
            until = float(snap.get("cooldown_until", 0.0) or 0.0)
            if not math.isfinite(until):
                raise ValueError("cooldown_until_not_finite")
        except Exception as exc:
            _log_killswitch_probe_failure(stage="cooldown_read", exc=exc, fail_closed=fail_closed)
            if fail_closed:
                return True, f"services.risk.killswitch.cooldown_read_failed:{type(exc).__name__}"
            return False, ""

        if until > time.time():
            return True, "services.risk.killswitch.snapshot.cooldown_active"

    if not probe_available:
        exc = RuntimeError("no_killswitch_probe_available")
        _log_killswitch_probe_failure(stage="missing_probe", exc=exc, fail_closed=fail_closed)
        if fail_closed:
            return True, "services.risk.killswitch.missing_probe:RuntimeError"

    return False, ""

def _is_armed() -> Tuple[bool, str]:
    # Fail-closed unless explicitly armed
    if _truthy(os.environ.get("CBP_EXECUTION_ARMED")):
        return True, "env:CBP_EXECUTION_ARMED"
    if _truthy(os.environ.get("CBP_LIVE_ENABLED")):
        return True, "env:CBP_LIVE_ENABLED"
    if _truthy(os.environ.get("CBP_EXECUTION_LIVE_ENABLED")):
        return True, "env:CBP_EXECUTION_LIVE_ENABLED"
    return False, "not_armed"

def _require_env_float(name: str) -> float:
    v = os.environ.get(name)
    if v is None or str(v).strip() == "":
        raise RuntimeError(f"CBP_ORDER_BLOCKED:missing_limit_env:{name}")
    try:
        out = float(str(v).strip())
        if not math.isfinite(out):
            raise ValueError("non_finite_limit_env")
        return out
    except Exception:
        raise RuntimeError(f"CBP_ORDER_BLOCKED:invalid_limit_env:{name}")

def _normalize_loss_limit(x: float) -> float:
    # Accept either -250 or 250; normalize to negative threshold.
    return -abs(float(x))

def _extract_create_order_args(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[str, str, Any, Any | None, Dict[str, Any], str]:
    # ccxt.create_order(symbol, type, side, amount, price=None, params={})
    symbol = str(args[0] if len(args) > 0 else (kwargs.get("symbol") or ""))
    otype = str(args[1] if len(args) > 1 else (kwargs.get("type") or ""))
    side = str(args[2] if len(args) > 2 else (kwargs.get("side") or ""))
    amount = args[3] if len(args) > 3 else kwargs.get("amount")

    price_val = None
    if len(args) > 4:
        price_val = args[4]
    elif "price" in kwargs:
        price_val = kwargs.get("price")

    params_val = args[5] if len(args) > 5 else kwargs.get("params")
    params = dict(params_val) if isinstance(params_val, dict) else {}

    return symbol, side, amount, price_val, params, otype


def _parse_order_amount(amount: Any) -> float:
    try:
        out = float(amount)
    except Exception as exc:
        raise RuntimeError(f"CBP_ORDER_BLOCKED:invalid_amount:{type(exc).__name__}") from exc
    if not math.isfinite(out):
        raise RuntimeError("CBP_ORDER_BLOCKED:invalid_amount:non_finite")
    if out <= 0:
        raise RuntimeError("CBP_ORDER_BLOCKED:invalid_amount:non_positive")
    return out


def _parse_order_price(price: Any | None, *, order_type: str) -> float | None:
    normalized_type = str(order_type or "").strip().lower()
    if price is None:
        if normalized_type == "limit":
            raise RuntimeError("CBP_ORDER_BLOCKED:missing_limit_price")
        return None
    try:
        out = float(price)
    except Exception as exc:
        raise RuntimeError(f"CBP_ORDER_BLOCKED:invalid_price:{type(exc).__name__}") from exc
    if not math.isfinite(out):
        raise RuntimeError("CBP_ORDER_BLOCKED:invalid_price:non_finite")
    if out <= 0:
        raise RuntimeError("CBP_ORDER_BLOCKED:invalid_price:non_positive")
    return out


def _boolish(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def _is_reduce_only(params: Dict[str, Any]) -> bool:
    if not isinstance(params, dict):
        return False
    if _boolish(params.get("reduceOnly")):
        return True
    if _boolish(params.get("reduce_only")):
        return True
    return False


def _load_latest_ops_risk_gate() -> Optional[Dict[str, Any]]:
    try:
        from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite

        db_path = str(os.environ.get("CBP_OPS_DB_PATH") or "").strip()
        store = OpsSignalStoreSQLite(path=db_path)
        return store.latest_risk_gate()
    except Exception:
        return None


def _enforce_ops_risk_gate(*, params: Dict[str, Any]) -> None:
    # Optional advanced mode: ops system emits a gate, bot execution enforces it.
    if not _truthy(os.environ.get("CBP_OPS_RISK_GATE_ENFORCE")):
        return

    fail_closed = _truthy(os.environ.get("CBP_OPS_RISK_GATE_FAIL_CLOSED"))
    gate_payload = _load_latest_ops_risk_gate()
    if not gate_payload:
        if fail_closed:
            raise RuntimeError("CBP_ORDER_BLOCKED:ops_risk_gate_missing")
        return

    try:
        from services.ops.risk_gate_contract import RiskGateSignal, evaluate_gate_for_order

        gate = RiskGateSignal.from_dict(gate_payload)
    except Exception as e:
        if fail_closed:
            raise RuntimeError(f"CBP_ORDER_BLOCKED:ops_risk_gate_invalid:{type(e).__name__}:{e}")
        return

    allow, reason = evaluate_gate_for_order(gate.gate_state, reduce_only=_is_reduce_only(params))
    if allow:
        return

    hazards = ",".join(gate.hazards[:3]) if gate.hazards else "none"
    raise RuntimeError(
        "CBP_ORDER_BLOCKED:ops_risk_gate:"
        f"{reason}:state={gate.gate_state.value}:hazards={hazards}"
    )

def _enforce_fail_closed(
    ex: Any,
    *,
    symbol: str,
    side: str,
    amount: Any,
    price: Any | None,
    params: Dict[str, Any],
    order_type: str,
) -> Tuple[str, float | None]:
    amount_f = _parse_order_amount(amount)
    price_f = _parse_order_price(price, order_type=order_type)

    # 1) Kill switch
    ks_on, ks_src = _killswitch_state()
    if ks_on:
        raise RuntimeError(f"CBP_ORDER_BLOCKED:kill_switch_on ({ks_src})")

    # 2) Explicit arming required
    armed, _why = _is_armed()
    if not armed:
        raise RuntimeError(
            "CBP_ORDER_BLOCKED:fail_closed_not_armed "
            "(set CBP_EXECUTION_ARMED=1 or CBP_LIVE_ENABLED=1 to allow create_order)"
        )

    # 3) Optional ops risk gate
    _enforce_ops_risk_gate(params=params)

    # 4) Limits must exist (fail closed if missing)
    max_trades_per_day = _require_env_float("CBP_MAX_TRADES_PER_DAY")
    max_daily_loss = _normalize_loss_limit(_require_env_float("CBP_MAX_DAILY_LOSS"))
    max_daily_notional = _require_env_float("CBP_MAX_DAILY_NOTIONAL")
    max_order_notional = _require_env_float("CBP_MAX_ORDER_NOTIONAL")

    # 5) Market orders disabled by default in LIVE
    allow_market = _truthy(os.environ.get("CBP_ALLOW_MARKET_ORDERS"))
    if price_f is None and not allow_market:
        raise RuntimeError("CBP_ORDER_BLOCKED:market_orders_disabled (set CBP_ALLOW_MARKET_ORDERS=1 to allow)")

    notional = None
    if price_f is not None:
        notional = amount_f * price_f

    if notional is not None and notional > float(max_order_notional):
        raise RuntimeError(f"CBP_ORDER_BLOCKED:order_notional_exceeds_limit notional={notional} max={max_order_notional}")

    # 6) Deterministic daily state (risk_daily)
    exec_db = _exec_db_path()
    try:
        from services.risk import risk_daily as rd  # type: ignore
        snap = rd.snapshot(exec_db=exec_db)
    except Exception as e:
        raise RuntimeError(f"CBP_ORDER_BLOCKED:missing_risk_daily_snapshot:{type(e).__name__}")

    if not isinstance(snap, dict) or not snap:
        raise RuntimeError("CBP_ORDER_BLOCKED:missing_risk_daily_snapshot")

    trades_today = float(snap.get("trades", 0) or 0)
    pnl_today = float(snap.get("pnl", 0) or 0)
    daily_notional = float(snap.get("notional", 0) or 0)

    if trades_today >= float(max_trades_per_day):
        raise RuntimeError(f"CBP_ORDER_BLOCKED:max_trades_per_day trades={trades_today} max={max_trades_per_day}")

    if pnl_today <= float(max_daily_loss):
        raise RuntimeError(f"CBP_ORDER_BLOCKED:max_daily_loss pnl={pnl_today} limit={max_daily_loss}")

    if notional is not None and (daily_notional + notional) > float(max_daily_notional):
        raise RuntimeError(f"CBP_ORDER_BLOCKED:max_daily_notional daily={daily_notional} add={notional} max={max_daily_notional}")

    # 7) Market rules prereq + validate (fail closed)
    venue = _venue_norm_for_market_rules(ex)
    ttl_s = float(os.environ.get("CBP_MARKET_RULES_TTL_S") or 6 * 3600.0)
    try:
        from services.markets.prereq import check_market_rules_prereq  # type: ignore
        pre = check_market_rules_prereq(exec_db=exec_db, ttl_s=ttl_s)
        ok = bool(getattr(pre, "ok", False))
        if not ok:
            msg = str(getattr(pre, "message", "MARKET_RULES_PREREQ_FAILED"))
            raise RuntimeError(msg)
    except Exception as e:
        raise RuntimeError(f"CBP_ORDER_BLOCKED:market_rules_prereq_failed:{type(e).__name__}:{e}")

    try:
        from services.markets.rules import validate as mr_validate  # type: ignore
        vres = mr_validate(exec_db, venue, symbol, qty=amount_f, notional=notional, ttl_s=ttl_s)
        ok = bool(getattr(vres, "ok", False))
        if not ok:
            code = str(getattr(vres, "code", "MARKET_RULES_FAIL"))
            msg = str(getattr(vres, "message", "Market rules validation failed"))
            raise RuntimeError(f"{code}:{msg}")
    except Exception as e:
        raise RuntimeError(f"CBP_ORDER_BLOCKED:market_rules_invalid:{type(e).__name__}:{e}")

    return exec_db, notional

def place_order(ex: Any, *args: Any, **kwargs: Any) -> Any:
    symbol, side, amount, price, params, otype = _extract_create_order_args(args, kwargs)
    exec_db, notional = _enforce_fail_closed(ex, symbol=symbol, side=side, amount=amount, price=price, params=params, order_type=otype)
    o = ex.create_order(*args, **kwargs)

    # Best-effort: count submits toward daily state (fills will refine pnl later)
    try:
        from services.risk import risk_daily as rd  # type: ignore
        if hasattr(rd, "record_order_attempt"):
            rd.record_order_attempt(notional_usd=notional, exec_db=exec_db)
    except Exception:
        pass

    return o

async def place_order_async(ex: Any, *args: Any, **kwargs: Any) -> Any:
    symbol, side, amount, price, params, otype = _extract_create_order_args(args, kwargs)
    exec_db, notional = _enforce_fail_closed(ex, symbol=symbol, side=side, amount=amount, price=price, params=params, order_type=otype)
    o = await ex.create_order(*args, **kwargs)

    try:
        from services.risk import risk_daily as rd  # type: ignore
        if hasattr(rd, "record_order_attempt"):
            rd.record_order_attempt(notional_usd=notional, exec_db=exec_db)
    except Exception:
        pass

    return o

def _cbp_guard_binance(ex_id: str) -> None:
    require_binance_allowed(ex_id)
