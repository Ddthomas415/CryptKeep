from __future__ import annotations

from dashboard.services import home_digest


def test_load_home_digest_reports_paper_truth(monkeypatch) -> None:
    monkeypatch.setattr(home_digest, "_load_trading_cfg", lambda: {"mode": "paper", "symbols": ["BTC/USD"]})
    monkeypatch.setattr(home_digest, "load_user_yaml", lambda: {})
    monkeypatch.setattr(home_digest, "is_live_enabled", lambda cfg=None: False)
    monkeypatch.setattr(home_digest, "live_enabled_and_armed", lambda: (False, "live_disabled"))
    monkeypatch.setattr(home_digest, "live_allowed", lambda: (False, "risk_enable_live_false", {"live_enabled": False}))
    monkeypatch.setattr(
        home_digest,
        "decide_start",
        lambda mode, cfg=None: type("Decision", (), {"ok": True, "mode": mode, "status": "OK", "reasons": [], "note": "Paper start allowed"})(),
    )
    monkeypatch.setattr(home_digest, "build_strategy_workbench", lambda **kwargs: {"ok": True, "leaderboard": {"rows": []}})
    monkeypatch.setattr(home_digest, "build_leaderboard_table_rows", lambda result: [])
    monkeypatch.setattr(
        home_digest,
        "load_crypto_edge_staleness_summary",
        lambda: {
            "ok": True,
            "needs_attention": False,
            "severity": "ok",
            "live_snapshot_freshness": "Fresh",
            "action_text": "No operator action needed.",
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
        lambda: {"ok": True, "status": "running", "freshness": "Fresh", "errors": 0},
    )
    monkeypatch.setattr(home_digest, "get_operations_snapshot", lambda: {"attention_services": 0, "unknown_services": 0})

    payload = home_digest.load_home_digest({"active_warnings": [], "blocked_trades_count": 0})

    assert payload["runtime_mode_label"] == "Paper"
    assert payload["execution_truth_label"] == "Paper Only"
    assert payload["live_safety_label"] == "Inactive"
    assert payload["structural_freshness_label"] == "Fresh"
    assert payload["attention_items"][0].startswith("Runtime remains paper-first")
    assert "Stock support is not proven." in payload["claim_boundaries"]


def test_load_home_digest_surfaces_blocked_live_attention(monkeypatch) -> None:
    monkeypatch.setattr(
        home_digest,
        "_load_trading_cfg",
        lambda: {"mode": "live", "live": {"sandbox": False}, "symbols": ["ETH/USD"]},
    )
    monkeypatch.setattr(home_digest, "load_user_yaml", lambda: {"execution": {"live_enabled": False}})
    monkeypatch.setattr(home_digest, "is_live_enabled", lambda cfg=None: False)
    monkeypatch.setattr(home_digest, "live_enabled_and_armed", lambda: (False, "live_not_armed"))
    monkeypatch.setattr(home_digest, "live_allowed", lambda: (False, "kill_switch_armed", {"kill_switch": {"armed": True}}))
    monkeypatch.setattr(
        home_digest,
        "decide_start",
        lambda mode, cfg=None: type(
            "Decision",
            (),
            {
                "ok": False,
                "mode": mode,
                "status": "BLOCK",
                "reasons": ["ENABLE_LIVE_TRADING!=YES"],
                "note": "Set ENABLE_LIVE_TRADING=YES to allow real live",
            },
        )(),
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
                    }
                ]
            },
        },
    )
    monkeypatch.setattr(
        home_digest,
        "build_leaderboard_table_rows",
        lambda result: [
            {
                "rank": 1,
                "candidate": "breakout_default",
                "strategy": "breakout_donchian",
                "leaderboard_score": 0.81,
                "return_pct": 4.2,
                "max_drawdown_pct": 1.1,
            }
        ],
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
        lambda: {"ok": True, "status": "stopped", "freshness": "Stale", "errors": 2},
    )
    monkeypatch.setattr(home_digest, "get_operations_snapshot", lambda: {"attention_services": 2, "unknown_services": 1})

    payload = home_digest.load_home_digest({"active_warnings": ["execution disabled"], "blocked_trades_count": 3})

    assert payload["runtime_mode_label"] == "Real Live"
    assert payload["execution_truth_label"] == "Real Live Blocked"
    assert payload["live_safety_label"] == "Blocked"
    assert payload["strategy_label"] == "Breakout Default"
    assert payload["collector_status_label"] == "Stopped"
    assert any("Live start is blocked." in item for item in payload["attention_items"])
    assert any("3 trade(s)" in item for item in payload["attention_items"])
    assert any("2 tracked service(s) need operator attention." in item for item in payload["attention_items"])
