from __future__ import annotations

import json

from dashboard.services.digest import strategy_evidence


def test_load_latest_strategy_evidence_reports_missing_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(strategy_evidence, "latest_strategy_evidence_path", lambda: tmp_path / "missing.json")

    out = strategy_evidence.load_latest_strategy_evidence()

    assert out["ok"] is False
    assert out["has_artifact"] is False
    assert out["freshness_status"] == "missing"
    assert "synthetic fallback" in out["caveat"].lower()


def test_load_latest_strategy_evidence_reads_persisted_artifact(tmp_path, monkeypatch) -> None:
    path = tmp_path / "strategy_evidence.latest.json"
    path.write_text(
        json.dumps(
            {
                "ok": True,
                "as_of": "2026-03-19T05:36:37Z",
                "source": "multi_window_synthetic",
                "window_count": 5,
                "aggregate_leaderboard": {
                    "candidate_count": 1,
                    "rows": [
                        {
                            "candidate": "breakout_default",
                            "strategy": "breakout_donchian",
                            "rank": 1,
                            "leaderboard_score": 0.57,
                            "net_return_after_costs_pct": 19.01,
                            "max_drawdown_pct": 7.83,
                        }
                    ],
                },
                "decisions": [{"candidate": "breakout_default", "decision": "keep"}],
                "comparison": {
                    "has_previous": True,
                    "previous_as_of": "2026-03-18T05:36:37Z",
                    "current_as_of": "2026-03-19T05:36:37Z",
                    "summary_text": "Top strategy changed from ema_cross to breakout_donchian.",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(strategy_evidence, "latest_strategy_evidence_path", lambda: path)

    out = strategy_evidence.load_latest_strategy_evidence()

    assert out["ok"] is True
    assert out["has_artifact"] is True
    assert out["source"] == "multi_window_synthetic"
    assert out["source_label"] == "Persisted Synthetic Evidence"
    assert out["rows"][0]["candidate"] == "breakout_default"
    assert out["decisions"][0]["decision"] == "keep"
    assert out["comparison"]["has_previous"] is True
    assert "Top strategy changed" in out["comparison"]["summary_text"]
