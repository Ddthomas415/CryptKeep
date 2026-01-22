from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, check=check)

def die(msg: str, out: str = "") -> None:
    print(f"ERROR: {msg}")
    if out:
        print(out[:12000])
    sys.exit(2)

def ok(msg: str) -> None:
    print(f"[OK] {msg}")

def info(msg: str) -> None:
    print(f"[INFO] {msg}")

def find_python_targets() -> list[str]:
    # Prefer src/ if present; always include dashboard/ and ops_system/ if present.
    targets: list[str] = []
    for d in ("src", "dashboard", "ops_system", "app", "bot"):
        p = ROOT / d
        if p.exists() and p.is_dir():
            targets.append(d)
    # fallback: current directory (still safe for ruff; mypy may be slower)
    if not targets:
        targets = ["."]
    return targets

def run_ruff(fix: bool = False) -> None:
    targets = find_python_targets()
    cmd = [sys.executable, "-m", "ruff", "check"] + targets
    if fix:
        cmd.append("--fix")
    p = run(cmd, check=False)
    if p.returncode != 0:
        die("ruff check failed", (p.stdout or "") + "\n" + (p.stderr or ""))
    ok("ruff check passed")

def run_mypy() -> None:
    targets = find_python_targets()
    # mypy on whole repo can be noisy; focus on code folders
    cmd = [sys.executable, "-m", "mypy"] + targets + ["--ignore-missing-imports"]
    p = run(cmd, check=False)
    if p.returncode != 0:
        die("mypy failed", (p.stdout or "") + "\n" + (p.stderr or ""))
    ok("mypy passed")

def run_pytest() -> None:
    tests = ROOT / "tests"
    if not tests.exists():
        info("tests/ not found; skipping pytest")
        return
    p = run([sys.executable, "-m", "pytest", "-q"], check=False)
    if p.returncode != 0:
        die("pytest failed", (p.stdout or "") + "\n" + (p.stderr or ""))
    ok("pytest passed")

def validate_yaml_configs() -> None:
    cfg = ROOT / "config"
    if not cfg.exists():
        info("config/ not found; skipping YAML validation")
        return
    try:
        import yaml  # type: ignore
    except Exception:
        info("PyYAML not installed; skipping YAML validation")
        return

    bad = []
    for p in list(cfg.rglob("*.yaml")) + list(cfg.rglob("*.yml")):
        try:
            yaml.safe_load(p.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            bad.append((str(p.relative_to(ROOT)), f"{type(e).__name__}: {e}"))

    if bad:
        out = "\n".join([f"- {a}: {b}" for a, b in bad])
        die("YAML config validation failed", out)
    ok("YAML configs validated")

def import_smoke() -> None:
    # Keep smoke minimal to avoid side effects (no live trading, no streamlit run).
    mods = [
        ("yaml", "PyYAML"),
        ("requests", "requests"),
    ]
    # Optional imports (only if installed)
    optional = ["ccxt", "pandas", "numpy"]
    errors = []

    for mod, label in mods:
        try:
            __import__(mod)
        except Exception as e:
            errors.append(f"{label} import failed: {type(e).__name__}: {e}")

    for mod in optional:
        try:
            __import__(mod)
        except Exception:
            pass

    if errors:
        die("Import smoke failed (required libs)", "\n".join(errors))
    ok("import smoke passed (required libs)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="run ruff --fix (still fail-closed)")
    ap.add_argument("--skip-mypy", action="store_true")
    ap.add_argument("--skip-pytest", action="store_true")
    ap.add_argument("--skip-config", action="store_true")
    ap.add_argument("--skip-imports", action="store_true")
    args = ap.parse_args()

    run_ruff(fix=args.fix)
    if not args.skip_mypy:
        run_mypy()
    if not args.skip_config:
        validate_yaml_configs()
    if not args.skip_imports:
        import_smoke()
    if not args.skip_pytest:
        run_pytest()

    ok("pre-release sanity suite complete")

if __name__ == "__main__":
    main()
