from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from services.ai_copilot.incident_analyst import analyze_incident
from services.ai_copilot.policy import report_root
from services.os.app_paths import ensure_dirs, runtime_dir
from services.process.bot_runtime_truth import canonical_service_status, read_heartbeat
from services.risk.system_health import get_system_health

logger = logging.getLogger(__name__)

MONITOR_NAME = "ai_alert_monitor"
_KEYWORDS = ("traceback", "exception", "error", "failed", "critical", "networkerror")
_LOG_NAMES = (
    "pipeline.log",
    "intent_consumer.log",
    "reconciler.log",
    "executor.log",
    "ops_risk_gate.log",
    "ops_signal_adapter.log",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _flags_dir() -> Path:
    return runtime_dir() / "flags"


def _health_dir() -> Path:
    return runtime_dir() / "health"


def stop_file() -> Path:
    return _flags_dir() / f"{MONITOR_NAME}.stop"


def status_file() -> Path:
    return _health_dir() / f"{MONITOR_NAME}.json"


def pid_file() -> Path:
    return _health_dir() / f"{MONITOR_NAME}.pid.json"


def cursor_file() -> Path:
    return _flags_dir() / f"{MONITOR_NAME}.cursor.json"


def _alert_log_path() -> Path:
    return runtime_dir() / "alerts" / "critical_alerts.jsonl"


def _write_status(obj: Dict[str, Any]) -> None:
    ensure_dirs()
    _health_dir().mkdir(parents=True, exist_ok=True)
    status_file().write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_pid_state(obj: Dict[str, Any]) -> None:
    ensure_dirs()
    _health_dir().mkdir(parents=True, exist_ok=True)
    pid_file().write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_cursor(obj: Dict[str, Any]) -> None:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    cursor_file().write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")) or {})


def _clear_pid_state() -> None:
    try:
        if pid_file().exists():
            pid_file().unlink()
    except Exception as exc:
        logger.warning("ai_alert_monitor_pid_file_clear_failed", extra={"path": str(pid_file()), "error_type": type(exc).__name__})


def _process_alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def _default_cursor() -> Dict[str, Any]:
    return {
        "alert_line_count": 0,
        "log_line_counts": {},
        "service_running": {},
    }


def _load_cursor() -> Dict[str, Any]:
    if not cursor_file().exists():
        return _default_cursor()
    try:
        payload = _load_json(cursor_file())
    except Exception:
        return _default_cursor()
    out = _default_cursor()
    out["alert_line_count"] = int(payload.get("alert_line_count") or 0)
    out["log_line_counts"] = dict(payload.get("log_line_counts") or {})
    out["service_running"] = {str(k): bool(v) for k, v in dict(payload.get("service_running") or {}).items()}
    return out


def load_runtime_status() -> Dict[str, Any]:
    payload: Dict[str, Any]
    if status_file().exists():
        try:
            payload = _load_json(status_file())
        except Exception as exc:
            return {
                "ok": False,
                "has_status": False,
                "reason": f"status_read_failed:{type(exc).__name__}",
                "summary_text": "AI alert monitor status is unavailable.",
            }
    else:
        payload = {
            "ok": True,
            "has_status": False,
            "reason": "status_missing",
            "status": "not_started",
            "summary_text": "AI alert monitor has not written runtime status yet.",
        }

    pid_state: Dict[str, Any] = {}
    if pid_file().exists():
        try:
            pid_state = _load_json(pid_file())
        except Exception as exc:
            payload["pid_reason"] = f"pid_read_failed:{type(exc).__name__}"

    status_pid = int(payload.get("pid") or 0) if payload else 0
    pid = int(pid_state.get("pid") or 0) if pid_state else 0
    if status_pid > 0 and (pid <= 0 or payload.get("status") == "running"):
        pid = status_pid
    pid_alive = _process_alive(pid) if pid > 0 else False

    payload["ok"] = bool(payload.get("ok", True))
    payload["has_status"] = bool(payload.get("has_status")) if "has_status" in payload else True
    payload["pid"] = pid or None
    payload["pid_alive"] = pid_alive
    payload["has_pid_file"] = bool(pid_state)
    payload["started_ts"] = str(pid_state.get("started_ts") or "")
    payload["poll_interval_sec"] = float(pid_state.get("poll_interval_sec") or 0.0) if pid_state else float(payload.get("poll_interval_sec") or 0.0)

    if pid_state and payload.get("status") == "running" and not pid_alive:
        payload["status"] = "dead"
        payload["reason"] = "process_not_running"
        payload["last_reason"] = str(payload.get("last_reason") or payload.get("reason") or "process_not_running")
    elif pid_state and not payload.get("has_status") and pid_alive:
        payload["status"] = "starting"
        payload["reason"] = "pid_alive_waiting_for_status"
        payload["has_status"] = True

    return payload


def _read_alert_lines() -> list[str]:
    path = _alert_log_path()
    if not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []


def _new_alert_events(previous_count: int) -> tuple[list[dict[str, Any]], int]:
    lines = _read_alert_lines()
    new_lines = lines[max(0, int(previous_count)) :]
    events: list[dict[str, Any]] = []
    for raw in new_lines[-10:]:
        raw = str(raw or "").strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"level": "error", "message": raw, "payload": {}}
        events.append(
            {
                "event_type": "alert",
                "level": str(payload.get("level") or "error"),
                "message": str(payload.get("message") or ""),
                "payload": dict(payload.get("payload") or {}),
                "ts": str(payload.get("ts") or ""),
            }
        )
    return events, len(lines)


