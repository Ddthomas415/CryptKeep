from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import argparse
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.desktop.logging_control import rotate_logs

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-bytes", type=int, default=5_000_000)
    ap.add_argument("--max-keep", type=int, default=5)
    args = ap.parse_args()

    out = rotate_logs(max_bytes=int(args.max_bytes), max_keep=int(args.max_keep))
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
