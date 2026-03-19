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

    def slider(self, label, min_value=None, max_value=None, value=None, **kwargs):
        return self._overrides.get(str(label), value)

    def form_submit_button(self, label, **kwargs) -> bool:
        return bool(self._overrides.get(str(label), False))


def _noop(*args, **kwargs) -> None:
    return None


def _patch_common_dashboard_renders(monkeypatch) -> None:
    from dashboard.components import activity, asset_detail, badges, cards, digest, header, logs, sidebar, summary_panels, tables

    monkeypatch.setattr(sidebar, "render_app_sidebar", _noop)
    monkeypatch.setattr(header, "render_page_header", _noop)
    monkeypatch.setattr(cards, "render_kpi_cards", _noop)
    monkeypatch.setattr(cards, "render_feature_hero", _noop)
    monkeypatch.setattr(cards, "render_prompt_actions", _noop)
    monkeypatch.setattr(cards, "render_section_intro", _noop)
    monkeypatch.setattr(badges, "render_badge_row", _noop)
    monkeypatch.setattr(tables, "render_table_section", _noop)
    monkeypatch.setattr(logs, "render_action_result", _noop)
    monkeypatch.setattr(activity, "render_activity_panel", _noop)
    monkeypatch.setattr(asset_detail, "render_asset_detail_card", _noop)
    monkeypatch.setattr(asset_detail, "render_evidence_section", _noop)
    monkeypatch.setattr(asset_detail, "render_research_lens", _noop)
    monkeypatch.setattr(asset_detail, "render_focus_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_market_context", _noop)
    monkeypatch.setattr(summary_panels, "render_collector_runtime_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_home_digest_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_overview_status_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_structural_edge_digest_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_structural_edge_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_structural_edge_health_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_signal_thesis", _noop)
    monkeypatch.setattr(summary_panels, "render_portfolio_position_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_trade_failure_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_trades_queue_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_automation_runtime_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_operations_status_summary", _noop)
    monkeypatch.setattr(summary_panels, "render_settings_profile_summary", _noop)
    monkeypatch.setattr(digest, "render_digest_page_header", _noop)
    monkeypatch.setattr(digest, "render_runtime_truth_strip", _noop)
    monkeypatch.setattr(digest, "render_attention_now", _noop)
    monkeypatch.setattr(digest, "render_leaderboard_summary", _noop)
    monkeypatch.setattr(digest, "render_scorecard_snapshot", _noop)
    monkeypatch.setattr(digest, "render_crypto_edge_summary", _noop)
    monkeypatch.setattr(digest, "render_safety_warnings", _noop)
    monkeypatch.setattr(digest, "render_mode_truth_card", _noop)
    monkeypatch.setattr(digest, "render_freshness_panel", _noop)
    monkeypatch.setattr(digest, "render_recent_incidents", _noop)
    monkeypatch.setattr(digest, "render_next_best_action", _noop)


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
    from dashboard.services.digest import builders as home_digest
    from dashboard.services import crypto_edge_research
    from dashboard.services import view_data

    calls: list[str | None] = []
    collector_calls: list[bool] = []
    health_calls: list[bool] = []
    digest_calls: list[bool] = []
    home_digest_calls: list[dict[str, Any]] = []

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
        crypto_edge_research,
        "load_latest_live_crypto_edge_snapshot",
        lambda: {
            "ok": True,
            "has_any_data": True,
            "has_live_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Fresh",
        },
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_collector_runtime",
        lambda: collector_calls.append(True)
        or {
            "ok": True,
            "has_status": True,
            "status": "running",
            "freshness": "Fresh",
            "writes": 2,
            "errors": 0,
        },
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_staleness_summary",
        lambda: health_calls.append(True) or {"ok": True, "needs_attention": False, "severity": "ok"},
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_staleness_digest",
        lambda: digest_calls.append(True)
        or {
            "ok": True,
            "needs_attention": False,
            "severity": "ok",
            "headline": "Structural-edge data is current",
            "while_away_summary": "Live structural-edge data is fresh and the collector loop is reporting normally.",
        },
    )
    monkeypatch.setattr(
        home_digest,
        "load_home_digest",
        lambda summary=None: home_digest_calls.append(dict(summary or {}))
        or {
            "as_of": "2026-03-18T12:00:00Z",
            "page_status": {"state": "ok", "caveat": None},
            "claim_boundaries": [],
            "runtime_truth": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "mode": {"value": "Paper", "label": "Runtime Mode", "state": "ok", "caveat": None, "age_seconds": None},
                "live_order_authority": {"value": "Healthy", "label": "Live-Order Authority", "state": "ok", "caveat": None, "age_seconds": None},
                "kill_switch": {"value": "Disarmed", "label": "Kill Switch", "state": "ok", "caveat": None, "age_seconds": None},
                "collector_freshness": {"value": "Fresh", "label": "Collector Freshness", "state": "ok", "caveat": None, "age_seconds": 0},
                "leaderboard_age": {"value": "Just Built", "label": "Leaderboard Age", "state": "warn", "caveat": None, "age_seconds": 0},
                "copilot_trust_layer": {"value": "Partial", "label": "Copilot Trust Layer", "state": "warn", "caveat": None, "age_seconds": None},
            },
            "attention_now": {"as_of": "2026-03-18T12:00:00Z", "caveat": None, "source_name": "test", "source_age_seconds": 0, "items": []},
            "leaderboard_summary": {"as_of": "2026-03-18T12:00:00Z", "caveat": None, "source_name": "test", "source_age_seconds": 0, "rows": []},
            "scorecard_snapshot": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "highlights": {
                    "best_post_cost": {"label": "Best post-cost performer", "strategy_name": None, "value": None, "context": None, "state": "unknown", "caveat": None},
                    "lowest_drawdown": {"label": "Lowest drawdown", "strategy_name": None, "value": None, "context": None, "state": "unknown", "caveat": None},
                    "most_regime_fragile": {"label": "Most regime-fragile", "strategy_name": None, "value": None, "context": None, "state": "unknown", "caveat": None},
                    "most_slippage_sensitive": {"label": "Most slippage-sensitive", "strategy_name": None, "value": None, "context": None, "state": "unknown", "caveat": None},
                    "most_stable": {"label": "Most stable", "strategy_name": None, "value": None, "context": None, "state": "unknown", "caveat": None},
                    "most_changed": {"label": "Most changed", "strategy_name": None, "value": None, "context": None, "state": "unknown", "caveat": None},
                },
            },
            "crypto_edge_summary": {"as_of": "2026-03-18T12:00:00Z", "caveat": None, "source_name": "test", "source_age_seconds": 0, "rows": []},
            "safety_warnings": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "items": [],
                "live_boundary_status": "healthy",
                "kill_switch_state": "disarmed",
            },
            "freshness_panel": {"as_of": "2026-03-18T12:00:00Z", "caveat": None, "source_name": "test", "source_age_seconds": 0, "rows": []},
            "mode_truth": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "current_mode": "paper",
                "label": "Paper",
                "allowed": ["paper execution"],
                "blocked": ["real live submission"],
                "promotion_blockers": [],
            },
            "recent_incidents": {"as_of": "2026-03-18T12:00:00Z", "caveat": None, "source_name": "test", "source_age_seconds": 0, "items": []},
            "next_best_action": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "title": "Review paper mode",
                "why": "Digest test stub.",
                "recommended_action": "None.",
                "secondary_actions": [],
                "source": "test",
            },
        },
    )
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
    assert collector_calls == [True]
    assert health_calls == [True]
    assert digest_calls == [True]
    assert len(home_digest_calls) == 1
    assert home_digest_calls[0].get("mode") == "research_only"


