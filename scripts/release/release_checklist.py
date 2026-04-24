from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from services.os import app_paths

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = ROOT / "releases"

# Include likely output dirs so manifests capture final signed artifacts too.
DIST_DIRS = [
    ROOT / "dist",
    ROOT / "build",
    app_paths.data_dir() / "reconcile_reports",
]

VERSION_RE = re.compile(r'(?m)^(version\s*=\s*")(\d+\.\d+\.\d+)(")\s*$')

def _run(cmd: list[str], cwd: Path | None = None) -> dict[str, Any]:
    t0 = time.time()
    p = subprocess.run(cmd, cwd=str(cwd or ROOT), capture_output=True, text=True)
    return {
        "cmd": cmd,
        "returncode": p.returncode,
        "stdout": (p.stdout or "")[:20000],
        "stderr": (p.stderr or "")[:20000],
        "seconds": round(time.time() - t0, 3),
        "ok": p.returncode == 0,
    }

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _collect_artifacts() -> list[dict[str, Any]]:
    arts: list[dict[str, Any]] = []
    for d in DIST_DIRS:
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if p.is_file():
                if p.name.endswith((".log", ".tmp")):
                    continue
                try:
                    arts.append({
                        "path": str(p.relative_to(ROOT)),
                        "bytes": p.stat().st_size,
                        "sha256": _sha256(p),
                        "mtime": p.stat().st_mtime,
                    })
                except Exception:
                    continue
    arts.sort(key=lambda x: x["path"])
    return arts

def _read_pyproject() -> tuple[Path, str]:
    p = ROOT / "pyproject.toml"
    if not p.exists():
        raise FileNotFoundError("pyproject.toml not found")
    return p, p.read_text(encoding="utf-8", errors="replace")

def _get_version(py_txt: str) -> str:
    m = VERSION_RE.search(py_txt)
    if not m:
        raise RuntimeError("Could not find version = \"x.y.z\" in pyproject.toml")
    return m.group(2)

def _bump(ver: str, kind: str) -> str:
    a, b, c = ver.split(".")
    A, B, C = int(a), int(b), int(c)
    if kind == "patch":
        C += 1
    elif kind == "minor":
        B += 1
        C = 0
    elif kind == "major":
        A += 1
        B = 0
        C = 0
    else:
        raise ValueError("bump must be patch|minor|major")
    return f"{A}.{B}.{C}"

def _set_version(py_txt: str, new_ver: str) -> str:
    m = VERSION_RE.search(py_txt)
    if not m:
        raise RuntimeError("Version line not found for replacement")
    return py_txt[:m.start()] + f'{m.group(1)}{new_ver}{m.group(3)}\n' + py_txt[m.end():]

def _write_manifest(man: dict[str, Any]) -> Path:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    out = MANIFEST_DIR / f"release_manifest_{ts}.json"
    out.write_text(json.dumps(man, indent=2, sort_keys=True), encoding="utf-8")
    return out

# --------------------------
# Signing helpers (FAIL-CLOSED)
# --------------------------
def _truthy_env(name: str) -> bool:
    v = (os.environ.get(name) or "").strip().lower()
    return v in ("1", "true", "yes", "on")

def _find_files(patterns: tuple[str, ...], roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        if not r.exists():
            continue
        for p in r.rglob("*"):
            if not p.is_file():
                continue
            lp = p.name.lower()
            if any(lp.endswith(suf) for suf in patterns):
                key = str(p.resolve())
                if key not in seen:
                    seen.add(key)
                    out.append(p)
    out.sort(key=lambda p: str(p))
    return out

def _find_apps(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        if not r.exists():
            continue
        for p in r.rglob("*.app"):
            if p.is_dir():
                key = str(p.resolve())
                if key not in seen:
                    seen.add(key)
                    out.append(p)
    out.sort(key=lambda p: str(p))
    return out

def _sign_windows(files: list[Path]) -> dict[str, Any]:
    # Required (one of):
    #  - SIGN_PFX_PATH + SIGN_PFX_PASSWORD
    #  - SIGN_CERT_THUMBPRINT
    pfx = os.environ.get("SIGN_PFX_PATH", "").strip()
    pwd = os.environ.get("SIGN_PFX_PASSWORD", "").strip()
    thumb = os.environ.get("SIGN_CERT_THUMBPRINT", "").strip()
    ts_url = os.environ.get("SIGN_TIMESTAMP_URL", "http://timestamp.digicert.com").strip()

    if not files:
        return {"ok": True, "did_work": False, "reason": "no_windows_artifacts_found"}

    if not ((pfx and pwd) or thumb):
        return {"ok": False, "reason": "missing_signing_credentials", "need": ["SIGN_PFX_PATH+SIGN_PFX_PASSWORD OR SIGN_CERT_THUMBPRINT"]}

    script = ROOT / "packaging" / "signing" / "windows_sign.ps1"
    if not script.exists():
        return {"ok": False, "reason": "windows_sign_script_missing", "path": str(script)}

    results = []
    for f in files:
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script), "-FilePath", str(f)]
        if pfx and pwd:
            cmd += ["-PfxPath", pfx, "-PfxPassword", pwd]
        else:
            cmd += ["-CertThumbprint", thumb]
        if ts_url:
            cmd += ["-TimeStampUrl", ts_url]
        results.append({"file": str(f.relative_to(ROOT)), **_run(cmd)})
        if results[-1].get("ok") is not True:
            # fail closed on first failure
            return {"ok": False, "reason": "sign_failed", "results": results}
    return {"ok": True, "did_work": True, "signed_n": len(results), "results": results}

