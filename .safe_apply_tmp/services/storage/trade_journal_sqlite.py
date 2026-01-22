# Stub to prevent panel crash
class TradeJournalSQLite:
    def __init__(self):
        pass
    def init_journal(self):
        return True
    def get_trades(self, limit=100):
        return []
