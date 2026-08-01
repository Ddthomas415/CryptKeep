from __future__ import annotations

from pathlib import Path
from typing import Any

from services.events.platform_event_integrity import check_platform_event_integrity
from services.events.platform_event_journal import summarize_platform_events
from services.events.platform_event_secret_scan import scan_platform_event_journal


def build_platform_event_packet_report(
    path: Path | None = None,
    *,
    require_events: bool = False,
) -> dict[str, Any]:
    summary = summarize_platform_events(path, require_events=require_events)
    integrity = check_platform_event_integrity(path, require_events=require_events)
    secrets = scan_platform_event_journal(path, require_events=require_events)
    source_path = str(path) if path is not None else str(summary.get("path") or integrity.get("path") or secrets.get("path") or "")

    checks = {
        "summary": bool(summary.get("ok")),
        "integrity": bool(integrity.get("ok")),
        "secrets": bool(secrets.get("ok")),
    }
    reasons = {
        name: report.get("reason") or (
            "ok" if checks[name] else f"{name}_check_failed"
        )
        for name, report in (
            ("summary", summary),
            ("integrity", integrity),
            ("secrets", secrets),
        )
    }
    return {
        "ok": all(checks.values()),
        "path": source_path,
        "require_events": bool(require_events),
        "checks": checks,
        "reasons": reasons,
        "event_count": int(summary.get("event_count") or integrity.get("event_count") or secrets.get("event_count") or 0),
        "summary": summary,
        "integrity": integrity,
        "secrets": secrets,
    }

