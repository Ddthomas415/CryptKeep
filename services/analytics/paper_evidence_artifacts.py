"""services/analytics/paper_evidence_artifacts.py

Evidence artifact path resolution — extracted from paper_strategy_evidence_service.py.

Owns: finding and refreshing evidence artifact paths (leaderboard + JSONL).
Does NOT own: campaign execution, process lifecycle, or evidence writing.

Called by: paper_strategy_evidence_service.run_campaign()
           scripts/check_promotion_gates.py
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir, code_root, state_root
from services.logging.app_logger import get_logger

_LOG = get_logger("analytics.paper_evidence_artifacts")


def _path_mtime(path: Path) -> float:
    try:
        return float(path.stat().st_mtime)
    except Exception:
        return 0.0


def latest_leaderboard_artifact(strategy_id: str | None = None) -> dict[str, Any]:
    """Return the leaderboard-style evidence artifact paths.

    This is the LEGACY evidence system. It is populated only when fills exist.
    For the canonical evidence system, use jsonl_evidence_summary() instead.
    See docs/EVIDENCE_MODEL.md.
    """
    root = (data_dir() / "strategy_evidence").resolve()
    latest_path = (root / "strategy_evidence.latest.json").resolve()
    history_paths = sorted(
        path.resolve()
        for path in root.glob("strategy_evidence.*.json")
        if path.name != "strategy_evidence.latest.json"
    )
    out: dict[str, Any] = {}
    if latest_path.exists():
        out["ok"] = True
        out["latest_path"] = str(latest_path)
        out["source"] = "leaderboard_legacy"
    if history_paths:
        out["history_path"] = str(history_paths[-1])
    return out


def decision_record_dir(*, create: bool = False) -> Path:
    """Return the canonical decision-record directory for the active state root.

    Normal repo-state runs continue to publish tracked records under docs/strategies.
    Isolated CBP_STATE_DIR runs keep records under the selected state root so proof
    runs do not dirty the repo worktree.
    """
    repo_state = (code_root() / ".cbp_state").resolve()
    active_state = state_root().resolve()
    if active_state == repo_state:
        root = (code_root() / "docs" / "strategies").resolve()
    else:
        root = (data_dir() / "strategy_evidence").resolve()
    if create:
        root.mkdir(parents=True, exist_ok=True)
    return root


def default_decision_record_path(*, report: dict[str, Any] | None = None) -> Path:
    payload = dict(report or {})
    as_of = str(payload.get("as_of") or datetime.now(timezone.utc).isoformat())
    date_token = as_of.split("T", 1)[0]
    return (decision_record_dir(create=True) / f"decision_record_{date_token}.md").resolve()


def latest_decision_record() -> dict[str, Any]:
    """Return the most recent decision record artifact."""
    root = decision_record_dir()
    records = sorted(path.resolve() for path in root.glob("decision_record_*.md"))
    if not records:
        return {}
    return {"ok": True, "path": str(records[-1])}


def jsonl_evidence_summary(strategy_id: str) -> dict[str, Any]:
    """Return a summary of JSONL evidence files for a strategy.

    This is the CANONICAL evidence system. See docs/EVIDENCE_MODEL.md.
    """
    ev_dir = (data_dir() / "evidence" / strategy_id).resolve()
    if not ev_dir.exists():
        return {"strategy_id": strategy_id, "ev_dir": str(ev_dir), "exists": False,
                "files_by_type": {}, "total_records": 0}

    files_by_type: dict[str, int] = {}
    total_records = 0
    for f in sorted(ev_dir.glob("*.jsonl")):
        record_type = f.name.split("_")[0]
        files_by_type[record_type] = files_by_type.get(record_type, 0) + 1
        try:
            lines = [l for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
            total_records += len(lines)
        except Exception as _err:
            _LOG.debug("could not count records in %s: %s", f.name, _err)

    return {
        "strategy_id": strategy_id,
        "ev_dir": str(ev_dir),
        "exists": True,
        "files_by_type": files_by_type,
        "total_records": total_records,
    }
