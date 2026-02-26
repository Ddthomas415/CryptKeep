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
from services.os.app_paths import data_dir

def main() -> int:
    p = data_dir() / "supervisor" / "status.json"
    if not p.exists():
        print("No status yet. Start supervisor first.")
        return 1
    print(json.dumps(json.loads(p.read_text(encoding="utf-8")), indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