def test_home_page_builds_digest(monkeypatch) -> None:
    from dashboard.services.digest import builders as home_digest

    digest_calls: list[bool] = []

    monkeypatch.setattr(
        home_digest,
        "build_home_digest",
        lambda: digest_calls.append(True)
        or {
            "as_of": "2026-03-18T12:00:00Z",
            "page_status": {"state": "warn", "caveat": "Collector freshness needs review."},
            "claim_boundaries": [],
            "runtime_truth": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "mode": {"value": "Paper", "label": "Runtime Mode", "state": "ok", "caveat": None, "age_seconds": None},
                "live_order_authority": {"value": "Healthy", "label": "Live-Order Authority", "state": "ok", "caveat": None, "age_seconds": None},
                "kill_switch": {"value": "Disarmed", "label": "Kill Switch", "state": "ok", "caveat": None, "age_seconds": None},
                "collector_freshness": {"value": "Aging", "label": "Collector Freshness", "state": "warn", "caveat": "Live-public data is aging.", "age_seconds": 4200},
                "leaderboard_age": {"value": "Just Built", "label": "Leaderboard Age", "state": "warn", "caveat": "Synthetic benchmark", "age_seconds": 0},
                "copilot_trust_layer": {"value": "Partial", "label": "Copilot Trust Layer", "state": "warn", "caveat": "Answer strips not universal.", "age_seconds": None},
            },
            "attention_now": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "items": [
                    {
                        "id": "attention-1",
                        "severity": "important",
                        "title": "Collector freshness needs attention",
                        "why_it_matters": "Research freshness is aging.",
                        "next_action": "Review the read-only collector loop.",
                        "source": "collector",
                        "as_of": "2026-03-18T12:00:00Z",
                        "link_target": "/Research",
                    }
                ],
            },
            "leaderboard_summary": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "rows": [
                    {
                        "strategy_id": "ema_cross",
                        "name": "Ema Cross Default",
                        "rank": 1,
                        "score": 0.72,
                        "score_label": "0.72",
                        "post_cost_return_pct": 4.2,
                        "max_drawdown_pct": 1.4,
                        "best_regime": "bull",
                        "worst_regime": "chop",
                        "paper_live_drift": "low",
                        "recommendation": "keep",
                        "as_of": "2026-03-18T12:00:00Z",
                        "caveat": "Synthetic benchmark row.",
                    }
                ],
            },
            "scorecard_snapshot": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "highlights": {
                    "best_post_cost": {"label": "Best post-cost performer", "strategy_name": "Ema Cross Default", "value": "+4.2%", "context": "after fees/slippage", "state": "ok", "caveat": None},
                    "lowest_drawdown": {"label": "Lowest drawdown", "strategy_name": "Ema Cross Default", "value": "1.4%", "context": "peak-to-trough loss", "state": "ok", "caveat": None},
                    "most_regime_fragile": {"label": "Most regime-fragile", "strategy_name": "Breakout Default", "value": "0.42", "context": "regime robustness", "state": "warn", "caveat": None},
                    "most_slippage_sensitive": {"label": "Most slippage-sensitive", "strategy_name": "Breakout Default", "value": "3.8%", "context": "return loss under stressed slippage", "state": "warn", "caveat": None},
                    "most_stable": {"label": "Most stable", "strategy_name": "Ema Cross Default", "value": "0.81", "context": "robustness across represented regimes", "state": "ok", "caveat": None},
                    "most_changed": {"label": "Most changed", "strategy_name": None, "value": None, "context": None, "state": "unknown", "caveat": "No persisted delta stream yet."},
                },
            },
            "crypto_edge_summary": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "rows": [
                    {"module_id": "funding", "name": "Funding analytics", "status": "aging", "last_update_ts": "2026-03-18T11:00:00Z", "age_seconds": 3600, "summary": "Bias Positive / carry 8.40%", "caveat": None}
                ],
            },
            "safety_warnings": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "items": [
                    {"severity": "watch", "title": "Structural research freshness is degraded", "summary": "Funding data is aging.", "source": "collector", "as_of": "2026-03-18T12:00:00Z", "caveat": None}
                ],
                "live_boundary_status": "healthy",
                "kill_switch_state": "disarmed",
            },
            "freshness_panel": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "rows": [
                    {"source_id": "collector_loop", "name": "Collector loop", "status": "aging", "last_update_ts": "2026-03-18T11:00:00Z", "age_seconds": 3600, "caveat": "Collector is aging."}
                ],
            },
            "mode_truth": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "current_mode": "paper",
                "label": "Paper",
                "allowed": ["paper execution", "research analytics"],
                "blocked": ["sandbox live submission", "real live submission"],
                "promotion_blockers": [],
            },
            "recent_incidents": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "items": [
                    {"id": "incident-1", "ts": "2026-03-18T12:00:00Z", "severity": "watch", "title": "Collector loop aging", "summary": "Funding freshness is aging.", "source": "collector"}
                ],
            },
            "next_best_action": {
                "as_of": "2026-03-18T12:00:00Z",
                "caveat": None,
                "source_name": "test",
                "source_age_seconds": 0,
                "title": "Review collector freshness",
                "why": "Structural-edge freshness is aging.",
                "recommended_action": "Inspect and restart the read-only collector loop if needed.",
                "secondary_actions": ["Review the latest funding snapshot."],
                "source": "collector",
            },
        },
    )

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/00_Home.py",
        module_name="dashboard_test_home_page",
    )

    assert digest_calls == [True]


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


