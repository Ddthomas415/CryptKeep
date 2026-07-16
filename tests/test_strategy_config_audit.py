from __future__ import annotations

from typing import Any

from services.admin import strategy_config_audit as audit


def test_strategy_state_extracts_only_strategy_mapping() -> None:
    assert audit.strategy_state({"strategy": {"name": "ema_cross"}, "api_key": "secret"}) == {
        "name": "ema_cross",
    }
    assert audit.strategy_state({"strategy": "ema_cross"}) == {}
    assert audit.strategy_state(None) == {}


def test_record_strategy_config_change_appends_operator_event(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    def _append_operator_event(**kwargs):
        calls.append(kwargs)
        return {"event_id": "evt-strategy", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setattr(audit, "append_operator_event", _append_operator_event)

    result = audit.record_strategy_config_change(
        pre_cfg={"strategy": {"name": "ema_cross", "trade_enabled": True}},
        post_cfg={"strategy": {"name": "pullback_recovery", "trade_enabled": False}},
        change_source="operations_strategy_params",
        source="dashboard.pages.60_Operations",
    )

    assert result == {"ok": True, "event_id": "evt-strategy", "path": "/tmp/operator_events.jsonl"}
    assert calls == [
        {
            "actor": "operator",
            "action": "strategy_config_change",
            "target": "user.yaml:strategy",
            "result": "success",
            "reason": "operations_strategy_params",
            "pre_state": {"strategy": {"name": "ema_cross", "trade_enabled": True}},
            "post_state": {"strategy": {"name": "pullback_recovery", "trade_enabled": False}},
            "source": "dashboard.pages.60_Operations",
            "extra": {
                "surface": "dashboard_operations",
                "change_source": "operations_strategy_params",
            },
        }
    ]


def test_record_strategy_config_change_skips_unchanged_strategy(monkeypatch) -> None:
    monkeypatch.setattr(
        audit,
        "append_operator_event",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("unchanged strategy should not append an event")
        ),
    )

    result = audit.record_strategy_config_change(
        pre_cfg={"strategy": {"name": "ema_cross"}},
        post_cfg={"strategy": {"name": "ema_cross"}, "other": True},
        change_source="operations_strategy_params",
        source="dashboard.pages.60_Operations",
    )

    assert result == {"ok": True, "skipped": True, "reason": "strategy_config_unchanged"}


def test_record_strategy_config_change_failure_is_explicit(monkeypatch) -> None:
    def _append_operator_event(**_kwargs):
        raise PermissionError("journal denied")

    monkeypatch.setattr(audit, "append_operator_event", _append_operator_event)

    result = audit.record_strategy_config_change(
        pre_cfg={"strategy": {"name": "ema_cross"}},
        post_cfg={"strategy": {"name": "pullback_recovery"}},
        change_source="operations_strategy_params",
        source="dashboard.pages.60_Operations",
    )

    assert result == {"ok": False, "reason": "operator_event_write_failed:PermissionError"}
