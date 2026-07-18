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
import shlex
import shutil
import subprocess

LONG_RUNNING_SERVICE_UNITS = (
    "cbp-collector.service",
    "cbp-crypto-edge-collector.service",
    "cbp-intent-consumer.service",
    "cbp-reconciler.service",
    "cbp-dashboard.service",
)
ONESHOT_SERVICE_UNITS = (
    "cbp-dead-man.service",
    "cbp-edge-cadence.service",
)
TIMER_UNITS = (
    "cbp-dead-man.timer",
    "cbp-edge-cadence.timer",
)
UNITS = LONG_RUNNING_SERVICE_UNITS + ONESHOT_SERVICE_UNITS + TIMER_UNITS
FORBIDDEN_TOKENS = ("CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED")


def _unit_dir() -> Path:
    return _REPO / "packaging" / "systemd"


def _parse_unit(text: str) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("["):
            continue
        if "=" in stripped:
            key, value = stripped.split("=", 1)
            parsed.setdefault(key.strip(), []).append(value.strip())
    return parsed


def _exec_start_script(value: str) -> str:
    try:
        parts = shlex.split(value)
    except ValueError:
        return ""
    for idx, part in enumerate(parts):
        if part.endswith("/python") or part.endswith("/python3") or part.endswith("/.venv/bin/python"):
            return parts[idx + 1] if idx + 1 < len(parts) else ""
    return parts[0] if parts else ""


def _verify_forbidden_tokens(name: str, text: str) -> list[str]:
    problems: list[str] = []
    effective = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )
    for token in FORBIDDEN_TOKENS:
        if token in effective:
            problems.append(f"{name}: forbidden arming token {token} present")
    return problems


def _verify_service_unit(name: str, *, long_running: bool) -> list[str]:
    problems: list[str] = []
    path = _unit_dir() / name
    if not path.exists():
        return [f"missing unit: {name}"]
    text = path.read_text(encoding="utf-8")
    parsed = _parse_unit(text)
    problems.extend(_verify_forbidden_tokens(name, text))
    if "EnvironmentFile" not in parsed:
        problems.append(f"{name}: EnvironmentFile missing")
    if parsed.get("User") != ["cbp"]:
        problems.append(f"{name}: User=cbp missing")
    if parsed.get("Group") != ["cbp"]:
        problems.append(f"{name}: Group=cbp missing")
    if parsed.get("NoNewPrivileges") != ["true"]:
        problems.append(f"{name}: NoNewPrivileges=true missing")
    if parsed.get("ProtectSystem") != ["strict"]:
        problems.append(f"{name}: ProtectSystem=strict missing")
    if parsed.get("ReadWritePaths") != ["/var/lib/cbp"]:
        problems.append(f"{name}: ReadWritePaths=/var/lib/cbp missing")
    if long_running:
        if parsed.get("Restart") != ["on-failure"]:
            problems.append(f"{name}: Restart=on-failure missing")
        if parsed.get("RestartSec") != ["5"]:
            problems.append(f"{name}: RestartSec=5 missing")
        if parsed.get("StartLimitIntervalSec") != ["300"]:
            problems.append(f"{name}: StartLimitIntervalSec=300 missing")
        if parsed.get("StartLimitBurst") != ["10"]:
            problems.append(f"{name}: StartLimitBurst=10 missing")
    elif parsed.get("Type") != ["oneshot"]:
        problems.append(f"{name}: Type=oneshot missing")
    execs = parsed.get("ExecStart") or []
    if len(execs) != 1:
        problems.append(f"{name}: exactly one ExecStart required")
    else:
        script = _exec_start_script(execs[0])
        rel = script.split("crypto-bot-pro/")[-1] if "crypto-bot-pro/" in script else script
        if rel.startswith("scripts/") and not (_REPO / rel).exists():
            problems.append(f"{name}: ExecStart script not in repo: {rel}")
    return problems


def _verify_timer_unit(name: str) -> list[str]:
    problems: list[str] = []
    path = _unit_dir() / name
    if not path.exists():
        return [f"missing unit: {name}"]
    text = path.read_text(encoding="utf-8")
    parsed = _parse_unit(text)
    problems.extend(_verify_forbidden_tokens(name, text))
    if "OnUnitActiveSec" not in parsed:
        problems.append(f"{name}: OnUnitActiveSec missing")
    if "WantedBy" not in parsed:
        problems.append(f"{name}: WantedBy missing")
    return problems


def _verify_units() -> list[str]:
    """Static checks; returns a list of problems (empty = ok)."""
    problems: list[str] = []
    for name in LONG_RUNNING_SERVICE_UNITS:
        problems.extend(_verify_service_unit(name, long_running=True))
    for name in ONESHOT_SERVICE_UNITS:
        problems.extend(_verify_service_unit(name, long_running=False))
    for name in TIMER_UNITS:
        problems.extend(_verify_timer_unit(name))
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
