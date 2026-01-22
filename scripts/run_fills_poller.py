from __future__ import annotations
import asyncio, json, signal
from services.fills.fills_poller import FillsPoller, load_cfg

async def main_async() -> int:
    cfg = load_cfg("config/trading.yaml")
    p = FillsPoller(cfg)
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, p.stop)
        except Exception:
            pass
    print(json.dumps({"ok": True, "service": "fills_poller", "cfg": cfg.__dict__}, indent=2))
    await p.run()
    return 0

def main() -> int:
    return asyncio.run(main_async())

if __name__ == "__main__":
    raise SystemExit(main())
