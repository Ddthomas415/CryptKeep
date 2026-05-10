from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from services.admin.live_disable_wizard import disable_live_now
from services.os.app_paths import runtime_dir
from services.process import heartbeat as legacy_heartbeat
from services.runtime.process_supervisor import status as supervisor_status, stop_process

FLAGS = runtime_dir() / "flags"
HEALTH = runtime_dir() / "health"

BOT_RUNNING_SERVICES = (
    "pipeline",
    "executor",
    "intent_consumer",
    "ops_signal_adapter",
    "ops_risk_gate",
    "reconciler",
)

CANONICAL_SERVICES = BOT_RUNNING_SERVICES + ("market_ws", "ai_alert_monitor")

CANONICAL_STATUS_FILES = {
    "bot_runner": FLAGS / "bot_runner.status.json",
    "pipeline": FLAGS / "pipeline.status.json",
    "executor": FLAGS / "intent_executor.status.json",
    "intent_consumer": FLAGS / "live_consumer.status.json",
    "ops_signal_adapter": HEALTH / "ops_signal_adapter.json",
    "ops_risk_gate": HEALTH / "ops_risk_gate_service.json",
    "reconciler": FLAGS / "live_reconciler.status.json",
    "market_ws": HEALTH / "market_ws.json",
}
LEGACY_RUNTIME_FALLBACK_ENV = "CBP_ALLOW_LEGACY_BOT_RUNTIME_FALLBACK"
LEGACY_RUNTIME_FALLBACK_NOTE = (
    "Legacy bot runtime fallback is compatibility-only. Canonical runtime truth "
    "uses process-supervisor services and runtime status files."
)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _ts_epoch_from_payload(payload: dict[str, Any]) -> float | None:
    raw_epoch = payload.get("ts_epoch")
    if raw_epoch is not None:
        try:
            return float(raw_epoch)
        except Exception:
            pass

    for key in ("ts", "ts_iso"):
        raw = payload.get(key)
        if not raw:
            continue
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
    return None


def canonical_service_status() -> dict[str, Any]:
    data = supervisor_status(list(CANONICAL_SERVICES))
    return data if isinstance(data, dict) else {}


def _legacy_runtime_fallback_enabled() -> bool:
    return str(os.environ.get(LEGACY_RUNTIME_FALLBACK_ENV, "")).strip().upper() in {"1", "TRUE", "YES", "ON"}


def _canonical_only_payload(*, source: str, services: dict[str, Any] | None = None, note: str) -> dict[str, Any]:
    return {
        "ok": True,
        "running": False,
        "pid": None,
        "state": {"services": dict(services or {})},
        "source": source,
        "legacy_fallback_enabled": False,
        "note": note,
    }


def _mark_legacy_fallback(payload: dict[str, Any], *, source: str) -> dict[str, Any]:
    out = dict(payload)
    out["source"] = source
    out["compatibility_only"] = True
    out["legacy_fallback_enabled"] = True
    out["legacy_fallback_env"] = LEGACY_RUNTIME_FALLBACK_ENV
    out["warning"] = LEGACY_RUNTIME_FALLBACK_NOTE
    return out


def canonical_bot_status() -> dict[str, Any]:
    services = canonical_service_status()
    running = {
        name: row
        for name, row in services.items()
        if name in BOT_RUNNING_SERVICES and bool((row or {}).get("running"))
    }
    if running:
        pid = next((int(row.get("pid")) for row in running.values() if row.get("pid")), None)
        return {
            "ok": True,
            "running": True,
            "pid": pid,
            "state": {"services": services},
            "source": "canonical_process_supervisor",
        }
    if not _legacy_runtime_fallback_enabled():
        return _canonical_only_payload(
            source="canonical_process_supervisor",
            services=services,
            note="no_canonical_running_services",
        )

    from services.process import bot_process as legacy_bot_process

    return _mark_legacy_fallback(
        legacy_bot_process.status(),
        source="legacy_bot_process_fallback",
    )


def read_heartbeat() -> dict[str, Any]:
    services = canonical_service_status()
    running = {name: row for name, row in services.items() if bool((row or {}).get("running"))}
    candidates: list[tuple[float, str, Path, dict[str, Any]]] = []

    for name, path in CANONICAL_STATUS_FILES.items():
        if name != "bot_runner" and running and name not in running:
            continue
        payload = _load_json(path)
        ts_epoch = _ts_epoch_from_payload(payload)
        if ts_epoch is None:
            continue
        candidates.append((float(ts_epoch), name, path, payload))

    if candidates:
        ts_epoch, name, path, payload = max(candidates, key=lambda item: item[0])
        out = dict(payload)
        out["ts_epoch"] = float(ts_epoch)
        out["source"] = name
        out["path"] = str(path)
        return out

    if not _legacy_runtime_fallback_enabled():
        return {
            "source": "canonical_status_files",
            "legacy_fallback_enabled": False,
            "note": "no_canonical_status_signal",
        }

    return _mark_legacy_fallback(
        legacy_heartbeat.read_heartbeat(),
        source="legacy_heartbeat_fallback",
    )


def stop_bot(*, hard: bool = True) -> dict[str, Any]:
    services = canonical_service_status()
    running = [name for name, row in services.items() if bool((row or {}).get("running"))]
    if not running:
        if not _legacy_runtime_fallback_enabled():
            return {
                "ok": True,
                "mode": "canonical",
                "running": [],
                "results": [],
                "legacy_fallback_enabled": False,
                "note": "no_canonical_running_services",
            }

        from services.process import bot_process as legacy_bot_process

        return _mark_legacy_fallback(
            legacy_bot_process.stop_bot(hard=hard),
            source="legacy_bot_process_fallback",
        )

    try:
        disable_live = disable_live_now(note="watchdog:heartbeat_stale")
    except Exception as exc:
        disable_live = {
            "ok": False,
            "reason": f"disable_live_failed:{type(exc).__name__}",
            "error": str(exc),
        }

    results = [stop_process(name) for name in running]
    ok = bool(disable_live.get("ok", True)) and all(bool(result.get("ok")) for result in results)
    return {
        "ok": ok,
        "mode": "canonical",
        "running": running,
        "disable_live": disable_live,
        "results": results,
    }
