from backend.app.core.envelopes import failure, success


def test_success_envelope_contract() -> None:
    payload = success(data={"ok": True}, request_id="req_test_1")
    assert payload["request_id"] == "req_test_1"
    assert payload["status"] == "success"
    assert payload["data"] == {"ok": True}
    assert payload["error"] is None
    assert payload["meta"] == {}


def test_failure_envelope_contract() -> None:
    payload = failure(
        code="MODE_BLOCKED",
        message="Blocked by mode",
        details={"mode": "research_only"},
        request_id="req_test_2",
    )
    assert payload["request_id"] == "req_test_2"
    assert payload["status"] == "error"
    assert payload["data"] is None
    assert payload["error"]["code"] == "MODE_BLOCKED"
    assert payload["error"]["details"]["mode"] == "research_only"
