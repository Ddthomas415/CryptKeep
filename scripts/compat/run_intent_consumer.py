#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)



import argparse

import json


RETIRED_REASON = "legacy_intent_consumer_retired"
CANONICAL_ENTRYPOINT = "scripts/run_intent_consumer_safe.py"


def _retired_payload() -> dict[str, object]:
    return {
        "ok": False,
        "reason": RETIRED_REASON,
        "canonical_entrypoint": CANONICAL_ENTRYPOINT,
    }


def _request_stop() -> object:
    from services.execution.intent_consumer import request_stop

    return request_stop()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Retired compatibility wrapper. Use "
            f"{CANONICAL_ENTRYPOINT} for managed intent consumption."
        )
    )
    ap.add_argument("cmd", choices=["run", "stop"], nargs="?", default="run")
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable retirement status.",
    )
    args = ap.parse_args(argv)
    if args.cmd == "stop":
        print(json.dumps(_request_stop(), sort_keys=True))
        return 0
    payload = _retired_payload()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"{RETIRED_REASON}: use {CANONICAL_ENTRYPOINT}",
            file=sys.stderr,
        )
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
