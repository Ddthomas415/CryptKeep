from __future__ import annotations

from dashboard.services.digest import builders as home_digest


class _Decision:
    def __init__(self, *, ok: bool, mode: str, status: str, reasons: list[str], note: str) -> None:
        self.ok = ok
        self.mode = mode
        self.status = status
        self.reasons = reasons
        self.note = note


def test_load_trading_cfg_uses_runtime_trading_config(monkeypatch) -> None:
    expected = {"execution": {"executor_mode": "live"}}
    monkeypatch.setattr(home_digest, "load_runtime_trading_config", lambda: expected)

    assert home_digest._load_trading_cfg() is expected


def test_runtime_mode_meta_prefers_execution_executor_mode() -> None:
    mode_value, label, note = home_digest._runtime_mode_meta(
        {"execution": {"executor_mode": "live"}, "live": {"sandbox": True}}
    )

    assert mode_value == "sandbox_live"
    assert label == "Sandbox Live"
    assert note == "Merged runtime config requests live mode with sandbox enabled."


def test_digest_source_map_uses_merged_runtime_config_labels() -> None:
    assert "merged runtime trading config" in home_digest.DIGEST_SOURCE_MAP["runtime_truth"]
    assert "merged runtime trading config" in home_digest.DIGEST_SOURCE_MAP["mode_truth"]


def test_load_home_digest_reports_paper_truth(monkeypatch) -> None:
    monkeypatch.setattr(home_digest, "_load_trading_cfg", lambda: {"mode": "paper", "symbols": ["BTC/USD"]})
    monkeypatch.setattr(home_digest, "load_user_yaml", lambda: {})
    monkeypatch.setattr(home_digest, "get_system_guard_state", lambda **_: {"state": "RUNNING", "writer": "test", "reason": "ok"})
    monkeypatch.setattr(
        home_digest,
        "load_latest_strategy_evidence",
        lambda: {
            "ok": False,
            "has_artifact": False,
            "artifact_path": "/tmp/strategy_evidence.latest.json",
            "freshness_status": "missing",
            "caveat": "Persisted strategy evidence artifact is missing; digest must use labeled synthetic fallback.",
        },
    )
    monkeypatch.setattr(home_digest, "is_live_enabled", lambda cfg=None: False)
    monkeypatch.setattr(home_digest, "live_enabled_and_armed", lambda: (False, "live_disabled"))
    monkeypatch.setattr(home_digest, "live_allowed", lambda: (False, "risk_enable_live_false", {"live_enabled": False}))
    monkeypatch.setattr(
        home_digest,
        "decide_start",
        lambda mode, cfg=None: _Decision(ok=True, mode=mode, status="OK", reasons=[], note="Paper start allowed"),
    )
    monkeypatch.setattr(home_digest, "build_strategy_workbench", lambda **kwargs: {"ok": True, "leaderboard": {"rows": []}})
    monkeypatch.setattr(
        home_digest,
        "load_latest_live_crypto_edge_snapshot",
        lambda: {
            "ok": True,
            "has_any_data": False,
            "has_live_data": False,
            "data_origin_label": "Live Public",
            "freshness_summary": "No Live Data",
        },
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_summary",
        lambda: {
            "ok": True,
            "needs_attention": False,
            "severity": "ok",
            "live_snapshot_freshness": "Fresh",
            "action_text": "No operator action needed.",
            "summary_text": "Structural-edge data is current.",
        },
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_digest",
        lambda: {"ok": True, "headline": "Structural-edge data is current", "while_away_summary": "All good."},
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_collector_runtime",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "running",
            "freshness": "Fresh",
            "errors": 0,
            "ts": "2026-03-18T12:00:00Z",
            "summary_text": "Collector loop is healthy.",
        },
    )
    monkeypatch.setattr(home_digest, "get_operations_snapshot", lambda: {"attention_services": 0, "unknown_services": 0, "last_health_ts": ""})

    payload = home_digest.load_home_digest({"active_warnings": [], "blocked_trades_count": 0})

    assert payload["page_status"]["state"] == "warn"
    assert payload["runtime_truth"]["mode"]["value"] == "Paper"
    assert payload["runtime_truth"]["live_order_authority"]["value"] == "Healthy"
    assert payload["runtime_truth"]["collector_freshness"]["value"] == "Fresh"
    assert payload["attention_now"]["items"][0]["title"] == "Runtime is paper-first"
    assert payload["leaderboard_summary"]["rows"] == []
    assert payload["mode_truth"]["current_mode"] == "paper"
    assert payload["mode_truth"]["promotion_stage"] == "Paper"
    assert payload["mode_truth"]["promotion_target"] == "Sandbox Live"
    assert payload["mode_truth"]["promotion_status"] == "warn"
    assert "real live submission" in payload["mode_truth"]["blocked"]
    assert "Stock support is not proven." in payload["claim_boundaries"]
    assert payload["next_best_action"]["title"] == "Runtime is paper-first"


