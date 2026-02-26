from __future__ import annotations

import os
import importlib.util
from pathlib import Path

import streamlit as st

st.title("Legacy UI (disabled by default)")
st.caption("This page imports the old monolithic dashboard. It is OFF by default to prevent widget collisions.")

enable = os.environ.get("CBP_ENABLE_LEGACY_UI", "").strip().lower() in {"1", "true", "yes", "on"}
if not enable:
    st.info("Legacy UI is disabled. Set environment variable CBP_ENABLE_LEGACY_UI=1 to enable it for this run.")
    st.stop()

st.warning("Legacy UI enabled. If you see Streamlit duplicate-widget errors, disable this page again.")

# Find the legacy module beside dashboard/app.py backups (the latest app_legacy_*.py)
dash = Path(__file__).resolve().parents[1]
candidates = sorted(dash.glob("app_legacy_*.py"))
if not candidates:
    st.error("No legacy backup found (dashboard/app_legacy_*.py).")
    st.stop()

legacy = candidates[-1]
st.code(f"Importing legacy file: {legacy.name}")

spec = importlib.util.spec_from_file_location("cbp_legacy_ui", legacy)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)  # type: ignore
