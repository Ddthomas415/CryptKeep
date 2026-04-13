from __future__ import annotations

# market_view.py — auto-split from view_data.py
from dashboard.services.views._shared import *  # noqa: F401,F403

def get_markets_view(selected_asset: str | None = None) -> dict[str, Any]:
    summary = get_dashboard_summary()
    recommendations = get_recommendations()
    current_regime = _load_current_regime() or str(summary.get("risk_status") or "")
    risk_status = str(summary.get("risk_status") or "")

    recommendation_map: dict[str, dict[str, Any]] = {}
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        asset = str(item.get("asset") or "").strip().upper()
        if asset and asset not in recommendation_map:
            recommendation_map[asset] = item

    raw_watchlist = summary.get("watchlist") if isinstance(summary.get("watchlist"), list) else []
    if not raw_watchlist:
        raw_watchlist = _default_dashboard_summary()["watchlist"]

    watchlist: list[dict[str, Any]] = []
    for item in raw_watchlist:
        if not isinstance(item, dict):
            continue
        asset = str(item.get("asset") or "").strip().upper()
        if not asset:
            continue
        recommendation = recommendation_map.get(asset, {})
        change_24h_pct = float(item.get("change_24h_pct") or 0.0)
        watchlist.append(
            _enrich_signal_row(
                {
                    "asset": asset,
                    "price": float(item.get("price") or 0.0),
                    "change_24h_pct": change_24h_pct,
                    "signal": str(item.get("signal") or recommendation.get("signal") or "watch"),
                    "confidence": float(recommendation.get("confidence") or 0.0),
                    "status": str(recommendation.get("status") or "monitor"),
                    "volume_trend": str(item.get("volume_trend") or _derive_volume_trend(change_24h_pct)),
                    "execution_state": str(recommendation.get("execution_state") or ""),
                    "evidence": str(recommendation.get("evidence") or ""),
                    "summary": str(recommendation.get("summary") or ""),
                },
                market_row=item,
                current_regime=current_regime,
                risk_status=risk_status,
            )
        )

    if not watchlist:
        watchlist = list(_default_dashboard_summary()["watchlist"])

    requested_asset = str(selected_asset or "").strip().upper()
    if requested_asset:
        selected_row = next((row for row in watchlist if str(row.get("asset")) == requested_asset), watchlist[0])
    else:
        selected_row = min(
            enumerate(watchlist),
            key=lambda item: (_asset_priority(str(item[1].get("signal") or "")), item[0]),
        )[1]

    asset = str(selected_row.get("asset") or "")
    watchlist_price = float(selected_row.get("price") or 0.0)
    change_24h_pct = float(selected_row.get("change_24h_pct") or 0.0)
    explain = get_research_explain(asset, question=f"Why is {asset} moving?")
    snapshot = _get_market_snapshot(asset) or {}
    price = float(snapshot.get("last_price") or watchlist_price or 0.0)
    bid = float(snapshot.get("bid") or 0.0)
    ask = float(snapshot.get("ask") or 0.0)
    spread = float(snapshot.get("spread") or 0.0)
    exchange = str(snapshot.get("exchange") or "coinbase")
    snapshot_timestamp = str(snapshot.get("timestamp") or "")
    snapshot_source = str(snapshot.get("source") or "watchlist")
    volume_24h = float(snapshot.get("volume_24h") or 0.0)

    related_signals = [
        _enrich_signal_row(
            {
                "asset": str(item.get("asset") or ""),
                "signal": str(item.get("signal") or "hold"),
                "confidence": float(item.get("confidence") or 0.0),
                "summary": str(item.get("summary") or ""),
                "status": str(item.get("status") or "pending"),
                "execution_state": str(item.get("execution_state") or ""),
                "evidence": str(item.get("evidence") or ""),
                "price": watchlist_price,
                "change_24h_pct": change_24h_pct,
            },
            market_row={
                **(selected_row if isinstance(selected_row, dict) else {}),
                **(snapshot if isinstance(snapshot, dict) else {}),
                "price": price,
                "change_24h_pct": change_24h_pct,
                "volume_24h": volume_24h,
                "spread": spread,
            },
            current_regime=current_regime,
            risk_status=risk_status,
        )
        for item in recommendations
        if isinstance(item, dict) and str(item.get("asset") or "").strip().upper() == asset
    ]
    if not related_signals:
        related_signals = [
            _enrich_signal_row(
                {
                "asset": asset,
                "signal": str(selected_row.get("signal") or "watch"),
                "confidence": float(selected_row.get("confidence") or 0.0),
                "summary": "No direct recommendation is available. Keep this asset in monitored research mode.",
                "status": str(selected_row.get("status") or "monitor"),
                "execution_state": str(selected_row.get("execution_state") or ""),
                "price": watchlist_price,
                "change_24h_pct": change_24h_pct,
                },
                market_row={
                    **(selected_row if isinstance(selected_row, dict) else {}),
                    **(snapshot if isinstance(snapshot, dict) else {}),
                    "price": price,
                    "change_24h_pct": change_24h_pct,
                    "volume_24h": volume_24h,
                    "spread": spread,
                },
                current_regime=current_regime,
                risk_status=risk_status,
            )
        ]

    lead_signal = recommendation_map.get(asset, {})
    current_cause = str(explain.get("current_cause") or "").strip()
    past_precedent = str(explain.get("past_precedent") or "").strip()
    future_catalyst = str(explain.get("future_catalyst") or "").strip()

    thesis = current_cause or str(lead_signal.get("summary") or "").strip()
    if not thesis:
        bias = _derive_market_bias(change_24h_pct)
        thesis = f"{asset} remains {bias} with {selected_row.get('volume_trend')} activity and watchlist support."

    evidence = str(lead_signal.get("evidence") or "").strip()
    raw_evidence = explain.get("evidence") if isinstance(explain.get("evidence"), list) else []
    evidence_items = [
        {
            "type": str(item.get("type") or ""),
            "source": str(item.get("source") or ""),
            "summary": str(item.get("summary") or ""),
            "timestamp": str(item.get("timestamp") or ""),
            "relevance": float(item.get("relevance") or 0.0),
        }
        for item in raw_evidence
        if isinstance(item, dict)
    ]
    if not evidence and evidence_items:
        evidence = str(evidence_items[0].get("summary") or "")
    if not evidence:
        evidence = f"24h change {change_24h_pct:+.1f}% with {selected_row.get('volume_trend')} participation."
    if not evidence_items:
        evidence_items = [
            {
                "type": "market",
                "source": "watchlist",
                "summary": evidence,
                "timestamp": "",
                "relevance": 0.7,
            }
        ]

    catalysts = [
        current_cause or thesis,
        past_precedent or f"Volume trend is {selected_row.get('volume_trend')}.",
        future_catalyst or f"Nearest support is ${price * 0.985:,.2f} and resistance is ${price * 1.015:,.2f}.",
        str(explain.get("risk_note") or f"Current workflow state is {str(selected_row.get('status') or 'monitor').replace('_', ' ')}."),
    ]

    detail = {
        "asset": asset,
        "price": price,
        "change_24h_pct": change_24h_pct,
        "signal": str(selected_row.get("signal") or "watch"),
        "confidence": float(explain.get("confidence") or lead_signal.get("confidence") or selected_row.get("confidence") or 0.0),
        "status": str(lead_signal.get("status") or selected_row.get("status") or "monitor"),
        "execution_state": str(lead_signal.get("execution_state") or ""),
        "market_bias": _derive_market_bias(change_24h_pct),
        "volume_trend": str(selected_row.get("volume_trend") or "steady"),
        "support": round(price * 0.985, 2),
        "resistance": round(price * 1.015, 2),
        "exchange": exchange,
        "bid": bid,
        "ask": ask,
        "spread": spread,
        "volume_24h": volume_24h,
        "snapshot_timestamp": snapshot_timestamp,
        "snapshot_source": snapshot_source,
        "thesis": thesis,
        "question": str(explain.get("question") or f"Why is {asset} moving?"),
        "current_cause": current_cause or thesis,
        "past_precedent": past_precedent,
        "future_catalyst": future_catalyst,
        "risk_note": str(explain.get("risk_note") or ""),
        "execution_disabled": bool(explain.get("execution_disabled", True)),
        "evidence": evidence,
        "evidence_items": evidence_items,
        "price_series": _get_market_price_series(asset, price, change_24h_pct),
        "catalysts": catalysts,
        "related_signals": related_signals,
    }
    detail = _enrich_signal_row(
        detail,
        market_row={
            **(snapshot if isinstance(snapshot, dict) else {}),
            "price": price,
            "change_24h_pct": change_24h_pct,
            "volume_24h": volume_24h,
            "spread": spread,
        },
        current_regime=current_regime,
        risk_status=risk_status,
    )

    return {
        "selected_asset": asset,
        "watchlist": watchlist,
        "detail": detail,
    }



