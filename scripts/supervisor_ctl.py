from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


import argparse
from pathlib import Path

from services.process.supervisor_process import status, stop

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "stop"])
    ap.add_argument("--hard", action="store_true")
    args = ap.parse_args()

    if args.cmd == "status":
        print(status()); return
    if args.cmd == "stop":
        print(stop(hard=bool(args.hard))); return

if __name__ == "__main__":
    main()
