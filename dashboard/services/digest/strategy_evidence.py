from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dashboard.services.digest.utils import age_seconds as _age_seconds
from services.os.app_paths import data_dir, ensure_dirs


def latest_strategy_evidence_path() -> Path:
    ensure_dirs()
    return data_dir() / "strategy_evidence" / "strategy_evidence.latest.json"


def _freshness_for_strategy_evidence(age_s: int | None) -> str:
    if age_s is None:
        return "missing"
    if age_s < 24 * 3600:
        return "fresh"
    if age_s < 7 * 24 * 3600:
        return "aging"
    return "stale"


def _missing_payload(path: Path, *, reason: str, caveat: str) -> dict[str, Any]:
    return {
        "ok": False,
        "has_artifact": False,
        "artifact_path": str(path),
        "reason": reason,
        "as_of": None,
        "age_seconds": None,
        "freshness_status": "missing",
        "source": "missing",
        "source_label": "Synthetic Fallback",
        "caveat": caveat,
        "rows": [],
        "decisions": [],
        "window_count": 0,
        "candidate_count": 0,
    }


def load_latest_strategy_evidence(path: str = "") -> dict[str, Any]:
    artifact_path = Path(path).expanduser().resolve() if path else latest_strategy_evidence_path().resolve()
    if not artifact_path.exists():
        return _missing_payload(
            artifact_path,
            reason="artifact_missing",
            caveat="Persisted strategy evidence artifact is missing; digest must use labeled synthetic fallback.",
        )

    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return _missing_payload(
            artifact_path,
            reason=f"artifact_read_failed:{type(exc).__name__}",
            caveat=f"Persisted strategy evidence artifact could not be read ({type(exc).__name__}); digest must use labeled synthetic fallback.",
        )

    if not isinstance(payload, dict):
        return _missing_payload(
            artifact_path,
            reason="artifact_not_dict",
            caveat="Persisted strategy evidence artifact is invalid; digest must use labeled synthetic fallback.",
        )

    aggregate = payload.get("aggregate_leaderboard") if isinstance(payload.get("aggregate_leaderboard"), dict) else {}
    rows = [dict(row) for row in list(aggregate.get("rows") or []) if isinstance(row, dict)]
    decisions = [dict(item) for item in list(payload.get("decisions") or []) if isinstance(item, dict)]
    comparison = dict(payload.get("comparison") or {}) if isinstance(payload.get("comparison"), dict) else {}
    as_of = str(payload.get("as_of") or "").strip() or None
    age_s = _age_seconds(as_of)
    freshness_status = _freshness_for_strategy_evidence(age_s)
    source = str(payload.get("source") or "unknown").strip().lower() or "unknown"
    source_label = "Persisted Synthetic Evidence" if source == "multi_window_synthetic" else source.replace("_", " ").title()
    caveat = (
        "Persisted synthetic multi-window strategy evidence artifact. Stronger than on-demand fallback, but still not market-history proof."
        if source == "multi_window_synthetic"
        else "Persisted strategy evidence artifact."
    )

    return {
        "ok": True,
        "has_artifact": True,
        "artifact_path": str(artifact_path),
        "reason": "artifact_loaded",
        "as_of": as_of,
        "age_seconds": age_s,
        "freshness_status": freshness_status,
        "source": source,
        "source_label": source_label,
        "caveat": caveat,
        "rows": rows,
        "decisions": decisions,
        "comparison": comparison,
        "window_count": int(payload.get("window_count") or 0),
        "candidate_count": int(aggregate.get("candidate_count") or len(rows)),
    }
