#!/usr/bin/env python3
from __future__ import annotations
import argparse
from services.meta.meta_strategy_runner import run_forever, stop

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "stop"], nargs="?", default="run")
    args = ap.parse_args()
    if args.cmd == "stop":
        stop()
        print({"ok": True, "stopped": True})
        return 0
    run_forever()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
