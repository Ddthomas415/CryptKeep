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

from services.audit.operator_event_secret_scan import scan_operator_event_journal

EXIT_OK = 0
EXIT_FAIL = 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan operator event journal payloads for unredacted secret-like fields."
    )
    parser.add_argument("--path", default="", help="operator event JSONL path; defaults to the repo state path")
    parser.add_argument("--require-events", action="store_true", help="fail if the journal is missing or empty")
    parser.add_argument("--json", action="store_true", help="print the full JSON report")
    parser.add_argument("--evidence-dest", default="", help="write the JSON report into this directory")
    args = parser.parse_args()

    report = scan_operator_event_journal(
        Path(args.path) if args.path else None,
        require_events=bool(args.require_events),
    )

    if args.evidence_dest:
        dest = Path(args.evidence_dest)
        dest.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        out_path = dest / f"operator-event-secret-scan-{stamp}.json"
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        report["evidence_path"] = str(out_path)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        verdict = "ok" if report["ok"] else "FAIL"
        print(f"operator event secret scan: {verdict}")
        print(f"path: {report['path']}")
        print(f"events: {report['event_count']}")
        print(f"findings: {report['finding_count']}")
        for finding in report["findings"]:
            loc = finding.get("path") or f"line:{finding.get('line')}"
            print(f"  {finding['reason']}: {loc}")
        if "evidence_path" in report:
            print(f"evidence: {report['evidence_path']}")

    return EXIT_OK if report["ok"] else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
