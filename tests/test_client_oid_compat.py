from __future__ import annotations

from services.execution.client_oid import make_client_oid32


def test_client_oid_accepts_intent_id_and_is_deterministic():
    a = make_client_oid32(intent_id="intent-123", prefix="cbp")
    b = make_client_oid32(intent_id="intent-123", prefix="cbp")
    c = make_client_oid32(intent_id="intent-456", prefix="cbp")

    assert a == b
    assert a != c
    assert len(a) <= 32
    assert "-" in a


def test_client_oid_random_fallback_without_intent_id():
    a = make_client_oid32(prefix="cbp")
    b = make_client_oid32(prefix="cbp")

    assert len(a) <= 32
    assert len(b) <= 32
    assert a != b