def test_research_page_fetches_workspace_on_import(monkeypatch) -> None:
    from dashboard.services import crypto_edge_research
    from dashboard.services import operator as operator_service

    workspace_calls: list[int] = []
    live_calls: list[bool] = []
    runtime_calls: list[bool] = []
    digest_calls: list[bool] = []

    def fake_load_crypto_edge_workspace(*, history_limit: int = 5) -> dict[str, Any]:
        workspace_calls.append(history_limit)
        return {
            "ok": True,
            "has_any_data": True,
            "store_path": "/tmp/crypto_edge_research.sqlite",
            "data_origin_label": "Live Public",
            "freshness_summary": "Fresh",
            "funding_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "basis_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "quote_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "funding": {"count": 1, "annualized_carry_pct": 12.0, "dominant_bias": "long_pays", "rows": [{"symbol": "BTC-PERP"}]},
            "basis": {"count": 1, "avg_basis_bps": 8.0, "widest_basis_bps": 8.0, "rows": [{"symbol": "BTC-PERP"}]},
            "dislocations": {"count": 1, "positive_count": 1, "top_dislocation": {"symbol": "BTC/USD", "gross_cross_bps": 6.0}, "rows": [{"symbol": "BTC/USD"}]},
            "history_rows": [{"kind": "quotes", "snapshot_id": "quotes-1", "capture_ts": "2026-03-18T10:00:00Z", "source": "sample_bundle", "row_count": 6}],
            "provenance_rows": [{"theme": "funding", "source": "Live Public", "capture_ts": "2026-03-18T10:00:00Z", "freshness": "Fresh"}],
            "funding_history": [{"capture_ts": "2026-03-18T10:00:00Z", "annualized_carry_pct": 12.0, "dominant_bias": "long_pays"}],
            "basis_history": [{"capture_ts": "2026-03-18T10:00:00Z", "avg_basis_bps": 8.0, "widest_basis_bps": 8.0}],
            "dislocation_history": [{"capture_ts": "2026-03-18T10:00:00Z", "positive_count": 1, "top_symbol": "BTC/USD", "top_gross_cross_bps": 6.0}],
            "trend_rows": [{"theme": "funding", "latest": "12.00%", "vs_prior": "No prior snapshot"}],
        }

    def fake_load_latest_live_crypto_edge_snapshot() -> dict[str, Any]:
        live_calls.append(True)
        return {
            "ok": True,
            "has_any_data": True,
            "has_live_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Recent",
            "funding": {"dominant_bias": "long_pays"},
            "basis": {"avg_basis_bps": 7.5},
            "dislocations": {"positive_count": 2, "top_dislocation": {"symbol": "BTC/USD"}},
            "summary_text": "Live Public snapshot shows funding bias long_pays.",
        }

    def fake_load_crypto_edge_collector_runtime() -> dict[str, Any]:
        runtime_calls.append(True)
        return {
            "ok": True,
            "has_status": True,
            "status": "running",
            "source_label": "Live Public",
            "freshness": "Fresh",
            "loops": 2,
            "writes": 2,
            "errors": 0,
            "last_reason": "collected",
            "summary_text": "Collector status running.",
        }

    def fake_load_crypto_edge_staleness_digest() -> dict[str, Any]:
        digest_calls.append(True)
        return {
            "ok": True,
            "needs_attention": False,
            "severity": "ok",
            "headline": "Structural-edge data is current",
            "while_away_summary": "Live structural-edge data is fresh and the collector loop is reporting normally.",
        }

    monkeypatch.setattr(crypto_edge_research, "load_crypto_edge_workspace", fake_load_crypto_edge_workspace)
    monkeypatch.setattr(
        crypto_edge_research,
        "load_latest_live_crypto_edge_snapshot",
        fake_load_latest_live_crypto_edge_snapshot,
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_collector_runtime",
        fake_load_crypto_edge_collector_runtime,
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_staleness_digest",
        fake_load_crypto_edge_staleness_digest,
    )
    monkeypatch.setattr(
        operator_service,
        "start_repo_script_background",
        lambda script_relpath, args=None: (0, "started"),
    )
    monkeypatch.setattr(
        operator_service,
        "run_repo_script",
        lambda script_relpath, args=None: (0, "stopped"),
    )

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/35_Research.py",
        module_name="dashboard_test_research_page",
    )

    assert workspace_calls == [5]
    assert live_calls == [True]
    assert runtime_calls == [True]
    assert digest_calls == [True]


