# Stub to prevent panel crash
class PaperTradingSQLite:
    def __init__(self):
        pass
    def init_db(self):
        return True
    def get_open_positions(self):
        return []
    def get_last_fills(self, limit=10):
        return []
