from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.desktop.simple_service_manager import (
    specs_default,
    start_service,
    stop_service,
    status_service,
    is_running,
    tail_log,
)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="", help="service name")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")
    sub.add_parser("start")
    sub.add_parser("stop")
    sub.add_parser("restart")
    sub.add_parser("status")
    logs = sub.add_parser("logs")
    logs.add_argument("--lines", type=int, default=80)

    args = ap.parse_args()
    specs = {s.name: s for s in specs_default()}

    if args.cmd == "list":
        for n in specs.keys():
            print(n)
        return 0

    if not args.name:
        print("missing --name", file=sys.stderr)
        return 2
    if args.name not in specs:
        print(f"unknown service: {args.name}", file=sys.stderr)
        return 2

    spec = specs[args.name]

    if args.cmd == "start":
        print(start_service(spec))
        return 0
    if args.cmd == "stop":
        print(stop_service(spec.name, hard=False))
        return 0
    if args.cmd == "restart":
        stop_service(spec.name, hard=False)
        print(start_service(spec))
        return 0
    if args.cmd == "status":
        print(status_service(spec.name))
        return 0
    if args.cmd == "logs":
        print(tail_log(spec.name, lines=args.lines))
        return 0

    return 2

if __name__ == "__main__":
    raise SystemExit(main())
