from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

_REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import shutil
import subprocess

UNITS = (
    "cbp-collector.service",
    "cbp-intent-consumer.service",
    "cbp-reconciler.service",
    "cbp-dashboard.service",
)
FORBIDDEN_TOKENS = ("CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED")


def _unit_dir() -> Path:
    return _REPO / "packaging" / "systemd"


def _verify_units() -> list[str]:
    """Static checks; returns a list of problems (empty = ok)."""
    problems: list[str] = []
    for name in UNITS:
        path = _unit_dir() / name
        if not path.exists():
            problems.append(f"missing unit: {name}")
            continue
        text = path.read_text(encoding="utf-8")
        effective = "\n".join(
            ln for ln in text.splitlines() if not ln.strip().startswith("#")
        )
        for token in FORBIDDEN_TOKENS:
            if token in effective:
                problems.append(f"{name}: forbidden arming token {token} present")
        if "Restart=on-failure" not in text:
            problems.append(f"{name}: Restart=on-failure missing")
        if "EnvironmentFile=" not in text:
            problems.append(f"{name}: EnvironmentFile missing")
        for line in text.splitlines():
            if line.startswith("ExecStart="):
                script = line.split()[-1]
                rel = script.split("crypto-bot-pro/")[-1] if "crypto-bot-pro/" in script else script
                if rel.startswith("scripts/") and not (_REPO / rel).exists():
                    problems.append(f"{name}: ExecStart script not in repo: {rel}")
    env_example = _unit_dir() / "cbp.env.example"
    if not env_example.exists():
        problems.append("missing cbp.env.example")
    else:
        env_text = env_example.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            for line in env_text.splitlines():
                if line.strip().startswith(token):
                    problems.append(f"cbp.env.example: forbidden arming assignment {token}")
    return problems


def _systemd_analyze(paths: list[Path]) -> int:
    """Run systemd-analyze verify; missing-executable complaints are
    expected when verifying off-host (the venv lives on the deploy host)
    and are reported as notes, while any other finding fails."""
    exe = shutil.which("systemd-analyze")
    if not exe:
        print("systemd-analyze unavailable; skipping daemon-level verify")
        return 0
    proc = subprocess.run(
        [exe, "verify", *[str(p) for p in paths]], capture_output=True, text=True
    )
    real_findings = []
    for line in (proc.stdout + proc.stderr).splitlines():
        line = line.strip()
        if not line:
            continue
        if "is not executable: No such file or directory" in line:
            print(f"note (off-host path, verified on deploy host): {line}")
            continue
        real_findings.append(line)
    for line in real_findings:
        print(f"analyze: {line}")
    return 1 if real_findings else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify and (optionally) install CryptKeep systemd units.")
    ap.add_argument("--apply", action="store_true", help="copy units into --dest (default: dry run)")
    ap.add_argument("--dest", default="/etc/systemd/system", help="unit install destination")
    args = ap.parse_args()

    problems = _verify_units()
    if problems:
        for p in problems:
            print(f"FAIL: {p}")
        return 1
    print(f"static verify ok: {', '.join(UNITS)}")

    rc = _systemd_analyze([_unit_dir() / n for n in UNITS])
    if rc != 0:
        print("FAIL: systemd-analyze verify reported problems")
        return 1

    if not args.apply:
        print(f"dry run: would copy units to {args.dest}; rerun with --apply")
        print("NOTE: installing units never arms live trading; arming flows only through the ceremony.")
        return 0

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    for name in UNITS:
        shutil.copy2(_unit_dir() / name, dest / name)
        print(f"installed {dest / name}")
    print("run: systemctl daemon-reload && systemctl enable --now <unit> (operator decision per unit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
