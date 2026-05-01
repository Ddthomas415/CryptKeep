#!/usr/bin/env python3
"""
Print current system health as JSON.

Exit codes:
  0 — HEALTHY
  1 — DEGRADED or HALTED
  2 — checker error
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    try:
        from services.risk.system_health import get_system_health

        health = get_system_health()
        print(json.dumps(health, indent=2, sort_keys=True))
        state = str(health.get("state") or "UNKNOWN")
        return 0 if state == "HEALTHY" else 1
    except Exception as err:
        print(
            json.dumps(
                {"state": "ERROR", "reasons": [f"{type(err).__name__}:{err}"]},
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
