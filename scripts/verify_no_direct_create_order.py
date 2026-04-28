from __future__ import annotations

import argparse
from pathlib import Path
import re

# CBP_BOOTSTRAP_SYS_PATH
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

TOKEN1 = ".create_" + "order("
TOKEN2 = ".create" + "Order("
PATTERNS = (
    re.compile(r"\.create_order\s*\("),
    re.compile(r"\.createOrder\s*\("),
    re.compile(r"getattr\s*\([^\n]*[\"']create_order[\"']"),
    re.compile(r"getattr\s*\([^\n]*[\"']createOrder[\"']"),
)

ALLOWED = {
    "services/execution/place_order.py",
}

SKIP_DIRS = {"tools", "attic", ".venv", "venv", "__pycache__", ".git", "data", "docs", "dist", "build", ".pytest_cache"}

def iter_py_files(root: Path):
    for p in root.rglob("*.py"):
        parts = set(p.parts)
        if any(part.startswith(".venv") for part in p.parts):
            continue
        if any(s in parts for s in SKIP_DIRS):
            continue
        yield p

def scan(root: Path) -> list[dict]:
    hits = []
    for p in iter_py_files(root):
        rel = p.relative_to(root).as_posix()
        if rel in ALLOWED:
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        # look for direct exchange order placement patterns
        # We explicitly block direct create_order usage anywhere outside place_order.py.
        if any(pattern.search(txt) for pattern in PATTERNS):
            for i, line in enumerate(txt.splitlines(), start=1):
                if any(pattern.search(line) for pattern in PATTERNS):
                    hits.append({"file": rel, "line": i, "text": line.strip()[:240]})
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repo root")
    ap.add_argument("--print", action="store_true", help="print full hits")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    hits = scan(root)
    if not hits:
        print({"ok": True, "violations": 0})
        raise SystemExit(0)

    out = {"ok": False, "violations": len(hits), "hits": hits}
    if args.print:
        print(out)
    else:
        # compact output
        print({"ok": False, "violations": len(hits), "sample": hits[:10]})
    raise SystemExit(2)

if __name__ == "__main__":
    main()
