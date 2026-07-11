"""Active backlog #23 proofs: strategy decision-change alerting."""
from __future__ import annotations

import json

import services.alerts.strategy_decision_events as sde
from services.backtest import evidence_cycle


def _capture(monkeypatch):
    sent: list[tuple[str, str, dict | None]] = []
    monkeypatch.setattr(
        sde,
        "_send",
        lambda level, message, payload: sent.append((level, message, payload)),
    )
    return sent


def _comparison(*changes, has_previous: bool = True) -> dict:
    return {
        "has_previous": has_previous,
        "previous_as_of": "2026-07-09T00:00:00Z",
        "current_as_of": "2026-07-10T00:00:00Z",
        "top_strategy_previous": "ema_cross",
        "top_strategy_current": "breakout_donchian",
        "top_strategy_changed": True,
        "changes": list(changes),
    }


def _change(
    strategy: str,
    *,
    previous_decision: str,
    current_decision: str,
    decision_changed: bool = True,
) -> dict:
    return {
        "strategy": strategy,
        "previous_decision": previous_decision,
        "current_decision": current_decision,
        "decision_changed": decision_changed,
    }


def test_first_persisted_evidence_is_silent_baseline(monkeypatch):
    sent = _capture(monkeypatch)
    assert sde.alert_strategy_decision_changes(_comparison(has_previous=False)) is False
    assert sent == []


def test_rank_or_score_only_changes_do_not_alert(monkeypatch):
    sent = _capture(monkeypatch)
    comparison = _comparison(
        _change(
            "breakout_donchian",
            previous_decision="keep",
            current_decision="keep",
            decision_changed=False,
        )
    )
    assert sde.alert_strategy_decision_changes(comparison) is False
    assert sent == []


def test_new_or_improved_decision_alerts_info(monkeypatch):
    sent = _capture(monkeypatch)
    comparison = _comparison(
        _change("breakout_donchian", previous_decision="", current_decision="improve"),
        _change("ema_cross", previous_decision="freeze", current_decision="improve"),
    )
    assert sde.alert_strategy_decision_changes(comparison) is True
    assert sent[0][0] == "info"
    assert sent[0][1] == "strategy_decisions:changed"
    assert sent[0][2]["decision_change_count"] == 2


def test_degraded_decision_alerts_warning(monkeypatch):
    sent = _capture(monkeypatch)
    comparison = _comparison(
        _change("ema_cross", previous_decision="keep", current_decision="freeze")
    )
    assert sde.alert_strategy_decision_changes(comparison) is True
    assert sent[0][0] == "warning"


def test_retire_decision_alerts_critical(monkeypatch):
    sent = _capture(monkeypatch)
    comparison = _comparison(
        _change("ema_cross", previous_decision="freeze", current_decision="retire")
    )
    assert sde.alert_strategy_decision_changes(comparison) is True
    assert sent[0][0] == "critical"


def test_never_raises_when_send_fails(monkeypatch):
    def _boom(level, message, payload):
        raise RuntimeError("dispatcher down")

    monkeypatch.setattr(sde, "_send", _boom)
    comparison = _comparison(
        _change("ema_cross", previous_decision="keep", current_decision="freeze")
    )
    assert sde.alert_strategy_decision_changes(comparison) is False


def test_persist_strategy_evidence_alerts_after_decision_change(monkeypatch, tmp_path):
    monkeypatch.setattr(evidence_cycle, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(evidence_cycle, "ensure_dirs", lambda: None)
    sent = _capture(monkeypatch)
    latest_dir = tmp_path / "strategy_evidence"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_path = latest_dir / "strategy_evidence.latest.json"
    latest_path.write_text(
        json.dumps(
            {
                "ok": True,
                "as_of": "2026-07-09T00:00:00Z",
                "aggregate_leaderboard": {
                    "rows": [
                        {
                            "strategy": "ema_cross",
                            "rank": 1,
                            "decision": "keep",
                            "leaderboard_score": 0.8,
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    evidence_cycle.persist_strategy_evidence(
        {
            "ok": True,
            "as_of": "2026-07-10T00:00:00Z",
            "aggregate_leaderboard": {
                "rows": [
                    {
                        "strategy": "ema_cross",
                        "rank": 1,
                        "decision": "freeze",
                        "leaderboard_score": 0.4,
                    }
                ]
            },
        }
    )

    assert sent
    assert sent[0][0] == "warning"
    assert sent[0][1] == "strategy_decisions:changed"
    assert sent[0][2]["changes"][0]["strategy"] == "ema_cross"


def test_persist_strategy_evidence_still_writes_when_alert_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(evidence_cycle, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(evidence_cycle, "ensure_dirs", lambda: None)
    latest_dir = tmp_path / "strategy_evidence"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_path = latest_dir / "strategy_evidence.latest.json"
    latest_path.write_text(
        json.dumps(
            {
                "ok": True,
                "as_of": "2026-07-09T00:00:00Z",
                "aggregate_leaderboard": {
                    "rows": [{"strategy": "ema_cross", "rank": 1, "decision": "keep"}]
                },
            }
        ),
        encoding="utf-8",
    )

    def _boom(level, message, payload):
        raise RuntimeError("dispatcher exploded")

    monkeypatch.setattr(sde, "_send", _boom)
    evidence_cycle.persist_strategy_evidence(
        {
            "ok": True,
            "as_of": "2026-07-10T00:00:00Z",
            "aggregate_leaderboard": {
                "rows": [{"strategy": "ema_cross", "rank": 1, "decision": "freeze"}]
            },
        }
    )

    written = json.loads(latest_path.read_text(encoding="utf-8"))
    assert written["as_of"] == "2026-07-10T00:00:00Z"
    assert written["comparison"]["changes"][0]["decision_changed"] is True