def test_load_home_digest_surfaces_blocked_live_attention(monkeypatch) -> None:
    monkeypatch.setattr(
        home_digest,
        "_load_trading_cfg",
        lambda: {"mode": "live", "live": {"sandbox": False}, "symbols": ["ETH/USD"]},
    )
    monkeypatch.setattr(home_digest, "load_user_yaml", lambda: {"execution": {"live_enabled": False}})
    monkeypatch.setattr(home_digest, "get_system_guard_state", lambda **_: {"state": "RUNNING", "writer": "test", "reason": "ok"})
    monkeypatch.setattr(
        home_digest,
        "load_latest_strategy_evidence",
        lambda: {
            "ok": False,
            "has_artifact": False,
            "artifact_path": "/tmp/strategy_evidence.latest.json",
            "freshness_status": "missing",
            "caveat": "Persisted strategy evidence artifact is missing; digest must use labeled synthetic fallback.",
        },
    )
    monkeypatch.setattr(home_digest, "is_live_enabled", lambda cfg=None: False)
    monkeypatch.setattr(home_digest, "live_enabled_and_armed", lambda: (False, "live_not_armed"))
    monkeypatch.setattr(
        home_digest,
        "live_allowed",
        lambda: (False, "kill_switch_armed", {"kill_switch": {"armed": True}}),
    )
    monkeypatch.setattr(
        home_digest,
        "decide_start",
        lambda mode, cfg=None: _Decision(
            ok=False,
            mode=mode,
            status="BLOCK",
            reasons=["ENABLE_LIVE_TRADING!=YES"],
            note="Set ENABLE_LIVE_TRADING=YES to allow real live",
        ),
    )
    monkeypatch.setattr(
        home_digest,
        "build_strategy_workbench",
        lambda **kwargs: {
            "ok": True,
            "leaderboard": {
                "rows": [
                    {
                        "rank": 1,
                        "candidate": "breakout_default",
                        "strategy": "breakout_donchian",
                        "leaderboard_score": 0.81,
                        "net_return_after_costs_pct": 4.2,
                        "max_drawdown_pct": 1.1,
                        "regime_robustness": 0.7,
                        "regime_return_dispersion_pct": 1.2,
                        "slippage_sensitivity_pct": 0.9,
                        "paper_live_drift_pct": None,
                        "regime_scorecards": {
                            "bull": {"bars": 10, "net_return_after_costs_pct": 6.0},
                            "bear": {"bars": 10, "net_return_after_costs_pct": -1.0},
                        },
                    }
                ]
            },
        },
    )
    monkeypatch.setattr(
        home_digest,
        "load_latest_live_crypto_edge_snapshot",
        lambda: {
            "ok": True,
            "has_any_data": True,
            "has_live_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Aging",
            "funding": {"dominant_bias": "positive", "annualized_carry_pct": 8.4},
            "basis": {"avg_basis_bps": 12.3},
            "dislocations": {"positive_count": 2},
            "funding_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "basis_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "quote_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
        },
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_summary",
        lambda: {
            "ok": True,
            "needs_attention": True,
            "severity": "warn",
            "live_snapshot_freshness": "Stale",
            "summary_text": "Structural-edge freshness needs attention.",
            "action_text": "Refresh the collector loop.",
        },
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_digest",
        lambda: {
            "ok": True,
            "needs_attention": True,
            "headline": "Structural-edge data needs attention",
            "while_away_summary": "Data is stale.",
            "action_text": "Refresh the collector loop.",
        },
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_collector_runtime",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "stopped",
            "freshness": "Stale",
            "errors": 2,
            "ts": "2026-03-18T09:00:00Z",
            "summary_text": "Collector runtime is stale.",
        },
    )
    monkeypatch.setattr(
        home_digest,
        "get_operations_snapshot",
        lambda: {"attention_services": 2, "unknown_services": 1, "last_health_ts": "2026-03-18T08:00:00Z"},
    )

    payload = home_digest.load_home_digest({"active_warnings": ["execution disabled"], "blocked_trades_count": 3})

    assert payload["page_status"]["state"] == "critical"
    assert payload["runtime_truth"]["mode"]["value"] == "Real Live"
    assert payload["runtime_truth"]["live_order_authority"]["value"] == "Blocked"
    assert payload["runtime_truth"]["kill_switch"]["value"] == "Armed"
    assert payload["leaderboard_summary"]["rows"][0]["name"] == "Breakout Default"
    assert payload["leaderboard_summary"]["rows"][0]["best_regime"] == "bull"
    assert payload["leaderboard_summary"]["rows"][0]["worst_regime"] == "bear"
    assert payload["scorecard_snapshot"]["highlights"]["best_post_cost"]["strategy_name"] == "Breakout Default"
    assert payload["safety_warnings"]["live_boundary_status"] == "blocked"
    assert any(item["title"].endswith("start is blocked") for item in payload["attention_now"]["items"])
    assert any("trade(s) are blocked" in item["title"] for item in payload["attention_now"]["items"])
    assert payload["mode_truth"]["promotion_stage"] == "Tiny Live"
    assert payload["mode_truth"]["promotion_status"] == "critical"
    assert "ENABLE_LIVE_TRADING!=YES" in payload["mode_truth"]["promotion_blockers"]
    assert payload["next_best_action"]["source"] == "mode"