def get_research_explain(asset: str, question: str | None = None) -> dict[str, Any]:
    asset_symbol = str(asset or "").strip().upper() or "SOL"
    resolved_question = question or f"Why is {asset_symbol} moving?"
    fallback = _default_explain_payload(asset_symbol, resolved_question)

    def _normalize_explain(
        envelope: dict[str, Any] | None,
        *,
        default_provider: str,
        default_fallback: bool,
    ) -> dict[str, Any] | None:
        if isinstance(envelope, dict) and isinstance(envelope.get("data"), dict):
            data = dict(envelope["data"])
        elif isinstance(envelope, dict):
            data = dict(envelope)
        else:
            return None

        if not any(key in data for key in ("current_cause", "past_precedent", "future_catalyst")):
            return None
        if _explain_mentions_foreign_asset(data, asset_symbol):
            return None

        data["asset"] = asset_symbol
        data["question"] = resolved_question
        assistant_status = data.get("assistant_status") if isinstance(data.get("assistant_status"), dict) else {}
        assistant_message = str(assistant_status.get("message") or "").strip()
        data["assistant_status"] = {
            "provider": str(assistant_status.get("provider") or default_provider),
            "model": assistant_status.get("model"),
            "fallback": bool(assistant_status.get("fallback")) if "fallback" in assistant_status else default_fallback,
            "message": assistant_message or None,
        }
        return data

    primary_envelope = _request_envelope(
        "/api/v1/research/explain",
        method="POST",
        payload={"asset": asset_symbol, "question": resolved_question},
    )
    primary = _normalize_explain(
        primary_envelope,
        default_provider="backend_api",
        default_fallback=False,
    )
    if primary is not None:
        return primary

    phase1 = _normalize_explain(
        _request_envelope_from_base(
            PHASE1_ORCHESTRATOR_URL,
            "/v1/explain",
            method="POST",
            payload={"asset": asset_symbol, "question": resolved_question, "lookback_minutes": 60},
        ),
        default_provider="phase1_copilot",
        default_fallback=False,
    )
    if phase1 is not None:
        return phase1

    mock = _read_mock_envelope("explain-sol.json")
    if asset_symbol == "SOL" and isinstance(mock, dict) and isinstance(mock.get("data"), dict):
        data = dict(mock["data"])
        data["asset"] = asset_symbol
        data["question"] = resolved_question
        data["assistant_status"] = {
            "provider": "dashboard_fallback",
            "model": None,
            "fallback": True,
            "message": "Static asset-aware dashboard fallback used because no valid explain response was available.",
        }
        return data

    return fallback


