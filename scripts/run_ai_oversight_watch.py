from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.ai_copilot.oversight_watch import (  # noqa: E402
    answer_repo_question,
    build_oversight_snapshot,
    render_oversight_context,
    write_oversight_report,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run the read-only CryptKeep repo oversight watch.")
    ap.add_argument("--question", default="", help="Repo or runtime question for the oversight watch.")
    ap.add_argument("--notes", default="", help="Extra operator notes to embed in the context.")
    ap.add_argument("--context-only", action="store_true", help="Emit the collected oversight context without calling an LLM.")
    ap.add_argument("--stem", default="", help="Optional report filename stem.")
    ap.add_argument("--write-report", action="store_true", help="Write JSON and Markdown report artifacts under runtime/ai_reports.")
    args = ap.parse_args(argv)

    if args.context_only:
        snapshot = build_oversight_snapshot(question=args.question, extra_notes=args.notes)
        payload: dict[str, object] = {
            "ok": True,
            "mode": "context_only",
            "context": render_oversight_context(snapshot),
            "snapshot": snapshot,
        }
    else:
        payload = answer_repo_question(question=args.question, extra_notes=args.notes)

    if args.write_report:
        payload.update(write_oversight_report(payload, stem=(args.stem or None)))

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
