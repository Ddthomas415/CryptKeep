from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]


class _DummyBlock:
    def __enter__(self) -> "_DummyBlock":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def __getattr__(self, _name: str):
        return lambda *args, **kwargs: None


class _FakeStreamlit:
    def __init__(self, *, overrides: dict[str, Any] | None = None) -> None:
        self.session_state: dict[str, Any] = {}
        self.sidebar = _DummyBlock()
        self._overrides = overrides or {}
        self.button = lambda label, *args, **kwargs: self._overrides.get(str(label), False)

    def __getattr__(self, _name: str):
        return lambda *args, **kwargs: None

    def set_page_config(self, *args, **kwargs) -> None:
        return None

    def columns(self, spec) -> list[_DummyBlock]:
        if isinstance(spec, int):
            count = spec
        else:
            count = len(spec)
        return [_DummyBlock() for _ in range(count)]

    def tabs(self, labels) -> list[_DummyBlock]:
        return [_DummyBlock() for _ in labels]

    def container(self, *args, **kwargs) -> _DummyBlock:
        return _DummyBlock()

    def expander(self, *args, **kwargs) -> _DummyBlock:
        return _DummyBlock()

    def form(self, *args, **kwargs) -> _DummyBlock:
        return _DummyBlock()

    def selectbox(self, label, options, index=0, **kwargs):
        values = list(options)
        return self._overrides.get(str(label), values[index] if values else None)

    def text_input(self, label, value="", **kwargs):
        return self._overrides.get(str(label), value)

    def checkbox(self, label, value=False, **kwargs):
        return self._overrides.get(str(label), value)

    def toggle(self, label, value=False, **kwargs):
        return self._overrides.get(str(label), value)

    def number_input(self, label, value=0, **kwargs):
        return self._overrides.get(str(label), value)

    def form_submit_button(self, label, **kwargs) -> bool:
        return bool(self._overrides.get(str(label), False))


def _noop(*args, **kwargs) -> None:
    return None


def _patch_common_dashboard_renders(monkeypatch) -> None:
    from dashboard.components import activity, asset_detail, badges, cards, header, sidebar, summary_panels, tables

    monkeypatch.setattr(sidebar, "render_app_sidebar", _noop)
    monkeypatch.setattr(header, "render_page_header", _noop)
    monkeypatch.setattr(cards, "render_kpi_cards", _noop)
    monkeypatch.setattr(cards, "render_feature_hero", _noop)
    monkeypatch.setattr(cards, "render_prompt_actions", _noop)
    monkeypatch.setattr(cards, "render_section_intro", _noop)
    monkeypatch.setattr(badges, "render_badge_row", _noop)
    monkeypatch.setattr(tables, "render_table_section", _noop)
    monkeypatch.setattr(activity, "render_activity_panel", _noop)
    monkeypatch.setattr(asset_detail, "render_asset_detail_card", _noop)
    monkeypatch.setattr(asset_detail, "render_evidence_section", _noop)
    monkeypatch.setattr(asset_detail, "render_research_lens", _noop)
    monkeypatch.setattr(asset_detail, "render_focus_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_market_context", _noop)
    monkeypatch.setattr(summary_panels, "render_overview_status_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_signal_thesis", _noop)
    monkeypatch.setattr(summary_panels, "render_portfolio_position_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_trade_failure_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_trades_queue_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_automation_runtime_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_operations_status_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_settings_profile_summary", _noop)


def _load_dashboard_module(
    monkeypatch,
    *,
    relative_path: str,
    module_name: str,
    streamlit_overrides: dict[str, Any] | None = None,
    prepare: Callable[[Any, _FakeStreamlit], None] | None = None,
) -> tuple[ModuleType, _FakeStreamlit]:
    fake_streamlit = _FakeStreamlit(overrides=streamlit_overrides)
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    from dashboard import auth_gate

    monkeypatch.setattr(
        auth_gate,
        "require_authenticated_role",
        lambda required_role="VIEWER": {"ok": True, "role": required_role},
    )
    _patch_common_dashboard_renders(monkeypatch)
    if prepare is not None:
        prepare(monkeypatch, fake_streamlit)

    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module, fake_streamlit


