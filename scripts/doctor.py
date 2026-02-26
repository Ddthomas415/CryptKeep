#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import json
from services.os import app_paths

def main() -> int:
    checks = []
    def ok(name, value=True, details=None):
        checks.append({"name": name, "ok": bool(value), "details": details})
    ok("repo_root_exists", ROOT.exists(), str(ROOT))
    ok("dashboard_app_exists", (ROOT/"dashboard"/"app.py").exists())
    ok("user_yaml_exists", (app_paths.config_dir()/"user.yaml").exists())
    ok("data_dir_exists", app_paths.data_dir().exists())
    ok("runtime_snapshots_dir_exists", (app_paths.runtime_dir()/"snapshots").exists())
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