def test_research_page_starts_collector_loop_from_dashboard(monkeypatch) -> None:
    from dashboard.services import crypto_edge_research
    from dashboard.services import operator as operator_service

    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_workspace",
        lambda history_limit=5: {
            "ok": True,
            "has_any_data": False,
            "data_origin_label": "No Snapshots",
            "freshness_summary": "Unknown",
        },
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_latest_live_crypto_edge_snapshot",
        lambda: {"ok": True, "has_live_data": False, "freshness_summary": "Unknown"},
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_collector_runtime",
        lambda: {"ok": True, "has_status": False, "status": "not_started", "freshness": "Unknown"},
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_staleness_digest",
        lambda: {"ok": True, "needs_attention": True, "severity": "warn", "headline": "Structural-edge data needs attention"},
    )
    monkeypatch.setattr(
        operator_service,
        "start_crypto_edge_collector_loop",
        lambda interval_sec, plan_file="sample_data/crypto_edges/live_collector_plan.json": captured.update({"interval_sec": interval_sec, "plan_file": plan_file}) or (0, "started"),
    )
    monkeypatch.setattr(
        operator_service,
        "stop_crypto_edge_collector_loop",
        lambda: (0, "stopped"),
    )

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/35_Research.py",
        module_name="dashboard_test_research_start_collector",
        streamlit_overrides={
            "Collector Loop Interval (sec)": 900.0,
            "Start Live Collector Loop": True,
        },
    )

    assert captured["plan_file"] == "sample_data/crypto_edges/live_collector_plan.json"
    assert captured["interval_sec"] == 900.0


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


