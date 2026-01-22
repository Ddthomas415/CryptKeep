# apply_phase120.py - Phase 120: Versioning + optional update check + manual download
from pathlib import Path

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"Written/Updated: {path}")

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        print(f"Skipping patch - file missing: {path}")
        return
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        print(f"Patched: {path}")
    else:
        print(f"No changes needed: {path}")

# 1) Version file (single source of truth)
if not Path("VERSION").exists():
    Path("VERSION").write_text("0.1.0\n", encoding="utf-8")
    print("Created VERSION file with initial 0.1.0")

# 2) Version helper
write("services/app/versioning.py", r'''from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone

def _repo_root() -> Path:
    # services/app/versioning.py -> repo root
    return Path(__file__).resolve().parents[2]

def current_version() -> str:
    try:
        v = (_repo_root() / "VERSION").read_text(encoding="utf-8").strip()
        return v or "0.0.0"
    except Exception:
        return "0.0.0"

def build_meta() -> dict:
    return {
        "version": current_version(),
        "build_ts_utc": datetime.now(timezone.utc).isoformat(),
    }
''')

# 3) Update checker (stdlib only)
write("services/app/update_checker.py", r'''from __future__ import annotations
import json
import socket
import urllib.request
from dataclasses import dataclass
from typing import Optional
from services.admin.config_editor import load_user_yaml

def _cfg() -> dict:
    cfg = load_user_yaml()
    u = cfg.get("updates") if isinstance(cfg.get("updates"), dict) else {}
    return {
        "enabled": bool(u.get("enabled", False)),
        "channel_url": str(u.get("channel_url", "") or "").strip(),
        "timeout_sec": float(u.get("timeout_sec", 5.0) or 5.0),
        "allow_download": bool(u.get("allow_download", False)),
    }

def _safe_fetch_json(url: str, timeout_sec: float) -> dict:
    socket.setdefaulttimeout(float(timeout_sec))
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoBotPro/1.0"})
    with urllib.request.urlopen(req, timeout=float(timeout_sec)) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)

def check_for_update(current_version: str) -> dict:
    cfg = _cfg()
    if not cfg["enabled"]:
        return {"ok": True, "enabled": False, "reason": "updates.disabled"}
    if not cfg["channel_url"]:
        return {"ok": False, "enabled": True, "reason": "updates.channel_url_missing"}
    try:
        data = _safe_fetch_json(cfg["channel_url"], cfg["timeout_sec"])
    except Exception as e:
        return {"ok": False, "enabled": True, "reason": f"fetch_failed:{type(e).__name__}:{e}"}
    latest = str(data.get("latest_version") or "").strip()
    if not latest:
        return {"ok": False, "enabled": True, "reason": "bad_channel_payload:missing_latest_version", "data": data}
    def parse(v: str):
        parts = v.strip().split(".")
        out = []
        for p in parts[:3]:
            try:
                out.append(int(p))
            except Exception:
                return None
        while len(out) < 3:
            out.append(0)
        return tuple(out)
    cur_p = parse(current_version)
    lat_p = parse(latest)
    is_newer = False
    if cur_p is not None and lat_p is not None:
        is_newer = lat_p > cur_p
    else:
        is_newer = latest != current_version
    return {
        "ok": True,
        "enabled": True,
        "current_version": current_version,
        "latest_version": latest,
        "update_available": bool(is_newer),
        "published_ts": data.get("published_ts"),
        "notes": data.get("notes"),
        "release_page_url": data.get("release_page_url"),
        "download_url": data.get("download_url"),
        "allow_download": bool(cfg["allow_download"]),
        "raw": data,
    }

def download_update(download_url: str, dest_path: str, *, timeout_sec: float = 30.0) -> dict:
    try:
        socket.setdefaulttimeout(float(timeout_sec))
        req = urllib.request.Request(download_url, headers={"User-Agent": "CryptoBotPro/1.0"})
        with urllib.request.urlopen(req, timeout=float(timeout_sec)) as resp:
            data = resp.read()
        import pathlib
        p = pathlib.Path(dest_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return {"ok": True, "saved_to": str(p), "bytes": len(data)}
    except Exception as e:
        return {"ok": False, "reason": f"download_failed:{type(e).__name__}:{e}"}
''')

