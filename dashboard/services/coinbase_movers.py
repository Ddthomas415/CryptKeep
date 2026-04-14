"""dashboard/services/coinbase_movers.py
Re-exports from canonical services/market_data/coinbase_movers.py.
"""
import warnings
warnings.warn(
    "dashboard.services.coinbase_movers is deprecated; use services.market_data.coinbase_movers",
    DeprecationWarning, stacklevel=2,
)
from services.market_data.coinbase_movers import fetch_coinbase_movers  # noqa: F401