def test_load_home_digest_pulls_overview_summary_when_not_supplied(monkeypatch) -> None:
    from dashboard.services import view_data

    monkeypatch.setattr(home_digest, "_load_trading_cfg", lambda: {"mode": "paper", "symbols": ["BTC/USD"]})
    monkeypatch.setattr(home_digest, "load_user_yaml", lambda: {})
    monkeypatch.setattr(home_digest, "get_system_guard_state", lambda **_: {"state": "RUNNING", "writer": "test", "reason": "ok"})
    monkeypatch.setattr(
        home_digest,
        "load_latest_strategy_evidence",
        lambda: {
            "ok": False,
            "has_artifact": False,
            "artifact_path": "/tmp/strategy_evidence.latest.json",
            "freshness_status": "missing",
            "caveat": "Persisted strategy evidence artifact is missing; digest must use labeled synthetic fallback.",
        },
    )
    monkeypatch.setattr(home_digest, "is_live_enabled", lambda cfg=None: False)
    monkeypatch.setattr(home_digest, "live_enabled_and_armed", lambda: (False, "live_disabled"))
    monkeypatch.setattr(home_digest, "live_allowed", lambda: (False, "risk_enable_live_false", {"live_enabled": False}))
    monkeypatch.setattr(
        home_digest,
        "decide_start",
        lambda mode, cfg=None: _Decision(ok=True, mode=mode, status="OK", reasons=[], note="Paper start allowed"),
    )
    monkeypatch.setattr(home_digest, "build_strategy_workbench", lambda **kwargs: {"ok": True, "leaderboard": {"rows": []}})
    monkeypatch.setattr(
        view_data,
        "get_overview_view",
        lambda selected_asset=None: {
            "summary": {"active_warnings": [], "blocked_trades_count": 2},
        },
    )
    monkeypatch.setattr(
        home_digest,
        "load_latest_live_crypto_edge_snapshot",
        lambda: {"ok": True, "has_any_data": False, "has_live_data": False, "data_origin_label": "Live Public"},
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_summary",
        lambda: {"ok": True, "needs_attention": False, "severity": "ok", "summary_text": "Fresh"},
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_digest",
        lambda: {"ok": True, "headline": "Structural-edge data is current", "while_away_summary": "All good."},
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_collector_runtime",
        lambda: {"ok": True, "has_status": False, "freshness": "Missing"},
    )
    monkeypatch.setattr(home_digest, "get_operations_snapshot", lambda: {"attention_services": 0, "unknown_services": 0, "last_health_ts": ""})

    payload = home_digest.load_home_digest()


