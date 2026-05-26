from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.ai_copilot.pr_reviewer import (  # noqa: E402
    build_review_packet,
    maybe_generate_llm_summary,
    write_review_report,
)


def _git_changed_files() -> list[str]:
    changed: set[str] = set()
    commands = (
        ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    for cmd in commands:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            continue
        changed.update(line.strip() for line in proc.stdout.splitlines() if line.strip())
    return sorted(changed)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate a read-only CryptKeep repo copilot review report.")
    ap.add_argument("--paths", default="", help="Comma-separated repo paths. Defaults to current git diff + untracked files.")
    ap.add_argument("--verify", action="append", default=[], help="Verification command or proof note to include.")
    ap.add_argument("--notes", default="", help="Extra operator notes to embed in the report.")
    ap.add_argument("--stem", default="", help="Optional output filename stem.")
    ap.add_argument("--llm", action="store_true", help="Request an optional LLM summary if a provider is configured.")
    args = ap.parse_args(argv)

    if args.paths.strip():
        changed_files = [item.strip() for item in args.paths.split(",") if item.strip()]
    else:
        changed_files = _git_changed_files()

    packet = build_review_packet(
        changed_files=changed_files,
        verification=args.verify,
        extra_notes=args.notes,
    )
    if args.llm:
        llm_summary = maybe_generate_llm_summary(packet)
        if llm_summary:
            packet["llm_summary"] = llm_summary

    output_paths = write_review_report(packet, stem=(args.stem or None))
    payload = {**packet, **output_paths}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
