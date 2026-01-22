from __future__ import annotations

import json
from pathlib import Path
import time

import yaml

from storage.ops_event_store_sqlite import OpsEventStore

RECO_PATH = Path("data/learning/recommended_model.json")
APPROVAL_PATH = Path("data/learning/model_switch_approval.json")

def _now_ms() -> int:
    return int(time.time() * 1000)

def main() -> int:
    cfg_p = Path("config/trading.yaml")
    cfg = yaml.safe_load(cfg_p.read_text(encoding="utf-8")) if cfg_p.exists() else {}
    cfg = cfg or {}
    learn = cfg.get("learning") or {}

    exec_db = str((cfg.get("execution") or {}).get("db_path") or "data/execution.sqlite")
    ops = OpsEventStore(exec_db=exec_db)

    if not RECO_PATH.exists():
        print({"ok": False, "note": "no_recommendation_file", "path": str(RECO_PATH)})
        return 2
    if not APPROVAL_PATH.exists():
        print({"ok": False, "note": "no_approval_file", "path": str(APPROVAL_PATH)})
        return 3

    reco = json.loads(RECO_PATH.read_text(encoding="utf-8"))
    appr = json.loads(APPROVAL_PATH.read_text(encoding="utf-8"))

    if reco.get("note") != "switch_recommended":
        print({"ok": True, "note": "no_switch_recommended_now", "recommendation_note": reco.get("note")})
        return 0

    best = (reco.get("best") or {})
    recommended_id = best.get("model_id")
    approved_id = appr.get("approved_model_id")

    if not recommended_id or not approved_id:
        print({"ok": False, "note": "missing_model_id_in_files"})
        return 4

    if str(recommended_id) != str(approved_id):
        print({"ok": False, "note": "approval_does_not_match_recommendation", "recommended": recommended_id, "approved": approved_id})
        return 5

    current_id = (learn.get("active_model_id") or "").strip() or None
    learn["active_model_id"] = str(recommended_id)
    cfg["learning"] = learn
    cfg_p.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    ops.add(
        severity="INFO",
        event_type="model_switch_applied",
        message="Applied approved model switch (paper gate)",
        meta={"from": current_id, "to": str(recommended_id), "approved_by": appr.get("approved_by"), "approved_ts_ms": appr.get("approved_ts_ms")},
        ts_ms=_now_ms(),
    )

    print({"ok": True, "note": "switched", "from": current_id, "to": str(recommended_id)})

    # Consume approval so it can't be reused accidentally
    try:
        APPROVAL_PATH.unlink()
    except Exception:
        pass

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