def test_load_home_digest_prefers_persisted_strategy_evidence(monkeypatch) -> None:
    monkeypatch.setattr(home_digest, "_load_trading_cfg", lambda: {"mode": "paper", "symbols": ["BTC/USD"]})
    monkeypatch.setattr(home_digest, "load_user_yaml", lambda: {})
    monkeypatch.setattr(home_digest, "get_system_guard_state", lambda **_: {"state": "RUNNING", "writer": "test", "reason": "ok"})
    monkeypatch.setattr(
        home_digest,
        "load_latest_strategy_evidence",
        lambda: {
            "ok": True,
            "has_artifact": True,
            "artifact_path": "/tmp/strategy_evidence.latest.json",
            "as_of": "2026-03-19T05:36:37Z",
            "age_seconds": 900,
            "freshness_status": "fresh",
            "source": "multi_window_synthetic",
            "source_label": "Persisted Synthetic Evidence",
            "caveat": "Persisted synthetic multi-window strategy evidence artifact. Stronger than on-demand fallback, but still not market-history proof.",
            "rows": [
                {
                    "candidate": "breakout_default",
                    "strategy": "breakout_donchian",
                    "rank": 1,
                    "leaderboard_score": 0.57,
                    "net_return_after_costs_pct": 19.01,
                    "max_drawdown_pct": 7.83,
                    "closed_trades": 4,
                    "trade_count": 10,
                    "exposure_fraction": 0.34,
                    "regime_robustness": 0.8,
                    "regime_return_dispersion_pct": 8.2,
                    "slippage_sensitivity_pct": 1.1,
                    "paper_live_drift_pct": None,
                    "decision": "keep",
                    "evidence_status": "paper_supported",
                    "confidence_label": "medium",
                    "evidence_note": "Persisted paper-history is present, but the current sample is still research-grade rather than promotion-grade.",
                }
            ],
            "decisions": [
                {
                    "candidate": "breakout_default",
                    "strategy": "breakout_donchian",
                    "rank": 1,
                    "decision": "keep",
                    "evidence_status": "paper_supported",
                    "confidence_label": "medium",
                    "evidence_note": "Persisted paper-history is present, but the current sample is still research-grade rather than promotion-grade.",
                }
            ],
            "window_count": 5,
        },
    )
    monkeypatch.setattr(home_digest, "build_strategy_workbench", lambda **kwargs: (_ for _ in ()).throw(AssertionError("synthetic fallback should not run")))
    monkeypatch.setattr(home_digest, "is_live_enabled", lambda cfg=None: False)
    monkeypatch.setattr(home_digest, "live_enabled_and_armed", lambda: (False, "live_disabled"))
    monkeypatch.setattr(home_digest, "live_allowed", lambda: (False, "risk_enable_live_false", {"live_enabled": False}))
    monkeypatch.setattr(
        home_digest,
        "decide_start",
        lambda mode, cfg=None: _Decision(ok=True, mode=mode, status="OK", reasons=[], note="Paper start allowed"),
    )
    monkeypatch.setattr(
        home_digest,
        "load_latest_live_crypto_edge_snapshot",
        lambda: {"ok": True, "has_any_data": False, "has_live_data": False, "data_origin_label": "Live Public"},
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_summary",
        lambda: {"ok": True, "needs_attention": False, "severity": "ok", "summary_text": "Fresh"},
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_digest",
        lambda: {"ok": True, "headline": "Structural-edge data is current", "while_away_summary": "All good."},
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_collector_runtime",
        lambda: {"ok": True, "has_status": True, "freshness": "Fresh", "errors": 0, "ts": "2026-03-19T05:40:00Z", "summary_text": "Collector loop is healthy."},
    )
    monkeypatch.setattr(home_digest, "get_operations_snapshot", lambda: {"attention_services": 0, "unknown_services": 0, "last_health_ts": ""})

    payload = home_digest.load_home_digest({"active_warnings": [], "blocked_trades_count": 0})

    assert payload["leaderboard_summary"]["source_name"] == home_digest.DIGEST_SOURCE_MAP["leaderboard_summary_artifact"]
    assert payload["leaderboard_summary"]["rows"][0]["recommendation"] == "keep"
    assert payload["runtime_truth"]["leaderboard_age"]["value"] == "15m old"
    assert any("execution.live_enabled remains false" in item for item in payload["mode_truth"]["promotion_blockers"])
    assert not any(item["title"] == "Persisted strategy evidence is unavailable" for item in payload["attention_now"]["items"])
    assert any(item["title"] == "Top strategy is not research-accepted" for item in payload["attention_now"]["items"])
    assert payload["scorecard_snapshot"]["source_name"] == home_digest.DIGEST_SOURCE_MAP["scorecard_snapshot_artifact"]