def test_overview_page_requests_selected_focus_asset(monkeypatch) -> None:
    from dashboard.components import focus_selector
    from dashboard.services import view_data

    calls: list[str | None] = []

    def fake_get_overview_view(selected_asset: str | None = None) -> dict[str, Any]:
        calls.append(selected_asset)
        asset = selected_asset or "SOL"
        return {
            "selected_asset": asset,
            "signals": [{"asset": "SOL"}, {"asset": "BTC"}],
            "detail": {
                "asset": asset,
                "signal": "buy",
                "status": "pending_review",
                "confidence": 0.81,
                "price": 200.0,
                "change_24h_pct": 6.5,
            },
            "summary": {
                "mode": "research_only",
                "risk_status": "safe",
                "execution_enabled": False,
                "portfolio": {"total_value": 1000.0, "cash": 300.0, "unrealized_pnl": 25.0},
            },
            "recent_activity": ["Generated explanation for SOL"],
        }

    monkeypatch.setattr(view_data, "get_overview_view", fake_get_overview_view)
    monkeypatch.setattr(
        focus_selector,
        "render_focus_selector",
        lambda *args, **kwargs: ("BTC", "SOL", ["SOL", "BTC"]),
    )

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/app.py",
        module_name="dashboard_test_overview_page",
    )

    assert calls == [None, "BTC"]


def test_markets_page_requests_selected_asset(monkeypatch) -> None:
    from dashboard.components import focus_selector
    from dashboard.services import view_data

    calls: list[str | None] = []

    def fake_get_markets_view(selected_asset: str | None = None) -> dict[str, Any]:
        calls.append(selected_asset)
        asset = selected_asset or "SOL"
        return {
            "selected_asset": asset,
            "watchlist": [{"asset": "SOL"}, {"asset": "ETH"}],
            "detail": {"asset": asset, "price": 187.42, "change_24h_pct": 6.9, "confidence": 0.78},
        }

    monkeypatch.setattr(view_data, "get_markets_view", fake_get_markets_view)
    monkeypatch.setattr(
        focus_selector,
        "render_focus_selector",
        lambda *args, **kwargs: ("ETH", "SOL", ["SOL", "ETH"]),
    )

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/10_Markets.py",
        module_name="dashboard_test_markets_page",
    )

    assert calls == [None, "ETH"]


def test_markets_page_uses_phase1_explain_fallback(monkeypatch) -> None:
    from dashboard.components import asset_detail, focus_selector
    from dashboard.services import view_data

    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        view_data,
        "get_dashboard_summary",
        lambda: {
            "watchlist": [
                {"asset": "BTC", "price": 90000.0, "change_24h_pct": 1.8, "signal": "watch"},
            ]
        },
    )
    monkeypatch.setattr(view_data, "get_recommendations", lambda: [])
    monkeypatch.setattr(view_data, "_request_envelope", lambda path, method="GET", payload=None: None)
    monkeypatch.setattr(
        view_data,
        "_request_envelope_from_base",
        lambda base_url, path, method="GET", payload=None: {
            "ok": True,
            "asset": "BTC",
            "question": "Why is BTC moving?",
            "current_cause": "BTC is firming on spot demand.",
            "past_precedent": "Prior breakouts held when liquidity stayed firm.",
            "future_catalyst": "Macro data later this week could matter.",
            "confidence": 0.72,
            "risk_note": "Research only. Execution disabled.",
            "execution_disabled": True,
            "evidence": [{"type": "market", "source": "coinbase", "summary": "spot support", "relevance": 0.8}],
            "assistant_status": {"provider": "openai", "fallback": False},
        }
        if base_url == view_data.PHASE1_ORCHESTRATOR_URL and path == "/v1/explain" and method == "POST"
        else None,
    )
    monkeypatch.setattr(view_data, "_load_local_market_snapshot", lambda venue, symbol, asset: None)
    monkeypatch.setattr(view_data, "_load_local_ohlcv", lambda venue, symbol, timeframe="1h", limit=24: [])
    monkeypatch.setattr(
        focus_selector,
        "render_focus_selector",
        lambda *args, **kwargs: ("BTC", "BTC", ["BTC"]),
    )

    def _prepare(monkeypatch, _fake_streamlit) -> None:
        monkeypatch.setattr(
            asset_detail,
            "render_asset_detail_card",
            lambda detail, **kwargs: captured.update(detail),
        )

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/10_Markets.py",
        module_name="dashboard_test_markets_phase1_fallback",
        prepare=_prepare,
    )

    assert captured["asset"] == "BTC"
    assert captured["current_cause"] == "BTC is firming on spot demand."
    assert captured["risk_note"] == "Research only. Execution disabled."
    assert captured["execution_disabled"] is True


