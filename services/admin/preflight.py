import asyncio
import os
from services.admin.kill_switch import get_state as kill_state, ensure_default as ensure_kill_default
from services.security.private_connectivity import test_private_connectivity
from services.security.permission_probes import run_probes, DEFAULT_PROBES

async def run_preflight(venues=["binance","coinbase","gateio"], symbols=["BTC/USDT"]):
    ensure_kill_default()
    return {"venues": venues, "symbols": symbols, "kill_switch": kill_state()}

if __name__ == "__main__":
    print(asyncio.run(run_preflight()))
