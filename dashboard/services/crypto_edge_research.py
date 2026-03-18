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
        report["history_rows"] = store.recent_snapshot_history(limit_per_kind=int(history_limit))
        report["funding_history"] = store.recent_funding_history(limit=int(history_limit))
        report["basis_history"] = store.recent_basis_history(limit=int(history_limit))
        report["dislocation_history"] = store.recent_dislocation_history(limit=int(history_limit))
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
