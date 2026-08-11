#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json

from services.security.credential_source_posture import credential_source_posture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report exchange credential source posture without printing values.")
    parser.add_argument("--venue", action="append", default=[], help="venue to inspect; may be repeated")
    parser.add_argument("--fail-on-env", action="store_true", help="exit nonzero when usable credentials come from env")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)

    report = credential_source_posture(venues=list(args.venue or []) or None)
    if args.fail_on_env and report.get("env_credential_venues"):
        report["ok"] = False
        report["status"] = "env_credentials_active"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status={report.get('status')}")
        print(f"read_only={report.get('read_only')}")
        for row in report.get("venues") or []:
            print(
                f"- {row.get('venue')}: source={row.get('source')} "
                f"api_key_present={row.get('api_key_present')} "
                f"secret_present={row.get('secret_present')}"
            )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
