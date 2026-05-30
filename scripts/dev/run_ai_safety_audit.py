from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.ai_copilot.safety_auditor import build_safety_report, write_safety_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate a read-only CryptKeep safety audit report.")
    ap.add_argument("--stem", default="", help="Optional output filename stem.")
    args = ap.parse_args(argv)

    report = build_safety_report()
    output_paths = write_safety_report(report, stem=(args.stem or None))
    payload = {**report, **output_paths}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