def test_signals_page_requests_selected_asset(monkeypatch) -> None:
    from dashboard.components import focus_selector
    from dashboard.services import view_data

    calls: list[str | None] = []

    def fake_get_signals_view(selected_asset: str | None = None) -> dict[str, Any]:
        calls.append(selected_asset)
        asset = selected_asset or "SOL"
        return {
            "selected_asset": asset,
            "signals": [{"asset": "SOL"}, {"asset": "BTC"}],
            "detail": {"asset": asset, "signal": "buy", "status": "pending_review", "confidence": 0.74},
        }

    monkeypatch.setattr(view_data, "get_signals_view", fake_get_signals_view)
    monkeypatch.setattr(
        focus_selector,
        "render_focus_selector",
        lambda *args, **kwargs: ("BTC", "SOL", ["SOL", "BTC"]),
    )

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/30_Signals.py",
        module_name="dashboard_test_signals_page",
    )

    assert calls == [None, "BTC"]


def test_portfolio_page_fetches_view_on_import(monkeypatch) -> None:
    from dashboard.services import view_data

    calls: list[bool] = []

    def fake_get_portfolio_view() -> dict[str, Any]:
        calls.append(True)
        return {
            "currency": "USD",
            "portfolio": {"total_value": 1000.0, "cash": 300.0, "unrealized_pnl": 25.0},
            "positions": [{"asset": "BTC"}],
        }

    monkeypatch.setattr(view_data, "get_portfolio_view", fake_get_portfolio_view)

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/20_Portfolio.py",
        module_name="dashboard_test_portfolio_page",
    )

    assert calls == [True]


def test_trades_page_fetches_view_on_import(monkeypatch) -> None:
    from dashboard.services import view_data

    calls: list[bool] = []

    def fake_get_trades_view() -> dict[str, Any]:
        calls.append(True)
        return {
            "approval_required": True,
            "pending_approvals": [{"asset": "SOL"}],
            "open_orders": [{"asset": "BTC"}],
            "failed_orders": [{"asset": "ETH"}],
            "recent_fills": [{"asset": "BTC"}],
        }

    monkeypatch.setattr(view_data, "get_trades_view", fake_get_trades_view)

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/40_Trades.py",
        module_name="dashboard_test_trades_page",
    )

    assert calls == [True]


def test_automation_page_builds_save_payload(monkeypatch) -> None:
    from dashboard.components import forms
    from dashboard.services import view_data

    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        view_data,
        "get_automation_view",
        lambda: {
            "execution_enabled": False,
            "dry_run_mode": True,
            "default_mode": "paper",
            "schedule": "manual",
            "marketplace_routing": "disabled",
            "approval_required_for_live": True,
            "executor_poll_sec": 1.5,
            "executor_max_per_cycle": 10,
            "paper_fee_bps": 7.0,
            "paper_slippage_bps": 2.0,
            "require_keys_for_live": True,
            "default_venue": "coinbase",
            "default_qty": 0.001,
            "order_type": "market",
            "config_path": "/tmp/runtime.yml",
            "executor_mode": "paper",
            "live_enabled": False,
        },
    )
    monkeypatch.setattr(forms, "render_save_action", lambda **kwargs: captured.update(kwargs))

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/50_Automation.py",
        module_name="dashboard_test_automation_page",
        streamlit_overrides={
            "Enable automation": True,
            "Dry run mode": False,
            "Default mode": "live_approval",
            "Schedule": "hourly",
            "Marketplace routing": "approval gated",
            "Require approval for live actions": True,
            "Executor poll (sec)": 3.0,
            "Max intents per cycle": 25,
            "Paper fee (bps)": 9.0,
            "Paper slippage (bps)": 4.0,
            "Require keys for live": True,
            "Default signal quantity": 0.25,
            "Default signal venue": "kraken",
            "Signal order type": "limit",
        },
    )

    assert captured["button_label"] == "Save automation settings"
    assert captured["payload"] == {
        "execution_enabled": True,
        "dry_run_mode": False,
        "default_mode": "live_approval",
        "schedule": "hourly",
        "marketplace_routing": "approval gated",
        "approval_required_for_live": True,
        "executor_poll_sec": 3.0,
        "executor_max_per_cycle": 25,
        "paper_fee_bps": 9.0,
        "paper_slippage_bps": 4.0,
        "require_keys_for_live": True,
        "default_venue": "kraken",
        "default_qty": 0.25,
        "order_type": "limit",
    }


