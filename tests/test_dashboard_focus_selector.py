from __future__ import annotations

from dashboard.components.focus_selector import resolve_focus_options


def test_resolve_focus_options_prefers_selected_asset() -> None:
    rows = [{"asset": "BTC"}, {"asset": "SOL"}]
    options, default_asset = resolve_focus_options(rows, selected_asset="SOL", fallback_asset="ETH")
    assert options == ["BTC", "SOL"]
    assert default_asset == "SOL"


def test_resolve_focus_options_falls_back_to_first_available_asset() -> None:
    rows = [{"asset": "BTC"}, {"asset": "SOL"}]
    options, default_asset = resolve_focus_options(rows, selected_asset="ETH", fallback_asset="ADA")
    assert options == ["BTC", "SOL"]
    assert default_asset == "BTC"


def test_resolve_focus_options_uses_fallback_when_rows_empty() -> None:
    options, default_asset = resolve_focus_options([], selected_asset=None, fallback_asset="SOL")
    assert options == []
    assert default_asset == "SOL"
