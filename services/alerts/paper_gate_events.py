"""
Paper/gate event alerting (Active backlog #23; evidence-writer hook
deferred here by substrate #9).

Notification-only by design: nothing in this module influences trading,
gating, or evidence decisions, and every entry point is best-effort and
never raises — an alerting problem must not break an evidence write or a
gate check. Channel selection lives in the existing alert dispatcher; with
no channels configured, the proven local JSONL fallback still records the
event.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.os.app_paths import runtime_dir

GATE_SNAPSHOT_NAME = "promotion_gates.last.json"


def _send(level: str, message: str, payload: dict | None) -> None:
    from services.alerts.alert_dispatcher import send_alert
    from services.config_loader import load_runtime_trading_config

    try:
        cfg = load_runtime_trading_config()
    except Exception:
        cfg = {}
    send_alert(
        cfg=cfg if isinstance(cfg, dict) else {},
        level=level,
        message=message,
        payload=payload,
    )


def alert_evidence_writer_transition(
    prev_status: str,
    new_status: str,
    payload: dict | None = None,
) -> bool:
    """
    Alert once per evidence-writer status TRANSITION (never per failure):
    -> refusing  = critical (the session is starving the promotion gate)
    ok -> degraded = warning
    -> ok from degraded/refusing = info recovery
    Returns True when an alert was dispatched. Never raises.
    """
    try:
        prev = str(prev_status or "ok").strip().lower() or "ok"
        new = str(new_status or "ok").strip().lower() or "ok"
        if prev == new:
            return False
        if new == "refusing":
            _send("critical", "evidence_writer:refusing", payload)
        elif new == "degraded" and prev == "ok":
            _send("warning", "evidence_writer:degraded", payload)
        elif new == "ok" and prev in ("degraded", "refusing"):
            _send("info", "evidence_writer:recovered", payload)
        else:
            return False
        return True
    except Exception:
        return False


def _snapshot_path() -> Path:
    return runtime_dir() / "health" / GATE_SNAPSHOT_NAME


def _load_snapshot() -> dict[str, Any]:
    try:
        loaded = json.loads(_snapshot_path().read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def _persist_snapshot(snapshot: dict[str, Any]) -> None:
    try:
        path = _snapshot_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _paper_progress_snapshot(result: dict[str, Any]) -> dict[str, Any] | None:
    progress = result.get("paper_progress")
    if not isinstance(progress, dict):
        return None
    observed = _int_or_none(progress.get("round_trips_recorded"))
    required = _int_or_none(progress.get("round_trips_required"))
    remaining = _int_or_none(progress.get("round_trips_remaining"))
    if observed is None:
        return None
    return {
        "round_trips_recorded": observed,
        "round_trips_required": required,
        "round_trips_remaining": remaining,
        "round_trips_ready": bool(progress.get("round_trips_ready")),
        "all_history_round_trips": _int_or_none(progress.get("all_history_round_trips")),
        "source": str(progress.get("source") or ""),
    }


def record_gate_result_and_alert(
    result: dict[str, Any],
    *,
    alert: bool,
    now_iso: str,
) -> dict[str, Any]:
    """
    Persist a per-gate pass/fail snapshot and (when ``alert``) dispatch on
    FLIPS versus the previous snapshot:
    ready True -> False = critical; any gate pass -> fail = warning;
    ready False -> True = info recovery. The first run establishes a
    baseline silently. Never raises; returns a summary for callers/tests.
    """
    out: dict[str, Any] = {"alerted": [], "baseline": False}
    try:
        gates = {
            str(g.get("label")): bool(g.get("passed"))
            for g in (result.get("gates") or [])
            if g.get("label") is not None and g.get("passed") is not None
        }
        ready = bool(result.get("ready"))
        paper_progress = _paper_progress_snapshot(result)
        prev = _load_snapshot()
        prev_gates = prev.get("gates") if isinstance(prev.get("gates"), dict) else None
        prev_paper_progress = (
            prev.get("paper_progress")
            if isinstance(prev.get("paper_progress"), dict)
            else None
        )

        if prev_gates is None:
            out["baseline"] = True
        elif alert:
            try:  # a raising channel must not freeze the snapshot below
                flipped_fail = sorted(
                    label for label, passed in gates.items()
                    if not passed and prev_gates.get(label) is True
                )
                prev_ready = bool(prev.get("ready"))
                if prev_ready and not ready:
                    _send(
                        "critical",
                        "promotion_gates:ready_lost",
                        {
                            "flipped_to_fail": flipped_fail,
                            "stage": result.get("stage"),
                        },
                    )
                    out["alerted"].append("ready_lost")
                elif flipped_fail:
                    _send(
                        "warning",
                        "promotion_gates:gate_flipped_fail",
                        {
                            "flipped_to_fail": flipped_fail,
                            "stage": result.get("stage"),
                        },
                    )
                    out["alerted"].append("gate_flipped_fail")
                if ready and not prev_ready:
                    _send("info", "promotion_gates:ready_recovered", {"stage": result.get("stage")})
                    out["alerted"].append("ready_recovered")
                if paper_progress is not None and prev_paper_progress is not None:
                    current_trips = paper_progress.get("round_trips_recorded")
                    previous_trips = _int_or_none(
                        prev_paper_progress.get("round_trips_recorded")
                    )
                    if (
                        isinstance(current_trips, int)
                        and previous_trips is not None
                        and current_trips != previous_trips
                    ):
                        delta = current_trips - previous_trips
                        _send(
                            "info" if delta > 0 else "warning",
                            "paper_gate:qualified_round_trips_changed",
                            {
                                "previous": previous_trips,
                                "current": current_trips,
                                "delta": delta,
                                "required": paper_progress.get("round_trips_required"),
                                "remaining": paper_progress.get("round_trips_remaining"),
                                "ready": paper_progress.get("round_trips_ready"),
                                "source": paper_progress.get("source"),
                                "stage": result.get("stage"),
                            },
                        )
                        out["alerted"].append("qualified_round_trips_changed")
            except Exception:
                out["alerted"] = []

        _persist_snapshot(
            {
                "ts": now_iso,
                "ready": ready,
                "stage": result.get("stage"),
                "gates": gates,
                "paper_progress": paper_progress,
            }
        )
    except Exception:
        pass
    return out
