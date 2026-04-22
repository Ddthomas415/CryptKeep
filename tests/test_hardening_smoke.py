import pytest

from scripts.run_bot_runner import desired_services
from scripts.supervisor import status as supervisor_status
from services.execution.execution_context import (
    ExecutionContext,
    LiveAuthorityViolation,
    _authorize_live,
)
from services.execution.state_authority import (
    LiveStateContext,
    LiveStateViolation,
    _authorize_state_write,
)


def test_live_orchestration_composition() -> None:
    services = desired_services(
        {"mode": "live", "live_enabled": True, "with_reconcile": True}
    )
    assert "intent_consumer" in services
    assert "reconciler" in services
    assert "executor" not in services
    assert "live_executor" not in services


def test_submit_authority_blocks_non_owner() -> None:
    with pytest.raises(LiveAuthorityViolation):
        _authorize_live(None)

    with pytest.raises(LiveAuthorityViolation):
        _authorize_live(
            ExecutionContext(
                mode="live",
                authority="NON_SUBMITTING_LIVE",
                origin="legacy_path",
            )
        )


def test_submit_authority_allows_owner() -> None:
    _authorize_live(
        ExecutionContext(
            mode="live",
            authority="LIVE_SUBMIT_OWNER",
            origin="intent_consumer",
        )
    )


def test_state_write_authority_allows_canonical_owners() -> None:
    _authorize_state_write(
        LiveStateContext(authority="INTENT_CONSUMER", origin="intent_consumer")
    )
    _authorize_state_write(
        LiveStateContext(authority="RECONCILER", origin="intent_reconciler")
    )


def test_state_write_authority_blocks_unknown() -> None:
    with pytest.raises(LiveStateViolation):
        _authorize_state_write(None)

    with pytest.raises(LiveStateViolation):
        _authorize_state_write(
            LiveStateContext(authority="UNKNOWN", origin="legacy_path")
        )


def test_status_reports_hardened_truth() -> None:
    status = supervisor_status()
    rt = status.get("runtime_truth", {})
    assert rt.get("canonical_submit_owner") == "intent_consumer"
    assert "executor" in rt.get("blocked_legacy_services", [])
    assert rt.get("topology_aligned") is True
