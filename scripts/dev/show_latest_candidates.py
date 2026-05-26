from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.signals.candidate_store import load_latest_candidates


def main() -> None:
    rows = load_latest_candidates()
    print(f"count: {len(rows)}")
    for r in rows:
        print({
            "symbol": r.get("symbol"),
            "composite_score": r.get("composite_score"),
            "trade_type": r.get("trade_type"),
            "preferred_strategy": r.get("preferred_strategy"),
            "mapping_reason": r.get("mapping_reason"),
        })


if __name__ == "__main__":
    main()
