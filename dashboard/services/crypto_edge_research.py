from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_capture_ts(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _source_label(source: Any) -> str:
    value = str(source or "").strip().lower()
    mapping = {
        "sample_bundle": "Sample Bundle",
        "live_public": "Live Public",
        "manual": "Manual Import",
    }
    return mapping.get(value, value.replace("_", " ").title() or "Unknown")


def _freshness_label(value: Any) -> str:
    ts = _parse_capture_ts(value)
    if ts is None:
        return "Unknown"
    age_seconds = max((datetime.now(timezone.utc) - ts).total_seconds(), 0.0)
    if age_seconds < 3600.0:
        return "Fresh"
    if age_seconds < 6 * 3600.0:
        return "Recent"
    if age_seconds < 24 * 3600.0:
        return "Aging"
    return "Stale"


def _build_provenance_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    meta_map = {
        "funding": dict(report.get("funding_meta") or {}),
        "basis": dict(report.get("basis_meta") or {}),
        "quotes": dict(report.get("quote_meta") or {}),
    }
    for theme, meta in meta_map.items():
        if not meta:
            continue
        rows.append(
            {
                "theme": theme,
                "source": _source_label(meta.get("source")),
                "capture_ts": str(meta.get("capture_ts") or "-"),
                "row_count": int(meta.get("row_count") or 0),
                "freshness": _freshness_label(meta.get("capture_ts")),
            }
        )
    return rows


def _build_origin_summary(provenance_rows: list[dict[str, Any]]) -> tuple[str, str]:
    if not provenance_rows:
        return "No Snapshots", "No freshness data"
    source_labels = sorted({str(row.get("source") or "Unknown") for row in provenance_rows})
    freshness_labels = [str(row.get("freshness") or "Unknown") for row in provenance_rows]
    if len(source_labels) == 1:
        data_origin = source_labels[0]
    else:
        data_origin = "Mixed Sources"
    if "Fresh" in freshness_labels:
        freshness = "Fresh"
    elif "Recent" in freshness_labels:
        freshness = "Recent"
    elif "Aging" in freshness_labels:
        freshness = "Aging"
    elif "Stale" in freshness_labels:
        freshness = "Stale"
    else:
        freshness = "Unknown"
    return data_origin, freshness


def _build_structural_summary(report: dict[str, Any], *, origin_label: str) -> str:
    if not bool(report.get("has_any_data")):
        return f"No {origin_label} structural edge snapshot is stored yet."
    funding = dict(report.get("funding") or {})
    basis = dict(report.get("basis") or {})
    dislocations = dict(report.get("dislocations") or {})
    top_symbol = str(((dislocations.get("top_dislocation") or {}).get("symbol") or "-"))
    return (
        f"{origin_label} snapshot shows funding bias {str(funding.get('dominant_bias') or 'flat')}, "
        f"average basis {float(basis.get('avg_basis_bps') or 0.0):.2f} bps, "
        f"{int(dislocations.get('positive_count') or 0)} positive venue dislocations, "
        f"top symbol {top_symbol}, freshness {str(report.get('freshness_summary') or 'Unknown')}."
    )


def _build_change_summary_text(workspace: dict[str, Any]) -> str:
    trend_rows = list(workspace.get("trend_rows") or [])
    if not trend_rows:
        return "Not enough stored structural edge history is available to summarize what changed."
    fragments: list[str] = []
    for row in trend_rows[:3]:
        fragments.append(
            f"{str(row.get('theme') or 'theme').title()} {str(row.get('latest') or '-')}"
            f" ({str(row.get('vs_prior') or 'no prior')})"
        )
    return (
        f"Recent structural changes from stored snapshots: {'; '.join(fragments)}. "
        f"Snapshot freshness is {str(workspace.get('freshness_summary') or 'Unknown')}."
    )


def _build_collector_runtime_summary(payload: dict[str, Any]) -> str:
    if not bool(payload.get("has_status")):
        return "Collector loop has not written runtime status yet."
    status = str(payload.get("status") or "unknown").replace("_", " ")
    reason = str(payload.get("reason") or payload.get("last_reason") or "unknown")
    return (
        f"Collector status {status}, source {str(payload.get('source_label') or payload.get('source') or 'Live Public')}, "
        f"{int(payload.get('writes') or 0)} writes, {int(payload.get('errors') or 0)} errors, "
        f"last reason {reason}."
    )


def _decorate_history_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decorated: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row or {})
        item["source_label"] = _source_label(item.get("source"))
        item["freshness"] = _freshness_label(item.get("capture_ts"))
        decorated.append(item)
    return decorated


