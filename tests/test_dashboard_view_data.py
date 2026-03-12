from __future__ import annotations

from dashboard.services import view_data


def test_dashboard_summary_uses_defaults_when_sources_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_fetch_envelope", lambda _path: None)
    monkeypatch.setattr(view_data, "_read_mock_envelope", lambda _name: None)

    summary = view_data.get_dashboard_summary()
    assert summary["mode"] == "research_only"
    assert summary["risk_status"] == "safe"
    assert float(summary["portfolio"]["total_value"]) > 0


def test_recommendations_map_api_payload(monkeypatch) -> None:
    payload = {
        "status": "success",
        "data": {
            "items": [
                {
                    "asset": "SOL",
                    "side": "buy",
                    "confidence": 0.74,
                    "strategy": "event_momentum",
                    "target_logic": "trailing",
                    "status": "pending_review",
                }
            ]
        },
    }

    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: payload if path == "/api/v1/trading/recommendations" else None,
    )
    rows = view_data.get_recommendations()
    assert rows[0]["asset"] == "SOL"
    assert rows[0]["signal"] == "buy"
    assert rows[0]["status"] == "pending_review"


def test_recent_activity_prefers_audit_details(monkeypatch) -> None:
    payload = {
        "status": "success",
        "data": {
            "items": [
                {"action": "explain_asset", "details": "Generated explanation for SOL"},
                {"action": "evaluate_trade", "details": "Execution disabled in research mode"},
            ]
        },
    }
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: payload if path == "/api/v1/audit/events" else None,
    )
    rows = view_data.get_recent_activity()
    assert rows == ["Generated explanation for SOL", "Execution disabled in research mode"]


def test_portfolio_view_uses_dashboard_watchlist_marks(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "portfolio": {
                "total_value": 1000.0,
                "cash": 300.0,
                "unrealized_pnl": 25.0,
                "exposure_used_pct": 17.5,
            },
            "watchlist": [
                {"asset": "BTC", "price": 90000.0},
                {"asset": "SOL", "price": 200.0},
            ],
        },
    )

    payload = view_data.get_portfolio_view()
    assert payload["portfolio"]["cash"] == 300.0
    assert payload["positions"][0]["asset"] == "BTC"
    assert payload["positions"][0]["mark"] == 90000.0
    assert payload["positions"][1]["mark"] == 200.0


def test_markets_view_prefers_requested_asset_and_related_signal(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8, "signal": "watch"},
                {"asset": "SOL", "price": 200.0, "change_24h_pct": 6.5, "signal": "research"},
            ]
        },
    )
    monkeypatch.setattr(
        view_data,
        "get_recommendations",
        lambda: [
            {
                "asset": "SOL",
                "signal": "buy",
                "confidence": 0.81,
                "summary": "Momentum with catalyst support",
                "evidence": "volume expansion",
                "status": "pending_review",
            }
        ],
    )
    monkeypatch.setattr(
        view_data,
        "get_research_explain",
        lambda asset, question=None: {
            "asset": asset,
            "question": question or f"Why is {asset} moving?",
            "current_cause": "Momentum with catalyst support",
            "past_precedent": "Prior momentum cycles showed similar behavior",
            "future_catalyst": "A governance milestone remains in focus",
            "confidence": 0.81,
            "risk_note": "Research only.",
            "execution_disabled": True,
            "evidence": [
                {
                    "type": "market",
                    "source": "coinbase",
                    "summary": "volume expansion",
                    "timestamp": "2026-03-11T12:55:00Z",
                    "relevance": 0.93,
                }
            ],
        },
    )

    payload = view_data.get_markets_view(selected_asset="SOL")
    assert payload["selected_asset"] == "SOL"
    assert payload["detail"]["asset"] == "SOL"
    assert payload["detail"]["confidence"] == 0.81
    assert payload["detail"]["market_bias"] == "bullish"
    assert payload["detail"]["price_series"][-1] == 200.0
    assert payload["detail"]["current_cause"] == "Momentum with catalyst support"
    assert payload["detail"]["evidence_items"][0]["summary"] == "volume expansion"
    assert payload["detail"]["related_signals"][0]["status"] == "pending_review"


