from __future__ import annotations
import io
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from services.os.app_paths import runtime_dir
from services.app.versioning import current_version

REPO_ROOT = Path(__file__).resolve().parents[2]
REDACT_KEYS = ("api_key", "apikey", "secret", "passphrase", "password", "private_key")

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _tail_text(p: Path, max_chars: int = 12000) -> str:
    try:
        s = p.read_text(encoding="utf-8", errors="replace")
        if len(s) > max_chars:
            return "\n...TRUNCATED...\n" + s[-max_chars:]
        return s
    except Exception as e:
        return f"(unreadable:{type(e).__name__}:{e})\n"

def _safe_yaml_text(raw: str) -> str:
    out = []
    for line in raw.splitlines():
        low = line.lower()
        if any(k in low for k in REDACT_KEYS) and ("_env" not in low):
            if ":" in line:
                out.append(line.split(":")[0] + ": ***REDACTED***")
            else:
                out.append("***REDACTED_LINE***")
        else:
            out.append(line)
    return "\n".join(out) + "\n"

def _read_sanitized_config() -> str:
    p = REPO_ROOT / "config" / "user_config.yaml"
    try:
        raw = p.read_text(encoding="utf-8", errors="replace")
        return _safe_yaml_text(raw)
    except Exception as e:
        return f"(missing:{p}:{type(e).__name__}:{e})\n"

def _iter_runtime_files() -> List[Path]:
    rt = runtime_dir()
    out = []
    for sub in ("flags", "locks", "supervisor", "snapshots"):
        d = rt / sub
        if d.exists():
            out.extend([x for x in d.rglob("*") if x.is_file()])
    logd = rt / "logs"
    if logd.exists():
        out.extend([x for x in logd.glob("*.log") if x.is_file()])
    return out

def build_diagnostics_zip_bytes() -> bytes:
    ts = _now()
    version = current_version()
    rt = runtime_dir()
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as z:
        manifest = {
            "generated_utc": ts,
            "version": version,
            "repo_root": str(REPO_ROOT),
            "runtime_dir": str(rt),
            "files": [],
        }
        def add_text(name: str, text: str):
            z.writestr(name, text)
        add_text("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        for rp in ["VERSION", "CHECKPOINTS.md", "INSTALL_APP.md", "PACKAGING.md"]:
            p = REPO_ROOT / rp
            if p.exists():
                add_text(f"repo/{rp}", _tail_text(p, max_chars=200000))
        add_text("config/user_config.yaml", _read_sanitized_config())
        for p in _iter_runtime_files():
            rel = p.relative_to(rt)
            arc = f"state/{rel.as_posix()}"
            if p.name.endswith(".log"):
                add_text(arc, _tail_text(p, max_chars=20000))
            else:
                add_text(arc, _tail_text(p, max_chars=200000))
        files = []
        for info in z.infolist():
            files.append({"name": info.filename, "size": info.file_size, "compressed": info.compress_size})
        final_manifest = {
            "generated_utc": ts,
            "version": version,
            "repo_root": str(REPO_ROOT),
            "runtime_dir": str(rt),
            "zip_entries": files,
        }
        z.writestr("manifest.json", json.dumps(final_manifest, indent=2, sort_keys=True))
    return mem.getvalue()

def export_zip_to_runtime() -> Path:
    out_dir = runtime_dir() / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"diagnostics_{stamp}.zip"
    out_path.write_bytes(build_diagnostics_zip_bytes())
    return out_path
