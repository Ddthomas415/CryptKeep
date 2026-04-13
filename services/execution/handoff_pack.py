from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from services.os.app_paths import runtime_dir, ensure_dirs
from storage.exec_metrics_sqlite import ExecMetricsSQLite
from storage.execution_report_sqlite import ExecutionReportSQLite
from storage.intent_queue_sqlite import IntentQueueSQLite
from services.os.file_utils import atomic_write


def build_handoff_pack(*, limit: int = 200) -> Dict[str, Any]:
    reports = []
    intents = []
    metrics = []
    errors: list[str] = []

    try:
        reports = ExecutionReportSQLite().recent(limit=int(limit))
    except Exception as e:
        errors.append(f"execution_reports: {type(e).__name__}: {e}")

    try:
        intents = IntentQueueSQLite().list_intents(limit=int(limit))
    except Exception as e:
        errors.append(f"intent_queue: {type(e).__name__}: {e}")

    try:
        metrics = ExecMetricsSQLite().recent(limit=int(limit))
    except Exception as e:
        errors.append(f"exec_metrics: {type(e).__name__}: {e}")

    return {
        "ok": len(errors) == 0,
        "ts": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "reports": len(reports),
            "intents": len(intents),
            "metrics": len(metrics),
        },
        "reports": reports,
        "intents": intents,
        "metrics": metrics,
        "errors": errors,
    }


def save_handoff_pack(*, path: str | Path | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_dirs()
    out = build_handoff_pack(limit=limit)
    target = Path(path) if path else (runtime_dir() / "snapshots" / "execution_handoff.latest.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(target, json.dumps(out, indent=2, sort_keys=True) + "\n")
    return {"ok": True, "path": str(target), "pack_ok": bool(out.get("ok"))}
