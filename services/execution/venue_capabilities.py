from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VenueCapabilities:
    venue: str
    supports_client_oid_lookup: bool
    idempotency_window_sec: int | None


_CAPS = {
    "binance": VenueCapabilities("binance", True, 1800),
    "coinbase": VenueCapabilities("coinbase", True, None),
}


def get_venue_capabilities(venue: str) -> VenueCapabilities | None:
    return _CAPS.get(str(venue).strip().lower())


def retry_is_safe_after_ambiguous_ack(
    *,
    venue: str,
    has_remote_order_id: bool,
    age_sec: int | None,
) -> bool:
    if has_remote_order_id:
        return False
    caps = get_venue_capabilities(venue)
    if caps is None or not caps.supports_client_oid_lookup:
        return False
    if caps.idempotency_window_sec is None:
        return True
    return age_sec is not None and age_sec <= caps.idempotency_window_sec
