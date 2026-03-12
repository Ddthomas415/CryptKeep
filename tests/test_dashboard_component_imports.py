from __future__ import annotations

import importlib


def test_dashboard_component_modules_import_together() -> None:
    modules = [
        "dashboard.components",
        "dashboard.components.asset_detail",
        "dashboard.components.focus_selector",
        "dashboard.components.kpi_builders",
        "dashboard.components.summary_panels",
    ]

    imported = {name: importlib.import_module(name) for name in modules}

    package = imported["dashboard.components"]
    assert callable(package.build_asset_detail_metrics)
    assert callable(package.build_focus_summary_metrics)
    assert callable(package.render_asset_detail_card)
    assert callable(package.render_focus_selector)
    assert callable(package.build_overview_kpis)
    assert callable(package.render_market_context)
    assert callable(package.build_market_snapshot_lines)
    assert callable(package.build_market_context_metrics)

    assert callable(imported["dashboard.components.asset_detail"].render_research_lens)
    assert callable(imported["dashboard.components.focus_selector"].resolve_focus_options)
    assert callable(imported["dashboard.components.kpi_builders"].build_signals_kpis)
    assert callable(imported["dashboard.components.summary_panels"].resolve_asset_row)