def _selected_log_paths() -> list[Path]:
    logs_dir = runtime_dir() / "logs"
    return [logs_dir / name for name in _LOG_NAMES if (logs_dir / name).exists()]


def _new_log_events(previous_counts: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    events: list[dict[str, Any]] = []
    current_counts: dict[str, int] = {}
    for path in _selected_log_paths():
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        current_counts[path.name] = len(lines)
        start = max(0, int(previous_counts.get(path.name) or 0))
        new_lines = lines[start:]
        matches = [
            line.strip()[:300]
            for line in new_lines
            if any(keyword in line.lower() for keyword in _KEYWORDS)
        ]
        if matches:
            events.append(
                {
                    "event_type": "log_match",
                    "log": path.name,
                    "match_count": len(matches),
                    "lines": matches[-8:],
                }
            )
    return events, current_counts


def _service_events(previous_running: dict[str, bool]) -> tuple[list[dict[str, Any]], dict[str, bool], dict[str, Any]]:
    services = canonical_service_status()
    current_running = {str(name): bool((row or {}).get("running")) for name, row in services.items()}
    events: list[dict[str, Any]] = []
    for name, is_running in sorted(current_running.items()):
        previous = previous_running.get(name)
        if is_running:
            continue
        if previous is False:
            continue
        row = dict(services.get(name) or {})
        events.append(
            {
                "event_type": "service_down",
                "service": name,
                "pid": row.get("pid"),
                "running": False,
            }
        )
    return events, current_running, services


def _event_severity(events: list[dict[str, Any]]) -> str:
    for event in events:
        if str(event.get("event_type") or "") == "service_down":
            return "critical"
        if str(event.get("event_type") or "") == "alert" and str(event.get("level") or "").lower() == "error":
            return "critical"
    return "warn"


def _event_summary(events: list[dict[str, Any]], runtime: dict[str, Any]) -> str:
    alert_count = sum(1 for event in events if event.get("event_type") == "alert")
    log_count = sum(1 for event in events if event.get("event_type") == "log_match")
    down_services = [str(event.get("service") or "") for event in events if event.get("event_type") == "service_down"]
    parts: list[str] = []
    if alert_count:
        parts.append(f"{alert_count} new critical alert(s)")
    if down_services:
        parts.append("service down: " + ", ".join(down_services))
    if log_count:
        parts.append(f"{log_count} runtime log error burst(s)")
    if not parts:
        stopped = list((runtime.get("stopped_services") or [])) if isinstance(runtime.get("stopped_services"), list) else []
        if stopped:
            parts.append("stopped services: " + ", ".join(str(item) for item in stopped))
    return "; ".join(parts) or "New operator-facing runtime anomaly detected."


def _event_notes(events: list[dict[str, Any]], runtime: dict[str, Any]) -> str:
    lines = [
        "AI alert monitor detected new runtime events.",
        "",
        "Current runtime summary:",
        json.dumps(
            {
                "heartbeat": read_heartbeat(),
                "system_health": get_system_health(),
                "running_services": runtime.get("running_services"),
                "stopped_services": runtime.get("stopped_services"),
            },
            indent=2,
            default=str,
        ),
        "",
        "New events:",
        json.dumps(events, indent=2, default=str),
    ]
    return "\n".join(lines)


def _fallback_analysis(*, summary: str, severity: str, events: list[dict[str, Any]], runtime: dict[str, Any], provider_error: str) -> str:
    stopped = runtime.get("stopped_services") if isinstance(runtime.get("stopped_services"), list) else []
    lines = [
        "1. **Status Summary**",
        f"Monitor detected `{severity}` runtime activity. {summary}",
        "",
        "2. **Issues Found**",
    ]
    if not events:
        lines.append("- No structured event bundle was retained; inspect current runtime health and logs directly.")
    for event in events[:8]:
        event_type = str(event.get("event_type") or "unknown")
        if event_type == "service_down":
            lines.append(f"- Service `{event.get('service')}` is down.")
        elif event_type == "alert":
            lines.append(f"- Alert `{event.get('level')}`: {event.get('message')}")
        elif event_type == "log_match":
            lines.append(f"- `{event.get('log')}` emitted {event.get('match_count')} new error-like line(s).")
    lines.extend(
        [
            "",
            "3. **Likely Cause**",
            f"Fresh alerts, stopped services, or new runtime log failures were detected. LLM analysis was unavailable (`{provider_error}`), so this report is heuristic only.",
            "",
            "4. **Recommended Actions**",
            f"1. Inspect stopped services: {', '.join(str(item) for item in stopped) or '(none shown)'}.",
            "2. Review the matching runtime logs and canonical status files for the affected services.",
            "3. Restore provider access if AI narrative analysis is required.",
        ]
    )
    return "\n".join(lines)


def render_incident_markdown(payload: dict[str, Any]) -> str:
    events = list(payload.get("events") or [])
    lines = [
        "# AI Alert Monitor Incident",
        "",
        f"- Generated: {payload.get('generated_at')}",
        f"- Severity: {payload.get('severity')}",
        f"- Summary: {payload.get('summary')}",
        f"- Analysis mode: {payload.get('analysis_mode')}",
        "",
        "## Analysis",
        "",
        str(payload.get("analysis") or "(no analysis)"),
        "",
        "## Events",
    ]
    if events:
        for event in events:
            lines.append(f"- `{event.get('event_type')}` — {json.dumps(event, ensure_ascii=False, default=str)}")
    else:
        lines.append("- (none)")
    return "\n".join(lines).strip() + "\n"


def _write_incident_report(payload: dict[str, Any], *, stem: str) -> dict[str, str]:
    root = report_root()
    json_path = root / f"{stem}.json"
    markdown_path = root / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_incident_markdown(payload), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(markdown_path)}