def test_operations_page_runs_strategy_workbench(monkeypatch) -> None:
    from dashboard.components import actions, logs
    from dashboard.services import crypto_edge_research
    from dashboard.services import operator as operator_service
    from dashboard.services import operator_tools, strategy_evaluation
    from services.admin import config_editor, repair_wizard
    from services.execution import idempotency_inspector
    from services.strategies import config_tools, presets

    collector_calls: list[bool] = []

    monkeypatch.setattr(actions, "render_system_action_buttons", lambda: None)
    monkeypatch.setattr(logs, "render_action_result", _noop)
    monkeypatch.setattr(
        operator_service,
        "get_operations_snapshot",
        lambda: {
            "tracked_services": 5,
            "healthy_services": 4,
            "unknown_services": 1,
            "attention_services": 1,
            "last_health_ts": "2026-03-18T10:00:00Z",
        },
    )
    monkeypatch.setattr(operator_service, "list_services", lambda: ["tick_publisher"])
    monkeypatch.setattr(operator_service, "run_op", lambda args: (0, "ok"))
    monkeypatch.setattr(operator_service, "run_repo_script", lambda script, args=None: (0, "{}"))
    monkeypatch.setattr(
        config_editor,
        "load_user_yaml",
        lambda: {"strategy": {"name": "ema_cross", "trade_enabled": True, "ema_fast": 12, "ema_slow": 26}},
    )
    monkeypatch.setattr(config_editor, "save_user_yaml", lambda cfg: (True, "saved"))
    monkeypatch.setattr(config_tools, "supported_strategies", lambda: ["ema_cross", "mean_reversion_rsi", "breakout_donchian"])
    monkeypatch.setattr(
        config_tools,
        "build_strategy_block",
        lambda name, trade_enabled, params: {"name": name, "trade_enabled": trade_enabled, **params},
    )
    monkeypatch.setattr(config_tools, "apply_strategy_block", lambda cfg, block: {**cfg, "strategy": dict(block)})
    monkeypatch.setattr(config_tools, "validate_cfg", lambda cfg: {"ok": True, "errors": [], "warnings": []})
    monkeypatch.setattr(config_tools, "apply_preset_and_validate", lambda cfg, preset: (cfg, {"ok": True, "errors": [], "warnings": []}))
    monkeypatch.setattr(presets, "list_presets", lambda: ["ema_cross_default"])
    monkeypatch.setattr(operator_tools, "synthetic_ohlcv", lambda count: [[1, 100, 101, 99, 100, 1.0]] * max(int(count), 1))
    monkeypatch.setattr(idempotency_inspector, "list_recent", lambda limit=10, status="error": {"ok": True, "rows": [], "path": "/tmp/db", "table": "idempotency"})
    monkeypatch.setattr(idempotency_inspector, "filter_rows", lambda rows, venue_filter, symbol_filter: [])
    monkeypatch.setattr(repair_wizard, "preflight_self_check", lambda: {"ok": True})
    monkeypatch.setattr(repair_wizard, "preview_reset", lambda include_locks=False: {"ok": True, "include_locks": include_locks})
    monkeypatch.setattr(repair_wizard, "execute_reset", lambda confirm_text="", include_locks=False: {"ok": False, "reason": "not_confirmed"})
    monkeypatch.setattr(
        strategy_evaluation,
        "build_strategy_workbench",
        lambda **kwargs: {
            "ok": True,
            "backtest": {
                "ok": True,
                "strategy": "ema_cross",
                "trade_count": 2,
                "metrics": {"final_equity": 10250.0, "total_return_pct": 2.5, "max_drawdown_pct": 1.2},
                "trades": [{"ts_ms": 1, "action": "buy"}],
                "equity": [{"equity": 10000.0}, {"equity": 10250.0}],
                "scorecard": {
                    "net_return_after_costs_pct": 2.5,
                    "max_drawdown_pct": 1.2,
                    "profit_factor": 1.4,
                    "expectancy": 5.0,
                    "closed_trades": 1,
                    "regime_scorecards": {},
                },
                "regime_scorecards": {
                    "bull": {
                        "bars": 10,
                        "net_return_after_costs_pct": 2.5,
                        "max_drawdown_pct": 1.2,
                        "win_rate_pct": 100.0,
                        "profit_factor": 1.4,
                        "expectancy": 5.0,
                        "closed_trades": 1,
                    }
                },
            },
            "leaderboard": {
                "ok": True,
                "candidate_count": 1,
                "rows": [
                    {
                        "rank": 1,
                        "candidate": "ema_cross_default",
                        "strategy": "ema_cross",
                        "leaderboard_score": 0.9,
                        "net_return_after_costs_pct": 2.5,
                        "max_drawdown_pct": 1.2,
                        "regime_robustness": 1.0,
                        "regime_return_dispersion_pct": 0.0,
                        "slippage_sensitivity_pct": 0.4,
                        "paper_live_drift_pct": None,
                    }
                ],
            },
            "hypothesis": {
                "strategy": "ema_cross",
                "expected_failure_regimes": ["low_vol"],
                "market_assumption": "trend persistence",
                "entry_rules": ["cross up"],
                "exit_rules": ["cross down"],
                "no_trade_rules": ["weak volume"],
                "invalidation_conditions": ["wrong-side slow ema"],
                "notes": ["not proven"],
            },
        },
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_report",
        lambda: {
            "ok": True,
            "has_any_data": True,
            "store_path": "/tmp/crypto_edge_research.sqlite",
            "funding_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "basis_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "quote_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "funding": {"count": 1, "annualized_carry_pct": 12.0, "dominant_bias": "long_pays", "rows": [{"symbol": "BTC-PERP"}]},
            "basis": {"count": 1, "avg_basis_bps": 8.0, "widest_basis_bps": 8.0, "rows": [{"symbol": "BTC-PERP"}]},
            "dislocations": {"count": 1, "positive_count": 1, "top_dislocation": {"symbol": "BTC/USD", "gross_cross_bps": 6.0}, "rows": [{"symbol": "BTC/USD"}]},
        },
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_latest_live_crypto_edge_snapshot",
        lambda: {
            "ok": True,
            "has_any_data": True,
            "has_live_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Recent",
            "funding": {"dominant_bias": "long_pays", "annualized_carry_pct": 12.0},
            "basis": {"avg_basis_bps": 8.0, "widest_basis_bps": 8.0},
            "dislocations": {"positive_count": 1, "top_dislocation": {"symbol": "BTC/USD"}},
            "summary_text": "Live Public snapshot shows funding bias long_pays.",
        },
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_collector_runtime",
        lambda: collector_calls.append(True)
        or {
            "ok": True,
            "has_status": True,
            "status": "running",
            "freshness": "Recent",
            "source_label": "Live Public",
            "writes": 3,
            "errors": 0,
        },
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_staleness_summary",
        lambda: {"ok": True, "needs_attention": False, "severity": "ok"},
    )

    _module, fake_streamlit = _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/60_Operations.py",
        module_name="dashboard_test_operations_page",
        streamlit_overrides={"Run Backtest Parity": True},
    )

    assert fake_streamlit.session_state["ops_ih6_workbench"]["ok"] is True
    assert fake_streamlit.session_state["ops_ih6_result"]["strategy"] == "ema_cross"
    assert collector_calls == [True]


