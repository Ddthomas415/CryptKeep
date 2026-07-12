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
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone

PINNED_FILES = ("requirements-pinned.txt", "requirements-dev-pinned.txt")

EXIT_OK = 0
EXIT_FAIL = 1

_PIN_RE = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)(?P<extras>\[[^\]]+\])?==(?P<version>[^;\s]+)(?P<marker>\s*;.*)?$")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_pinned_file(path: Path) -> dict:
    """
    Parse a pip-compile-style pinned file. Every requirement line must be an
    exact `name==version` pin (extras and environment markers allowed);
    comments, blanks, `-r` includes, and option lines are ignored. Returns
    pins plus any offending lines.
    """
    pins: dict[str, str] = {}
    problems: list[str] = []
    if not path.exists():
        return {"pins": pins, "problems": [f"missing_file:{path.name}"]}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(("#", "-r ", "--")):
            continue
        m = _PIN_RE.match(line)
        if not m:
            problems.append(f"{path.name}:{lineno}: not exactly pinned: {line}")
            continue
        name = _norm(m.group("name"))
        version = m.group("version")
        if name in pins and pins[name] != version:
            problems.append(f"{path.name}:{lineno}: conflicting pin for {name}: {pins[name]} vs {version}")
            continue
        pins[name] = version
    return {"pins": pins, "problems": problems}


def check_pin_integrity(repo: Path = _REPO) -> dict:
    """Every pinned file parses clean; pins shared across files agree."""
    problems: list[str] = []
    per_file: dict[str, dict[str, str]] = {}
    for fname in PINNED_FILES:
        parsed = parse_pinned_file(repo / fname)
        problems += parsed["problems"]
        per_file[fname] = parsed["pins"]
    runtime = per_file.get(PINNED_FILES[0], {})
    dev = per_file.get(PINNED_FILES[1], {})
    for name in sorted(set(runtime) & set(dev)):
        if runtime[name] != dev[name]:
            problems.append(f"cross_file_conflict:{name}: {runtime[name]} (runtime) vs {dev[name]} (dev)")
    return {"ok": not problems, "problems": problems, "pins": runtime, "dev_pins": dev}


def check_environment_matches(pins: dict[str, str]) -> dict:
    """
    Installed distributions must match pinned versions. A pinned package
    that is not installed is a note (optional extras exist); an installed
    package at a DIFFERENT version than its pin is a failure — the running
    environment is not the reviewed environment.
    """
    from importlib import metadata

    mismatches: list[str] = []
    missing: list[str] = []
    checked = 0
    for name, pinned in sorted(pins.items()):
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            missing.append(name)
            continue
        checked += 1
        if installed != pinned:
            mismatches.append(f"{name}: installed {installed} != pinned {pinned}")
    return {"ok": not mismatches, "checked": checked, "mismatches": mismatches, "not_installed": missing}


def run_vulnerability_audit(timeout_s: int = 300) -> dict:
    """
    Best-effort `pip-audit` lane. Per the supply-chain policy, audit
    findings are review-not-block for paper operation; absence of the tool
    is recorded, never fabricated.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--format", "json", "--progress-spinner", "off"],
            capture_output=True, text=True, timeout=timeout_s,
        )
    except FileNotFoundError:
        return {"ran": False, "reason": "pip_audit_unavailable"}
    except subprocess.TimeoutExpired:
        return {"ran": False, "reason": "pip_audit_timeout"}
    except Exception as exc:
        return {"ran": False, "reason": f"pip_audit_error:{type(exc).__name__}"}
    if proc.returncode not in (0, 1) or (not proc.stdout.strip() and "No module named" in proc.stderr):
        return {"ran": False, "reason": "pip_audit_unavailable"}
    try:
        parsed = json.loads(proc.stdout)
        deps = parsed.get("dependencies") if isinstance(parsed, dict) else parsed
        vulns = [
            {"name": d.get("name"), "version": d.get("version"), "vulns": d.get("vulns")}
            for d in (deps or [])
            if d.get("vulns")
        ]
        return {"ran": True, "vulnerable_count": len(vulns), "findings": vulns}
    except Exception:
        return {"ran": False, "reason": "pip_audit_output_unparseable"}


def _git(args: list[str]) -> str:
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, cwd=str(_REPO), timeout=30
        ).stdout.strip()
    except Exception:
        return ""


def build_evidence(*, audit: dict | None) -> dict:
    """Provenance evidence for the current SHA: git identity, requirement
    file hashes, pin counts, environment verdicts, optional audit output."""
    integrity = check_pin_integrity()
    env = check_environment_matches(integrity["pins"])
    req_hashes = {}
    for fname in PINNED_FILES:
        path = _REPO / fname
        if path.exists():
            req_hashes[fname] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "created": _iso_now(),
        "git_sha": _git(["rev-parse", "HEAD"]),
        "git_dirty": bool(_git(["status", "--porcelain"])),
        "requirement_file_sha256": req_hashes,
        "pin_integrity": {"ok": integrity["ok"], "problems": integrity["problems"], "pin_count": len(integrity["pins"])},
        "environment": env,
        "vulnerability_audit": audit if audit is not None else {"ran": False, "reason": "not_requested"},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Supply-chain verification: pin integrity, environment match, audit evidence.")
    ap.add_argument("--audit", action="store_true", help="run pip-audit if available (best-effort; review-not-block per policy)")
    ap.add_argument("--strict-audit", action="store_true", help="fail the exit code on audit findings (capped-live posture)")
    ap.add_argument("--evidence-dest", default=None, help="write a provenance evidence JSON into this directory")
    ap.add_argument("--json", action="store_true", help="print the full JSON report")
    args = ap.parse_args()

    audit = run_vulnerability_audit() if (args.audit or args.strict_audit) else None
    evidence = build_evidence(audit=audit)

    ok = evidence["pin_integrity"]["ok"] and evidence["environment"]["ok"]
    if args.strict_audit:
        a = evidence["vulnerability_audit"]
        ok = ok and a.get("ran") is True and int(a.get("vulnerable_count") or 0) == 0

    if args.evidence_dest:
        dest = Path(args.evidence_dest)
        dest.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        out_path = dest / f"supply-chain-evidence-{stamp}.json"
        out_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        evidence["evidence_path"] = str(out_path)

    if args.json:
        print(json.dumps(evidence, indent=2))
    else:
        pi = evidence["pin_integrity"]
        env = evidence["environment"]
        print(f"pin integrity: {'ok' if pi['ok'] else 'FAIL'} ({pi['pin_count']} pins)")
        for p in pi["problems"]:
            print(f"  {p}")
        print(f"environment: {'ok' if env['ok'] else 'FAIL'} ({env['checked']} checked, {len(env['not_installed'])} not installed)")
        for m in env["mismatches"]:
            print(f"  {m}")
        a = evidence["vulnerability_audit"]
        print(f"audit: {'ran, %d vulnerable' % a.get('vulnerable_count', 0) if a.get('ran') else a.get('reason')}")
        if "evidence_path" in evidence:
            print(f"evidence: {evidence['evidence_path']}")

    return EXIT_OK if ok else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
