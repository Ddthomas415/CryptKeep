from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

WS_SURFACES = {
    "services/market_data/ws_ticker_feed.py": "Optional real ticker websocket wrapper",
    "scripts/data/run_ws_ticker_feed.py": "Operator service wrapper for ticker websocket",
    "scripts/run_ws_ticker_feed.py": "Compatibility wrappers",
    "scripts/run_ws_ticker_feed_safe.py": "Compatibility wrappers",
    "services/fills/user_stream_ws.py": "Optional authenticated user-trade websocket service",
    "services/fills/user_stream_router.py": "Canonical user-stream fill routing adapter",
    "scripts/dev/run_user_stream_fills.py": "User-stream fill service CLI and wrapper",
    "scripts/run_user_stream_fills.py": "User-stream fill service CLI and wrapper",
    "services/market_data/ws_clients.py": "Status helper, not a websocket client",
    "services/market_data/ws_common.py": "Normalization helper",
    "services/market_data/ws_feature_blacklist.py": "Feature disable/blacklist state",
    "services/monitoring/ws_health_logger.py": "Persisted websocket health logger",
    "services/ws/last_price_provider.py": "Last-price reader over tick-store quotes, not a websocket transport",
}


NON_TRANSPORT_HELPERS = {
    "services/market_data/ws_clients.py",
    "services/market_data/ws_common.py",
    "services/market_data/ws_feature_blacklist.py",
    "services/monitoring/ws_health_logger.py",
    "services/ws/last_price_provider.py",
}


def test_websocket_surface_classification_doc_covers_current_ws_surfaces() -> None:
    doc = (REPO / "docs/architecture/websocket_surface_classification.md").read_text(encoding="utf-8")
    for rel, status in WS_SURFACES.items():
        assert (REPO / rel).is_file(), rel
        assert f"`{rel}`" in doc
        assert status in doc


def test_ws_named_helpers_do_not_open_websocket_transports() -> None:
    transport_patterns = [
        r"\bccxt\.pro\b",
        r"\bwatch_ticker\b",
        r"\bwatchTicker\b",
        r"\bwatch_my_trades\b",
        r"\bwatchMyTrades\b",
    ]
    hits: list[str] = []
    for rel in sorted(NON_TRANSPORT_HELPERS):
        text = (REPO / rel).read_text(encoding="utf-8")
        for pattern in transport_patterns:
            if re.search(pattern, text):
                hits.append(f"{rel}:{pattern}")
    assert hits == []


def test_retired_marketdata_websocket_paths_are_not_reintroduced() -> None:
    assert list((REPO / "services/marketdata").glob("*.py")) == []
    assert not (REPO / "services/market_data/ws_microstructure_manager.py").exists()
    assert not (REPO / "services/marketdata/ws_microstructure_manager.py").exists()
