from __future__ import annotations

import argparse
from services.process.watchdog import run_watchdog_once, run_watchdog_loop, read_last

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=15)
    ap.add_argument("--show_last", action="store_true")
    args = ap.parse_args()

    if args.show_last:
        print(read_last()); return
    if args.loop:
        run_watchdog_loop(interval_sec=int(args.interval)); return
    # default: once
    print(run_watchdog_once())

if __name__ == "__main__":
    main()
