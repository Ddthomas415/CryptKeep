from __future__ import annotations

import importlib.util

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
import os
import subprocess
import time
from datetime import datetime, timezone

SCHEMA_VERSION = 1

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


def _run_capture_cmd(label: str, cmd: list[str]) -> dict:
    p = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    return {
        "label": label,
        "cmd": cmd,
        "rc": p.returncode,
        "stdout": (p.stdout or "")[:20000],
        "stderr": (p.stderr or "")[:20000],
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env_flag(name: str) -> bool:
    v = (os.environ.get(name, "") or "").strip().lower()
    return v in {"1", "true", "yes", "on"}

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
    if importlib.util.find_spec("ruff") is None:
        info("ruff not installed; skipping ruff")
        return
    targets = find_python_targets()
    cmd = [sys.executable, "-m", "ruff", "check"] + targets
    if fix:
        cmd.append("--fix")
    p = run(cmd, check=False)
    if p.returncode != 0:
        die("ruff check failed", (p.stdout or "") + "\n" + (p.stderr or ""))
    ok("ruff check passed")

def run_mypy() -> None:
    if importlib.util.find_spec("mypy") is None:
        info("mypy not installed; skipping mypy")
        return
    targets = find_python_targets()
    p = run([sys.executable, "-m", "mypy"] + targets, check=False)
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

def run_alignment_gate() -> None:
    p = run([sys.executable, "scripts/check_repo_alignment.py"], check=False)
    if p.returncode != 0:
        die("alignment gate failed", (p.stdout or "") + "\n" + (p.stderr or ""))
    ok("alignment gate passed")


def _validate_yaml_configs_capture() -> dict:
    cfg = ROOT / "config"
    if not cfg.exists():
        return {"label": "yaml_config_validation", "rc": 0, "stdout": "config/ not found; skipped", "stderr": ""}
    try:
        import yaml  # type: ignore
    except Exception:
        return {"label": "yaml_config_validation", "rc": 0, "stdout": "PyYAML not installed; skipped", "stderr": ""}

    bad = []
    for p in list(cfg.rglob("*.yaml")) + list(cfg.rglob("*.yml")):
        try:
            yaml.safe_load(p.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            bad.append((str(p.relative_to(ROOT)), f"{type(e).__name__}: {e}"))

    if bad:
        out = "\n".join([f"- {a}: {b}" for a, b in bad])
        return {"label": "yaml_config_validation", "rc": 2, "stdout": "", "stderr": out[:20000]}
    return {"label": "yaml_config_validation", "rc": 0, "stdout": "YAML configs validated", "stderr": ""}


def _import_smoke_capture() -> dict:
    mods = [
        ("yaml", "PyYAML"),
        ("requests", "requests"),
    ]
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
        return {"label": "import_smoke", "rc": 2, "stdout": "", "stderr": "\n".join(errors)[:20000]}
    return {"label": "import_smoke", "rc": 0, "stdout": "import smoke passed (required libs)", "stderr": ""}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="run ruff --fix (still fail-closed)")
    ap.add_argument("--json", action="store_true", help="emit structured JSON status")
    ap.add_argument("--skip-ruff", action="store_true")
    ap.add_argument("--skip-mypy", action="store_true")
    ap.add_argument("--skip-pytest", action="store_true")
    ap.add_argument("--skip-config", action="store_true")
    ap.add_argument("--skip-imports", action="store_true")
    args = ap.parse_args()

    if args.json:
        skip_flags = [args.skip_ruff, args.skip_mypy, args.skip_pytest, args.skip_config, args.skip_imports]
        mode = "quick" if all(skip_flags) else ("full" if not any(skip_flags) else "custom")
        started_at = _utc_now_iso()
        t0 = time.monotonic()

        def _emit(ok: bool, steps: list[dict]) -> None:
            print(
                json.dumps(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "mode": mode,
                        "ok": ok,
                        "started_at": started_at,
                        "finished_at": _utc_now_iso(),
                        "duration_seconds": round(time.monotonic() - t0, 3),
                        "steps": steps,
                    },
                    indent=2,
                )
            )

        steps: list[dict] = []
        step = _run_capture_cmd("alignment_gate", [sys.executable, "scripts/check_repo_alignment.py"])
        steps.append(step)
        if step["rc"] != 0:
            _emit(False, steps)
            return step["rc"]

        if args.skip_ruff:
            steps.append({"label": "ruff", "rc": 0, "skipped": True, "stdout": "skipped via --skip-ruff", "stderr": ""})
        else:
            targets = find_python_targets()
            cmd = [sys.executable, "-m", "ruff", "check"] + targets
            if args.fix:
                cmd.append("--fix")
            step = _run_capture_cmd("ruff", cmd)
            steps.append(step)
            if step["rc"] != 0:
                _emit(False, steps)
                return step["rc"]

        if args.skip_mypy:
            steps.append({"label": "mypy", "rc": 0, "skipped": True, "stdout": "skipped via --skip-mypy", "stderr": ""})
        else:
            targets = find_python_targets()
            step = _run_capture_cmd("mypy", [sys.executable, "-m", "mypy", *targets, "--ignore-missing-imports"])
            steps.append(step)
            if step["rc"] != 0:
                _emit(False, steps)
                return step["rc"]

        if args.skip_config:
            steps.append({"label": "yaml_config_validation", "rc": 0, "skipped": True, "stdout": "skipped via --skip-config", "stderr": ""})
        else:
            step = _validate_yaml_configs_capture()
            steps.append(step)
            if step["rc"] != 0:
                _emit(False, steps)
                return step["rc"]

        if args.skip_imports:
            steps.append({"label": "import_smoke", "rc": 0, "skipped": True, "stdout": "skipped via --skip-imports", "stderr": ""})
        else:
            step = _import_smoke_capture()
            steps.append(step)
            if step["rc"] != 0:
                _emit(False, steps)
                return step["rc"]

        if args.skip_pytest:
            steps.append({"label": "pytest", "rc": 0, "skipped": True, "stdout": "skipped via --skip-pytest", "stderr": ""})
            _emit(True, steps)
            return 0

        if _env_flag("CBP_PRE_RELEASE_SKIP_PYTEST"):
            steps.append({"label": "pytest", "rc": 0, "skipped": True, "stdout": "skipped via CBP_PRE_RELEASE_SKIP_PYTEST", "stderr": ""})
            _emit(True, steps)
            return 0

        tests = ROOT / "tests"
        if not tests.exists():
            steps.append({"label": "pytest", "rc": 0, "skipped": True, "stdout": "tests/ not found; skipped", "stderr": ""})
            _emit(True, steps)
            return 0

        step = _run_capture_cmd("pytest", [sys.executable, "-m", "pytest", "-q"])
        steps.append(step)
        if step["rc"] != 0:
            _emit(False, steps)
            return step["rc"]

        _emit(True, steps)
        return 0

    run_alignment_gate()
    if not args.skip_ruff:
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
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
