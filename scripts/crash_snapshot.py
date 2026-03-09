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
from services.process.crash_snapshot import read_crash_snapshot

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    if args.show:
        print(read_crash_snapshot())
        return
    print("Use: python scripts/crash_snapshot.py --show")

if __name__ == "__main__":
    main()
