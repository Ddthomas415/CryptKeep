#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import getpass
import json

from services.security.hetzner_token_store import (
    delete_hetzner_api_token,
    hetzner_api_token_status,
    set_hetzner_api_token,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Store, inspect, or delete the Hetzner read-only API token in the OS keyring."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--status", action="store_true", help="Report whether a token is stored")
    mode.add_argument("--delete", action="store_true", help="Delete the stored token")
    args = parser.parse_args(argv)

    if args.status:
        result = hetzner_api_token_status()
    elif args.delete:
        result = delete_hetzner_api_token()
    else:
        token = getpass.getpass("New Hetzner read-only API token: ")
        confirmation = getpass.getpass("Confirm token: ")
        if token != confirmation:
            result = {"ok": False, "reason": "token_confirmation_mismatch"}
        else:
            result = set_hetzner_api_token(token)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if bool(result.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
