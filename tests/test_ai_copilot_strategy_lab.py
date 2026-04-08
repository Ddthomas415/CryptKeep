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
                    "max_drawdown_pct": 2.1,
                    "closed_trades": 9,
                    "evidence_status": "supported",
                    "confidence_label": "medium",
                    "paper_history_note": "Supported by paper history.",
                    "biggest_weakness": "Thin loser sample.",
                    "next_improvement": "Study the latest losing exit cluster.",
                }
            ]
        },
    }

    monkeypatch.setattr("services.ai_copilot.strategy_lab._latest_evidence_path", lambda: Path("/tmp/strategy_evidence.latest.json"))
    monkeypatch.setattr("services.ai_copilot.strategy_lab._load_json", lambda path: sample_payload)
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
    assert report["selected_strategy"] == "ema_cross"
    assert report["loss_replay"]["losing_trade_count"] == 2
    assert any("Top strategy changed" in item for item in report["recommendations"])
    assert any("Study the latest losing exit cluster." in item for item in report["recommendations"])


def test_build_strategy_lab_report_handles_missing_evidence(monkeypatch):
    monkeypatch.setattr("services.ai_copilot.strategy_lab._latest_evidence_path", lambda: Path("/tmp/missing.latest.json"))

    report = build_strategy_lab_report(include_loss_replay=False)

    assert report["ok"] is False
    assert report["severity"] == "warn"
    assert report["top_rows"] == []
    assert any("Run a fresh strategy evidence cycle" in item for item in report["recommendations"])


def test_write_strategy_lab_report_writes_files(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    report = {
        "generated_at": "2026-04-08T00:00:00+00:00",
        "severity": "ok",
        "ok": True,
        "summary": "Strategy lab report built.",
        "selected_strategy": "ema_cross",
        "symbol": "BTC/USD",
        "top_rows": [{"strategy": "ema_cross", "rank": 1, "decision": "keep", "leaderboard_score": 0.8, "max_drawdown_pct": 2.0}],
        "paper_history": {"status": "available", "fills_count": 12, "strategy_count": 3, "caveat": ""},
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
