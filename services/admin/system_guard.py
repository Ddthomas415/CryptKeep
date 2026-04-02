from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

from services.os.app_paths import ensure_dirs, runtime_dir

ensure_dirs()
GUARD_PATH = runtime_dir() / "system_guard.json"
VALID_STATES = {"RUNNING", "HALTING", "HALTED"}
_LOG = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_payload(
    *,
    state: str,
    writer: str,
    reason: str,
    epoch: int = 0,
    cancel_requested: bool = False,
) -> dict[str, Any]:
    return {
        "state": str(state).upper(),
        "ts": _now(),
        "writer": str(writer),
        "reason": str(reason),
        "epoch": int(epoch),
        "cancel_requested": bool(cancel_requested),
    }


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    state = str(payload.get("state") or "").upper().strip()
    if state not in VALID_STATES:
        raise ValueError(f"invalid_guard_state:{state or 'missing'}")
    try:
        epoch = int(payload.get("epoch") or 0)
    except Exception as exc:
        raise ValueError("invalid_guard_epoch") from exc
    out = _default_payload(
        state=state,
        writer=str(payload.get("writer") or "system_guard"),
        reason=str(payload.get("reason") or ""),
        epoch=max(0, epoch),
        cancel_requested=bool(payload.get("cancel_requested", False)),
    )
    ts = str(payload.get("ts") or "").strip()
    if ts:
        out["ts"] = ts
    return out


def _read_state() -> dict[str, Any]:
    return json.loads(GUARD_PATH.read_text(encoding="utf-8"))


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def get_state(*, fail_closed: bool = False) -> dict[str, Any]:
    try:
        if not GUARD_PATH.exists():
            if fail_closed:
                return _default_payload(state="HALTED", writer="system_guard", reason="missing", epoch=0)
            return _default_payload(state="RUNNING", writer="system_guard", reason="missing", epoch=0)
        return _normalize_payload(_read_state())
    except Exception as exc:
        _LOG.warning("system guard state read failed: %s: %s", type(exc).__name__, exc)
        if fail_closed:
            return _default_payload(state="HALTED", writer="system_guard", reason="invalid", epoch=0)
        return _default_payload(state="RUNNING", writer="system_guard", reason="invalid", epoch=0)


def set_state(
    state: str,
    *,
    writer: str,
    reason: str = "",
    epoch: int | None = None,
    cancel_requested: bool = False,
) -> dict[str, Any]:
    state_up = str(state or "").upper().strip()
    if state_up not in VALID_STATES:
        raise ValueError(f"invalid_guard_state:{state_up or 'missing'}")
    current = get_state(fail_closed=False)
    next_epoch = int(epoch) if epoch is not None else int(current.get("epoch") or 0) + 1
    payload = _default_payload(
        state=state_up,
        writer=str(writer or "system_guard"),
        reason=str(reason or ""),
        epoch=max(0, next_epoch),
        cancel_requested=bool(cancel_requested),
    )
    _write_atomic(GUARD_PATH, payload)
    return payload