def test_settings_page_builds_save_payload(monkeypatch) -> None:
    from dashboard.components import forms
    from dashboard.services import view_data

    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        view_data,
        "get_settings_view",
        lambda: {
            "general": {
                "timezone": "America/New_York",
                "default_currency": "USD",
                "startup_page": "/dashboard",
                "default_mode": "research_only",
                "watchlist_defaults": ["BTC", "ETH"],
            },
            "notifications": {
                "email": False,
                "email_enabled": False,
                "email_address": "",
                "delivery_mode": "instant",
                "daily_digest_enabled": True,
                "weekly_digest_enabled": True,
                "confidence_threshold": 0.72,
                "opportunity_threshold": 0.7,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "06:00",
                "telegram": True,
                "categories": {
                    "top_opportunities": True,
                    "paper_trade_opened": True,
                    "paper_trade_closed": True,
                    "macro_events": True,
                    "provider_failures": True,
                    "daily_summary": True,
                    "weekly_summary": True,
                },
            },
            "ai": {
                "explanation_length": "normal",
                "tone": "balanced",
                "evidence_verbosity": "standard",
                "show_evidence": True,
                "show_confidence": True,
                "include_archives": True,
                "include_onchain": True,
                "allow_hypotheses": True,
                "provider_assisted_explanations": True,
                "autopilot_explanation_depth": "standard",
                "away_summary_mode": "prioritized",
            },
            "autopilot": {
                "autopilot_enabled": False,
                "scout_mode_enabled": True,
                "paper_trading_enabled": True,
                "learning_enabled": False,
                "scan_interval_minutes": 15,
                "candidate_limit": 12,
                "confidence_threshold": 0.72,
                "alert_threshold": 0.8,
                "default_market_universe": "core_watchlist",
                "enabled_asset_classes": ["crypto"],
                "exclusion_list": [],
                "digest_frequency": "daily",
            },
            "providers": {
                "coingecko": {
                    "enabled": True,
                    "api_key": "",
                    "status": "ready",
                    "role": "Crypto breadth",
                    "last_sync": "Starter dataset",
                },
                "smtp": {
                    "enabled": False,
                    "api_key": "",
                    "status": "local",
                    "role": "Email delivery",
                    "last_sync": "Configure host",
                },
            },
            "paper_trading": {
                "enabled": True,
                "fee_bps": 7.0,
                "slippage_bps": 2.0,
                "approval_required": True,
                "max_position_size_usd": 5000.0,
                "max_daily_loss_pct": 2.0,
            },
            "security": {
                "session_timeout_minutes": 60,
                "secret_masking": True,
                "audit_export_allowed": True,
            },
        },
    )
    monkeypatch.setattr(forms, "render_save_action", lambda **kwargs: captured.update(kwargs))

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/70_Settings.py",
        module_name="dashboard_test_settings_page",
        streamlit_overrides={
            "Timezone": "UTC",
            "Default currency": "EUR",
            "Default mode": "paper",
            "Startup page": "/signals",
            "Watchlist defaults (comma separated)": "btc, sol, link",
            "Email enabled": True,
            "Notification email": "desk@example.com",
            "Delivery mode": "digest",
            "Daily digest": False,
            "Weekly digest": True,
            "Confidence threshold": 0.81,
            "Opportunity threshold": 0.76,
            "Quiet hours start": "21:30",
            "Quiet hours end": "07:15",
            "Top opportunities": False,
            "Paper trade opened": False,
            "Paper trade closed": True,
            "Macro events": False,
            "Provider / system failures": True,
            "Daily summary": False,
            "Weekly summary": True,
            "Telegram channel": False,
            "Explanation length": "detailed",
            "Explanation tone": "concise",
            "Evidence verbosity": "deep",
            "\"While away\" summary mode": "detailed",
            "Autopilot explanation depth": "operator",
            "Show evidence": True,
            "Show confidence": False,
            "Use archive context": False,
            "Use on-chain context": True,
            "Provider-assisted explanations": False,
            "Allow hypotheses": False,
            "Autopilot enabled": True,
            "Scout mode enabled": False,
            "Paper trading enabled": False,
            "Learning enabled": True,
            "Scan interval (minutes)": 30,
            "Candidate limit": 20,
            "Scout confidence threshold": 0.84,
            "Scout alert threshold": 0.88,
            "Default market universe": "cross_asset",
            "Digest frequency": "weekly",
            "Crypto": True,
            "Equities": True,
            "ETFs": True,
            "Forex": False,
            "Commodities": True,
            "Exclusion list (comma separated)": "doge, pepe",
            "Enabled": True,
            "API key / credential": "smtp-secret",
            "Role / priority": "Alerts",
            "Status note": "Healthy",
            "Session timeout (minutes)": 90,
            "Secret masking": False,
            "Audit export allowed": False,
            "Paper trading default": False,
            "Paper fee (bps)": 9.5,
            "Paper slippage (bps)": 3.5,
            "Approval required for live handoff": False,
            "Max position size (USD)": 7500.0,
            "Max daily loss (%)": 1.5,
        },
    )

    assert captured["button_label"] == "Save settings"
    assert captured["payload"]["general"] == {
        "timezone": "UTC",
        "default_currency": "EUR",
        "startup_page": "/signals",
        "default_mode": "paper",
        "watchlist_defaults": ["BTC", "SOL", "LINK"],
    }
    assert captured["payload"]["notifications"]["email_enabled"] is True
    assert captured["payload"]["notifications"]["email_address"] == "desk@example.com"
    assert captured["payload"]["notifications"]["delivery_mode"] == "digest"
    assert captured["payload"]["notifications"]["confidence_threshold"] == 0.81
    assert captured["payload"]["notifications"]["categories"] == {
        "top_opportunities": False,
        "paper_trade_opened": False,
        "paper_trade_closed": True,
        "macro_events": False,
        "provider_failures": True,
        "daily_summary": False,
        "weekly_summary": True,
    }
    assert captured["payload"]["ai"]["tone"] == "concise"
    assert captured["payload"]["ai"]["evidence_verbosity"] == "deep"
    assert captured["payload"]["ai"]["provider_assisted_explanations"] is False
    assert captured["payload"]["autopilot"] == {
        "autopilot_enabled": True,
        "scout_mode_enabled": False,
        "paper_trading_enabled": False,
        "learning_enabled": True,
        "scan_interval_minutes": 30,
        "candidate_limit": 20,
        "confidence_threshold": 0.84,
        "alert_threshold": 0.88,
        "default_market_universe": "cross_asset",
        "enabled_asset_classes": ["crypto", "equities", "etf", "commodities"],
        "exclusion_list": ["DOGE", "PEPE"],
        "digest_frequency": "weekly",
    }
    assert captured["payload"]["providers"]["smtp"]["enabled"] is True
    assert captured["payload"]["providers"]["smtp"]["api_key"] == "smtp-secret"
    assert captured["payload"]["providers"]["smtp"]["role"] == "Alerts"
    assert captured["payload"]["paper_trading"] == {
        "enabled": False,
        "fee_bps": 9.5,
        "slippage_bps": 3.5,
        "approval_required": False,
        "max_position_size_usd": 7500.0,
        "max_daily_loss_pct": 1.5,
    }
    assert captured["payload"]["security"] == {
        "session_timeout_minutes": 90,
        "secret_masking": False,
        "audit_export_allowed": False,
    }
