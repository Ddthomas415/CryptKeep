#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


# CBP_BOOTSTRAP: ensure repo root on sys.path so `import services` works when running scripts directly
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
from services.supervisor.supervisor import start, stop, status

def main():
    ap = argparse.ArgumentParser(description="CryptoBotPro Supervisor (start/stop/status).")
    ap.add_argument("cmd", choices=["start","stop","status"], nargs="?", default="status")
    ap.add_argument("--no-dashboard", action="store_true")
    ap.add_argument("--no-tick", action="store_true")
    ap.add_argument("--no-webhook", action="store_true")
    ap.add_argument("--host", default=None)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--timeout-sec", type=int, default=6)
    args = ap.parse_args()
    if args.cmd == "status":
        print(json.dumps(status(), indent=2))
        return 0
    if args.cmd == "start":
        out = start(
            with_dashboard=not args.no_dashboard,
            start_tick=not args.no_tick,
            start_webhook=not args.no_webhook,
            host=args.host,
            port=args.port,
            open_browser=not args.no_browser,
        )
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 2
    out = stop(
        stop_dashboard=not args.no_dashboard,
        stop_tick=not args.no_tick,
        stop_webhook=not args.no_webhook,
        timeout_sec=int(args.timeout_sec),
    )
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 2

if __name__ == "__main__":
    raise SystemExit(main())
