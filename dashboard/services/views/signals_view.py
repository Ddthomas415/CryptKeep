from __future__ import annotations
from typing import Any

# signals_view.py — auto-split from view_data.py
from dashboard.services.views._shared import (  # noqa: F401
    _apply_local_execution_state_to_recommendations,
    _default_recommendations,
    _enrich_signal_row,
    _fetch_envelope,
    _load_current_regime,
    _load_local_recommendations,
)

def _view_data():
    from dashboard.services import view_data

    return view_data

def get_recommendations() -> list[dict[str, Any]]:
    vd = _view_data()
    local_rows = vd._load_local_recommendations(limit=20)
    if local_rows:
        return vd._apply_local_execution_state_to_recommendations(local_rows)

    envelope = vd._fetch_envelope("/api/v1/trading/recommendations")
    if isinstance(envelope, dict) and envelope.get("status") == "success":
        data = envelope.get("data")
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            mapped: list[dict[str, Any]] = []
            for item in data["items"]:
                if not isinstance(item, dict):
                    continue
                mapped.append(
                    {
                        "asset": str(item.get("asset") or ""),
                        "signal": str(item.get("side") or "hold"),
                        "confidence": float(item.get("confidence") or 0.0),
                        "summary": str(item.get("strategy") or ""),
                        "evidence": str(item.get("target_logic") or ""),
                        "status": str(item.get("status") or "pending"),
                    }
                )
            if mapped:
                return vd._apply_local_execution_state_to_recommendations(mapped)
    return vd._apply_local_execution_state_to_recommendations(vd._default_recommendations())



def get_signals_view(selected_asset: str | None = None) -> dict[str, Any]:
    vd = _view_data()
    recommendations = vd.get_recommendations()
    summary = vd.get_dashboard_summary()
    current_regime = vd._load_current_regime() or str(summary.get("risk_status") or "")
    watchlist = summary.get("watchlist") if isinstance(summary.get("watchlist"), list) else []

    market_rows: dict[str, dict[str, Any]] = {}
    for item in watchlist:
        if not isinstance(item, dict):
            continue
        asset = str(item.get("asset") or "").strip().upper()
        if asset:
            market_rows[asset] = item

    signals: list[dict[str, Any]] = []
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        asset = str(item.get("asset") or "").strip().upper()
        market = market_rows.get(asset, {})
        signals.append(
            vd._enrich_signal_row(
                {
                    "asset": asset,
                    "signal": str(item.get("signal") or "hold"),
                    "confidence": float(item.get("confidence") or 0.0),
                    "summary": str(item.get("summary") or ""),
                    "status": str(item.get("status") or "pending"),
                    "execution_state": str(item.get("execution_state") or ""),
                    "evidence": str(item.get("evidence") or ""),
                    "price": float(market.get("price") or 0.0),
                    "change_24h_pct": float(market.get("change_24h_pct") or 0.0),
                },
                market_row=market,
                current_regime=current_regime,
                risk_status=str(summary.get("risk_status") or ""),
            )
        )

    if not signals:
        markets_view = vd.get_markets_view(selected_asset=selected_asset)
        detail = markets_view.get("detail") if isinstance(markets_view.get("detail"), dict) else {}
        fallback_asset = str(detail.get("asset") or selected_asset or "SOL")
        signals = [
            {
                "asset": fallback_asset,
                "signal": str(detail.get("signal") or "watch"),
                "confidence": float(detail.get("confidence") or 0.0),
                "summary": str(detail.get("current_cause") or detail.get("thesis") or ""),
                "status": str(detail.get("status") or "monitor"),
                "execution_state": str(detail.get("execution_state") or ""),
                "evidence": str(detail.get("evidence") or ""),
                "price": float(detail.get("price") or 0.0),
                "change_24h_pct": float(detail.get("change_24h_pct") or 0.0),
                "regime": str(detail.get("regime") or current_regime or ""),
                "regime_fit": float(detail.get("regime_fit") or 0.0),
                "tradeability": float(detail.get("tradeability") or 0.0),
                "setup_quality": float(detail.get("setup_quality") or 0.0),
                "expected_return": float(detail.get("expected_return") or 0.0),
                "risk_penalty": float(detail.get("risk_penalty") or 0.0),
                "opportunity_score": float(detail.get("opportunity_score") or 0.0),
                "category": str(detail.get("category") or ""),
            }
        ]
        return {
            "selected_asset": fallback_asset,
            "signals": signals,
            "detail": detail,
        }

    requested_asset = str(selected_asset or "").strip().upper()
    if requested_asset and any(row["asset"] == requested_asset for row in signals):
        resolved_asset = requested_asset
    else:
        resolved_asset = max(
            signals,
            key=lambda row: (
                str(row.get("status") or "") == "pending_review",
                str(row.get("signal") or "") in {"buy", "research"},
                float(row.get("confidence") or 0.0),
            ),
        )["asset"]

    markets_view = vd.get_markets_view(selected_asset=resolved_asset)
    detail = dict(markets_view.get("detail")) if isinstance(markets_view.get("detail"), dict) else {}
    selected_signal = next((row for row in signals if str(row.get("asset") or "") == resolved_asset), {})
    if detail and isinstance(selected_signal, dict):
        detail.update(
            {
                "regime": str(selected_signal.get("regime") or ""),
                "regime_fit": float(selected_signal.get("regime_fit") or 0.0),
                "tradeability": float(selected_signal.get("tradeability") or 0.0),
                "setup_quality": float(selected_signal.get("setup_quality") or 0.0),
                "expected_return": float(selected_signal.get("expected_return") or 0.0),
                "risk_penalty": float(selected_signal.get("risk_penalty") or 0.0),
                "opportunity_score": float(selected_signal.get("opportunity_score") or 0.0),
                "category": str(selected_signal.get("category") or ""),
            }
        )

    return {
        "selected_asset": resolved_asset,
        "signals": signals,
        "detail": detail,
    }
