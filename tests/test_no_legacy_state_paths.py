from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("services", "scripts", "storage", "core", "dashboard", "adapters", "tests")
EXCLUDE = {
    "tests/test_no_legacy_state_paths.py",
}

# These patterns are the legacy repo-root state paths we want to prevent.
PATTERNS = [
    re.compile(r'Path\("data"\)'),
    re.compile(r'Path\("runtime"\)'),
    re.compile(r'"' + "data" + "/"),
    re.compile(r'"' + "runtime" + "/"),
    re.compile(r'\b(?:ROOT|REPO|_REPO)\s*/\s*"data"'),
    re.compile(r'\b(?:ROOT|REPO|_REPO)\s*/\s*"runtime"'),
]


def _should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if rel in EXCLUDE:
        return True
    if ".bak" in rel:
        return True
    if "__pycache__" in rel:
        return True
    return False


def test_no_legacy_repo_state_paths():
    offenders: list[str] = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if _should_skip(p):
                continue
            txt = p.read_text(encoding="utf-8", errors="replace")
            for rx in PATTERNS:
                if rx.search(txt):
                    offenders.append(f"{p.relative_to(ROOT)} :: {rx.pattern}")
                    break

    assert not offenders, "Legacy state paths found:\n" + "\n".join(sorted(offenders))
