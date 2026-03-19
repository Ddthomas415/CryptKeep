from __future__ import annotations

import importlib


def test_dashboard_component_modules_import_together() -> None:
    modules = [
        "dashboard.components",
        "dashboard.components.activity",
        "dashboard.components.asset_detail",
        "dashboard.components.badges",
        "dashboard.components.digest",
        "dashboard.components.focus_selector",
        "dashboard.components.kpi_builders",
        "dashboard.components.summary_panels",
    ]

    imported = {name: importlib.import_module(name) for name in modules}

    package = imported["dashboard.components"]
    assert callable(package.normalize_activity_items)
    assert callable(package.render_activity_panel)
    assert callable(package.badge_html)
    assert callable(package.badge_row_html)
    assert callable(package.render_badge_row)
    assert callable(package.render_prompt_actions)
    assert callable(package.build_assistant_status_message)
    assert callable(package.build_assistant_status_summary)
    assert callable(package.build_asset_detail_metrics)
    assert callable(package.build_focus_summary_metrics)
    assert callable(package.render_asset_detail_card)
    assert callable(package.render_feature_hero)
    assert callable(package.render_digest_page_header)
    assert callable(package.render_runtime_truth_strip)
    assert callable(package.render_attention_now)
    assert callable(package.render_leaderboard_summary)
    assert callable(package.render_scorecard_snapshot)
    assert callable(package.render_crypto_edge_summary)
    assert callable(package.render_safety_warnings)
    assert callable(package.render_mode_truth_card)
    assert callable(package.render_freshness_panel)
    assert callable(package.render_recent_incidents)
    assert callable(package.render_next_best_action)
    assert callable(package.render_focus_selector)
    assert callable(package.build_automation_kpis)
    assert callable(package.build_overview_kpis)
    assert callable(package.build_portfolio_kpis)
    assert callable(package.build_settings_kpis)
    assert callable(package.build_trades_kpis)
    assert callable(package.build_automation_runtime_metrics)
    assert callable(package.render_market_context)
    assert callable(package.build_market_snapshot_lines)
    assert callable(package.build_market_context_metrics)
    assert callable(package.build_operations_status_metrics)
    assert callable(package.build_overview_status_metrics)
    assert callable(package.build_portfolio_position_metrics)
    assert callable(package.build_settings_profile_metrics)
    assert callable(package.build_trade_failure_metrics)
    assert callable(package.build_trades_queue_metrics)
    assert callable(package.render_automation_runtime_summary)
    assert callable(package.render_operations_status_summary)
    assert callable(package.render_portfolio_position_summary)
    assert callable(package.render_overview_status_summary)
    assert callable(package.render_settings_profile_summary)
    assert callable(package.render_trade_failure_summary)
    assert callable(package.render_trades_queue_summary)

    assert callable(imported["dashboard.components.asset_detail"].render_research_lens)
    assert callable(imported["dashboard.components.activity"].normalize_activity_items)
    assert callable(imported["dashboard.components.badges"].badge_row_html)
    assert callable(imported["dashboard.components.digest"].render_runtime_truth_strip)
    assert callable(imported["dashboard.components.focus_selector"].resolve_focus_options)
    assert callable(imported["dashboard.components.kpi_builders"].build_signals_kpis)
    assert callable(imported["dashboard.components.summary_panels"].build_overview_status_metrics)
    assert callable(imported["dashboard.components.summary_panels"].build_operations_status_metrics)
    assert callable(imported["dashboard.components.summary_panels"].resolve_asset_row)