# 4) Version bump script
write("scripts/bump_version.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

def parse(v: str):
    parts = v.strip().split(".")
    if len(parts) < 1:
        return (0,0,0)
    nums = []
    for i in range(3):
        try:
            nums.append(int(parts[i]) if i < len(parts) else 0)
        except Exception:
            nums.append(0)
    return tuple(nums)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("part", choices=["major","minor","patch"], nargs="?", default="patch")
    args = ap.parse_args()
    vf = Path("VERSION")
    cur = vf.read_text(encoding="utf-8").strip() if vf.exists() else "0.0.0"
    a,b,c = parse(cur)
    if args.part == "major":
        a, b, c = a+1, 0, 0
    elif args.part == "minor":
        b, c = b+1, 0
    else:
        c = c+1
    nv = f"{a}.{b}.{c}"
    vf.write_text(nv + "\n", encoding="utf-8")
    print({"ok": True, "from": cur, "to": nv})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 5) Dashboard panel: About + Updates
def patch_dashboard(t: str) -> str:
    if "About / Updates" in t and "services.app.update_checker" in t:
        return t
    add = r'''
st.divider()
st.header("About / Updates")
st.caption("Versioning is local (VERSION file). Update check is optional, manual, and OFF by default. No auto-install.")
try:
    import os as _os
    from pathlib import Path as _Path
    from services.app.versioning import current_version
    from services.app.update_checker import check_for_update, download_update
    from services.admin.config_editor import load_user_yaml
    v = current_version()
    st.success({"version": v})
    cfg = load_user_yaml()
    u = cfg.get("updates", {}) if isinstance(cfg.get("updates"), dict) else {}
    st.subheader("Update settings (config/user.yaml → updates)")
    st.json(u)
    if st.button("Check for update now"):
        res = check_for_update(v)
        st.json(res)
        if res.get("ok") and res.get("update_available") and res.get("allow_download") and res.get("download_url"):
            st.warning("Manual download only. This will NOT run or install anything.")
            if st.button("Download update artifact"):
                dest = _Path("runtime") / "downloads"
                dest.mkdir(parents=True, exist_ok=True)
                fn = f"CryptoBotPro_update_{res.get('latest_version')}"
                out = download_update(res["download_url"], str(dest / fn))
                st.json(out)
        elif res.get("ok") and res.get("update_available") and not res.get("allow_download"):
            st.info("Update found, but updates.allow_download is false. Enable it to allow manual download.")
except Exception as e:
    st.error(f"Updates panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 6) Config validation: updates.*
def patch_config_editor(t: str) -> str:
    if "updates.channel_url" in t and "updates.allow_download" in t:
        return t
    insert = """
    # Updates (optional)
    up = cfg.get("updates", {})
    if up is not None and not isinstance(up, dict):
        errors.append("updates:must_be_mapping")
        up = {}
    if isinstance(up, dict):
        if "enabled" in up and up["enabled"] is not None and not _is_bool(up["enabled"]):
            errors.append("updates.enabled:must_be_bool")
        if "allow_download" in up and up["allow_download"] is not None and not _is_bool(up["allow_download"]):
            errors.append("updates.allow_download:must_be_bool")
        if "timeout_sec" in up and up["timeout_sec"] is not None and not _is_float(up["timeout_sec"]):
            errors.append("updates.timeout_sec:must_be_float")
        if "channel_url" in up and up["channel_url"] is not None:
            try: str(up["channel_url"])
            except Exception: errors.append("updates.channel_url:must_be_string")
"""
    anchor = "ok = len(errors) == 0"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 7) install.py defaults: updates block (OFF by default)
def patch_install_py(t: str) -> str:
    if "updates:" in t:
        return t
    block = (
        "updates:\n"
        " enabled: false\n"
        " channel_url: \"\"\n"
        " timeout_sec: 5.0\n"
        " allow_download: false\n\n"
    )
    if "preflight:\n" in t:
        return t.replace("preflight:\n", block + "preflight:\n", 1)
    return t + "\n# Added by Phase 120\n" + block

patch("install.py", patch_install_py)

# 8) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DP) Versioning + Safe Update Check" in t:
        return t
    return t + (
        "\n## DP) Versioning + Safe Update Check\n"
        "- ✅ DP1: VERSION file is the single source of truth for app version\n"
        "- ✅ DP2: Dashboard About/Updates panel shows version and can check a JSON update channel (optional)\n"
        "- ✅ DP3: Manual download only (no auto-install). Guarded by updates.allow_download\n"
        "- ✅ DP4: bump_version script for controlled version increments\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 120 applied (versioning + optional update check + manual download + checkpoints).")
print("Next steps:")
print("  1. Bump version (optional): python3 scripts/bump_version.py patch")
print("  2. Check dashboard 'About / Updates' panel for version + check button")
print("  3. Set updates.channel_url in config/user.yaml to test update check")
END