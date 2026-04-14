"""dashboard/services/views/_shared.py — facade, re-exports all private helpers."""
from __future__ import annotations

from dashboard.services.views._shared_execution import (  # noqa: F401
    _apply_local_execution_state_to_recommendations,
    _default_activity,
    _default_positions,
    _default_recent_fills,
    _load_local_failed_orders,
    _load_local_open_orders,
    _load_local_pending_approvals,
    _load_local_recent_activity,
    _load_local_recent_fills,
    _normalize_order_status,
    _resolve_execution_db_path,
)
from dashboard.services.views._shared_http import (  # noqa: F401
    _fetch_envelope,
    _read_mock_envelope,
    _request_envelope,
    _request_envelope_from_base,
)
from dashboard.services.views._shared_market import (  # noqa: F401
    _build_price_series,
    _build_watchlist_preview,
    _canonical_market_symbol,
    _default_watchlist_rows,
    _derive_market_bias,
    _get_market_price_series,
    _get_market_snapshot,
    _load_automation_operations_snapshot,
    _load_local_market_snapshot,
    _load_local_ohlcv,
    _load_local_portfolio_snapshot,
    _normalize_market_snapshot,
    _repo_default_watchlist_assets,
    _snapshot_spread,
    _to_price,
)
from dashboard.services.views._shared_ops import (  # noqa: F401
    _apply_local_summary_overrides,
    _default_dashboard_summary,
    _gate_state_to_risk_status,
    _load_local_connections_summary,
    _load_local_kill_switch_state,
    _load_local_risk_overlay,
    _load_local_system_guard_state,
)
from dashboard.services.views._shared_settings import (  # noqa: F401
    _apply_local_settings_overrides,
    _default_settings_payload,
)
from dashboard.services.views._shared_shared import (  # noqa: F401
    _attach_data_provenance,
    _derive_volume_trend,
    _extract_close_series,
    _normalize_asset_symbol,
)
from dashboard.services.views._shared_signals import (  # noqa: F401
    _asset_priority,
    _dedupe_recommendation_rows,
    _default_explain_payload,
    _default_recommendations,
    _enrich_signal_row,
    _explain_mentions_foreign_asset,
    _load_current_regime,
    _load_local_recommendations,
    _load_signal_reliability,
    _normalize_signal_action,
    _normalize_signal_status,
)
