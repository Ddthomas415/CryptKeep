from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from cbp_desktop.logging_control import rotate_logs

def main() -> int:
    out = rotate_logs()
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