def test_markets_view_defaults_to_research_asset(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8, "signal": "watch"},
                {"asset": "ETH", "price": 4100.0, "change_24h_pct": 0.7, "signal": "monitor"},
                {"asset": "SOL", "price": 200.0, "change_24h_pct": 6.5, "signal": "research"},
            ]
        },
    )
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])
    monkeypatch.setattr(
        view_data,
        "get_research_explain",
        lambda asset, question=None: {
            "asset": asset,
            "question": question or f"Why is {asset} moving?",
            "current_cause": "",
            "past_precedent": "",
            "future_catalyst": "",
            "confidence": 0.0,
            "risk_note": "",
            "execution_disabled": True,
            "evidence": [],
        },
    )

    payload = view_data.get_markets_view()
    assert payload["selected_asset"] == "SOL"
    assert payload["detail"]["asset"] == "SOL"
    assert payload["detail"]["related_signals"][0]["summary"].startswith("No direct recommendation")
    assert payload["detail"]["question"] == "Why is SOL moving?"


def test_signals_view_prefers_pending_review_signal(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_recommendations",
        lambda: [
            {
                "asset": "BTC",
                "signal": "hold",
                "confidence": 0.66,
                "summary": "Range breakout not confirmed",
                "status": "watch",
                "evidence": "weak continuation volume",
            },
            {
                "asset": "SOL",
                "signal": "buy",
                "confidence": 0.81,
                "summary": "Momentum with catalyst support",
                "status": "pending_review",
                "evidence": "volume expansion",
            },
        ],
    )
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8},
                {"asset": "SOL", "price": 200.0, "change_24h_pct": 6.5},
            ]
        },
    )
    monkeypatch.setattr(
        view_data,
        "get_markets_view",
        lambda selected_asset=None: {
            "detail": {
                "asset": selected_asset or "SOL",
                "current_cause": "Momentum with catalyst support",
                "price": 200.0,
                "change_24h_pct": 6.5,
                "signal": "buy",
                "status": "pending_review",
                "confidence": 0.81,
                "execution_disabled": True,
                "risk_note": "Research only.",
                "price_series": [190.0, 195.0, 200.0],
                "evidence_items": [{"summary": "volume expansion"}],
            }
        },
    )

    payload = view_data.get_signals_view()
    assert payload["selected_asset"] == "SOL"
    assert payload["signals"][0]["asset"] == "BTC"
    assert payload["signals"][1]["price"] == 200.0
    assert payload["detail"]["asset"] == "SOL"
    assert payload["detail"]["current_cause"] == "Momentum with catalyst support"


def test_signals_view_respects_requested_asset(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_recommendations",
        lambda: [
            {"asset": "BTC", "signal": "hold", "confidence": 0.66, "summary": "Range trade", "status": "watch", "evidence": "volume"},
            {"asset": "SOL", "signal": "buy", "confidence": 0.81, "summary": "Momentum", "status": "pending_review", "evidence": "catalyst"},
        ],
    )
    monkeypatch.setattr(view_data, "get_dashboard_summary", lambda: {"watchlist": []})
    monkeypatch.setattr(
        view_data,
        "get_markets_view",
        lambda selected_asset=None: {"detail": {"asset": selected_asset or "BTC"}},
    )

    payload = view_data.get_signals_view(selected_asset="BTC")
    assert payload["selected_asset"] == "BTC"
    assert payload["detail"]["asset"] == "BTC"


def test_research_explain_uses_api_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_request_envelope",
        lambda path, method="GET", payload=None: {
            "status": "success",
            "data": {
                "asset": "BTC",
                "question": "Why is BTC moving?",
                "current_cause": "Spot demand improved.",
                "past_precedent": "Breakout history is constructive.",
                "future_catalyst": "Macro events remain pending.",
                "confidence": 0.74,
                "risk_note": "Research only.",
                "execution_disabled": True,
                "evidence": [{"type": "market", "source": "coinbase", "summary": "bid support", "relevance": 0.82}],
            },
        }
        if path == "/api/v1/research/explain" and method == "POST"
        else None,
    )

    payload = view_data.get_research_explain("BTC")
    assert payload["asset"] == "BTC"
    assert payload["current_cause"] == "Spot demand improved."
    assert payload["confidence"] == 0.74


