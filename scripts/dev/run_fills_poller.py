from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)



# CBP_SCRIPT_SYSPATH_FIX_V1
import sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

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
