#!/usr/bin/env python3
from __future__ import annotations
import argparse
from services.signals.webhook_server import run

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    args = ap.parse_args()
    run(args.host, args.port)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
