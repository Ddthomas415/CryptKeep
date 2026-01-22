from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

APPROVAL_PATH = Path("data/learning/model_switch_approval.json")
RECO_PATH = Path("data/learning/recommended_model.json")

def _now_ms() -> int:
    return int(time.time() * 1000)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_id", required=True)
    ap.add_argument("--approved_by", default="operator")
    args = ap.parse_args()

    reco = {}
    if RECO_PATH.exists():
        try:
            reco = json.loads(RECO_PATH.read_text(encoding="utf-8"))
        except Exception:
            reco = {}

    payload = {
        "approved_ts_ms": _now_ms(),
        "approved_by": str(args.approved_by),
        "approved_model_id": str(args.model_id),
        "recommendation_snapshot": reco,
    }

    APPROVAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    APPROVAL_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print({"ok": True, "approval_path": str(APPROVAL_PATH), "approved_model_id": args.model_id})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
