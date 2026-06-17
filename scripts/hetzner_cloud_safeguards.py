#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.ops.hetzner_cloud import (  # noqa: E402
    HetznerCloudError,
    apply_cloud_safeguards,
    plan_cloud_safeguards,
)
from services.security.hetzner_token_store import get_hetzner_api_token  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or apply Hetzner Cloud safeguards for the CryptKeep paper host."
        )
    )
    parser.add_argument(
        "--server-id",
        type=int,
        required=True,
        help="Hetzner server id to inspect or protect.",
    )
    parser.add_argument(
        "--ssh-source-cidr",
        action="append",
        default=[],
        help=(
            "Operator or VPN CIDR allowed to reach SSH. Repeat for multiple "
            "CIDRs. Broad internet CIDRs are rejected."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Apply the planned cloud changes. Without this flag the command "
            "performs read-only planning."
        ),
    )
    parser.add_argument(
        "--confirm-server-id",
        type=int,
        help="Required with --apply and must match --server-id exactly.",
    )
    return parser


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    token = get_hetzner_api_token()
    if not token:
        _print({"ok": False, "reason": "hetzner_token_not_configured"})
        return 1
    if args.apply and args.confirm_server_id is None:
        _print({"ok": False, "reason": "confirm_server_id_required"})
        return 1

    try:
        if args.apply:
            result = apply_cloud_safeguards(
                token,
                server_id=args.server_id,
                confirm_server_id=int(args.confirm_server_id),
                ssh_source_cidrs=list(args.ssh_source_cidr),
            )
        else:
            result = plan_cloud_safeguards(
                token,
                server_id=args.server_id,
                ssh_source_cidrs=list(args.ssh_source_cidr),
            )
    except HetznerCloudError as exc:
        result = {"ok": False, "reason": str(exc)}

    _print(result)
    return 0 if bool(result.get("ok")) else 1


if __name__ == "__main__":
    sys.exit(main())
