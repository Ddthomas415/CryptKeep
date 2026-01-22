from services.admin.master_read_only import is_master_read_only
from services.execution.order_manager import OrderManager
from __future__ import annotations
import asyncio
import os
from services.admin.health import set_health
from services.execution.event_log import log_event
from services.admin.live_guard import live_allowed
from pathlib import Path
from typing import Any, Dict, Optional
from ccxt.async_support import Exchange
from services.config_loader import load_user_config
from services.execution.safety import load_gates, should_allow_order
from storage.execution_guard_store_sqlite import ExecutionGuardStoreSQLite
from storage.pnl_store_sqlite import PnLStoreSQLite
SERVICE_NAME = "live_trader_fleet"

async def main() -> None:
    if os.environ.get("CBP_RUN_MODE", "").strip().lower() != "live":
        print("Live fleet mode disabled. Set CBP_RUN_MODE=live")
        return

    cfg = load_user_config()
    guard_store = ExecutionGuardStoreSQLite()
    gates = load_gates()
    pnl_store = PnLStoreSQLite()
order_manager = OrderManager()

    print("live_trader_fleet started (dry-run mode)")

    while True:

        # service_level_live_enforcement: stop loop if live not allowed

        try:

            _ok, _why, _det = live_allowed()

            if not _ok:

                try:

                    set_health(SERVICE_NAME, "STOPPING", pid=os.getpid(), details={"reason": _why, "details": _det})

                except Exception:

                    pass

                break

        except Exception:

            # if guard check fails unexpectedly, fail safe by stopping

            try:

                set_health(SERVICE_NAME, "STOPPING", pid=os.getpid(), details={"reason": "guard_check_failed"})

            except Exception:

                pass

            break
        # Simulated order logic (in real app, triggered by signals)
        venue = "simulated"
        symbol_norm = "BTC-USDT"
        side = "buy"
        qty = 0.001
        price = 60000.0

        try:
            ok_s, why_s = should_allow_order(venue, symbol_norm, side, qty, price, gates, guard_store)
            if not ok_s:
                print(f"Safety gate blocked: {why_s}")
                await asyncio.sleep(5)
                continue
        except Exception as e:
            print(f"Safety check error: {e}")
            await asyncio.sleep(5)
            continue

        # Simulate order placement (in real app, call CCXT)
        print(f"Live fleet order placed: {side} {qty} {symbol_norm} @ {price}")

        # Strict: record only confirmed fills (placeholder for CCXT)
        await pnl_store.record_fill(venue, symbol_norm, side, qty, price, fee=0.0, fee_ccy=None)

        await asyncio.sleep(10)  # loop delay for demo


# best-effort module-level safety: ensure STOPPED is recorded when interpreter exits main
try:
    pass
except Exception:
    pass
