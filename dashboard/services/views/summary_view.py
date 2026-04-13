from __future__ import annotations

# summary_view.py — auto-split from view_data.py
from dashboard.services.views._shared import *  # noqa: F401,F403

def get_dashboard_summary() -> dict[str, Any]:
    envelope = _fetch_envelope("/api/v1/dashboard/summary")
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        return _attach_data_provenance(
            _apply_local_summary_overrides(dict(envelope["data"])),
            source="api_with_local_overlays",
            fallback=False,
            message="Workspace status is using runtime/API data with local overlays.",
        )

    mock = _read_mock_envelope("dashboard.json")
    if isinstance(mock, dict) and isinstance(mock.get("data"), dict):
        return _attach_data_provenance(
            _apply_local_summary_overrides(dict(mock["data"])),
            source="mock_bundle_with_local_overlays",
            fallback=True,
            message="Workspace status is using bundled mock data because live dashboard summary data was unavailable.",
        )
    return _attach_data_provenance(
        _apply_local_summary_overrides(_default_dashboard_summary()),
        source="dashboard_fallback",
        fallback=True,
        message="Workspace status is using static fallback/sample data because no live or mock dashboard summary was available.",
    )



def get_overview_view(selected_asset: str | None = None) -> dict[str, Any]:
    summary = get_dashboard_summary()
    recent_activity = get_recent_activity()
    signals_view = get_signals_view(selected_asset=selected_asset)
    signals = signals_view.get("signals") if isinstance(signals_view.get("signals"), list) else []
    detail = signals_view.get("detail") if isinstance(signals_view.get("detail"), dict) else {}

    signal_rows = [
        {
            "asset": str(item.get("asset") or ""),
            "signal": str(item.get("signal") or ""),
            "confidence": float(item.get("confidence") or 0.0),
            "status": str(item.get("status") or ""),
            "execution_state": str(item.get("execution_state") or ""),
            "thesis": str(item.get("summary") or ""),
            "regime": str(item.get("regime") or ""),
            "category": str(item.get("category") or ""),
            "opportunity_score": float(item.get("opportunity_score") or 0.0),
        }
        for item in signals[:6]
        if isinstance(item, dict)
    ]

    return {
        "summary": summary,
        "recent_activity": recent_activity,
        "watchlist_preview": _build_watchlist_preview(summary),
        "signals": signal_rows,
        "selected_asset": str(signals_view.get("selected_asset") or detail.get("asset") or ""),
        "detail": detail,
    }


