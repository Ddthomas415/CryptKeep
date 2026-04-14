"""
dashboard/services/view_data.py — public API facade

Implementation has moved to dashboard/services/views/.
All existing callers continue to work without changes.
New code should import directly from the sub-modules.
"""
from __future__ import annotations

from dashboard.services.views.summary_view import (   # noqa: F401
    get_dashboard_summary,
    get_overview_view,
)
from dashboard.services.views.market_view import (    # noqa: F401
    get_markets_view,
    get_research_explain,
)
from dashboard.services.views.signals_view import (   # noqa: F401
    get_recommendations,
    get_signals_view,
)
from dashboard.services.views.execution_view import ( # noqa: F401
    get_recent_activity,
    get_portfolio_view,
    get_trades_view,
)
from dashboard.services.views.settings_view import (  # noqa: F401
    get_settings_view,
    update_settings_view,
    get_automation_view,
    update_automation_view,
)

# Private helpers explicitly re-exported for legacy callers
from dashboard.services.views._shared import (  # noqa: F401
    _attach_data_provenance,
    _repo_default_watchlist_assets,
    _default_watchlist_rows,
    _default_dashboard_summary,
    _default_recommendations,
    _default_activity,
    _default_positions,
    _default_recent_fills,
    _default_settings_payload,
    _default_explain_payload,
    _derive_market_bias,
    _derive_volume_trend,
    _normalize_asset_symbol,
    _normalize_signal_action,
    _normalize_signal_status,
    _normalize_order_status,
    _build_price_series,
    _extract_close_series,
    _to_price,
    _snapshot_spread,
    _canonical_market_symbol,
    _normalize_market_snapshot,
    _load_local_market_snapshot,
    _get_market_snapshot,
    _load_local_ohlcv,
    _load_local_portfolio_snapshot,
    _load_local_recent_fills,
    _load_local_pending_approvals,
    _load_local_open_orders,
    _load_local_failed_orders,
    _read_mock_envelope,
    _request_envelope_from_base,
    _request_envelope,
    _fetch_envelope,
    _asset_priority,
    _build_watchlist_preview,
)
