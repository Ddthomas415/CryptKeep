# apply_phase122.py - Phase 122: System Health + Diagnostics Export + checkpoints
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

# 1) Diagnostics exporter (zip, redacts obvious secret-like keys)
write("services/app/diagnostics_exporter.py", r'''from __future__ import annotations
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
            arc = f"runtime/{rel.as_posix()}"
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
''')

# 2) CLI script
write("scripts/export_diagnostics.py", r'''#!/usr/bin/env python3
from __future__ import annotations
from services.app.diagnostics_exporter import export_zip_to_runtime

def main():
    p = export_zip_to_runtime()
    print({"ok": True, "exported_to": str(p)})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 3) Health collector helper (dashboard uses this)
write("services/app/system_health.py", r'''from __future__ import annotations
import json
from pathlib import Path
from services.os.app_paths import runtime_dir
from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_venue, normalize_symbol
from services.market_data.multi_venue_view import venue_rows, rank_rows

def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def collect_process_files() -> dict:
    rt = runtime_dir()
    flags = rt / "flags"
    locks = rt / "locks"
    sup = rt / "supervisor"
    snaps = rt / "snapshots"
    def list_files(d: Path):
        if not d.exists():
            return []
        out = []
        for p in sorted(d.glob("*")):
            if p.is_file():
                out.append({"path": str(p), "name": p.name, "mtime": p.stat().st_mtime})
        return out
    return {
        "flags": list_files(flags),
        "locks": list_files(locks),
        "supervisor": list_files(sup),
        "snapshots": list_files(snaps),
        "pids": _read_json(sup / "pids.json") if (sup / "pids.json").exists() else None,
    }

def collect_market_health() -> list[dict]:
    cfg = load_user_yaml()
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venues = pf.get("venues") if isinstance(pf.get("venues"), list) else ["binance","coinbase","gateio"]
    symbols = pf.get("symbols") if isinstance(pf.get("symbols"), list) else ["BTC/USDT"]
    venues = [normalize_venue(str(v)) for v in venues]
    symbols = [normalize_symbol(str(s)) for s in symbols]
    rows_all = []
    for sym in symbols:
        rows = rank_rows(venue_rows(venues, sym))
        for r in rows:
            r2 = dict(r)
            r2["symbol"] = sym
            rows_all.append(r2)
    return rows_all
''')

# 4) Dashboard: System Health + Diagnostics section
def patch_dashboard(t: str) -> str:
    if "System Health + Diagnostics" in t and "Download diagnostics zip" in t:
        return t
    add = r'''
st.divider()
st.header("System Health + Diagnostics")
st.caption("One place to see process status/locks, queue depths, and multi-venue tick freshness/spreads. Export diagnostics zip is sanitized (no secrets).")
try:
    import pandas as pd
    from pathlib import Path as _Path
    from services.os.app_paths import runtime_dir
    from services.app.system_health import collect_process_files, collect_market_health
    from services.app.diagnostics_exporter import build_diagnostics_zip_bytes, export_zip_to_runtime
    # 1) Process files (flags/locks/pids/snapshots)
    st.subheader("Process status / locks")
    proc = collect_process_files()
    st.json({"pids": proc.get("pids")})
    c1, c2 = st.columns(2)
    with c1:
        st.write("Flags")
        st.dataframe(pd.DataFrame(proc.get("flags") or []), width='stretch', height=180)
        st.write("Snapshots")
        st.dataframe(pd.DataFrame(proc.get("snapshots") or []), width='stretch', height=180)
    with c2:
        st.write("Locks")
        st.dataframe(pd.DataFrame(proc.get("locks") or []), width='stretch', height=180)
        st.write("Supervisor")
        st.dataframe(pd.DataFrame(proc.get("supervisor") or []), width='stretch', height=180)
    # 2) Queue depths (paper + live if present)
    st.subheader("Queue depth")
    try:
        from storage.intent_queue_sqlite import IntentQueueSQLite
        qdb = IntentQueueSQLite()
        q_sub = len(qdb.list_intents(2000, status="submitted"))
        q_que = len(qdb.list_intents(2000, status="queued"))
        q_fill = len(qdb.list_intents(2000, status="filled"))
        st.json({"paper_intents": {"queued": q_que, "submitted": q_sub, "filled_recent": q_fill}})
    except Exception as e:
        st.warning(f"Paper queue unavailable: {type(e).__name__}: {e}")
    try:
        from storage.live_intent_queue_sqlite import LiveIntentQueueSQLite
        lq = LiveIntentQueueSQLite()
        l_que = len(lq.list_intents(2000, status="queued"))
        l_sub = len(lq.list_intents(2000, status="submitted"))
        l_fill = len(lq.list_intents(2000, status="filled"))
        st.json({"live_intents": {"queued": l_que, "submitted": l_sub, "filled_recent": l_fill}})
    except Exception:
        st.info("Live queue not present or not initialized (expected unless you enabled live scaffold).")
    # 3) Market data health (multi-venue)
    st.subheader("Market data health (multi-venue)")
    rows = collect_market_health()
    df = pd.DataFrame(rows)
    if len(df) > 0:
        st.dataframe(df, width='stretch', height=320)
    else:
        st.info("No market health rows yet (ensure tick publisher is running and preflight venues/symbols are set).")
    # 4) Diagnostics export
    st.subheader("Export diagnostics (sanitized)")
    c3, c4 = st.columns(2)
    with c3:
        if st.button("Export diagnostics zip to runtime/exports"):
            p = export_zip_to_runtime()
            st.success({"ok": True, "exported_to": str(p)})
    with c4:
        zbytes = build_diagnostics_zip_bytes()
        st.download_button(
            "Download diagnostics zip",
            data=zbytes,
            file_name="diagnostics.zip",
            mime="application/zip",
        )
    st.caption(f"Exports folder: {runtime_dir() / 'exports'}")
except Exception as e:
    st.error(f"System Health panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 5) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DR) System Health + Diagnostics Export" in t:
        return t
    return t + (
        "\n## DR) System Health + Diagnostics Export\n"
        "- ✅ DR1: System health collector (flags/locks/pids/snapshots + market health rows)\n"
        "- ✅ DR2: Dashboard System Health panel (process files + queue depth + market health table)\n"
        "- ✅ DR3: Diagnostics exporter builds a sanitized zip (runtime tails + config snapshot + manifests)\n"
        "- ✅ DR4: scripts/export_diagnostics.py CLI export to runtime/exports\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 122 applied (System Health + Diagnostics Export + checkpoints).")
print("Next steps:")
print("  1. Export diagnostics zip: python3 scripts/export_diagnostics.py")
print("  2. Check dashboard 'System Health + Diagnostics' panel for process status + market health + export button")
print("  3. When ready for live test: arm env + enqueue tiny intent via dashboard")
END_OF_FINAL