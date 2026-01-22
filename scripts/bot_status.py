from __future__ import annotations
from services.runtime.process_supervisor import status

def main() -> int:
    print(status(["pipeline","executor","reconciler"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
