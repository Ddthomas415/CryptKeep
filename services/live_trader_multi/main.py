from __future__ import annotations

import asyncio
import os

from services.admin.health import set_health
from services.admin.live_guard import live_allowed
from services.execution.safety import load_gates, should_allow_order
from services.markets.symbols import env_symbol
from storage.execution_guard_store_sqlite import ExecutionGuardStoreSQLite
from storage.pnl_store_sqlite import PnLStoreSQLite

SERVICE_NAME = "live_trader_multi"


async def main() -> None:
    if os.environ.get("CBP_RUN_MODE", "").strip().lower() != "live":
        print("Live multi mode disabled. Set CBP_RUN_MODE=live")
        return

    guard_store = ExecutionGuardStoreSQLite()
    gates = load_gates()
    pnl_store = PnLStoreSQLite()

    print("live_trader_multi started (dry-run mode)")

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
        symbol_norm = env_symbol(venue=os.environ.get("CBP_VENUE") or "coinbase", out="dash")
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
        print(f"Live multi order placed: {side} {qty} {symbol_norm} @ {price}")

        # Strict: record only confirmed fills (placeholder for CCXT)
        await pnl_store.record_fill(venue, symbol_norm, side, qty, price, fee=0.0, fee_ccy=None)
        await guard_store.record_order(venue, symbol_norm, side, qty, price)

        await asyncio.sleep(10)  # loop delay for demo


if __name__ == "__main__":
    asyncio.run(main())
