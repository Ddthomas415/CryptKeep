#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json

from services.analytics.paper_campaign_recovery import (
    DEFAULT_CONFIG_PATH,
    load_campaign_specs,
    manage_campaigns,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Check or idempotently restore configured paper evidence campaigns."
    )
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--status", action="store_true", help="Check configured campaign processes without starting them")
    mode.add_argument("--restore", action="store_true", help="Start only configured campaigns whose collectors are not alive")
    ap.add_argument(
        "--campaign",
        action="append",
        default=[],
        help="Limit the operation to a configured campaign name; may be repeated",
    )
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Paper campaign manifest path")
    args = ap.parse_args(argv)

    try:
        specs = load_campaign_specs(args.config, repo_root=ROOT)
        payload = manage_campaigns(
            specs,
            restore=bool(args.restore),
            selected_names=args.campaign,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "ok": False,
            "action": "restore" if args.restore else "status",
            "reason": f"invalid_campaign_config:{type(exc).__name__}",
        }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if bool(payload.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