def list_recent_incidents(*, limit: int = 10) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for json_path in report_root().glob("*.json"):
        try:
            payload = _load_json(json_path)
        except Exception:
            continue
        if str(payload.get("monitor_name") or "") != MONITOR_NAME:
            continue
        rows.append(
            {
                "stem": json_path.stem,
                "generated_at": str(payload.get("generated_at") or ""),
                "severity": str(payload.get("severity") or "unknown"),
                "summary": str(payload.get("summary") or "").strip(),
                "event_count": int(len(list(payload.get("events") or []))),
                "json_path": str(json_path),
                "payload": payload,
            }
        )
    rows.sort(key=lambda item: (str(item.get("generated_at") or ""), str(item.get("stem") or "")), reverse=True)
    return rows[: max(1, int(limit))]


def process_once() -> Dict[str, Any]:
    ensure_dirs()
    current_status = load_runtime_status()
    cursor = _load_cursor()
    alert_events, alert_count = _new_alert_events(int(cursor.get("alert_line_count") or 0))
    log_events, log_counts = _new_log_events(dict(cursor.get("log_line_counts") or {}))
    service_events, service_running, services = _service_events(dict(cursor.get("service_running") or {}))
    runtime = {
        "canonical_services": services,
        "running_services": sorted(name for name, row in services.items() if bool((row or {}).get("running"))),
        "stopped_services": sorted(name for name, row in services.items() if not bool((row or {}).get("running"))),
    }
    events = [*alert_events, *service_events, *log_events]
    next_cursor = {
        "alert_line_count": int(alert_count),
        "log_line_counts": {str(k): int(v) for k, v in log_counts.items()},
        "service_running": {str(k): bool(v) for k, v in service_running.items()},
    }
    _write_cursor(next_cursor)

    if not events:
        out = {
            "ok": True,
            "status": "idle",
            "reason": "no_new_events",
            "ts": _now_iso(),
            "last_report_stem": str(current_status.get("last_report_stem") or ""),
            "incidents_written": int(current_status.get("incidents_written") or 0),
        }
        _write_status({**dict(current_status), **out})
        return out

    severity = _event_severity(events)
    summary = _event_summary(events, runtime)
    notes = _event_notes(events, runtime)
    analysis_result = analyze_incident(
        question="Summarize the new alert-worthy runtime events and the safest next operator actions.",
        extra_notes=notes,
    )
    if bool(analysis_result.get("ok")):
        analysis = str(analysis_result.get("analysis") or "").strip() or summary
        analysis_mode = "llm"
        warning = None
    else:
        warning = str(analysis_result.get("error") or "copilot_unavailable")
        analysis = _fallback_analysis(summary=summary, severity=severity, events=events, runtime=runtime, provider_error=warning)
        analysis_mode = "heuristic_fallback"

    stem = f"{MONITOR_NAME}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    payload = {
        "generated_at": _now_iso(),
        "monitor_name": MONITOR_NAME,
        "severity": severity,
        "summary": summary,
        "analysis_mode": analysis_mode,
        "analysis": analysis,
        "warning": warning,
        "provider": analysis_result.get("provider"),
        "model": analysis_result.get("model"),
        "context_chars": int(analysis_result.get("context_chars") or 0),
        "events": events,
        "runtime": runtime,
    }
    paths = _write_incident_report(payload, stem=stem)
    incidents_written = int(current_status.get("incidents_written") or 0) + 1
    _write_status(
        {
            "ok": True,
            "has_status": True,
            "status": "running",
            "ts": _now_iso(),
            "last_reason": "incident_written",
            "last_report_stem": stem,
            "last_severity": severity,
            "last_summary": summary,
            "last_event_count": len(events),
            "incidents_written": incidents_written,
            "alert_line_count": alert_count,
            "provider": analysis_result.get("provider"),
            "model": analysis_result.get("model"),
            "json_path": paths["json_path"],
            "markdown_path": paths["markdown_path"],
            "pid": os.getpid(),
        }
    )
    return {"ok": True, "status": "incident_written", "severity": severity, "summary": summary, "report_stem": stem, "event_count": len(events)}


