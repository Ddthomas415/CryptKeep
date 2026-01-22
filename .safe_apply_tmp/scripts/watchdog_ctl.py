from __future__ import annotations

import argparse
from services.process.watchdog_process import status, start_watchdog, stop_watchdog, clear_stale

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "start", "stop", "clear_stale"])
    ap.add_argument("--interval", type=int, default=15)
    ap.add_argument("--hard", action="store_true")
    args = ap.parse_args()

    if args.cmd == "status":
        print(status()); return
    if args.cmd == "start":
        print(start_watchdog(interval_sec=int(args.interval))); return
    if args.cmd == "stop":
        print(stop_watchdog(hard=bool(args.hard))); return
    if args.cmd == "clear_stale":
        print(clear_stale()); return

if __name__ == "__main__":
    main()
