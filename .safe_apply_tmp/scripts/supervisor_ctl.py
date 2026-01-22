from __future__ import annotations

import argparse
from pathlib import Path

from services.process.supervisor_process import status, stop

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "stop"])
    ap.add_argument("--hard", action="store_true")
    args = ap.parse_args()

    if args.cmd == "status":
        print(status()); return
    if args.cmd == "stop":
        print(stop(hard=bool(args.hard))); return

if __name__ == "__main__":
    main()
