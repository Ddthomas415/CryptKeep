"""
dashboard/services/view_data.py — public API facade

Implementation has moved to dashboard/services/views/.
All existing callers continue to work without changes.
New code should import directly from the sub-modules.
"""
from __future__ import annotations

from services.admin.config_editor import (  # noqa: F401
    CONFIG_PATH,
    load_user_yaml,
    save_user_yaml,
)

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
    _load_local_recent_activity,
    _resolve_execution_db_path,
    _load_local_recommendations,
    _load_local_pending_approvals,
    _load_local_open_orders,
    _load_local_failed_orders,
    _load_local_connections_summary,
    _load_local_risk_overlay,
    _read_mock_envelope,
    _request_envelope_from_base,
    _request_envelope,
    _fetch_envelope,
    _asset_priority,
    _build_watchlist_preview,
    _apply_local_summary_overrides,
    _apply_local_settings_overrides,
    _apply_local_execution_state_to_recommendations,
    _gate_state_to_risk_status,
    _load_current_regime,
    _load_signal_reliability,
    _explain_mentions_foreign_asset,
)
from dashboard.services.views._shared_market import (  # noqa: F401
    _get_market_price_series,
    _load_automation_operations_snapshot,
)
from dashboard.services.views._shared_signals import (  # noqa: F401
    _enrich_signal_row,
)
from dashboard.services.views._shared_http import (  # noqa: F401
    PHASE1_ORCHESTRATOR_URL,
)


# facade exports for split view modules/tests
from dashboard.services.views._shared_ops import (
    _load_local_kill_switch_state as _ops__load_local_kill_switch_state,
    _load_local_system_guard_state as _ops__load_local_system_guard_state,
)

_load_local_kill_switch_state = _ops__load_local_kill_switch_state
_load_local_system_guard_state = _ops__load_local_system_guard_state
