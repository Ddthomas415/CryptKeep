#!/usr/bin/env python3
"""Inventory shared artifacts without extracting or executing archive content."""
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    downloads = Path("/Users/baitus/Downloads")
    paths = sorted(downloads.glob("*cryptkeep_review_bundle_2026-10-02*.zip"))
    paths += sorted(Path("/Users/baitus/.codex/attachments").glob("*/Pasted text.txt"))
    paths += [downloads / name for name in (
        "codex_review_response_2026-10-02.docx", "cryptkeep_fee_scenarios.xlsx",
        "market_quality_strict_lookback_2026-10-03.xlsx",
        "cryptkeep_exit_wiring_checkpoint_2026-10-04.xlsx",
        "cryptkeep_fc01_count_status_2026-10-04.xlsx",
        "cryptkeep_series_acceptance_ledger_2026-10-04.xlsx")]
    files = []
    for path in paths:
        if not path.is_file():
            files.append(dict(path=str(path), status="missing"))
            continue
        data = path.read_bytes()
        record = dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                      status="readable", semantic_review="tracked separately")
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                members = []
                for item in archive.infolist():
                    if item.is_dir():
                        continue
                    body = archive.read(item)
                    members.append(dict(name=item.filename, bytes=len(body),
                                        sha256=hashlib.sha256(body).hexdigest()))
                record["members"] = members
                record["crc_verified"] = True
        files.append(record)
    members = [member for file in files for member in file.get("members", [])]
    print(json.dumps(dict(scope="available review-bundle family, pasted attachments, six standalone documents; reconcile with user submission scope",
                         files=files, summary=dict(files=len(files),
                         missing=sum(f["status"] == "missing" for f in files),
                         archive_members=len(members),
                         unique_member_contents=len({m["sha256"] for m in members}))),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
