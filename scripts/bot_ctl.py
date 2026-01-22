from __future__ import annotations

import argparse
from services.process.bot_process import start_bot, stop_bot, stop_all, status

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "start", "stop", "stop_all"])
    ap.add_argument("--venue", default="binance")
    ap.add_argument("--symbols", default="BTC/USDT", help="Comma list")
    ap.add_argument("--force", action="store_true", help="Start even if preflight fails (unsafe)")
    ap.add_argument("--hard", action="store_true", help="Hard stop (kill)")
    args = ap.parse_args()

    if args.cmd == "status":
        print(status()); return
    if args.cmd == "start":
        syms = [s.strip().upper().replace("-", "/") for s in args.symbols.split(",") if s.strip()]
        print(start_bot(venue=args.venue, symbols=syms, force=bool(args.force))); return
    if args.cmd == "stop":
        print(stop_bot(hard=bool(args.hard))); return
    if args.cmd == "stop_all":
        print(stop_all(hard=bool(args.hard))); return

if __name__ == "__main__":
    main()