def _notarize_macos(apps: list[Path]) -> dict[str, Any]:
    identity = (os.environ.get("MAC_SIGN_IDENTITY") or "").strip()
    bundle_id = (os.environ.get("MAC_BUNDLE_ID") or "").strip()
    profile = (os.environ.get("MAC_NOTARY_PROFILE") or "").strip()

    if not apps:
        return {"ok": True, "did_work": False, "reason": "no_macos_apps_found"}

    if not (identity and bundle_id and profile):
        return {"ok": False, "reason": "missing_notarization_params", "need": ["MAC_SIGN_IDENTITY", "MAC_BUNDLE_ID", "MAC_NOTARY_PROFILE"]}

    script = ROOT / "packaging" / "signing" / "macos_sign_and_notarize.sh"
    if not script.exists():
        return {"ok": False, "reason": "macos_sign_script_missing", "path": str(script)}

    results = []
    for app in apps:
        cmd = [
            "bash", str(script),
            "--app", str(app),
            "--identity", identity,
            "--bundle-id", bundle_id,
            "--notary-profile", profile,
        ]
        results.append({"app": str(app.relative_to(ROOT)), **_run(cmd)})
        if results[-1].get("ok") is not True:
            return {"ok": False, "reason": "notarize_failed", "results": results}
    return {"ok": True, "did_work": True, "notarized_n": len(results), "results": results}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bump", choices=["none", "patch", "minor", "major"], default="none")
    ap.add_argument("--sync-requires", action="store_true", help="run scripts/sync_briefcase_requires.py")
    ap.add_argument("--briefcase", action="store_true", help="run briefcase create/build/package for the current OS")
    ap.add_argument("--pyinstaller", action="store_true", help="run pyinstaller wrapper build for the current OS")
    ap.add_argument("--dry-run", action="store_true")

    # Opt-in signing hooks (also controllable via env vars)
    ap.add_argument("--sign-windows", action="store_true", help="sign windows artifacts (requires env creds); or set RELEASE_SIGN_WINDOWS=1")
    ap.add_argument("--notarize-mac", action="store_true", help="sign+notarize mac apps (requires env creds); or set RELEASE_NOTARIZE_MAC=1")

    args = ap.parse_args()

    pyproject_path, py_txt = _read_pyproject()
    old_ver = _get_version(py_txt)
    new_ver = old_ver

    steps: list[dict[str, Any]] = []
    ok_all = True

    # Version bump (optional)
    if args.bump != "none":
        new_ver = _bump(old_ver, args.bump)
        steps.append({"step": "version_bump_plan", "from": old_ver, "to": new_ver})
        if not args.dry_run:
            bak = pyproject_path.with_suffix(".toml.bak")
            bak.write_text(py_txt, encoding="utf-8")
            pyproject_path.write_text(_set_version(py_txt, new_ver), encoding="utf-8")
            steps.append({"step": "version_bump_write", "ok": True, "backup": str(bak)})

    # Requires sync (optional)
    if args.sync_requires:
        r = _run([sys.executable, "scripts/sync_briefcase_requires.py"])
        r["step"] = "sync_briefcase_requires"
        steps.append(r)
        ok_all = ok_all and bool(r.get("ok"))

    # Builds (optional)
    if args.pyinstaller:
        if platform.system().lower().startswith("win"):
            r = _run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "packaging/pyinstaller/build.ps1"])
        else:
            r = _run(["bash", "packaging/pyinstaller/build.sh"])
        r["step"] = "pyinstaller_build"
        steps.append(r)
        ok_all = ok_all and bool(r.get("ok"))

    if args.briefcase:
        if platform.system().lower().startswith("win"):
            r = _run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "packaging/briefcase/build_windows.ps1"])
        else:
            r = _run(["bash", "packaging/briefcase/build_macos.sh"])
        r["step"] = "briefcase_package"
        steps.append(r)
        ok_all = ok_all and bool(r.get("ok"))

    # Signing/notarization (opt-in; FAIL-CLOSED)
    want_sign_windows = args.sign_windows or _truthy_env("RELEASE_SIGN_WINDOWS")
    want_notarize_mac = args.notarize_mac or _truthy_env("RELEASE_NOTARIZE_MAC")

    if not args.dry_run and want_sign_windows and platform.system().lower().startswith("win"):
        files = _find_files((".exe", ".msi"), [ROOT / "dist", ROOT / "build"])
        rep = _sign_windows(files)
        steps.append({"step": "windows_sign", **rep})
        ok_all = ok_all and bool(rep.get("ok"))

    if not args.dry_run and want_notarize_mac and platform.system().lower() == "darwin":
        apps = _find_apps([ROOT / "dist", ROOT / "build"])
        rep = _notarize_macos(apps)
        steps.append({"step": "macos_notarize", **rep})
        ok_all = ok_all and bool(rep.get("ok"))

    man = {
        "ok": bool(ok_all),
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": sys.version,
        },
        "repo_root": str(ROOT),
        "version": {"old": old_ver, "new": new_ver},
        "options": {
            "sync_requires": bool(args.sync_requires),
            "pyinstaller": bool(args.pyinstaller),
            "briefcase": bool(args.briefcase),
            "sign_windows_requested": bool(want_sign_windows),
            "notarize_mac_requested": bool(want_notarize_mac),
        },
        "steps": steps,
        "artifacts": _collect_artifacts(),
    }

    out = _write_manifest(man) if not args.dry_run else None
    print(json.dumps({
        "ok": man["ok"],
        "manifest_written": (str(out) if out else None),
        "version": man["version"],
        "steps_n": len(steps),
        "artifacts_n": len(man["artifacts"]),
    }, indent=2))

if __name__ == "__main__":
    import datetime
    main()
