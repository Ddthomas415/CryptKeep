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



from services.app.diagnostics_exporter import export_zip_to_runtime

def main():
    export_zip_to_runtime()
    print({"ok": True})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
