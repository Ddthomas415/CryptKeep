from __future__ import annotations

from typing import Any

from dashboard.services.digest.utils import age_seconds, fmt_age, freshness_state_from_age


def _freshness_label(seconds: int | None) -> str:
    state = freshness_state_from_age(seconds)
    mapping = {
        "fresh": "Fresh",
        "aging": "Aging",
        "stale": "Stale",
        "missing": "Unknown",
        "not_active": "Not Active",
    }
    return mapping.get(state, "Unknown")


def _runtime_alert(payload: dict[str, Any]) -> tuple[str, str]:
    summary = str(payload.get("summary_text") or "").strip()
    normalized = summary.lower()
    if "waiting for fresh market ticks" in normalized:
        return "warning", summary
    if str(payload.get("recommendation") or "").strip().lower() == "investigate":
        return "warning", summary or "Paper sim monitor recommends investigation."
    return "", ""


def load_paper_strategy_evidence_runtime() -> dict[str, Any]:
    try:
        from services.analytics.paper_strategy_evidence_service import load_runtime_status
    except Exception as exc:
        return {
            "ok": False,
            "has_status": False,
            "reason": f"service_import_failed:{type(exc).__name__}",
            "summary_text": "Paper strategy evidence collector runtime is unavailable.",
        }

    payload = dict(load_runtime_status() or {})
    age_s = age_seconds(payload.get("ts") or payload.get("started_ts"))
    payload["age_seconds"] = age_s
    payload["freshness"] = _freshness_label(age_s)
    payload["age_label"] = fmt_age(age_s)
    payload["completed_summary"] = (
        f"{int(payload.get('completed_strategies') or 0)}/{int(payload.get('total_strategies') or 0)}"
        if payload.get("total_strategies") is not None
        else "0/0"
    )
    watch_seed = (
        dict(payload.get("paper_sim_monitor_watch_seed") or {})
        if isinstance(payload.get("paper_sim_monitor_watch_seed"), dict)
        else {}
    )
    payload["paper_sim_watch_seed_ok"] = bool(watch_seed.get("ok", True)) if watch_seed else True
    payload["paper_sim_watch_seed_reason"] = str(watch_seed.get("reason") or "")
    payload["paper_sim_watch_seed_count"] = int(
        watch_seed.get("watch_count")
        or len(list(watch_seed.get("watch_names") or []))
        or 0
    )
    if not str(payload.get("summary_text") or "").strip():
        payload["summary_text"] = (
            f"Paper strategy evidence collector status {str(payload.get('status') or 'unknown')}, "
            f"{payload['completed_summary']} strategies complete."
        )
    tone, text = _runtime_alert(payload)
    if not text and watch_seed and not payload["paper_sim_watch_seed_ok"]:
        reason = payload["paper_sim_watch_seed_reason"] or "unknown"
        tone, text = "warning", f"Paper sim default watch registration degraded: {reason}"
    payload["alert_tone"] = tone
    payload["alert_text"] = text
    return payload


def load_paper_sim_monitor_runtime() -> dict[str, Any]:
    try:
        from services.analytics.paper_sim_monitor import load_runtime_status
    except Exception as exc:
        return {
            "ok": False,
            "has_status": False,
            "reason": f"service_import_failed:{type(exc).__name__}",
            "summary_text": "Paper sim monitor runtime is unavailable.",
        }

    payload = dict(load_runtime_status() or {})
    age_s = age_seconds(payload.get("ts") or payload.get("started_ts"))
    payload["age_seconds"] = age_s
    payload["freshness"] = _freshness_label(age_s)
    payload["age_label"] = fmt_age(age_s)
    watches = [dict(item) for item in list(payload.get("watches") or []) if isinstance(item, dict)]
    recent_reports = [dict(item) for item in list(payload.get("recent_watch_reports") or []) if isinstance(item, dict)]
    payload["watch_count"] = len(watches)
    payload["recent_report_count"] = len(recent_reports)
    payload["registered_watch_names"] = [str(item.get("name") or "") for item in watches if str(item.get("name") or "").strip()]
    payload["desktop_notify_enabled"] = bool(payload.get("desktop_notify", True))
    payload["last_watch_report"] = dict(recent_reports[0]) if recent_reports else {}
    promotion_progress = (
        dict(payload.get("promotion_progress") or {})
        if isinstance(payload.get("promotion_progress"), dict)
        else {}
    )
    payload["promotion_thresholds_ready"] = bool(promotion_progress.get("thresholds_ready"))
    payload["promotion_progress_summary"] = str(
        payload.get("promotion_progress_summary")
        or promotion_progress.get("summary_text")
        or ""
    )
    payload["promotion_blocking_threshold_count"] = len(
        [item for item in list(promotion_progress.get("blocking_thresholds") or []) if isinstance(item, dict)]
    )
    last_notification = (
        dict(payload["last_watch_report"].get("desktop_notification") or {})
        if isinstance(payload.get("last_watch_report"), dict)
        else {}
    )
    payload["last_desktop_notification"] = last_notification
    if not payload["desktop_notify_enabled"]:
        payload["notification_status"] = "disabled"
        payload["notification_reason"] = "disabled"
    elif last_notification:
        if bool(last_notification.get("sent")):
            payload["notification_status"] = "sent"
        elif bool(last_notification.get("attempted")):
            payload["notification_status"] = "failed"
        else:
            payload["notification_status"] = "unknown"
        payload["notification_reason"] = str(last_notification.get("reason") or "")
    else:
        payload["notification_status"] = "pending"
        payload["notification_reason"] = ""
    if not str(payload.get("summary_text") or "").strip():
        payload["summary_text"] = (
            f"Paper sim monitor status {str(payload.get('status') or 'unknown')}, "
            f"{int(payload.get('watch_count') or 0)} watch(es), "
            f"{int(payload.get('recent_report_count') or 0)} recent report(s)."
        )
    tone, text = _runtime_alert(payload)
    if not text and str(payload.get("notification_status") or "") == "failed":
        tone, text = "warning", "Latest paper sim desktop notification failed."
    payload["alert_tone"] = tone
    payload["alert_text"] = text
    return payload
