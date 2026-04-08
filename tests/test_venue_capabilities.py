from services.execution.venue_capabilities import (
    get_venue_capabilities,
    retry_is_safe_after_ambiguous_ack,
)


def test_gateio_capabilities_match_safe_client_oid_retry_contract():
    caps = get_venue_capabilities("gateio")

    assert caps is not None
    assert caps.supports_client_oid_lookup is True
    assert caps.idempotency_window_sec == 1800
    assert retry_is_safe_after_ambiguous_ack(
        venue="gateio",
        has_remote_order_id=False,
        age_sec=60,
    ) is True
