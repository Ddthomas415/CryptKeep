#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    checks = []
    def ok(name, value=True, details=None):
        checks.append({"name": name, "ok": bool(value), "details": details})
    ok("repo_root_exists", ROOT.exists(), str(ROOT))
    ok("dashboard_app_exists", (ROOT/"dashboard"/"app.py").exists())
    ok("user_yaml_exists", (ROOT/"runtime"/"config"/"user.yaml").exists())
    ok("data_dir_exists", (ROOT/"data").exists())
    ok("runtime_snapshots_dir_exists", (ROOT/"runtime"/"snapshots").exists())
    try:
        import streamlit  # noqa
        ok("import_streamlit", True)
    except Exception as e:
        ok("import_streamlit", False, f"{type(e).__name__}: {e}")
    try:
        import ccxt  # noqa
        ok("import_ccxt", True)
    except Exception as e:
        ok("import_ccxt", False, f"{type(e).__name__}: {e}")
    try:
        import yaml  # noqa
        ok("import_pyyaml", True)
    except Exception as e:
        ok("import_pyyaml", False, f"{type(e).__name__}: {e}")
    print(json.dumps({"ok": all(c["ok"] for c in checks), "checks": checks}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
