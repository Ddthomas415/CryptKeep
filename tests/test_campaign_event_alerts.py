"""Active backlog #23 proofs: campaign stop/failure event alerting.

Notification-only contract pinned here (mirrors test_paper_gate_event_alerts):
- alerts fire once per TRANSITION into a stop/failure state, never per write
- first observation (no prior status) is a silent baseline
- normal "completed" is not alerted; "stopped" warns; "failed"/"error"/
  "aborted" are critical
- the alerter never raises, and the caller invokes it only after the status
  write succeeds so a raising channel cannot block campaign advancement
"""
from __future__ import annotations

import pytest

import services.alerts.campaign_events as ce


@pytest.fixture(autouse=True)
def isolate_state(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))


def _capture(monkeypatch):
    sent: list[tuple[str, str, dict | None]] = []
    monkeypatch.setattr(
        ce, "_send",
        lambda level, message, payload: sent.append((level, message, payload)),
    )
    return sent


def test_first_observation_is_silent_baseline(monkeypatch):
    from services.events.platform_event_journal import load_platform_events

    sent = _capture(monkeypatch)
    # No previous status -> nothing to transition from.
    assert ce.alert_campaign_status_transition("", "failed") is False
    assert sent == []
    assert load_platform_events(event_type="CampaignStarted") == []


def test_first_running_observation_emits_campaign_started_event(monkeypatch):
    from services.events.platform_event_journal import load_platform_events

    sent = _capture(monkeypatch)
    payload = {"symbol": "BTC/USD", "strategy_id": "es_daily_trend_v1", "run_id": "run-1"}

    assert ce.alert_campaign_status_transition("", "running", payload) is False

    assert sent == []
    events = load_platform_events(event_type="CampaignStarted")
    assert len(events) == 1
    event = events[0]
    assert event["provenance"]["strategy_id"] == "es_daily_trend_v1"
    assert event["provenance"]["run_id"] == "run-1"
    assert event["payload"]["prev_status"] == ""
    assert event["payload"]["new_status"] == "running"
    assert event["payload"]["symbol"] == "BTC/USD"


def test_transition_into_failed_is_critical(monkeypatch):
    sent = _capture(monkeypatch)
    assert ce.alert_campaign_status_transition("running", "failed") is True
    assert sent == [("critical", "campaign:failed", None)]


def test_transition_into_stopped_is_warning(monkeypatch):
    sent = _capture(monkeypatch)
    assert ce.alert_campaign_status_transition("running", "stopped") is True
    assert sent[0][0] == "warning"
    assert sent[0][1] == "campaign:stopped"


def test_error_and_aborted_are_critical(monkeypatch):
    sent = _capture(monkeypatch)
    assert ce.alert_campaign_status_transition("running", "error") is True
    assert ce.alert_campaign_status_transition("running", "aborted") is True
    assert [s[0] for s in sent] == ["critical", "critical"]


def test_completed_is_not_alerted(monkeypatch):
    sent = _capture(monkeypatch)
    # A clean finish is not an incident.
    assert ce.alert_campaign_status_transition("running", "completed") is False
    assert sent == []


def test_no_alert_when_status_unchanged(monkeypatch):
    sent = _capture(monkeypatch)
    assert ce.alert_campaign_status_transition("failed", "failed") is False
    assert sent == []


def test_transition_out_of_failure_not_alerted(monkeypatch):
    sent = _capture(monkeypatch)
    # Only transitions INTO a stop/failure state alert; recovery does not.
    assert ce.alert_campaign_status_transition("failed", "running") is False
    assert sent == []


def test_case_and_whitespace_insensitive(monkeypatch):
    sent = _capture(monkeypatch)
    assert ce.alert_campaign_status_transition("RUNNING", "  Failed ") is True
    assert sent[0] == ("critical", "campaign:failed", None)


def test_payload_forwarded(monkeypatch):
    sent = _capture(monkeypatch)
    payload = {"reason": "stop_requested", "symbol": "BTC/USDT"}
    ce.alert_campaign_status_transition("running", "stopped", payload)
    assert sent[0][2] == payload


def test_never_raises_when_send_fails(monkeypatch):
    def _boom(level, message, payload):
        raise RuntimeError("dispatcher down")

    monkeypatch.setattr(ce, "_send", _boom)
    # A raising channel must be swallowed; returns False, does not propagate.
    assert ce.alert_campaign_status_transition("running", "failed") is False


def test_failed_transition_emits_campaign_ended_event(monkeypatch):
    from services.events.platform_event_journal import load_platform_events

    sent = _capture(monkeypatch)
    payload = {"reason": "boom", "symbol": "BTC/USD", "strategy_id": "es_daily_trend_v1"}

    assert ce.alert_campaign_status_transition("running", "failed", payload) is True

    assert sent == [("critical", "campaign:failed", payload)]
    events = load_platform_events(event_type="CampaignEnded")
    assert len(events) == 1
    event = events[0]
    assert event["provenance"]["strategy_id"] == "es_daily_trend_v1"
    assert event["payload"]["prev_status"] == "running"
    assert event["payload"]["new_status"] == "failed"
    assert event["payload"]["reason"] == "boom"
    assert event["payload"]["symbol"] == "BTC/USD"


def test_completed_transition_emits_campaign_ended_event_without_alert(monkeypatch):
    from services.events.platform_event_journal import load_platform_events

    sent = _capture(monkeypatch)

    assert ce.alert_campaign_status_transition("running", "completed", {"reason": "normal"}) is False

    assert sent == []
    events = load_platform_events(event_type="CampaignEnded")
    assert len(events) == 1
    assert events[0]["payload"]["new_status"] == "completed"
    assert events[0]["payload"]["reason"] == "normal"


def test_alert_failure_does_not_block_campaign_ended_event(monkeypatch):
    from services.events.platform_event_journal import load_platform_events

    def _boom(level, message, payload):
        raise RuntimeError("dispatcher down")

    monkeypatch.setattr(ce, "_send", _boom)

    assert ce.alert_campaign_status_transition("running", "failed", {"reason": "boom"}) is False
    events = load_platform_events(event_type="CampaignEnded")
    assert len(events) == 1
    assert events[0]["payload"]["new_status"] == "failed"
