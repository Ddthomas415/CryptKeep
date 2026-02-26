# Phase IF: Position Accounting (skeleton)
from services.os.app_paths import data_dir, ensure_dirs

class PositionAccounting:
    def __init__(self, db_path=None):
        ensure_dirs()
        self.db_path = db_path or str(data_dir() / "portfolio.sqlite")

    def apply_fill(self, fill: dict):
        """Apply BUY/SELL fill to positions + cash ledger."""
        pass

    def snapshot(self) -> dict:
        return {
            "positions": [],
            "cash": {},
            "realized": 0.0,
            "unrealized": 0.0,
        }
