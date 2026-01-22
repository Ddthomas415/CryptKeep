from __future__ import annotations

import subprocess
import sys

def main() -> int:
    print("[validate] running preflight...")
    r1 = subprocess.call([sys.executable, "scripts/preflight.py"])
    if r1 != 0:
        print("[validate] FAIL: preflight")
        return r1

    print("[validate] running pytest...")
    r2 = subprocess.call([sys.executable, "-m", "pytest"])
    if r2 != 0:
        print("[validate] FAIL: pytest")
        return r2

    print("[validate] OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
