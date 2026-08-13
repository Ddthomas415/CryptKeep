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
import time

from services.audit.backup_artifact_secret_scan import scan_backup_artifact
from services.audit.operator_event_journal import append_operator_event

EXIT_OK = 0
EXIT_FAIL = 1


def _write_evidence(report: dict, dest: str) -> str:
    target = Path(dest)
    target.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = target / f"backup-artifact-secret-scan-{stamp}.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def _record_operator_event(report: dict) -> dict:
    try:
        event = append_operator_event(
            actor="operator",
            action="state_backup_secret_scan",
            target="state_dir",
            result="success" if bool(report.get("ok")) else "failed",
            reason="backup_artifact_secret_scan",
            source="scripts.check_backup_artifact_secrets",
            pre_state={"backup_dir": str(report.get("backup_dir") or "")},
            post_state={
                "ok": bool(report.get("ok")),
                "finding_count": int(report.get("finding_count") or 0),
                "files_scanned": int(report.get("files_scanned") or 0),
                "evidence_path": str(report.get("evidence_path") or ""),
            },
        )
        return {"ok": True, "event_id": event.get("event_id"), "path": event.get("path")}
    except Exception as exc:
        return {"ok": False, "reason": f"operator_event_write_failed:{type(exc).__name__}"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan a state backup artifact for high-confidence secret indicators without printing secret values."
    )
    parser.add_argument("backup_dir", help="backup directory containing backup_manifest.json")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument("--evidence-dest", default="", help="write JSON evidence into this directory")
    args = parser.parse_args(argv)

    report = scan_backup_artifact(Path(args.backup_dir))
    if args.evidence_dest:
        report["evidence_path"] = _write_evidence(report, str(args.evidence_dest))
    report["operator_event"] = _record_operator_event(report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        verdict = "ok" if report["ok"] else "FAIL"
        print(f"backup artifact secret scan: {verdict}")
        print(f"backup_dir: {report['backup_dir']}")
        print(f"files_scanned: {report['files_scanned']}")
        print(f"findings: {report['finding_count']}")
        for finding in report["findings"]:
            print(f"  {finding.get('reason')}: {finding.get('path')}")
        if "evidence_path" in report:
            print(f"evidence: {report['evidence_path']}")
    return EXIT_OK if bool(report.get("ok")) else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
