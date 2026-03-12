from dashboard.components.activity import normalize_activity_items, render_activity_panel
from dashboard.components.asset_detail import (
    build_asset_detail_metrics,
    build_focus_summary_metrics,
    render_asset_detail_card,
    render_evidence_section,
    render_focus_summary,
    render_research_lens,
)
from dashboard.components.actions import render_system_action_buttons
from dashboard.components.cards import render_kpi_cards
from dashboard.components.focus_selector import render_focus_selector, resolve_focus_options
from dashboard.components.forms import render_save_action
from dashboard.components.header import render_page_header
from dashboard.components.kpi_builders import (
    build_automation_kpis,
    build_markets_kpis,
    build_overview_kpis,
    build_portfolio_kpis,
    build_settings_kpis,
    build_signals_kpis,
    build_trades_kpis,
)
from dashboard.components.logs import render_action_result
from dashboard.components.sidebar import render_app_sidebar
from dashboard.components.summary_panels import (
    build_automation_runtime_metrics,
    build_market_context_metrics,
    build_market_snapshot_lines,
    build_operations_status_metrics,
    build_overview_status_metrics,
    build_portfolio_position_metrics,
    build_settings_profile_metrics,
    build_trade_failure_metrics,
    build_trades_queue_metrics,
    render_automation_runtime_summary,
    render_market_context,
    render_operations_status_summary,
    render_overview_status_summary,
    render_portfolio_position_summary,
    render_settings_profile_summary,
    render_trade_failure_summary,
    render_signal_thesis,
    render_trades_queue_summary,
    resolve_asset_row,
)
from dashboard.components.tables import render_table_section

__all__ = [
    "normalize_activity_items",
    "render_activity_panel",
    "render_page_header",
    "render_kpi_cards",
    "build_asset_detail_metrics",
    "build_focus_summary_metrics",
    "render_asset_detail_card",
    "render_evidence_section",
    "render_focus_summary",
    "render_research_lens",
    "render_focus_selector",
    "resolve_focus_options",
    "build_automation_kpis",
    "build_markets_kpis",
    "build_overview_kpis",
    "build_portfolio_kpis",
    "build_settings_kpis",
    "build_signals_kpis",
    "build_trades_kpis",
    "build_automation_runtime_metrics",
    "build_market_snapshot_lines",
    "build_market_context_metrics",
    "build_operations_status_metrics",
    "build_overview_status_metrics",
    "build_portfolio_position_metrics",
    "build_settings_profile_metrics",
    "build_trade_failure_metrics",
    "build_trades_queue_metrics",
    "render_automation_runtime_summary",
    "render_market_context",
    "render_operations_status_summary",
    "render_overview_status_summary",
    "render_portfolio_position_summary",
    "render_settings_profile_summary",
    "render_trade_failure_summary",
    "render_signal_thesis",
    "render_trades_queue_summary",
    "resolve_asset_row",
    "render_save_action",
    "render_system_action_buttons",
    "render_action_result",
    "render_app_sidebar",
    "render_table_section",
]
