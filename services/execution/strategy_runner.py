import traceback
import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
import threading
import time
from services.execution.execution_throttle import can_trade, record_trade
from services.execution.orderbook_sanity import check_orderbook
from services.execution.event_log import log_event
from services.execution.execution_latency import ExecutionLatencyTracker
from storage.market_ws_store_sqlite import SQLiteMarketWsStore

# -------------------------------------------------------------------
# Mock strategy runner placeholders
# -------------------------------------------------------------------
def run_once():
    """
    Replace this logic with your actual strategy computation.
    Currently simulates action and applies throttle/orderbook checks.
    """
    # --- Strategy logic placeholder ---
    action = "hold"
    side = None
    reason = "insufficient_candles"
    print(f"[EXECUTE] Action={action} Side={side} Reason={reason}")

    # --- Throttle check ---
    throttle = can_trade(venue=VENUE, symbol=SYMBOL, min_seconds_between_orders=20)
    if not throttle.ok:
        print(f"[THROTTLE] Waiting {throttle.wait_seconds:.1f}s before next order")
        return
    else:
        record_trade(venue=VENUE, symbol=SYMBOL)
        print("[THROTTLE] Trade executed and recorded")

    # --- Optional orderbook sanity check (OFF by default) ---
    ob_sanity = check_orderbook(
        venue=VENUE,
        symbol=SYMBOL,
        max_spread_bps=30.0,
        min_top_quote=50.0
    )
    if not ob_sanity.get("ok", False):
        print(f"[SANITY] Orderbook check failed: {ob_sanity.get('reason')}")
    else:
        print(f"[SANITY] Orderbook OK: bid={ob_sanity.get('bid_px')} ask={ob_sanity.get('ask_px')}")

# -------------------------------------------------------------------
# Continuous loop
# -------------------------------------------------------------------
_SHUTDOWN_EVENT = threading.Event()
_SIGNAL_HANDLERS_INSTALLED = False


def request_shutdown(reason: str = "requested") -> None:
    if _SHUTDOWN_EVENT.is_set():
        return
    _SHUTDOWN_EVENT.set()
    try:
        log_event(VENUE, SYMBOL, "strategy_shutdown", payload={"reason": str(reason)})
    except Exception:
        pass


def _handle_shutdown_signal(signum: int, _frame) -> None:
    request_shutdown(reason=f"signal_{int(signum)}")


def _install_shutdown_signal_handlers() -> None:
    global _SIGNAL_HANDLERS_INSTALLED
    if _SIGNAL_HANDLERS_INSTALLED:
        return
    for sig_name in ("SIGTERM", "SIGINT"):
        sig_obj = getattr(signal, sig_name, None)
        if sig_obj is None:
            continue
        try:
            signal.signal(sig_obj, _handle_shutdown_signal)
        except Exception:
            continue
    _SIGNAL_HANDLERS_INSTALLED = True


def run_forever(interval_sec: float = 10.0) -> None:
    _install_shutdown_signal_handlers()
    _SHUTDOWN_EVENT.clear()
    print("[LIVE] Starting modular live strategy runner...")
    while not _SHUTDOWN_EVENT.is_set():
        try:
            _runner_iteration()
        except Exception as e:
            log_event(VENUE, SYMBOL, "strategy_error", payload={"error": f"{type(e).__name__}: {e}"})
            traceback.print_exc()
        if _SHUTDOWN_EVENT.wait(max(0.05, float(interval_sec))):
            break
    print("[LIVE] strategy runner stopped cleanly")

_LATENCY_TRACKER = ExecutionLatencyTracker(store=SQLiteMarketWsStore())


def _runner_iteration() -> None:
    if _SHUTDOWN_EVENT.is_set():
        return
    log_event(VENUE, SYMBOL, "strategy_heartbeat", payload={"timestamp": time.time()})
    _record_heartbeat_latency()
    try:
        run_once()
    except Exception as exc:
        log_event(VENUE, SYMBOL, "strategy_error", payload={"error": f"{type(exc).__name__}: {exc}"})
        raise


def _record_heartbeat_latency() -> None:
    try:
        client_order_id = f"heartbeat-{int(time.time() * 1000)}"
        _LATENCY_TRACKER.record_submit(
            client_order_id=client_order_id,
            exchange=VENUE,
            symbol=SYMBOL,
            side="heartbeat",
            qty=0.0,
        )
        _LATENCY_TRACKER.record_ack(
            client_order_id=client_order_id,
            exchange=VENUE,
            symbol=SYMBOL,
        )
        _LATENCY_TRACKER.record_fill(
            client_order_id=client_order_id,
            exchange=VENUE,
            symbol=SYMBOL,
            price=None,
            qty=None,
        )
    except Exception:
        pass

# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    run_forever()

# --- compat entrypoint for scripts/run_bot_safe.py ---
def run(*args, **kwargs):
    # Try common runner function names
    for fn_name in ("run_loop", "run_forever", "start", "serve", "loop", "run_once"):
        fn = globals().get(fn_name)
        if callable(fn):
            return fn(*args, **kwargs)
    raise SystemExit("strategy_runner: no runnable function found (expected one of run_loop/run_forever/start/serve/loop/run_once)")

# --- compat entrypoint for scripts/run_bot_safe.py ---
def main(argv=None):
    # ignore argv to keep signature flexible
    if callable(globals().get("run")):
        return globals()["run"]()
    for fn_name in ("run_loop", "run_forever", "start", "serve", "loop", "run_once"):
        fn = globals().get(fn_name)
        if callable(fn):
            return fn()
    raise SystemExit("strategy_runner: no runnable function found (expected run or run_loop/run_forever/start/serve/loop/run_once)")


# ---- runtime overrides from env (set by scripts/bot_ctl.py) ----
VENUE = (os.environ.get("CBP_VENUE") or os.environ.get("VENUE") or "coinbase").lower()
_symbols_raw = os.environ.get("CBP_SYMBOLS") or os.environ.get("SYMBOLS") or ""
SYMBOL = ([x.strip() for x in _symbols_raw.split(",") if x.strip()] or ["BTC/USD"])[0]


# ---- runtime defaults (prefer env set by bot_ctl / run_bot_safe) ----
DEFAULT_VENUE = (os.environ.get("CBP_VENUE") or "coinbase").lower().strip()
DEFAULT_SYMBOL = ([x.strip() for x in (os.environ.get("CBP_SYMBOLS") or "").split(",") if x.strip()] or ["BTC/USD"])[0]

# --- env helpers (Bundle 58): dynamic venue/symbol ---
def _env_venue(default: str = "coinbase") -> str:
    import os
    return (os.environ.get("CBP_VENUE") or default).lower().strip()

def _env_symbol(default: str = "BTC/USD") -> str:
    import os
    raw = (os.environ.get("CBP_SYMBOLS") or "").strip()
    if raw:
        parts = [x.strip() for x in raw.split(",") if x.strip()]
        if parts:
            return parts[0]
    return default

_venue = _env_venue()
_symbol = _env_symbol()
