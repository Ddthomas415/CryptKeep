from __future__ import annotations

import argparse

from cbp_desktop.service_manager import specs_default, start_service, stop_service, is_running


def main() -> int:
    specs = specs_default()

    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["list", "start", "stop", "status"])
    p.add_argument("--name", default="")
    args = p.parse_args()

    if args.cmd == "list":
        for k in specs:
            print(k)
        return 0

    name = args.name.strip()
    if not name:
        print("ERROR: --name required")
        return 2
    if name not in specs:
        print("ERROR: unknown service:", name)
        return 3

    if args.cmd == "status":
        ok, msg = is_running(name)
        print(name, "running=" + str(ok), msg)
        return 0

    if args.cmd == "start":
        ok, msg = start_service(specs[name])
        print(name, msg)
        return 0 if ok else 4

    if args.cmd == "stop":
        ok, msg = stop_service(name)
        print(name, msg)
        return 0 if ok else 5

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
