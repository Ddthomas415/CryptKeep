from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from services.ai_copilot.policy import report_root


def _parse_iso(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def _classify_report(payload: dict[str, Any]) -> str:
    if "risk_tier" in payload and "changed_files" in payload:
        return "repo_review"
    if "runtime" in payload and "place_order_contract" in payload:
        return "safety_audit"
    if "checks" in payload and "issues" in payload:
        return "drift_audit"
    if "job" in payload and "command" in payload:
        return "simulation"
    if "selected_strategy" in payload and "top_rows" in payload:
        return "strategy_lab"
    return "unknown"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return {
            "ok": False,
            "severity": "warn",
            "summary": f"failed_to_parse_json:{type(exc).__name__}",
            "generated_at": "",
        }
    return dict(payload) if isinstance(payload, dict) else {}


def list_copilot_reports(*, limit: int = 25) -> list[dict[str, Any]]:
    root = report_root()
    rows: list[dict[str, Any]] = []
    for json_path in root.glob("*.json"):
        payload = _read_json(json_path)
        markdown_path = json_path.with_suffix(".md")
        generated_at = str(payload.get("generated_at") or "")
        rows.append(
            {
                "stem": json_path.stem,
                "kind": _classify_report(payload),
                "generated_at": generated_at,
                "generated_dt": _parse_iso(generated_at),
                "severity": str(payload.get("severity") or payload.get("risk_tier") or "unknown"),
                "summary": str(payload.get("summary") or "").strip(),
                "json_path": str(json_path),
                "markdown_path": str(markdown_path) if markdown_path.exists() else "",
                "payload": payload,
            }
        )
    rows.sort(
        key=lambda item: (
            item.get("generated_dt") or datetime.min,
            str(item.get("stem") or ""),
        ),
        reverse=True,
    )
    return rows[: max(1, int(limit))]


def load_copilot_report_bundle(stem: str) -> dict[str, Any]:
    safe_stem = str(stem or "").strip()
    path = report_root() / f"{safe_stem}.json"
    payload = _read_json(path) if path.exists() else {}
    markdown_path = path.with_suffix(".md")
    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    return {
        "stem": safe_stem,
        "kind": _classify_report(payload) if payload else "unknown",
        "json_path": str(path),
        "markdown_path": str(markdown_path) if markdown_path.exists() else "",
        "payload": payload,
        "markdown": markdown,
    }


def summarize_copilot_reports(*, limit: int = 50) -> dict[str, Any]:
    rows = list_copilot_reports(limit=limit)
    kind_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    for row in rows:
        kind = str(row.get("kind") or "unknown")
        severity = str(row.get("severity") or "unknown")
        kind_counts[kind] = int(kind_counts.get(kind, 0)) + 1
        severity_counts[severity] = int(severity_counts.get(severity, 0)) + 1
    latest = rows[0] if rows else {}
    return {
        "report_count": int(len(rows)),
        "kind_counts": kind_counts,
        "severity_counts": severity_counts,
        "latest_stem": str(latest.get("stem") or ""),
        "latest_kind": str(latest.get("kind") or ""),
        "latest_generated_at": str(latest.get("generated_at") or ""),
    }


def build_copilot_report_focus(*, kind: str, severity: str, payload: dict[str, Any]) -> dict[str, Any]:
    kind_text = str(kind or "unknown").replace("_", " ").title()
    severity_text = str(severity or "unknown").strip().lower()
    summary = str((payload or {}).get("summary") or "No summary recorded.").strip()

    tone = "info"
    title = f"{kind_text} report"
    message = summary
    details: dict[str, Any] = {}

    if severity_text == "critical":
        tone = "error"
        title = f"{kind_text} needs immediate operator review"
    elif severity_text == "warn":
        tone = "warning"
        title = f"{kind_text} needs operator attention"
    elif severity_text == "ok":
        tone = "success"

    if str(kind or "") == "strategy_lab":
        runtime = dict((payload or {}).get("collector_runtime") or {})
        research_acceptance = dict((payload or {}).get("research_acceptance") or {})
        details = {
            "status": str(runtime.get("status") or "unknown"),
            "completed_strategies": int(runtime.get("completed_strategies") or 0),
            "total_strategies": int(runtime.get("total_strategies") or 0),
            "summary_text": str(runtime.get("summary_text") or ""),
            "research_acceptance_status": str(research_acceptance.get("status") or "unknown"),
            "research_acceptance_summary": str(research_acceptance.get("summary") or ""),
            "research_acceptance_accepted": bool(research_acceptance.get("accepted")),
            "research_acceptance_blockers": [
                str(item).strip()
                for item in list(research_acceptance.get("blockers") or [])
                if str(item).strip()
            ],
        }
        if severity_text in {"warn", "critical"} and details["summary_text"]:
            message = f"{summary} {details['summary_text']}".strip()

    return {
        "tone": tone,
        "title": title,
        "message": message,
        "details": details,
    }