def test_operations_page_starts_collector_loop(monkeypatch) -> None:
    from dashboard.components import actions, logs
    from dashboard.services import crypto_edge_research
    from dashboard.services import operator as operator_service
    from dashboard.services import operator_tools, strategy_evaluation
    from services.admin import config_editor, repair_wizard
    from services.execution import idempotency_inspector
    from services.strategies import config_tools, presets

    captured: dict[str, Any] = {}

    monkeypatch.setattr(actions, "render_system_action_buttons", lambda: None)
    monkeypatch.setattr(logs, "render_action_result", _noop)
    monkeypatch.setattr(
        operator_service,
        "get_operations_snapshot",
        lambda: {
            "tracked_services": 5,
            "healthy_services": 4,
            "unknown_services": 1,
            "attention_services": 1,
            "last_health_ts": "2026-03-18T10:00:00Z",
        },
    )
    monkeypatch.setattr(operator_service, "list_services", lambda: ["tick_publisher"])
    monkeypatch.setattr(operator_service, "run_op", lambda args: (0, "ok"))
    monkeypatch.setattr(
        operator_service,
        "start_crypto_edge_collector_loop",
        lambda interval_sec, plan_file="sample_data/crypto_edges/live_collector_plan.json": captured.update({"interval_sec": interval_sec, "plan_file": plan_file}) or (0, "started"),
    )
    monkeypatch.setattr(operator_service, "stop_crypto_edge_collector_loop", lambda: (0, "stopped"))
    monkeypatch.setattr(
        config_editor,
        "load_user_yaml",
        lambda: {"strategy": {"name": "ema_cross", "trade_enabled": True, "ema_fast": 12, "ema_slow": 26}},
    )
    monkeypatch.setattr(config_editor, "save_user_yaml", lambda cfg: (True, "saved"))
    monkeypatch.setattr(config_tools, "supported_strategies", lambda: ["ema_cross", "mean_reversion_rsi", "breakout_donchian"])
    monkeypatch.setattr(
        config_tools,
        "build_strategy_block",
        lambda name, trade_enabled, params: {"name": name, "trade_enabled": trade_enabled, **params},
    )
    monkeypatch.setattr(config_tools, "apply_strategy_block", lambda cfg, block: {**cfg, "strategy": dict(block)})
    monkeypatch.setattr(config_tools, "validate_cfg", lambda cfg: {"ok": True, "errors": [], "warnings": []})
    monkeypatch.setattr(config_tools, "apply_preset_and_validate", lambda cfg, preset: (cfg, {"ok": True, "errors": [], "warnings": []}))
    monkeypatch.setattr(presets, "list_presets", lambda: ["ema_cross_default"])
    monkeypatch.setattr(operator_tools, "synthetic_ohlcv", lambda count: [[1, 100, 101, 99, 100, 1.0]] * max(int(count), 1))
    monkeypatch.setattr(idempotency_inspector, "list_recent", lambda limit=10, status="error": {"ok": True, "rows": [], "path": "/tmp/db", "table": "idempotency"})
    monkeypatch.setattr(idempotency_inspector, "filter_rows", lambda rows, venue_filter, symbol_filter: [])
    monkeypatch.setattr(repair_wizard, "preflight_self_check", lambda: {"ok": True})
    monkeypatch.setattr(repair_wizard, "preview_reset", lambda include_locks=False: {"ok": True, "include_locks": include_locks})
    monkeypatch.setattr(repair_wizard, "execute_reset", lambda confirm_text="", include_locks=False: {"ok": False, "reason": "not_confirmed"})
    monkeypatch.setattr(
        strategy_evaluation,
        "build_strategy_workbench",
        lambda **kwargs: {"ok": True, "backtest": {}, "leaderboard": {}, "hypothesis": {}},
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_report",
        lambda: {
            "ok": True,
            "has_any_data": True,
            "store_path": "/tmp/crypto_edge_research.sqlite",
            "funding_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "basis_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "quote_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "funding": {"count": 1, "annualized_carry_pct": 12.0, "dominant_bias": "long_pays", "rows": [{"symbol": "BTC-PERP"}]},
            "basis": {"count": 1, "avg_basis_bps": 8.0, "widest_basis_bps": 8.0, "rows": [{"symbol": "BTC-PERP"}]},
            "dislocations": {"count": 1, "positive_count": 1, "top_dislocation": {"symbol": "BTC/USD", "gross_cross_bps": 6.0}, "rows": [{"symbol": "BTC/USD"}]},
        },
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_latest_live_crypto_edge_snapshot",
        lambda: {
            "ok": True,
            "has_any_data": True,
            "has_live_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Recent",
            "funding": {"dominant_bias": "long_pays", "annualized_carry_pct": 12.0},
            "basis": {"avg_basis_bps": 8.0, "widest_basis_bps": 8.0},
            "dislocations": {"positive_count": 1, "top_dislocation": {"symbol": "BTC/USD"}},
            "summary_text": "Live Public snapshot shows funding bias long_pays.",
        },
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_collector_runtime",
        lambda: {"ok": True, "has_status": True, "status": "running", "freshness": "Recent"},
    )
    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_staleness_summary",
        lambda: {"ok": True, "needs_attention": False, "severity": "ok"},
    )

    _load_dashboard_module(
        monkeypatch,
        relative_path="dashboard/pages/60_Operations.py",
        module_name="dashboard_test_operations_start_collector",
        streamlit_overrides={
            "Collector Loop Interval (sec)": 900.0,
            "Start Live Collector Loop": True,
        },
    )

    assert captured["plan_file"] == "sample_data/crypto_edges/live_collector_plan.json"
    assert captured["interval_sec"] == 900.0


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
            "discord": False,
            "webhook": False,
            "price_alerts": True,
            "news_alerts": True,
            "catalyst_alerts": True,
            "risk_alerts": True,
            "approval_requests": True,
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
                "include_social": False,
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
            "Discord channel": True,
            "Webhook delivery": True,
            "Price alerts": False,
            "News alerts": False,
            "Catalyst alerts": True,
            "Risk alerts": False,
            "Approval requests": True,
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
            "Use social context": True,
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
            "Email / SMTP enabled": True,
            "Email / SMTP credential": "smtp-secret",
            "Email / SMTP role / priority": "Alerts",
            "Email / SMTP status note": "Healthy",
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
    assert captured["payload"]["notifications"]["discord"] is True
    assert captured["payload"]["notifications"]["webhook"] is True
    assert captured["payload"]["notifications"]["price_alerts"] is False
    assert captured["payload"]["notifications"]["news_alerts"] is False
    assert captured["payload"]["notifications"]["catalyst_alerts"] is True
    assert captured["payload"]["notifications"]["risk_alerts"] is False
    assert captured["payload"]["notifications"]["approval_requests"] is True
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
    assert captured["payload"]["ai"]["include_social"] is True
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
