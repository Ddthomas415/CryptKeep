from __future__ import annotations

import json
from pathlib import Path

def main() -> int:
    p = Path("data/supervisor/status.json")
    if not p.exists():
        print("No status yet. Start supervisor first.")
        return 1
    print(json.dumps(json.loads(p.read_text(encoding="utf-8")), indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
