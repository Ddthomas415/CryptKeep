#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import json
import subprocess
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


def _smoke_path() -> Path:
    return ROOT / "phase1_research_copilot" / "scripts" / "smoke_phase1_copilot.py"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    target = _smoke_path()
    if not target.exists():
        payload = {
            "ok": True,
            "skipped": True,
            "reason": "phase1_research_copilot smoke script is not installed",
            "path": str(target.relative_to(ROOT)),
        }
        if "--json" in args:
            print(json.dumps(payload, indent=2))
        else:
            print(f"[phase1-smoke] skipped: {payload['reason']} ({payload['path']})")
        return 0

    proc = subprocess.run([sys.executable, str(target), *args], cwd=str(ROOT), check=False)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
