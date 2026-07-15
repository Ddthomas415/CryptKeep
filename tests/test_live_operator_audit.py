from __future__ import annotations

from services.admin import live_operator_audit


def test_record_live_disable_event_writes_required_operator_payload(monkeypatch):
    calls: list[dict] = []

    def _append(**kwargs):
        calls.append(dict(kwargs))
        return {"event_id": "evt-1", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setattr(live_operator_audit, "append_operator_event", _append)

    out = live_operator_audit.record_live_disable_event(
        source="test",
        reason="operator_stop",
        result="ok",
        pre_state={"live_enabled": True},
        post_state={"live_enabled": False},
        extra={"run_id": "run-1"},
    )

    assert out == {"ok": True, "event_id": "evt-1", "path": "/tmp/operator_events.jsonl"}
    assert calls == [
        {
            "actor": "operator",
            "action": "live_disable",
            "target": "live_trading",
            "result": "ok",
            "reason": "operator_stop",
            "pre_state": {"live_enabled": True},
            "post_state": {"live_enabled": False},
            "source": "test",
            "extra": {"run_id": "run-1"},
        }
    ]


def test_record_live_enable_event_writes_required_operator_payload(monkeypatch):
    calls: list[dict] = []

    def _append(**kwargs):
        calls.append(dict(kwargs))
        return {"event_id": "evt-enable", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setattr(live_operator_audit, "append_operator_event", _append)

    out = live_operator_audit.record_live_enable_event(
        source="token_ceremony",
        reason="token_enable_live",
        result="ok",
        pre_state={"live_enabled_before": False},
        post_state={"changed": {"execution.live_enabled": True}},
        extra={"preflight": {"ok": True}},
    )

    assert out == {"ok": True, "event_id": "evt-enable", "path": "/tmp/operator_events.jsonl"}
    assert calls == [
        {
            "actor": "operator",
            "action": "live_enable",
            "target": "live_trading",
            "result": "ok",
            "reason": "token_enable_live",
            "pre_state": {"live_enabled_before": False},
            "post_state": {"changed": {"execution.live_enabled": True}},
            "source": "token_ceremony",
            "extra": {"preflight": {"ok": True}},
        }
    ]


def test_record_live_resume_event_writes_required_operator_payload(monkeypatch):
    calls: list[dict] = []

    def _append(**kwargs):
        calls.append(dict(kwargs))
        return {"event_id": "evt-resume", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setattr(live_operator_audit, "append_operator_event", _append)

    out = live_operator_audit.record_live_resume_event(
        source="resume_gate",
        reason="post_halt_resume",
        result="ok",
        pre_state={"provenance": {"ok": True}},
        post_state={"system_guard": {"state": "RUNNING"}},
    )

    assert out == {"ok": True, "event_id": "evt-resume", "path": "/tmp/operator_events.jsonl"}
    assert calls == [
        {
            "actor": "operator",
            "action": "live_resume",
            "target": "live_trading",
            "result": "ok",
            "reason": "post_halt_resume",
            "pre_state": {"provenance": {"ok": True}},
            "post_state": {"system_guard": {"state": "RUNNING"}},
            "source": "resume_gate",
            "extra": {},
        }
    ]


def test_record_live_disable_event_failure_is_reported_not_raised(monkeypatch):
    def _append(**_kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(live_operator_audit, "append_operator_event", _append)

    out = live_operator_audit.record_live_disable_event(
        source="test",
        reason="operator_stop",
        pre_state={},
        post_state={},
    )

    assert out == {"ok": False, "reason": "operator_event_write_failed:PermissionError"}


def test_risk_increasing_operator_event_failure_is_reported_not_raised(monkeypatch):
    def _append(**_kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(live_operator_audit, "append_operator_event", _append)

    out = live_operator_audit.record_live_enable_event(
        source="test",
        reason="enable",
        pre_state={},
        post_state={},
    )

    assert out == {"ok": False, "reason": "operator_event_write_failed:PermissionError"}
