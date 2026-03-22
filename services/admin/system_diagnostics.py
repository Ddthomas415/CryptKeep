from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.admin.health import list_health
from services.app.dashboard_diagnostics import run_dashboard_diagnostics
from services.app.diagnostics_exporter import export_zip_to_runtime
from services.app.preflight_wizard import run_preflight as run_app_preflight
from services.app.system_health import collect_process_files
from services.os.app_paths import data_dir, ensure_dirs, runtime_dir

REPO_ROOT = Path(__file__).resolve().parents[2]


def _repo_relative_str(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return raw
    try:
        path = Path(raw).expanduser().resolve()
        return str(path.relative_to(REPO_ROOT))
    except Exception:
        return raw


def _runtime_relative_str(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return raw
    try:
        path = Path(raw).expanduser().resolve()
        return str(path.relative_to(runtime_dir()))
    except Exception:
        return _repo_relative_str(raw)


def _normalize_detail_text(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return raw
    prefix = "db_path="
    if raw.startswith(prefix):
        return prefix + _repo_relative_str(raw[len(prefix):])
    return raw
from services.preflight.preflight import run_preflight as run_core_preflight

RUNNING_STATUSES = {"RUNNING", "OK", "HEALTHY", "STARTING"}
ATTENTION_STATUSES = {"ERROR", "FAILED", "UNHEALTHY", "DEGRADED", "STOPPED"}
REPAIRABLE_ACTIONS = {"remove_stale_lock", "remove_stale_pid_file", "remove_stale_stop_file"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _age_seconds(ts: Any) -> int | None:
    raw = str(ts or "").strip()
    if not raw:
        return None
    try:
        normalized = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()))
    except Exception:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _pid_alive(pid: int | None) -> bool:
    try:
        value = int(pid or 0)
    except Exception:
        return False
    if value <= 0:
        return False
    try:
        os.kill(value, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def _safe_remove_file(path: Path) -> bool:
    root = runtime_dir().resolve()
    try:
        resolved = path.resolve()
    except Exception:
        return False
    if root not in resolved.parents:
        return False
    if not resolved.exists() or not resolved.is_file():
        return False
    try:
        resolved.unlink()
        return True
    except Exception:
        return False


def _artifact_summary() -> dict[str, Any]:
    evidence_dir = data_dir() / "strategy_evidence"
    latest_path = evidence_dir / "strategy_evidence.latest.json"
    trade_journal = data_dir() / "trade_journal.sqlite"
    decision_dir = Path(__file__).resolve().parents[2] / "docs" / "strategies"
    decision_records = sorted(decision_dir.glob("decision_record_*.md"))
    latest_record = decision_records[-1] if decision_records else None
    return {
        "strategy_evidence_latest": {
            "path": _repo_relative_str(latest_path),
            "exists": latest_path.exists(),
            "age_seconds": _age_seconds(datetime.fromtimestamp(latest_path.stat().st_mtime, tz=timezone.utc).isoformat()) if latest_path.exists() else None,
        },
        "trade_journal": {
            "path": _repo_relative_str(trade_journal),
            "exists": trade_journal.exists(),
            "age_seconds": _age_seconds(datetime.fromtimestamp(trade_journal.stat().st_mtime, tz=timezone.utc).isoformat()) if trade_journal.exists() else None,
        },
        "decision_record_latest": {
            "path": _repo_relative_str(latest_record) if latest_record else "",
            "exists": bool(latest_record and latest_record.exists()),
            "age_seconds": (
                _age_seconds(datetime.fromtimestamp(latest_record.stat().st_mtime, tz=timezone.utc).isoformat())
                if latest_record and latest_record.exists()
                else None
            ),
        },
    }


def _load_managed_runtime(loader) -> dict[str, Any]:
    try:
        payload = dict(loader() or {})
    except Exception as exc:
        return {"ok": False, "reason": f"runtime_load_failed:{type(exc).__name__}"}
    payload["age_seconds"] = _age_seconds(payload.get("ts") or payload.get("started_ts"))
    return payload


def _latest_health_rows() -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in list_health():
        if not isinstance(row, dict):
            continue
        service = str(row.get("service") or "").strip()
        if not service:
            continue
        current_ts = str(row.get("ts") or "")
        previous = latest.get(service) or {}
        if current_ts >= str(previous.get("ts") or ""):
            latest[service] = row
    return [latest[name] for name in sorted(latest)]


def _lock_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((runtime_dir() / "locks").glob("*")):
        if not path.is_file():
            continue
        row: dict[str, Any] = {
            "path": _runtime_relative_str(path),
            "name": path.name,
            "service": path.stem,
            "repairable": False,
            "repair_action": "",
        }
        try:
            payload = _read_json(path)
            pid = int(payload.get("pid") or 0)
            row["pid"] = pid or None
            row["ts"] = str(payload.get("ts") or "")
            row["pid_alive"] = _pid_alive(pid)
            if not row["pid_alive"]:
                row["repairable"] = True
                row["repair_action"] = "remove_stale_lock"
                row["reason"] = "pid_not_running"
        except Exception as exc:
            row["pid"] = None
            row["pid_alive"] = False
            row["repairable"] = True
            row["repair_action"] = "remove_stale_lock"
            row["reason"] = f"lock_parse_failed:{type(exc).__name__}"
        rows.append(row)
    return rows


def _pid_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((runtime_dir() / "pids").glob("*.pid")):
        if not path.is_file():
            continue
        raw = ""
        pid: int | None = None
        try:
            raw = path.read_text(encoding="utf-8").strip()
            pid = int(raw)
        except Exception:
            pid = None
        alive = _pid_alive(pid)
        rows.append(
            {
                "path": _runtime_relative_str(path),
                "name": path.name,
                "service": path.stem,
                "pid": pid,
                "pid_alive": alive,
                "repairable": not alive,
                "repair_action": "remove_stale_pid_file" if not alive else "",
                "reason": "pid_not_running" if pid and not alive else ("invalid_pid_file" if pid is None else ""),
            }
        )
    return rows


def _related_process_alive(service_name: str) -> bool:
    lock_path = runtime_dir() / "locks" / f"{service_name}.lock"
    if lock_path.exists():
        try:
            if _pid_alive(int((_read_json(lock_path)).get("pid") or 0)):
                return True
        except Exception:
            pass
    pid_path = runtime_dir() / "pids" / f"{service_name}.pid"
    if pid_path.exists():
        try:
            if _pid_alive(int(pid_path.read_text(encoding="utf-8").strip())):
                return True
        except Exception:
            pass
    managed_pid = runtime_dir() / "health" / f"{service_name}.pid.json"
    if managed_pid.exists():
        try:
            if _pid_alive(int((_read_json(managed_pid)).get("pid") or 0)):
                return True
        except Exception:
            pass
    return False


def _stop_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((runtime_dir() / "flags").glob("*.stop")):
        if not path.is_file():
            continue
        service = path.stem
        alive = _related_process_alive(service)
        rows.append(
            {
                "path": _runtime_relative_str(path),
                "name": path.name,
                "service": service,
                "pid_alive": alive,
                "repairable": not alive,
                "repair_action": "remove_stale_stop_file" if not alive else "",
                "reason": "stop_file_without_live_process" if not alive else "",
            }
        )
    return rows


def _issue(
    *,
    issue_id: str,
    severity: str,
    category: str,
    title: str,
    summary: str,
    repairable: bool = False,
    repair_action: str = "",
    path: str = "",
    service: str = "",
) -> dict[str, Any]:
    return {
        "id": issue_id,
        "severity": severity,
        "category": category,
        "title": title,
        "summary": summary,
        "repairable": repairable,
        "repair_action": repair_action,
        "path": path,
        "service": service,
    }


def _repair_plan_from_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    plan: list[dict[str, Any]] = []
    for item in issues:
        action = str(item.get("repair_action") or "")
        path = str(item.get("path") or "")
        if action not in REPAIRABLE_ACTIONS or not path:
            continue
        key = (action, path)
        if key in seen:
            continue
        seen.add(key)
        plan.append(
            {
                "action": action,
                "path": path,
                "service": str(item.get("service") or ""),
                "reason": str(item.get("summary") or item.get("title") or ""),
            }
        )
    return plan


def run_full_diagnostics(*, export_bundle: bool = False) -> dict[str, Any]:
    ensure_dirs()
    issues: list[dict[str, Any]] = []

    try:
        core_preflight = run_core_preflight()
        core_preflight_payload = {
            "ok": bool(getattr(core_preflight, "ok", False)),
            "checks": list(getattr(core_preflight, "checks", []) or []),
        }
    except Exception as exc:
        core_preflight_payload = {"ok": False, "checks": [], "reason": f"core_preflight_failed:{type(exc).__name__}"}
        issues.append(
            _issue(
                issue_id="core_preflight_failed",
                severity="critical",
                category="preflight",
                title="Core preflight failed",
                summary=str(core_preflight_payload["reason"]),
            )
        )

    for idx, check in enumerate(list(core_preflight_payload.get("checks") or [])):
        if bool(check.get("ok")):
            continue
        severity = "critical" if str(check.get("severity") or "").upper() == "ERROR" else "warn"
        issues.append(
            _issue(
                issue_id=f"core_preflight_{idx}",
                severity=severity,
                category="preflight",
                title=str(check.get("name") or "preflight_check"),
                summary=str(check.get("detail") or "Preflight check failed."),
            )
        )

    try:
        app_preflight_payload = dict(run_app_preflight() or {})
    except Exception as exc:
        app_preflight_payload = {"ready": False, "problems": [], "reason": f"app_preflight_failed:{type(exc).__name__}"}
        issues.append(
            _issue(
                issue_id="app_preflight_failed",
                severity="warn",
                category="environment",
                title="Environment preflight failed",
                summary=str(app_preflight_payload["reason"]),
            )
        )

    for idx, problem in enumerate(list(app_preflight_payload.get("problems") or [])):
        issues.append(
            _issue(
                issue_id=f"app_preflight_problem_{idx}",
                severity="warn",
                category="environment",
                title=str(problem).replace("_", " "),
                summary=f"Setup preflight reported: {problem}",
            )
        )

    dashboard_runtime = run_dashboard_diagnostics(startup_smoke=False)
    for idx, item in enumerate(list(dashboard_runtime.get("issues") or [])):
        issues.append(
            _issue(
                issue_id=f"dashboard_issue_{idx}",
                severity="critical" if str(item.get("severity") or "") == "critical" else "warn",
                category="dashboard",
                title=str(item.get("title") or "dashboard issue"),
                summary=str(item.get("summary") or ""),
                path=str(item.get("path") or ""),
            )
        )

    process_files = collect_process_files()
    health_rows = _latest_health_rows()
    for row in health_rows:
        service = str(row.get("service") or "")
        status = str(row.get("status") or "").upper()
        pid = int(row.get("pid") or 0) if row.get("pid") is not None else 0
        pid_alive = _pid_alive(pid)
        if status in ATTENTION_STATUSES:
            issues.append(
                _issue(
                    issue_id=f"health_{service}",
                    severity="warn",
                    category="service_health",
                    title=f"{service} status {status.lower()}",
                    summary=f"Health file reports {status.lower()} for {service}.",
                    service=service,
                )
            )
        elif status in RUNNING_STATUSES and pid and not pid_alive:
            issues.append(
                _issue(
                    issue_id=f"health_stale_{service}",
                    severity="warn",
                    category="service_health",
                    title=f"{service} health is stale",
                    summary=f"Health file still reports {status.lower()} but pid {pid} is not running.",
                    service=service,
                )
            )

    lock_rows = _lock_rows()
    for row in lock_rows:
        if bool(row.get("repairable")):
            issues.append(
                _issue(
                    issue_id=f"stale_lock_{row['name']}",
                    severity="warn",
                    category="runtime_lock",
                    title=f"Stale lock file {row['name']}",
                    summary=f"Lock file exists for {row['service']} but the recorded pid is not running or the lock is invalid.",
                    repairable=True,
                    repair_action=str(row.get("repair_action") or ""),
                    path=str(row.get("path") or ""),
                    service=str(row.get("service") or ""),
                )
            )

    pid_rows = _pid_rows()
    for row in pid_rows:
        if bool(row.get("repairable")):
            issues.append(
                _issue(
                    issue_id=f"stale_pid_{row['name']}",
                    severity="warn",
                    category="runtime_pid",
                    title=f"Stale pid file {row['name']}",
                    summary=f"Pid file exists for {row['service']} but the pid is invalid or no longer running.",
                    repairable=True,
                    repair_action=str(row.get("repair_action") or ""),
                    path=str(row.get("path") or ""),
                    service=str(row.get("service") or ""),
                )
            )

    stop_rows = _stop_rows()
    for row in stop_rows:
        if bool(row.get("repairable")):
            issues.append(
                _issue(
                    issue_id=f"stale_stop_{row['name']}",
                    severity="warn",
                    category="runtime_flag",
                    title=f"Stale stop file {row['name']}",
                    summary=f"Stop file exists for {row['service']} but no related live process is running.",
                    repairable=True,
                    repair_action=str(row.get("repair_action") or ""),
                    path=str(row.get("path") or ""),
                    service=str(row.get("service") or ""),
                )
            )

    try:
        from services.analytics.crypto_edge_collector_service import load_runtime_status as load_collector_runtime_status
    except Exception as exc:
        collector_runtime = {"ok": False, "reason": f"runtime_import_failed:{type(exc).__name__}"}
    else:
        collector_runtime = _load_managed_runtime(load_collector_runtime_status)

    try:
        from services.analytics.paper_strategy_evidence_service import load_runtime_status as load_paper_evidence_runtime_status
    except Exception as exc:
        paper_evidence_runtime = {"ok": False, "reason": f"runtime_import_failed:{type(exc).__name__}"}
    else:
        paper_evidence_runtime = _load_managed_runtime(load_paper_evidence_runtime_status)
    for name, payload in (
        ("crypto_edge_collector", collector_runtime),
        ("paper_strategy_evidence", paper_evidence_runtime),
    ):
        status = str(payload.get("status") or "").lower()
        reason = str(payload.get("reason") or payload.get("summary_text") or "").strip()
        if not bool(payload.get("ok", True)) and reason:
            issues.append(
                _issue(
                    issue_id=f"{name}_runtime_unavailable",
                    severity="warn",
                    category="managed_runtime",
                    title=f"{name.replace('_', ' ')} runtime unavailable",
                    summary=reason,
                    service=name,
                )
            )
        elif status in {"failed", "dead", "blocked"}:
            issues.append(
                _issue(
                    issue_id=f"{name}_{status}",
                    severity="warn",
                    category="managed_runtime",
                    title=f"{name.replace('_', ' ')} {status}",
                    summary=reason or f"{name.replace('_', ' ')} runtime needs attention.",
                    service=name,
                )
            )

    artifacts = _artifact_summary()
    evidence_latest = dict(artifacts.get("strategy_evidence_latest") or {})
    if not bool(evidence_latest.get("exists")):
        issues.append(
            _issue(
                issue_id="missing_strategy_evidence_artifact",
                severity="warn",
                category="artifact",
                title="Strategy evidence artifact missing",
                summary="No persisted strategy evidence artifact is available yet.",
            )
        )

    repair_plan = _repair_plan_from_issues(issues)
    critical_count = sum(1 for item in issues if str(item.get("severity") or "") == "critical")
    warning_count = sum(1 for item in issues if str(item.get("severity") or "") == "warn")
    status = "critical" if critical_count else ("warn" if warning_count else "ok")
    export_path = ""
    if bool(export_bundle):
        try:
            export_path = _runtime_relative_str(export_zip_to_runtime())
        except Exception as exc:
            issues.append(
                _issue(
                    issue_id="diagnostics_export_failed",
                    severity="warn",
                    category="diagnostics_export",
                    title="Diagnostics export failed",
                    summary=f"{type(exc).__name__}: {exc}",
                )
            )
            repair_plan = _repair_plan_from_issues(issues)
            critical_count = sum(1 for item in issues if str(item.get("severity") or "") == "critical")
            warning_count = sum(1 for item in issues if str(item.get("severity") or "") == "warn")
            status = "critical" if critical_count else ("warn" if warning_count else "ok")

    return {
        "ok": True,
        "as_of": _now_iso(),
        "status": status,
        "summary": {
            "critical_issues": critical_count,
            "warning_issues": warning_count,
            "repairable_issues": len(repair_plan),
            "health_services": len(health_rows),
            "runtime_locks": len(lock_rows),
            "runtime_pids": len(pid_rows),
            "runtime_stop_files": len(stop_rows),
        },
        "core_preflight": core_preflight_payload,
        "app_preflight": app_preflight_payload,
        "dashboard": dashboard_runtime,
        "process_files": process_files,
        "health_rows": health_rows,
        "lock_rows": lock_rows,
        "pid_rows": pid_rows,
        "stop_rows": stop_rows,
        "managed_runtime": {
            "crypto_edge_collector": collector_runtime,
            "paper_strategy_evidence": paper_evidence_runtime,
        },
        "artifacts": artifacts,
        "issues": issues,
        "repair_plan": repair_plan,
        "export_path": export_path,
    }


def preview_safe_self_repair() -> dict[str, Any]:
    diagnostics = run_full_diagnostics(export_bundle=False)
    repair_plan = list(diagnostics.get("repair_plan") or [])
    return {
        "ok": True,
        "non_destructive": True,
        "as_of": str(diagnostics.get("as_of") or _now_iso()),
        "status": str(diagnostics.get("status") or "unknown"),
        "repair_plan": repair_plan,
        "repairable_issues": int((diagnostics.get("summary") or {}).get("repairable_issues") or 0),
    }


def apply_safe_self_repair(*, export_bundle: bool = True) -> dict[str, Any]:
    preview = preview_safe_self_repair()
    repair_plan = list(preview.get("repair_plan") or [])
    removed: list[str] = []
    failed: list[dict[str, Any]] = []
    export_path = ""

    if bool(export_bundle):
        try:
            export_path = _runtime_relative_str(export_zip_to_runtime())
        except Exception as exc:
            failed.append({"action": "export_diagnostics", "error": f"{type(exc).__name__}: {exc}"})

    for item in repair_plan:
        path = Path(str(item.get("path") or ""))
        if not _safe_remove_file(path):
            failed.append({"action": str(item.get("action") or ""), "path": _runtime_relative_str(path), "error": "remove_failed"})
            continue
        removed.append(_runtime_relative_str(path))

    diagnostics_after = run_full_diagnostics(export_bundle=False)
    return {
        "ok": len(failed) == 0,
        "non_destructive": False,
        "as_of": _now_iso(),
        "removed_count": len(removed),
        "removed_paths": removed,
        "failed_actions": failed,
        "export_path": export_path,
        "diagnostics_after": diagnostics_after,
    }