def run_forever(*, poll_interval_sec: float = 30.0, max_loops: int | None = None) -> Dict[str, Any]:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    current_pid = int(os.getpid())
    existing = load_runtime_status()
    if bool(existing.get("pid_alive")) and int(existing.get("pid") or 0) not in {0, current_pid}:
        return {
            "ok": True,
            "status": "running",
            "reason": "already_running",
            "pid": int(existing.get("pid") or 0),
            "poll_interval_sec": float(existing.get("poll_interval_sec") or poll_interval_sec),
        }
    try:
        if stop_file().exists():
            stop_file().unlink()
    except Exception as exc:
        logger.warning("ai_alert_monitor_stop_file_clear_failed", extra={"path": str(stop_file()), "error_type": type(exc).__name__})

    _write_pid_state({"pid": current_pid, "started_ts": _now_iso(), "poll_interval_sec": float(poll_interval_sec)})

    loops = 0
    incidents_written = int(existing.get("incidents_written") or 0)
    errors = 0
    last_result: Dict[str, Any] = {}
    _write_status(
        {
            "ok": True,
            "has_status": True,
            "status": "running",
            "ts": _now_iso(),
            "loops": 0,
            "errors": 0,
            "incidents_written": incidents_written,
            "pid": current_pid,
            "poll_interval_sec": float(poll_interval_sec),
        }
    )

    while True:
        loops += 1
        if stop_file().exists():
            out = {
                "ok": True,
                "status": "stopped",
                "reason": "stop_requested",
                "ts": _now_iso(),
                "loops": loops,
                "errors": errors,
                "incidents_written": incidents_written,
                "last_result": last_result,
                "pid": current_pid,
                "poll_interval_sec": float(poll_interval_sec),
            }
            _write_status(out)
            _clear_pid_state()
            return out

        try:
            last_result = process_once()
            if str(last_result.get("status") or "") == "incident_written":
                incidents_written += 1
        except Exception as exc:
            errors += 1
            last_result = {
                "ok": False,
                "status": "error",
                "reason": f"monitor_loop_failed:{type(exc).__name__}",
                "error": str(exc),
            }
            logger.exception("ai_alert_monitor_loop_failed")
            _write_status(
                {
                    "ok": True,
                    "has_status": True,
                    "status": "running",
                    "ts": _now_iso(),
                    "loops": loops,
                    "errors": errors,
                    "incidents_written": incidents_written,
                    "last_reason": str(last_result.get("reason") or ""),
                    "last_result": last_result,
                    "pid": current_pid,
                    "poll_interval_sec": float(poll_interval_sec),
                }
            )

        if max_loops is not None and loops >= int(max_loops):
            out = {
                "ok": True,
                "status": "stopped",
                "reason": "max_loops",
                "ts": _now_iso(),
                "loops": loops,
                "errors": errors,
                "incidents_written": incidents_written,
                "last_result": last_result,
                "pid": current_pid,
                "poll_interval_sec": float(poll_interval_sec),
            }
            _write_status(out)
            _clear_pid_state()
            return out

        time.sleep(max(2.0, float(poll_interval_sec)))


def request_stop() -> Dict[str, Any]:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    stop_file().write_text(_now_iso() + "\n", encoding="utf-8")
    runtime = load_runtime_status()
    return {
        "ok": True,
        "status": str(runtime.get("status") or "unknown"),
        "pid": runtime.get("pid"),
        "stop_file": str(stop_file()),
    }
