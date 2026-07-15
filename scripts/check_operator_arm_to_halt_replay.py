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

from services.audit.operator_event_replay import replay_live_arm_to_halt, report_to_json

EXIT_OK = 0
EXIT_FAIL = 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replay a live arm-to-halt drill from operator-event journal records."
    )
    parser.add_argument("--path", default="", help="operator event JSONL path; defaults to the repo state path")
    parser.add_argument("--json", action="store_true", help="print the full JSON report")
    parser.add_argument("--evidence-dest", default="", help="write the JSON report into this directory")
    args = parser.parse_args()

    report = replay_live_arm_to_halt(Path(args.path) if args.path else None)
    if args.evidence_dest:
        dest = Path(args.evidence_dest)
        dest.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        out_path = dest / f"operator-arm-to-halt-replay-{stamp}.json"
        out_path.write_text(report_to_json(report), encoding="utf-8")
        report["evidence_path"] = str(out_path)

    if args.json:
        print(report_to_json(report))
    else:
        verdict = "ok" if report["ok"] else "FAIL"
        print(f"operator arm-to-halt replay: {verdict}")
        print(f"path: {report['path']}")
        print(f"events: {report['event_count']}")
        print(f"reason: {report['reason']}")
        if report.get("arm_event"):
            print(f"arm_event: {report['arm_event']}")
        if report.get("halt_event"):
            print(f"halt_event: {report['halt_event']}")
        if "evidence_path" in report:
            print(f"evidence: {report['evidence_path']}")

    return EXIT_OK if report["ok"] else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