def test_research_explain_rejects_foreign_asset_copy(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_request_envelope",
        lambda path, method="GET", payload=None: {
            "status": "success",
            "data": {
                "asset": "BTC",
                "question": "Why is BTC moving?",
                "current_cause": "SOL is rising alongside increased spot volume and fresh ecosystem headlines.",
                "past_precedent": "Similar moves previously followed ecosystem upgrade narratives.",
                "future_catalyst": "A scheduled governance milestone may still matter.",
                "confidence": 0.78,
                "risk_note": "Research only.",
                "execution_disabled": True,
                "evidence": [],
            },
        }
        if path == "/api/v1/research/explain" and method == "POST"
        else None,
    )

    payload = view_data.get_research_explain("BTC")
    assert payload["asset"] == "BTC"
    assert "SOL" not in payload["current_cause"]
    assert payload["current_cause"].startswith("BTC is firming")


def test_research_explain_falls_back_for_non_sol_assets(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_request_envelope", lambda path, method="GET", payload=None: None)
    monkeypatch.setattr(view_data, "_read_mock_envelope", lambda _name: None)

    payload = view_data.get_research_explain("ADA")
    assert payload["asset"] == "ADA"
    assert payload["question"] == "Why is ADA moving?"
    assert payload["execution_disabled"] is True
    assert len(payload["evidence"]) == 1


def test_trades_view_maps_recommendations_to_pending_approvals(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {"approval_required": False},
    )
    monkeypatch.setattr(
        view_data,
        "get_recommendations",
        lambda: [
            {
                "id": "rec_99",
                "asset": "SOL",
                "signal": "buy",
                "risk_size_pct": 1.5,
                "status": "pending_review",
            }
        ],
    )

    payload = view_data.get_trades_view()
    assert payload["approval_required"] is False
    assert payload["pending_approvals"][0]["id"] == "rec_99"
    assert payload["pending_approvals"][0]["side"] == "buy"
    assert len(payload["recent_fills"]) >= 1


def test_settings_view_uses_api_payload(monkeypatch) -> None:
    payload = {
        "status": "success",
        "data": {
            "general": {"timezone": "UTC", "default_mode": "paper"},
            "notifications": {"telegram": False},
            "ai": {"tone": "concise"},
            "security": {"secret_masking": False},
        },
    }
    monkeypatch.setattr(
        view_data,
        "_fetch_envelope",
        lambda path: payload if path == "/api/v1/settings" else None,
    )

    settings = view_data.get_settings_view()
    assert settings["general"]["timezone"] == "UTC"
    assert settings["ai"]["tone"] == "concise"


def test_automation_view_uses_settings_and_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {"execution_enabled": True, "approval_required": False, "mode": "paper"},
    )
    monkeypatch.setattr(
        view_data,
        "get_settings_view",
        lambda: {"general": {"default_mode": "live_approval"}},
    )

    payload = view_data.get_automation_view()
    assert payload["execution_enabled"] is True
    assert payload["dry_run_mode"] is False
    assert payload["default_mode"] == "live_approval"
    assert payload["approval_required_for_live"] is False


def test_update_settings_view_reports_success(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "_request_envelope",
        lambda path, method="GET", payload=None: {"status": "success", "data": payload}
        if path == "/api/v1/settings" and method == "PUT"
        else None,
    )

    payload = {"general": {"timezone": "UTC"}}
    result = view_data.update_settings_view(payload)
    assert result["ok"] is True
    assert result["data"] == payload


def test_update_settings_view_reports_api_failure(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "_request_envelope", lambda path, method="GET", payload=None: None)

    result = view_data.update_settings_view({"general": {"timezone": "UTC"}})
    assert result["ok"] is False
    assert "unavailable" in result["message"].lower()


