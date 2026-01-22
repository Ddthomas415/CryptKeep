from __future__ import annotations

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
