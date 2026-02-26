from __future__ import annotations
from services.markets.symbols import env_symbol
from services.markets.symbols import env_symbol, normalize_symbol
import asyncio
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from ccxt.async_support import Exchange
from services.config_loader import load_user_config
from services.execution.safety import load_gates, should_allow_order
from storage.execution_guard_store_sqlite import ExecutionGuardStoreSQLite
from services.execution.latency import sleep_paper_latency
from storage.pnl_store_sqlite import PnLStoreSQLite

def _env_on(name: str) -> bool:
    return (os.environ.get(name, "") or "").strip().lower() in ("1", "true", "yes", "on")

async def main() -> None:
    if not _env_on("CBP_RUN_MODE") == "paper":
        print("Paper mode disabled. Set CBP_RUN_MODE=paper")
        return

    cfg = load_user_config()
    guard_store = ExecutionGuardStoreSQLite()
    gates = load_gates()
    pnl_store = PnLStoreSQLite()

    print("paper executor started (simulated mode)")

    while True:
        # Simulate order logic (in real app, this would be triggered by signals)
        venue = "simulated"
        symbol_norm = env_symbol(venue=os.environ.get("CBP_VENUE") or "coinbase", out="dash")
        side = "buy"
        qty = 0.001
        price = 60000.0  # simulated price

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

        # Simulate latency
        latency_ms = sleep_paper_latency()
        print(f"Paper latency applied: {latency_ms} ms")

        # Simulate fill (in real app, this would be from exchange confirmation)
        fee = 0.0  # simulated
        await pnl_store.record_fill(venue, symbol_norm, side, qty, price, fee=fee, fee_ccy=None)

        # Update guard store
        await guard_store.record_order(venue, symbol_norm, side, qty, price)

        print(f"Paper order simulated: {side} {qty} {symbol_norm} @ {price}")

        await asyncio.sleep(10)  # loop delay for demo

if __name__ == "__main__":
    asyncio.run(main())