def _trend_value(latest: dict[str, Any] | None, previous: dict[str, Any] | None, field: str) -> float | None:
    if not latest or not previous:
        return None
    try:
        return float(latest.get(field) or 0.0) - float(previous.get(field) or 0.0)
    except Exception:
        return None


def _build_trend_rows(
    *,
    funding_history: list[dict[str, Any]],
    basis_history: list[dict[str, Any]],
    dislocation_history: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    latest_funding = funding_history[0] if funding_history else None
    previous_funding = funding_history[1] if len(funding_history) > 1 else None
    carry_delta = _trend_value(latest_funding, previous_funding, "annualized_carry_pct")
    if latest_funding:
        rows.append(
            {
                "theme": "funding",
                "current_state": str(latest_funding.get("dominant_bias") or "flat").replace("_", " ").title(),
                "latest": f"{float(latest_funding.get('annualized_carry_pct') or 0.0):.2f}%",
                "vs_prior": f"{carry_delta:+.2f} pts" if carry_delta is not None else "No prior snapshot",
                "capture_ts": str(latest_funding.get("capture_ts") or "-"),
            }
        )

    latest_basis = basis_history[0] if basis_history else None
    previous_basis = basis_history[1] if len(basis_history) > 1 else None
    basis_delta = _trend_value(latest_basis, previous_basis, "avg_basis_bps")
    if latest_basis:
        rows.append(
            {
                "theme": "basis",
                "current_state": "Premium" if float(latest_basis.get("avg_basis_bps") or 0.0) > 0.0 else "Discount" if float(latest_basis.get("avg_basis_bps") or 0.0) < 0.0 else "Flat",
                "latest": f"{float(latest_basis.get('avg_basis_bps') or 0.0):.2f} bps",
                "vs_prior": f"{basis_delta:+.2f} bps" if basis_delta is not None else "No prior snapshot",
                "capture_ts": str(latest_basis.get("capture_ts") or "-"),
            }
        )

    latest_dislocation = dislocation_history[0] if dislocation_history else None
    previous_dislocation = dislocation_history[1] if len(dislocation_history) > 1 else None
    count_delta = _trend_value(latest_dislocation, previous_dislocation, "positive_count")
    if latest_dislocation:
        rows.append(
            {
                "theme": "dislocations",
                "current_state": str(latest_dislocation.get("top_symbol") or "-"),
                "latest": str(int(latest_dislocation.get("positive_count") or 0)),
                "vs_prior": f"{count_delta:+.0f} venues" if count_delta is not None else "No prior snapshot",
                "capture_ts": str(latest_dislocation.get("capture_ts") or "-"),
            }
        )

    return rows


def load_crypto_edge_report() -> dict[str, Any]:
    try:
        from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_import_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
        }

    try:
        store = CryptoEdgeStoreSQLite()
        report = store.latest_report()
        report["ok"] = True
        report["research_only"] = True
        report["execution_enabled"] = False
        return report
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_read_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
        }


def load_crypto_edge_workspace(*, history_limit: int = 5) -> dict[str, Any]:
    report = load_crypto_edge_report()
    if not bool(report.get("ok")):
        report["history_rows"] = []
        report["funding_history"] = []
        report["basis_history"] = []
        report["dislocation_history"] = []
        report["trend_rows"] = []
        report["provenance_rows"] = []
        report["data_origin_label"] = "Unavailable"
        report["freshness_summary"] = "Unavailable"
        return report

    try:
        from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite
    except Exception as exc:
        report["history_rows"] = []
        report["funding_history"] = []
        report["basis_history"] = []
        report["dislocation_history"] = []
        report["trend_rows"] = []
        report["provenance_rows"] = []
        report["data_origin_label"] = "Unavailable"
        report["freshness_summary"] = "Unavailable"
        report["history_reason"] = f"store_import_failed:{type(exc).__name__}"
        return report

    try:
        store = CryptoEdgeStoreSQLite()
        report["history_rows"] = _decorate_history_rows(
            store.recent_snapshot_history(limit_per_kind=int(history_limit))
        )
        report["funding_history"] = _decorate_history_rows(
            store.recent_funding_history(limit=int(history_limit))
        )
        report["basis_history"] = _decorate_history_rows(
            store.recent_basis_history(limit=int(history_limit))
        )
        report["dislocation_history"] = _decorate_history_rows(
            store.recent_dislocation_history(limit=int(history_limit))
        )
        report["trend_rows"] = _build_trend_rows(
            funding_history=list(report.get("funding_history") or []),
            basis_history=list(report.get("basis_history") or []),
            dislocation_history=list(report.get("dislocation_history") or []),
        )
        report["provenance_rows"] = _build_provenance_rows(report)
        report["data_origin_label"], report["freshness_summary"] = _build_origin_summary(list(report.get("provenance_rows") or []))
        return report
    except Exception as exc:
        report["history_rows"] = []
        report["funding_history"] = []
        report["basis_history"] = []
        report["dislocation_history"] = []
        report["trend_rows"] = []
        report["provenance_rows"] = []
        report["data_origin_label"] = "Unavailable"
        report["freshness_summary"] = "Unavailable"
        report["history_reason"] = f"history_read_failed:{type(exc).__name__}"
        return report


