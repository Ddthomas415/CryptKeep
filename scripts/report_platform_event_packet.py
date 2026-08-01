#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

_REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json
import time

from services.events.platform_event_packet import build_platform_event_packet_report

EXIT_OK = 0
EXIT_FAIL = 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a read-only platform event evidence-packet report."
    )
    parser.add_argument("--path", default="", help="platform event JSONL path; defaults to the repo state path")
    parser.add_argument("--require-events", action="store_true", help="fail if the journal is missing or empty")
    parser.add_argument("--json", action="store_true", help="print the full JSON report")
    parser.add_argument("--evidence-dest", default="", help="write the JSON report into this directory")
    args = parser.parse_args()

    report = build_platform_event_packet_report(
        Path(args.path) if args.path else None,
        require_events=bool(args.require_events),
    )

    if args.evidence_dest:
        dest = Path(args.evidence_dest)
        dest.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        out_path = dest / f"platform-event-packet-{stamp}.json"
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        report["evidence_path"] = str(out_path)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        verdict = "ok" if report["ok"] else "FAIL"
        print(f"platform event packet: {verdict}")
        print(f"path: {report['path']}")
        print(f"events: {report['event_count']}")
        for name, ok in report["checks"].items():
            label = "ok" if ok else "FAIL"
            print(f"{name}: {label} ({report['reasons'][name]})")
        if "evidence_path" in report:
            print(f"evidence: {report['evidence_path']}")

    return EXIT_OK if report["ok"] else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())

