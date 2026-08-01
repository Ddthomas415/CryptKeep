#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.events.platform_event_journal import SUPPORTED_EVENT_TYPES, summarize_platform_events


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize the append-only platform event journal."
    )
    parser.add_argument("--path", default="")
    parser.add_argument("--event-type", choices=SUPPORTED_EVENT_TYPES)
    parser.add_argument("--require-events", action="store_true")
    args = parser.parse_args()

    report = summarize_platform_events(
        Path(args.path) if args.path else None,
        event_type=args.event_type,
        require_events=args.require_events,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

