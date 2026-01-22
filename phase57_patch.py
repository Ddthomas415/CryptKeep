from pathlib import Path

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        raise RuntimeError(f"Missing file: {path}")
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")

# --- 1) Patch cbp_desktop/service_manager.py ---
SM_PATH = "cbp_desktop/service_manager.py"

def patch_service_manager(t: str) -> str:
    if "def known_service_names" in t:
        return t

    add = """

def known_service_names() -> list[str]:
    try:
        return sorted(list(SERVICE_SPECS.keys()))
    except Exception:
        return []
"""
    return t + add

patch(SM_PATH, patch_service_manager)

# --- 2) Patch dashboard/app.py ---
def patch_dashboard(t: str) -> str:
    if "Service controls" in t:
        return t

    add = """
st.divider()
st.header("Service controls")

st.caption("Stop services safely using PID files.")

try:
    from services.admin.service_controls import stop_all_services_from_pids, clean_stale_pid_files

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Stop all services"):
            st.json(stop_all_services_from_pids())

    with c2:
        if st.button("Clean stale PID files"):
            st.json(clean_stale_pid_files())

except Exception as e:
    st.error(f"Service controls failed: {type(e).__name__}: {e}")
"""
    return t + add

patch("dashboard/app.py", patch_dashboard)

# --- 3) Patch CHECKPOINTS.md ---
def patch_cp(t: str) -> str:
    if "## BE) Dashboard Service Controls" in t:
        return t
    return t + """
## BE) Dashboard Service Controls
- ✅ BE1: service_manager exposes known_service_names
- ✅ BE2: PID-scoped stop & cleanup helpers
- ✅ BE3: Dashboard buttons added
"""

patch("CHECKPOINTS.md", patch_cp)

print("OK: Phase 57 applied cleanly.")

