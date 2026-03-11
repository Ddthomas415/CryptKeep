from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_normalize import normalize_symbol
from storage.evidence_signals_sqlite import EvidenceSignalsSQLite

ALLOWED_SIDES = {"buy","sell","long","short","flat"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return _now_iso()
    if isinstance(value, (int, float)):
        v = float(value)
        if v > 10_000_000_000:
            return datetime.fromtimestamp(v / 1000.0, tz=timezone.utc).isoformat()
        return datetime.fromtimestamp(v, tz=timezone.utc).isoformat()
    s = str(value).strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).astimezone(timezone.utc).isoformat()
    except Exception:
        return _now_iso()


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except Exception:
        return None


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(value)
    except Exception:
        return None


def _cfg() -> Dict[str, Any]:
    cfg = load_user_yaml()
    evidence = cfg.get("evidence") if isinstance(cfg.get("evidence"), dict) else {}
    ingest = evidence.get("ingest") if isinstance(evidence.get("ingest"), dict) else {}
    return {
        "default_source_id": str(ingest.get("default_source_id") or "manual_default"),
        "default_source_type": str(ingest.get("default_source_type") or "manual"),
        "default_display_name": str(ingest.get("default_display_name") or "Manual Source"),
        "default_consent_confirmed": bool(ingest.get("default_consent_confirmed", True)),
    }


def ensure_source(
    store: EvidenceSignalsSQLite,
    *,
    source_id: str,
    source_type: str,
    display_name: str,
    consent_confirmed: bool,
) -> Dict[str, Any]:
    src = store.get_source(source_id)
    if src:
        return src
    return store.upsert_source(
        source_id=str(source_id),
        source_type=str(source_type),
        display_name=str(display_name),
        consent_confirmed=bool(consent_confirmed),
    )


def _side_normalized(raw: Any) -> str:
    side = str(raw or "").strip().lower()
    if side == "long":
        return "buy"
    if side == "short":
        return "sell"
    return side


def ingest_event(
    event: Dict[str, Any],
    *,
    source_id: str | None = None,
    source_type: str | None = None,
    display_name: str | None = None,
    consent_confirmed: bool | None = None,
) -> Dict[str, Any]:
    payload = dict(event or {})
    cfg = _cfg()
    store = EvidenceSignalsSQLite()

    sid = str(source_id or payload.get("source_id") or cfg["default_source_id"]).strip()
    stype = str(source_type or payload.get("source_type") or cfg["default_source_type"]).strip()
    dname = str(display_name or payload.get("source_name") or cfg["default_display_name"]).strip()
    consent = bool(cfg["default_consent_confirmed"] if consent_confirmed is None else consent_confirmed)

    ensure_source(
        store,
        source_id=sid,
        source_type=stype,
        display_name=dname,
        consent_confirmed=consent,
    )

    event_id = str(payload.get("event_id") or uuid.uuid4())
    store.insert_raw_event(event_id=event_id, source_id=sid, payload_json=json.dumps(payload, default=str, sort_keys=True))

    raw_symbol = str(payload.get("symbol") or "").strip()
    symbol = normalize_symbol(raw_symbol) if raw_symbol else ""
    side = _side_normalized(payload.get("side"))
    ts = _parse_ts(payload.get("ts") or payload.get("timestamp") or payload.get("time"))

    if not raw_symbol or not symbol:
        quarantine_id = str(uuid.uuid4())
        store.insert_quarantine(
            quarantine_id=quarantine_id,
            event_id=event_id,
            source_id=sid,
            reason="invalid_or_missing_symbol",
            payload_json=json.dumps(payload, default=str, sort_keys=True),
        )
        return {"ok": False, "event_id": event_id, "source_id": sid, "quarantined": True, "reason": "invalid_or_missing_symbol", "quarantine_id": quarantine_id}

    if side not in ALLOWED_SIDES:
        quarantine_id = str(uuid.uuid4())
        store.insert_quarantine(
            quarantine_id=quarantine_id,
            event_id=event_id,
            source_id=sid,
            reason="invalid_or_missing_side",
            payload_json=json.dumps(payload, default=str, sort_keys=True),
        )
        return {"ok": False, "event_id": event_id, "source_id": sid, "quarantined": True, "reason": "invalid_or_missing_side", "quarantine_id": quarantine_id}

    signal_id = str(payload.get("signal_id") or uuid.uuid4())
    store.insert_signal(
        signal_id=signal_id,
        event_id=event_id,
        source_id=sid,
        ts=ts,
        venue=(str(payload.get("venue")).strip() if payload.get("venue") not in (None, "") else None),
        symbol=symbol,
        side=side,
        confidence=_safe_float(payload.get("confidence")),
        size_hint=_safe_float(payload.get("size_hint") or payload.get("size")),
        horizon_sec=_safe_int(payload.get("horizon_sec") or payload.get("horizon")),
        notes=(str(payload.get("notes") or payload.get("note") or "").strip() or None),
    )
    return {
        "ok": True,
        "signal_id": signal_id,
        "event_id": event_id,
        "source_id": sid,
        "symbol": symbol,
        "side": side,
        "ts": ts,
    }


def ingest_csv(
    csv_path: str | Path,
    *,
    source_id: str | None = None,
    source_type: str | None = None,
    display_name: str | None = None,
    consent_confirmed: bool | None = None,
) -> Dict[str, Any]:
    p = Path(csv_path)
    if not p.exists():
        return {"ok": False, "reason": "csv_not_found", "path": str(p)}

    rows = 0
    accepted = 0
    quarantined = 0
    errors = 0
    details: list[Dict[str, Any]] = []

    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):
            # Skip blank CSV lines.
            if not row or not any((str(v).strip() for v in row.values() if v is not None)):
                continue
            rows += 1
            try:
                out = ingest_event(
                    row,
                    source_id=source_id,
                    source_type=source_type,
                    display_name=display_name,
                    consent_confirmed=consent_confirmed,
                )
                if out.get("ok"):
                    accepted += 1
                elif out.get("quarantined"):
                    quarantined += 1
                else:
                    errors += 1
                if not out.get("ok"):
                    details.append({"line": idx, "result": out})
            except Exception as e:
                errors += 1
                details.append({"line": idx, "error": f"{type(e).__name__}: {e}"})

    return {
        "ok": True,
        "path": str(p),
        "rows": rows,
        "accepted": accepted,
        "quarantined": quarantined,
        "errors": errors,
        "details": details[:50],
    }
