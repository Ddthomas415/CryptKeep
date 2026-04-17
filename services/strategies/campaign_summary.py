"""services/strategies/campaign_summary.py

Campaign summary reporting — truthful reporting of evidence state.

Separated from paper_strategy_evidence_service.py so the reporting layer
is independently testable and does not require running a full campaign.

Called by: scripts/run_es_daily_trend_paper.py (summary output)
           scripts/check_promotion_gates.py (evidence state check)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir
from services.logging.app_logger import get_logger

_LOG = get_logger("strategies.campaign_summary")


def evidence_dir(strategy_id: str) -> Path:
    """Return the JSONL evidence directory for a strategy."""
    return data_dir() / "evidence" / strategy_id


def evidence_summary(strategy_id: str) -> dict[str, Any]:
    """Return counts of evidence records by type for a strategy.

    Reads the JSONL evidence directory — NOT the old leaderboard artifact.
    Returns:
        {
            "strategy_id": str,
            "ev_dir": str,
            "exists": bool,
            "files_by_type": {"signal": 2, "session": 1, ...},
            "total_records": int,
        }
    """
    ev_dir = evidence_dir(strategy_id)
    if not ev_dir.exists():
        return {
            "strategy_id": strategy_id,
            "ev_dir": str(ev_dir),
            "exists": False,
            "files_by_type": {},
            "total_records": 0,
        }

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


def print_campaign_summary(
    strategy_id: str,
    result: dict[str, Any],
    *,
    verbose: bool = False,
) -> None:
    """Print a truthful campaign summary to stdout.

    Reports the JSONL evidence directory directly, not the leaderboard artifact.
    """
    status = result.get("status", "unknown")
    reason = result.get("reason", "")
    completed = result.get("completed_strategies", 0)

    print(f"\nCampaign: {status} ({reason})")
    print(f"Completed strategies: {completed}")

    # Report actual JSONL evidence directory.
    # Prefer the pre-computed summary from run_campaign() result if available,
    # otherwise read it directly from disk.
    summary = result.get("jsonl_evidence") or evidence_summary(strategy_id)
    if summary["exists"]:
        print(f"Evidence dir: {summary['ev_dir']}")
        if summary["files_by_type"]:
            type_str = ", ".join(
                f"{k}: {v} file(s)" for k, v in sorted(summary["files_by_type"].items())
            )
            print(f"Evidence files: {type_str}")
            print(f"Total records: {summary['total_records']}")
        else:
            print("Evidence files: directory exists but no .jsonl files yet")
    else:
        print(f"Evidence dir: not yet created ({summary['ev_dir']})")

    # Teardown status if provided
    if "teardown" in result:
        td = result["teardown"]
        if td.get("clean"):
            print("Teardown: clean — all child processes stopped")
        else:
            still_alive = td.get("still_alive", [])
            print(f"Teardown: {still_alive} still running — run 'make paper-stop'")

    # Legacy leaderboard artifact (informational only)
    if verbose:
        ev = result.get("evidence") or {}
        if ev.get("latest_path"):
            print(f"Leaderboard artifact (legacy): {ev['latest_path']}")
        dr = result.get("decision_record") or {}
        if dr.get("path"):
            print(f"Decision record: {dr['path']}")
