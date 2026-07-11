#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.analytics.edge_cadence import check_edge_cadence

EXIT_HEALTHY = 0
EXIT_STALE = 1
EXIT_MISSING = 2


def _dispatch_alert(result: dict) -> None:
    try:
        from services.alerts.alert_dispatcher import send_alert
        from services.config_loader import load_runtime_trading_config

        try:
            cfg = load_runtime_trading_config()
        except Exception:
            cfg = {}
        missing = list(result.get("missing") or [])
        stale = list(result.get("stale") or [])
        level = "critical" if missing or result.get("store_error") else "warning"
        send_alert(
            cfg=cfg if isinstance(cfg, dict) else {},
            level=level,
            message=f"edge_collector_cadence:{'missing' if missing else 'stale'}",
            payload=result,
        )
    except Exception as exc:
        print(f"alert dispatch unavailable: {type(exc).__name__}: {exc}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only crypto-edge collector cadence check.")
    parser.add_argument("--store-path", default=None, help="override crypto-edge SQLite store path")
    parser.add_argument("--json", action="store_true", help="print JSON result")
    parser.add_argument("--alert", action="store_true", help="dispatch an alert on stale/missing cadence")
    args = parser.parse_args(argv)

    result = check_edge_cadence(store_path=args.store_path)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["ok"]:
        print(f"edge cadence OK: {', '.join(result['checked']) or '(none)'}")
    else:
        if result.get("store_error"):
            print(f"edge cadence FAIL store_error={result['store_error']}")
        if result.get("missing"):
            print(f"edge cadence MISSING: {', '.join(result['missing'])}")
        if result.get("stale"):
            print(f"edge cadence STALE: {', '.join(result['stale'])}")

    if args.alert and not result["ok"]:
        _dispatch_alert(result)

    if result.get("store_error") or result.get("missing"):
        return EXIT_MISSING
    if result.get("stale"):
        return EXIT_STALE
    return EXIT_HEALTHY


if __name__ == "__main__":
    raise SystemExit(main())