def load_latest_live_crypto_edge_snapshot() -> dict[str, Any]:
    try:
        from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_import_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
            "has_live_data": False,
            "data_origin_label": "Unavailable",
            "freshness_summary": "Unavailable",
            "summary_text": "Live-public structural edge snapshots are unavailable.",
        }

    try:
        store = CryptoEdgeStoreSQLite()
        report = store.latest_report_for_source(source="live_public")
        report["ok"] = True
        report["research_only"] = True
        report["execution_enabled"] = False
        report["has_live_data"] = bool(report.get("has_any_data"))
        report["provenance_rows"] = _build_provenance_rows(report)
        report["data_origin_label"], report["freshness_summary"] = _build_origin_summary(
            list(report.get("provenance_rows") or [])
        )
        if not bool(report.get("provenance_rows")):
            report["data_origin_label"] = "Live Public"
            report["freshness_summary"] = "No Live Data"
        report["summary_text"] = _build_structural_summary(
            report,
            origin_label=str(report.get("data_origin_label") or "Live Public"),
        )
        return report
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_read_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
            "has_live_data": False,
            "data_origin_label": "Unavailable",
            "freshness_summary": "Unavailable",
            "summary_text": "Live-public structural edge snapshots could not be read.",
        }


def load_crypto_edge_change_summary(*, history_limit: int = 5) -> dict[str, Any]:
    workspace = load_crypto_edge_workspace(history_limit=max(int(history_limit), 2))
    change_rows = list(workspace.get("trend_rows") or [])
    return {
        "ok": bool(workspace.get("ok")),
        "reason": workspace.get("reason") or workspace.get("history_reason"),
        "research_only": True,
        "execution_enabled": False,
        "has_any_data": bool(workspace.get("has_any_data")),
        "has_change_data": bool(change_rows),
        "data_origin_label": workspace.get("data_origin_label") or "Unknown",
        "freshness_summary": workspace.get("freshness_summary") or "Unknown",
        "rows": change_rows,
        "summary_text": _build_change_summary_text(workspace),
    }


def load_crypto_edge_collector_runtime() -> dict[str, Any]:
    try:
        from services.analytics.crypto_edge_collector_service import status_file
    except Exception as exc:
        return {
            "ok": False,
            "has_status": False,
            "reason": f"status_import_failed:{type(exc).__name__}",
            "summary_text": "Collector runtime status is unavailable.",
        }

    try:
        path = status_file()
        if not path.exists():
            return {
                "ok": True,
                "has_status": False,
                "reason": "status_missing",
                "status": "not_started",
                "freshness": "Unknown",
                "summary_text": "Collector loop has not written runtime status yet.",
            }
        import json

        payload = dict(json.loads(path.read_text(encoding="utf-8")) or {})
        payload["ok"] = True
        payload["has_status"] = True
        payload["freshness"] = _freshness_label(payload.get("ts"))
        payload["source_label"] = _source_label(payload.get("source"))
        payload["summary_text"] = _build_collector_runtime_summary(payload)
        return payload
    except Exception as exc:
        return {
            "ok": False,
            "has_status": False,
            "reason": f"status_read_failed:{type(exc).__name__}",
            "summary_text": "Collector runtime status is unavailable.",
        }
