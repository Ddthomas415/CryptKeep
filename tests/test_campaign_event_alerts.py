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

import services.alerts.campaign_events as ce


def _capture(monkeypatch):
    sent: list[tuple[str, str, dict | None]] = []
    monkeypatch.setattr(
        ce, "_send",
        lambda level, message, payload: sent.append((level, message, payload)),
    )
    return sent


def test_first_observation_is_silent_baseline(monkeypatch):
    sent = _capture(monkeypatch)
    # No previous status -> nothing to transition from.
    assert ce.alert_campaign_status_transition("", "failed") is False
    assert sent == []


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
