from __future__ import annotations

import json
from pathlib import Path

from services.ai_copilot.strategy_lab import build_strategy_lab_report, write_strategy_lab_report


def test_build_strategy_lab_report_uses_top_strategy_and_loss_replay(monkeypatch):
    sample_payload = {
        "as_of": "2026-04-08T00:00:00Z",
        "symbol": "BTC/USD",
        "paper_history": {"status": "available", "fills_count": 12, "strategy_count": 3, "journal_path": "/tmp/trade_journal.sqlite"},
        "comparison": {
            "has_previous": True,
            "summary_text": "Top strategy changed from mean_reversion_rsi to ema_cross.",
            "top_strategy_previous": "mean_reversion_rsi",
            "top_strategy_current": "ema_cross",
            "top_strategy_changed": True,
            "improved_count": 1,
            "degraded_count": 1,
            "unchanged_count": 0,
            "new_count": 0,
        },
        "aggregate_leaderboard": {
            "rows": [
                {
                    "strategy": "ema_cross",
                    "candidate": "ema_cross_default",
                    "rank": 1,
                    "decision": "improve",
                    "leaderboard_score": 0.81,
                    "avg_return_pct": 5.2,
                    "net_return_after_costs_pct": 5.2,
                    "max_drawdown_pct": 2.1,
                    "closed_trades": 34,
                    "closed_trade_window_count": 3,
                    "active_window_count": 3,
                    "slippage_sensitivity_pct": 1.1,
                    "evidence_status": "paper_supported",
                    "confidence_label": "medium",
                    "paper_history_note": "Supported by paper history.",
                    "biggest_weakness": "Thin loser sample.",
                    "next_improvement": "Study the latest losing exit cluster.",
                    "paper_history": {"closed_trades": 34, "fills": 68, "net_realized_pnl": 212.5},
                    "walk_forward": {
                        "available": True,
                        "status": "ok",
                        "research_only": True,
                        "bars": 240,
                        "window_count": 4,
                        "summary": {
                            "avg_test_return_pct": 1.6,
                            "avg_test_max_drawdown_pct": 2.3,
                            "non_negative_test_window_ratio": 0.75,
                            "total_test_trades": 10,
                            "total_test_closed_trades": 5,
                        },
                    },
                }
            ]
        },
    }

    monkeypatch.setattr("services.ai_copilot.strategy_lab._latest_evidence_path", lambda: Path("/tmp/strategy_evidence.latest.json"))
    monkeypatch.setattr("services.ai_copilot.strategy_lab._load_json", lambda path: sample_payload)
    monkeypatch.setattr(
        "services.ai_copilot.strategy_lab.load_evidence_runtime_status",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "stopped",
            "completed_strategies": 3,
            "total_strategies": 3,
            "summary_text": "Paper evidence collector is stopped after a complete run.",
        },
    )
    monkeypatch.setattr(
        "services.ai_copilot.strategy_lab.build_loss_replay",
        lambda **kwargs: {
            "losing_trade_count": 2,
            "closed_trade_count": 9,
            "summary": {"net_realized_pnl": -12.5},
            "loss_replays": [{"symbol": "BTC/USD", "net_pnl": -7.0}],
        },
    )

    report = build_strategy_lab_report()

    assert report["ok"] is True
    assert report["severity"] == "ok"
    assert report["selected_strategy"] == "ema_cross"
    assert report["research_acceptance"]["accepted"] is True
    assert report["walk_forward"]["available"] is True
    assert report["walk_forward"]["window_count"] == 4
    assert report["walk_forward"]["summary"]["avg_test_return_pct"] == 1.6
    assert report["loss_replay"]["losing_trade_count"] == 2
    assert any("Top strategy changed" in item for item in report["recommendations"])
    assert any("Study the latest losing exit cluster." in item for item in report["recommendations"])


def test_build_strategy_lab_report_handles_missing_evidence(monkeypatch):
    monkeypatch.setattr("services.ai_copilot.strategy_lab._latest_evidence_path", lambda: Path("/tmp/missing.latest.json"))
    monkeypatch.setattr("services.ai_copilot.strategy_lab.load_evidence_runtime_status", lambda: {})

    report = build_strategy_lab_report(include_loss_replay=False)

    assert report["ok"] is False
    assert report["severity"] == "warn"
    assert report["top_rows"] == []
    assert any("Run a fresh strategy evidence cycle" in item for item in report["recommendations"])


