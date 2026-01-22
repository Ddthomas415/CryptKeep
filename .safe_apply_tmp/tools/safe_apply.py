from __future__ import annotations

import argparse
import ast
import datetime as dt
import re
import shutil
import subprocess
import sys
import traceback
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
    t = payload.strip()
    # Flexible match for python3 - <<PY / <<'PY' / <<"PY" etc.
    m = re.search(r"python3\s*-\s*<<\s*['\"]?PY['\"]?\s*(?:\n|\Z)", t, re.IGNORECASE)
    if not m:
        return t  # assume raw python
    start = m.end()
    # Find last line that is exactly "PY" (possibly with trailing whitespace)
    lines = t.splitlines()
    for i in range(len(lines)-1, -1, -1):
        if lines[i].strip() == "PY":
            # Reconstruct up to but not including the PY line
            end_pos = sum(len(lines[j]) + 1 for j in range(i))
            return t[start:end_pos].rstrip()
    # If no terminator found, take everything after start
    print("[safe_apply] Warning: No PY terminator found → using remainder of input")
    return t[start:].rstrip()

def looks_like_python_patch(py: str) -> bool:
    s = py.lstrip()
    if not s.strip():
        return False
    first_line = s.splitlines()[0].strip()
    # Reject obvious non-python starters
    reject_starts = ("./", "docker ", "docker-compose ", "bash ", "sh ", "git ", "cd ", "rm ", "mv ", "echo ", "cat ")
    if any(first_line.startswith(x) for x in reject_starts):
        return False
    # Require at least one strong python indicator
    markers = (
        "from __future__", "import ", "from ", "def ", "class ", "@", 
        "Path(", "write_text(", "append_checkpoint(", "safe_patch_text(",
        "print(", "with open(", "pd.", "np.", "datetime"
    )
    return any(m in s for m in markers)

def check_syntax(py_code: str) -> tuple[bool, str]:
    try:
        ast.parse(py_code)
        return True, ""
    except SyntaxError as e:
        msg = f"SyntaxError: {e.msg}"
        if e.lineno is not None:
            msg += f" (line {e.lineno}"
            if e.offset is not None:
                msg += f", column {e.offset}"
            msg += ")"
        if e.text:
            msg += f"\n  {e.text.rstrip()}"
            if e.offset:
                msg += "\n  " + " " * (e.offset - 1 if e.offset > 0 else 0) + "^"
        
        # Add context lines
        try:
            lines = py_code.splitlines()
            start = max(0, (e.lineno or 1) - 5)
            end = min(len(lines), (e.lineno or 1) + 4)
            context_lines = []
            for i, line in enumerate(lines[start:end], start + 1):
                prefix = "→ " if i == e.lineno else "  "
                context_lines.append(f"{prefix}{i:4d} | {line.rstrip()}")
            msg += "\n\nNearby code:\n" + "\n".join(context_lines)
        except Exception:
            pass
        return False, msg
    except Exception as e:
        return False, f"Unexpected parser failure: {type(e).__name__}: {e}"

def copy_repo(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    def ignore(_dir, names):
        return {n for n in names if n in IGNORES}
    shutil.copytree(src, dst, ignore=ignore)

def compileall_check(root: Path) -> Tuple[bool, str]:
    cp = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "."],
        cwd=str(root), capture_output=True, text=True,
    )
    out = (cp.stdout + cp.stderr).strip()
    return cp.returncode == 0, out


def _list_py_files(root: Path) -> List[Path]:
    out: List[Path] = []
    for fp in root.rglob("*.py"):
        if any(part in IGNORES for part in fp.parts):
            continue
        out.append(fp)
    return out

def _forbidden_create_order_hits(root: Path) -> List[str]:
    # Build token without embedding it literally in this file
    token = ".create_" + "order" + "("
    hits: List[str] = []
    for fp in _list_py_files(root):
        rel = fp.relative_to(root).as_posix()
        if rel == ALLOWED_CREATE_ORDER_FILE:
            continue
        txt = fp.read_text(encoding="utf-8", errors="replace")
        if token in txt:
            for i, line in enumerate(txt.splitlines(), start=1):
                if token in line:
                    hits.append(f"{rel}:{i}  {line.strip()[:240]}")
    return hits

