from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
BACKTICK_PATH_RE = re.compile(r"`([^`]+)`")


def _referenced_test_paths() -> set[pathlib.Path]:
    content = CHECKPOINTS_PATH.read_text(encoding="utf-8")
    out: set[pathlib.Path] = set()
    for token in BACKTICK_PATH_RE.findall(content):
        if any(ch in token for ch in "*?[]"):
            continue
        if token.startswith("tests/") and token.endswith(".py"):
            out.add(pathlib.Path(token))
    return out


def test_checkpoints_referenced_test_files_exist() -> None:
    refs = _referenced_test_paths()
    assert refs, "No test-file references found in CHECKPOINTS.md"

    missing = sorted(str(p) for p in refs if not p.exists())
    assert not missing, f"Missing referenced test files: {missing}"



def test_checkpoints_referenced_test_files_are_unique() -> None:
    refs = _referenced_test_paths()
    assert len(refs) == len(set(refs)), "Duplicate test-file references found"