def test_build_strategy_lab_report_warns_when_evidence_is_partial_or_thin(monkeypatch):
    sample_payload = {
        "as_of": "2026-04-08T00:00:00Z",
        "symbol": "BTC/USD",
        "paper_history": {"status": "available", "fills_count": 2, "strategy_count": 1, "journal_path": "/tmp/trade_journal.sqlite"},
        "comparison": {"summary_text": "Unchanged."},
        "aggregate_leaderboard": {
            "rows": [
                {
                    "strategy": "breakout_donchian",
                    "candidate": "breakout_default",
                    "rank": 1,
                    "decision": "improve",
                    "leaderboard_score": 0.57,
                    "avg_return_pct": 15.0,
                    "net_return_after_costs_pct": 15.0,
                    "max_drawdown_pct": 8.4,
                    "closed_trades": 1,
                    "closed_trade_window_count": 1,
                    "active_window_count": 1,
                    "slippage_sensitivity_pct": 16.0,
                    "evidence_status": "paper_thin",
                    "confidence_label": "low",
                    "paper_history_note": "1 closed trade, thin sample.",
                    "biggest_weakness": "Thin sample.",
                    "next_improvement": "Run more windows.",
                    "paper_history": {"closed_trades": 1, "fills": 2, "net_realized_pnl": 4.0},
                    "walk_forward": {
                        "available": False,
                        "status": "insufficient_candles",
                        "research_only": True,
                        "bars": 20,
                        "window_count": 0,
                        "summary": {},
                    },
                }
            ]
        },
    }

    monkeypatch.setattr("services.ai_copilot.strategy_lab._latest_evidence_path", lambda: Path("/tmp/strategy_evidence.latest.json"))
    monkeypatch.setattr("services.ai_copilot.strategy_lab._load_json", lambda path: sample_payload)
    monkeypatch.setattr(
        "services.ai_copilot.strategy_lab.load_evidence_runtime_status",
        lambda: {
            "ok": True,
            "has_status": True,
            "status": "stopped",
            "completed_strategies": 1,
            "total_strategies": 3,
            "summary_text": "Paper evidence collector is stopped (1/3 complete).",
        },
    )
    monkeypatch.setattr("services.ai_copilot.strategy_lab.build_loss_replay", lambda **kwargs: {"losing_trade_count": 0, "closed_trade_count": 0, "summary": {}, "loss_replays": []})

    report = build_strategy_lab_report()

    assert report["ok"] is True
    assert report["severity"] == "warn"
    assert report["research_acceptance"]["accepted"] is False
    assert "partial evidence" in report["summary"]
    assert "does not meet the current research-acceptance floor" in report["research_acceptance"]["summary"]
    assert report["collector_runtime"]["completed_strategies"] == 1
    assert any("Finish the current paper evidence cycle" in item for item in report["recommendations"])
    assert any("credible edge" in item for item in report["recommendations"])
    assert any("Research acceptance blocker:" in item for item in report["recommendations"])


def test_write_strategy_lab_report_writes_files(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    report = {
        "generated_at": "2026-04-08T00:00:00+00:00",
        "severity": "ok",
        "ok": True,
        "summary": "Strategy lab report built.",
        "selected_strategy": "ema_cross",
        "symbol": "BTC/USD",
        "top_rows": [
            {
                "strategy": "ema_cross",
                "rank": 1,
                "decision": "keep",
                "leaderboard_score": 0.8,
                "max_drawdown_pct": 2.0,
                "walk_forward": {"status": "ok"},
            }
        ],
        "walk_forward": {
            "available": True,
            "status": "ok",
            "research_only": True,
            "bars": 240,
            "window_count": 4,
            "summary": {
                "avg_test_return_pct": 1.6,
                "avg_test_max_drawdown_pct": 2.3,
                "non_negative_test_window_ratio": 0.75,
                "total_test_closed_trades": 5,
            },
        },
        "collector_runtime": {"status": "stopped", "completed_strategies": 3, "total_strategies": 3, "summary_text": "Complete run."},
        "paper_history": {"status": "available", "fills_count": 12, "strategy_count": 3, "caveat": ""},
        "research_acceptance": {"status": "accepted", "summary": "ema_cross meets the current research-acceptance floor.", "blockers": []},
        "comparison": {"summary_text": "Unchanged.", "top_strategy_changed": False, "improved_count": 0, "degraded_count": 0},
        "loss_replay": {"available": True, "losing_trade_count": 1, "closed_trade_count": 4},
        "recommendations": ["Keep it paper-only."],
    }

    paths = write_strategy_lab_report(report, stem="strategy_lab_test")

    json_path = Path(paths["json_path"])
    markdown_path = Path(paths["markdown_path"])
    assert json_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["selected_strategy"] == "ema_cross"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# CryptKeep Strategy Lab" in markdown
    assert "ema_cross" in markdown
    assert "## Evidence Runtime" in markdown
    assert "## Research Acceptance" in markdown
    assert "## Walk-Forward" in markdown
