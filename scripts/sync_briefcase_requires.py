
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
import re
from typing import Iterable


DEFAULT_SRC = ROOT / "requirements.txt"
DEFAULT_DST = ROOT / "requirements" / "briefcase.txt"

# Build/test tooling should not leak into briefcase runtime deps.
EXCLUDED_NAMES = {
    "pytest",
    "pyinstaller",
}


def _pkg_name(req_line: str) -> str:
    s = req_line.strip()
    if not s:
        return ""
    if s.startswith("-r "):
        return ""
    if s.startswith("#"):
        return ""
    # Remove env markers for name extraction.
    s = s.split(";", 1)[0].strip()
    m = re.match(r"^([A-Za-z0-9_.-]+)", s)
    if not m:
        return ""
    return m.group(1).lower().replace("_", "-")


def _sanitize(lines: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r "):
            continue
        name = _pkg_name(line)
        if not name:
            continue
        if name in EXCLUDED_NAMES:
            continue
        if name in seen:
            continue
        seen.add(name)
        out.append(line)
    return out


def sync_requires(src: Path = DEFAULT_SRC, dst: Path = DEFAULT_DST) -> dict:
    if not src.exists():
        return {"ok": False, "reason": "source_missing", "source": str(src)}
    src_lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
    wanted = _sanitize(src_lines)

    dst.parent.mkdir(parents=True, exist_ok=True)
    prior = dst.read_text(encoding="utf-8", errors="replace") if dst.exists() else ""
    new_text = "\n".join(wanted) + ("\n" if wanted else "")
    changed = new_text != prior
    if changed:
        dst.write_text(new_text, encoding="utf-8")

    return {
        "ok": True,
        "source": str(src),
        "target": str(dst),
        "count": len(wanted),
        "changed": bool(changed),
        "excluded_names": sorted(EXCLUDED_NAMES),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync requirements.txt into requirements/briefcase.txt")
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    ap.add_argument("--dst", default=str(DEFAULT_DST))
    args = ap.parse_args()

    rep = sync_requires(Path(args.src), Path(args.dst))
    print(json.dumps(rep, indent=2))
    return 0 if rep.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