def test_build_mode_truth_digest_warns_when_promotion_review_is_clear_but_research_confidence_is_not() -> None:
    payload = home_digest.build_mode_truth_digest(
        as_of="2026-03-19T12:00:00Z",
        runtime_context={
            "mode_value": "sandbox_live",
            "mode_label": "Sandbox Live",
            "normalized_live_enabled": True,
            "guard_allowed": True,
            "armed": True,
            "start_decision": _Decision(ok=True, mode="live", status="OK", reasons=[], note="Sandbox start allowed"),
        },
        promotion_readiness={
            "current_stage_label": "Sandbox Live",
            "target_stage_label": "Tiny Live",
            "status": "ok",
            "summary": "Current evidence is strong enough to review promotion from Sandbox Live to Tiny Live.",
            "pass_criteria": [],
            "rollback_criteria": [],
            "blockers": [],
        },
        strategy_context={
            "raw_rows": [
                {
                    "strategy": "breakout_donchian",
                    "candidate": "breakout_default",
                    "evidence_status": "paper_supported",
                    "confidence_label": "medium",
                    "closed_trades": 6,
                    "closed_trade_window_count": 1,
                    "net_return_after_costs_pct": 12.0,
                    "max_drawdown_pct": 4.0,
                    "slippage_sensitivity_pct": 0.3,
                    "research_acceptance": {
                        "accepted": False,
                        "status": "not_accepted",
                        "summary": "`breakout_donchian` does not meet the current research-acceptance floor yet.",
                        "blockers": [
                            "Persisted paper history only has 6 closed trade(s); the current research floor requires 30."
                        ],
                    },
                }
            ]
        },
    )

    assert payload["promotion_status"] == "warn"
    assert any("research-acceptance floor" in item for item in payload["promotion_blockers"])


def test_load_home_digest_surfaces_system_guard_blocking(monkeypatch) -> None:
    monkeypatch.setattr(
        home_digest,
        "_load_trading_cfg",
        lambda: {"mode": "live", "live": {"sandbox": False}, "symbols": ["BTC/USD"]},
    )
    monkeypatch.setattr(home_digest, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    monkeypatch.setattr(home_digest, "get_system_guard_state", lambda **_: {"state": "HALTING", "writer": "watchdog", "reason": "heartbeat_stale"})
    monkeypatch.setattr(
        home_digest,
        "load_latest_strategy_evidence",
        lambda: {
            "ok": False,
            "has_artifact": False,
            "artifact_path": "/tmp/strategy_evidence.latest.json",
            "freshness_status": "missing",
            "caveat": "Persisted strategy evidence artifact is missing; digest must use labeled synthetic fallback.",
        },
    )
    monkeypatch.setattr(home_digest, "is_live_enabled", lambda cfg=None: True)
    monkeypatch.setattr(home_digest, "live_enabled_and_armed", lambda: (True, "env:CBP_EXECUTION_ARMED"))
    monkeypatch.setattr(
        home_digest,
        "live_allowed",
        lambda: (True, "ok", {"kill_switch": {"armed": False}, "live_enabled": True, "risk": {"enable_live": True}}),
    )
    monkeypatch.setattr(
        home_digest,
        "decide_start",
        lambda mode, cfg=None: _Decision(ok=True, mode=mode, status="OK", reasons=[], note="Live start allowed"),
    )
    monkeypatch.setattr(home_digest, "build_strategy_workbench", lambda **kwargs: {"ok": True, "leaderboard": {"rows": []}})
    monkeypatch.setattr(
        home_digest,
        "load_latest_live_crypto_edge_snapshot",
        lambda: {"ok": True, "has_any_data": False, "has_live_data": False, "data_origin_label": "Live Public"},
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_summary",
        lambda: {"ok": True, "needs_attention": False, "severity": "ok", "summary_text": "Fresh"},
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_digest",
        lambda: {"ok": True, "headline": "Structural-edge data is current", "while_away_summary": "All good."},
    )
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_collector_runtime",
        lambda: {"ok": True, "has_status": True, "freshness": "Fresh", "errors": 0, "ts": "2026-03-19T05:40:00Z", "summary_text": "Collector loop is healthy."},
    )
    monkeypatch.setattr(home_digest, "get_operations_snapshot", lambda: {"attention_services": 0, "unknown_services": 0, "last_health_ts": ""})

    payload = home_digest.load_home_digest({"active_warnings": [], "blocked_trades_count": 0})

    assert payload["runtime_truth"]["live_order_authority"]["value"] == "Blocked"
    assert payload["runtime_truth"]["live_order_authority"]["state"] == "warn"
    assert payload["runtime_truth"]["system_guard"]["value"] == "Halting"
    assert payload["runtime_truth"]["system_guard"]["state"] == "warn"
    assert payload["safety_warnings"]["live_boundary_status"] == "blocked"
    assert payload["safety_warnings"]["system_guard_state"] == "halting"
    assert any(item["title"] == "System Guard is Halting" for item in payload["safety_warnings"]["items"])
