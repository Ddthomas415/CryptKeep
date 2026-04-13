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

# Private helpers re-exported for any legacy caller using private names
from dashboard.services.views._shared import *  # noqa: F401,F403
