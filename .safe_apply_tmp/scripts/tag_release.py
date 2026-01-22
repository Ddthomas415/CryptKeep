from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
RELEASE_NOTES = ROOT / "releases" / "RELEASE_NOTES.md"

VERSION_RE = re.compile(r'(?m)^(version\s*=\s*")(\d+\.\d+\.\d+)(")\s*$')

def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, check=check)

def git(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return run(["git"] + cmd, check=check)

def fail(msg: str, extra: str = "") -> None:
    print(f"ERROR: {msg}")
    if extra:
        print(extra.strip()[:8000])
    sys.exit(2)

def require_git_repo() -> None:
    try:
        git(["rev-parse", "--is-inside-work-tree"])
    except Exception as e:
        fail("Not a git repo (or git not installed).", str(e))

def require_clean_worktree() -> None:
    p = git(["status", "--porcelain"], check=True)
    if (p.stdout or "").strip():
        fail("Working tree not clean. Commit/stash changes first.", p.stdout)

def require_release_notes() -> None:
    if not RELEASE_NOTES.exists():
        fail("Missing releases/RELEASE_NOTES.md. Generate notes first (Phase 314).")

def read_pyproject_version() -> str:
    if not PYPROJECT.exists():
        fail("pyproject.toml not found.")
    txt = PYPROJECT.read_text(encoding="utf-8", errors="replace")
    m = VERSION_RE.search(txt)
    if not m:
        fail('Could not find version = "x.y.z" in pyproject.toml')
    return m.group(2)

def tag_exists(tag: str) -> bool:
    p = git(["tag", "--list", tag], check=True)
    return bool((p.stdout or "").strip())

def tests_exist() -> bool:
    return (ROOT / "tests").exists()

def run_tests() -> None:
    # Only run if tests folder exists
    if not tests_exist():
        print("No tests/ directory found; skipping pytest.")
        return
    print("Running pytest...")
    p = run([sys.executable, "-m", "pytest", "-q"], check=False)
    if p.returncode != 0:
        fail("Tests failed. Refusing to tag.", (p.stdout or "") + "\n" + (p.stderr or ""))

def build_tag_message(tag: str) -> str:
    try:
        first = RELEASE_NOTES.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
        if first.startswith("#"):
            first = first.lstrip("#").strip()
        return first or f"Release {tag}"
    except Exception:
        return f"Release {tag}"

def create_annotated_tag(tag: str, message: str) -> None:
    p = git(["tag", "-a", tag, "-m", message], check=False)
    if p.returncode != 0:
        fail("Failed to create tag.", (p.stdout or "") + "\n" + (p.stderr or ""))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="Tag like v0.1.0")
    ap.add_argument("--run-tests", action="store_true", help="Run pytest before tagging (only if tests/ exists)")
    ap.add_argument("--dry-run", action="store_true", help="Validate only; do not create tag")
    args = ap.parse_args()

    tag = args.tag.strip()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        fail("Invalid tag format. Expected vX.Y.Z (e.g., v0.1.0).")

    require_git_repo()
    require_clean_worktree()
    require_release_notes()

    ver = read_pyproject_version()
    if tag[1:] != ver:
        fail(f"Tag version ({tag[1:]}) does not match pyproject version ({ver}).")

    if tag_exists(tag):
        fail(f"Tag already exists: {tag}")

    if args.run_tests:
        run_tests()

    msg = build_tag_message(tag)
    print(f"Validated OK. Tag to create: {tag}")
    print(f"Message: {msg}")

    if args.dry_run:
        print("Dry-run only. No tag created.")
        return

    create_annotated_tag(tag, msg)
    print(f"Created local tag: {tag}")
    print("Next (manual):")
    print(f"  git push origin {tag}")

if __name__ == "__main__":
    main()
