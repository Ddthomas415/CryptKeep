#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from scripts._bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parents[1])

from services.analytics.roadmap_tracking_status import build_roadmap_tracking_status  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report roadmap tracking checklist health without running campaigns or changing state."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    args = parser.parse_args(argv)

    out = build_roadmap_tracking_status(repo_root=ROOT)
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        summary = dict(out.get("summary") or {})
        print("=== Roadmap Tracking Status ===")
        print(
            f"ok={bool(out.get('ok'))} "
            f"sources={summary.get('source_docs_linked')}/{summary.get('source_doc_count')} "
            f"commands={summary.get('commands_listed')}/{summary.get('command_count')} "
            f"boundaries={summary.get('boundaries_present')}/{summary.get('boundary_count')}"
        )
        if out.get("reason"):
            print(f"reason={out.get('reason')}")
        print(f"roadmap_doc={out.get('roadmap_doc')}")
        if out.get("missing_docs"):
            print("missing_docs=" + ",".join(str(item) for item in out["missing_docs"]))
        if out.get("unlinked_docs"):
            print("unlinked_docs=" + ",".join(str(item) for item in out["unlinked_docs"]))
        if out.get("missing_commands"):
            print("missing_commands=" + " | ".join(str(item) for item in out["missing_commands"]))
        if out.get("missing_make_targets"):
            print("missing_make_targets=" + ",".join(str(item) for item in out["missing_make_targets"]))
        if out.get("missing_boundaries"):
            print("missing_boundaries=" + " | ".join(str(item) for item in out["missing_boundaries"]))
    return 0 if bool(out.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
