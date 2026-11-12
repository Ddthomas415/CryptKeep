"""Read runner v2 archives offline. This command never loads runtime config."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.strategies.signal_input_capture import iter_runner_records, replay_runner_decision


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="one JSONL journal or an archive folder")
    parser.add_argument("--object-directory", type=Path, help="CAS folder (default: inferred from each journal)")
    parser.add_argument("--expected-sha256", help="expected whole-file hash; valid for one journal only")
    args = parser.parse_args(argv)
    # Loading the runner for its loaded-code fingerprint must not create its
    # normal runtime log from this read-only, isolated CLI process.
    for name in ("execution.strategy_runner", "strategy.evidence_logger", "strategy.es_daily_trend",
                 "managed_component", "runtime_identity"):
        logger = logging.getLogger(name)
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
    counts = {"decision_match": 0, "decision_mismatch": 0, "diagnostic_verified": 0, "errors": 0}
    try:
        if args.path.is_dir():
            if args.expected_sha256:
                raise ValueError("folder_hash_not_supported")
            journals = sorted(args.path.rglob("*.jsonl"))
        else:
            journals = [args.path]
        if not journals:
            raise ValueError("no_runner_journals")
        for journal in journals:
            try:
                for envelope in iter_runner_records(journal, expected_sha256=args.expected_sha256,
                                                    object_directory=args.object_directory):
                    result = replay_runner_decision(envelope, object_directory=args.object_directory)
                    counts[result["status"]] += 1
                    print(json.dumps(result, sort_keys=True))
            except Exception:
                counts["errors"] += 1
                print(json.dumps({"status": "error", "reason": "invalid_or_incomplete_archive"}))
    except Exception:
        counts["errors"] += 1
        print(json.dumps({"status": "error", "reason": "invalid_or_incomplete_archive"}))
    print(json.dumps({"summary": counts}, sort_keys=True))
    return int(bool(counts["errors"] or counts["decision_mismatch"]))


if __name__ == "__main__":
    raise SystemExit(main())
