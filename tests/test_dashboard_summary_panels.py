from __future__ import annotations

from dashboard.components.summary_panels import resolve_asset_row


def test_resolve_asset_row_returns_matching_asset() -> None:
    rows = [
        {"asset": "BTC", "summary": "Range trade"},
        {"asset": "SOL", "summary": "Momentum"},
    ]
    payload = resolve_asset_row(rows, asset="SOL")
    assert payload["summary"] == "Momentum"


def test_resolve_asset_row_returns_empty_dict_when_missing() -> None:
    rows = [{"asset": "BTC", "summary": "Range trade"}]
    payload = resolve_asset_row(rows, asset="ETH")
    assert payload == {}
