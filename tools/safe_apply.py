from __future__ import annotations

import argparse
import datetime as _dt
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple

IGNORES = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "data", "logs", "build", "dist", ".ipynb_checkpoints", ".DS_Store"
}

ALLOWED_CREATE_ORDER_FILE = "services/execution/place_order.py"

SMART_QUOTES = {
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "—": "-", "–": "-",
    "…": "...",
}

def repo_root() -> Path:
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        if (p / "CHECKPOINTS.md").exists() or (p / ".git").exists():
            return p
    return here

def sanitize_text(s: str) -> str:
    for a, b in SMART_QUOTES.items():
        s = s.replace(a, b)
    return s.replace("\r\n", "\n").replace("\r", "\n")

def extract_python(payload: str) -> str:
    m = re.search(r"python3\s*-\s*<<\s*['\"]?PY['\"]?\s*\n", payload, re.I)
    if not m:
        return payload
    start = m.end()
    end = payload.rfind("\nPY")
    return payload[start:end] if end > start else payload[start:]

def looks_like_python_patch(py: str) -> bool:
    s = py.strip()
    return bool(s) and not s.startswith("./")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch-file", required=True)
    args = ap.parse_args()

    py = sanitize_text(Path(args.patch_file).read_text())
    py = extract_python(py)

    subprocess.run([sys.executable, "-"], input=py, text=True, check=True)
    print("[safe_apply] OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