def diff_paths(a: Path, b: Path) -> List[str]:
    changed = []
    files = set()
    for base in (a, b):
        for p in base.rglob("*"):
            if any(part in IGNORES for part in p.parts):
                continue
            if p.is_file():
                files.add(p.relative_to(base).as_posix())
    for rel in sorted(files):
        pa, pb = a / rel, b / rel
        if pa.is_file() and pb.is_file():
            try:
                if pa.read_bytes() != pb.read_bytes():
                    changed.append(rel)
            except:
                changed.append(rel)
        else:
            changed.append(rel)
    return changed

def backup_files(root: Path, rels: List[str], backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    for rel in rels:
        src = root / rel
        if src.is_file():
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

def apply_changes(tmp: Path, real: Path, changed: List[str]) -> None:
    for rel in changed:
        src = tmp / rel
        dst = real / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dst)
        elif dst.exists():
            dst.unlink(missing_ok=True)

def run_pytest(tmp_root: Path) -> Tuple[bool, str]:
    cp = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(tmp_root), capture_output=True, text=True
    )
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()

def run_docker_tests(real_root: Path, compose_file: str) -> Tuple[bool, str]:
    cmd = ["docker", "compose", "-f", compose_file, "run", "--rm", "backend", "pytest", "-q"]
    cp = subprocess.run(cmd, cwd=str(real_root), capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()

def main() -> int:
    parser = argparse.ArgumentParser(description="Safely apply pasted Python patches")
    parser.add_argument("--patch-file", default="", help="File containing the patch (instead of stdin)")
    parser.add_argument("--apply", action="store_true", help="Actually write changes to repo")
    parser.add_argument("--run-pytest", action="store_true", help="Run pytest in sandbox")
    parser.add_argument("--run-docker-tests", action="store_true", help="Run docker pytest after apply")
    parser.add_argument("--compose-file", default="docker/docker-compose.yml")
    args = parser.parse_args()

    real = repo_root()
    tmp = real / ".safe_apply_tmp"
    backups = real / ".safe_apply_backups" / dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if args.patch_file:
        payload = Path(args.patch_file).read_text(encoding="utf-8", errors="replace")
    else:
        payload = sys.stdin.read()

    payload = sanitize_text(payload)
    py = extract_python(payload)

    print(f"[safe_apply] repo_root  = {real}")
    print(f"[safe_apply] sandbox    = {tmp}")
    print(f"[safe_apply] patch size = {len(py):,} characters")

    # Step 1: Syntax check (very cheap)
    ok, err_msg = check_syntax(py)
    if not ok:
        print("\n[safe_apply] SYNTAX CHECK FAILED (before sandbox execution):")
        print(err_msg)
        print("\n→ Patch rejected. Fix the syntax error and copy again.")
        return 2

    # Step 2: Semantic check
    if not looks_like_python_patch(py):
        print("[safe_apply] Code parses OK but doesn't look like a patch script")
        print("   (no def/class/import/Path/write/append_checkpoint markers found)")
        return 2

    print("[safe_apply] Syntax OK + looks like patch → proceeding")

    copy_repo(real, tmp)

    cp = subprocess.run([sys.executable, "-"], input=py, cwd=str(tmp), text=True, capture_output=True)
    if cp.returncode != 0:
        print("[safe_apply] Execution failed in sandbox:")
        print(cp.stderr or cp.stdout or "<no output>")
        return 3
    print("[safe_apply] Patch executed successfully in sandbox")

    ok, out = compileall_check(tmp)
    if not ok:
        print("[safe_apply] compileall check failed:")
        print(out or "<no output>")
        return 4

    # SAFE_APPLY_CREATE_ORDER_GUARD
    hits = _forbidden_create_order_hits(tmp)
    if hits:
        print("[safe_apply] forbidden create_order usage found (outside allowed file):")
        print("\n".join(hits[:200]))
        return 5


    changed = diff_paths(real, tmp)
    print(f"[safe_apply] Files changed: {len(changed)}")
    for rel in changed[:40]:
        print(f"  - {rel}")
    if len(changed) > 40:
        print(f"  ... ({len(changed)-40} more)")

    if not args.apply:
        print("\n[safe_apply] Dry-run complete. Re-run with --apply to write changes.")
        return 0

    backup_files(real, changed, backups)
    apply_changes(tmp, real, changed)
    print(f"[safe_apply] Changes applied. Backups saved → {backups}")

    if args.run_docker_tests:
        ok, out = run_docker_tests(real, args.compose_file)
        if not ok:
            print("[safe_apply] Docker tests FAILED:")
            print(out or "<no output>")
            return 7
        print("[safe_apply] Docker tests passed")

    print("[safe_apply] DONE.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
