# Phase IF: Position Accounting (skeleton)

class PositionAccounting:
    def __init__(self, db_path="data/portfolio.sqlite"):
        self.db_path = db_path

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
