from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import yaml

def main() -> int:
    cfg = yaml.safe_load(open("config/app.yaml","r",encoding="utf-8").read()) or {}
    v = (((cfg.get("app") or {}).get("version")) or "0.0.0")
    print(str(v))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