def test_get_automation_view_prefers_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(
        view_data,
        "load_user_yaml",
        lambda: {
            "execution": {
                "executor_mode": "live",
                "live_enabled": False,
                "executor_poll_sec": 3.0,
                "executor_max_per_cycle": 25,
                "paper_fee_bps": 9.0,
                "paper_slippage_bps": 4.0,
                "require_keys_for_live": False,
            },
            "signals": {
                "auto_route_to_paper": True,
                "default_venue": "kraken",
                "default_qty": 0.25,
                "order_type": "limit",
            },
            "dashboard_ui": {
                "automation": {
                    "enabled": True,
                    "dry_run_mode": False,
                    "default_mode": "live_approval",
                    "schedule": "hourly",
                    "marketplace_routing": "approval gated",
                    "approval_required_for_live": True,
                }
            },
        },
    )
    monkeypatch.setattr(view_data, "get_dashboard_summary", lambda: {"execution_enabled": False, "approval_required": False})
    monkeypatch.setattr(view_data, "get_settings_view", lambda: {"general": {"default_mode": "paper"}})

    payload = view_data.get_automation_view()
    assert payload["execution_enabled"] is True
    assert payload["default_mode"] == "live_approval"
    assert payload["schedule"] == "hourly"
    assert payload["marketplace_routing"] == "approval gated"
    assert payload["executor_poll_sec"] == 3.0
    assert payload["executor_max_per_cycle"] == 25
    assert payload["paper_fee_bps"] == 9.0
    assert payload["paper_slippage_bps"] == 4.0
    assert payload["require_keys_for_live"] is False
    assert payload["default_venue"] == "kraken"
    assert payload["default_qty"] == 0.25
    assert payload["order_type"] == "limit"


def test_update_automation_view_persists_runtime_and_settings(monkeypatch) -> None:
    saved_cfg: dict[str, object] = {}

    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})

    def _fake_save(cfg, dry_run=False):
        saved_cfg.update(cfg)
        return True, "Saved"

    monkeypatch.setattr(view_data, "save_user_yaml", _fake_save)
    monkeypatch.setattr(view_data, "update_settings_view", lambda payload: {"ok": True, "data": payload})

    result = view_data.update_automation_view(
        {
            "execution_enabled": True,
            "dry_run_mode": False,
            "default_mode": "live_auto",
            "schedule": "every 15 min",
            "marketplace_routing": "paper only",
            "approval_required_for_live": False,
            "executor_poll_sec": 2.5,
            "executor_max_per_cycle": 42,
            "paper_fee_bps": 11.0,
            "paper_slippage_bps": 6.5,
            "require_keys_for_live": False,
            "default_venue": "kraken",
            "default_qty": 0.5,
            "order_type": "limit",
        }
    )

    assert result["ok"] is True
    execution = saved_cfg["execution"]
    assert execution["executor_mode"] == "live"
    assert execution["live_enabled"] is True
    assert execution["executor_poll_sec"] == 2.5
    assert execution["executor_max_per_cycle"] == 42
    assert execution["paper_fee_bps"] == 11.0
    assert execution["paper_slippage_bps"] == 6.5
    assert execution["require_keys_for_live"] is False
    assert saved_cfg["signals"]["auto_route_to_paper"] is True
    assert saved_cfg["signals"]["default_venue"] == "kraken"
    assert saved_cfg["signals"]["default_qty"] == 0.5
    assert saved_cfg["signals"]["order_type"] == "limit"
    assert saved_cfg["dashboard_ui"]["automation"]["schedule"] == "every 15 min"


def test_update_automation_view_allows_partial_success(monkeypatch) -> None:
    monkeypatch.setattr(view_data, "load_user_yaml", lambda: {})
    monkeypatch.setattr(view_data, "save_user_yaml", lambda cfg, dry_run=False: (True, "Saved"))
    monkeypatch.setattr(view_data, "update_settings_view", lambda payload: {"ok": False, "message": "api down"})

    result = view_data.update_automation_view(
        {
            "execution_enabled": False,
            "dry_run_mode": True,
            "default_mode": "research_only",
            "schedule": "manual",
            "marketplace_routing": "disabled",
            "approval_required_for_live": True,
        }
    )
    assert result["ok"] is True
    assert "sync skipped" in result["message"].lower()
