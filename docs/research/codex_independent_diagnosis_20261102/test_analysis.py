import importlib.util
from pathlib import Path
import unittest

def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

class AnalysisTests(unittest.TestCase):
    def test_open_events_excluded_and_repeated_exposures_disclosed(self):
        events = [{"symbol": "A", "entry_time": 1, "net_pnl_usd": 10, "gross_return": .02, "status": "TARGET_EXIT"},
                  {"symbol": "A", "entry_time": 1, "net_pnl_usd": -30, "gross_return": -.02, "status": "TIMEOUT_EXIT"},
                  {"symbol": "B", "entry_time": 2, "status": "OPEN_AT_SEGMENT_END"}]
        result = load("analyze_saved").closed_events(events)
        self.assertEqual(result["closed"], 2)
        self.assertEqual(result["mean_net_usd_per_event"], -10)
        self.assertEqual(result["duplicate_symbol_entry_exposures"], 1)
        self.assertEqual(result["target_exit_sum_usd"] + result["timeout_exit_sum_usd"], -20)

    def test_config_filter_discards_credentials_and_unapproved_nested_fields(self):
        result = load("capture_config").filtered({"venue": "coinbase", "api_key": "private",
            "strategy": {"name": "momentum", "secret": "private"}, "symbols": ["BTC/USD"],
            "token": "private", "arbitrary": {"password": "private"}})
        self.assertEqual(result, {"venue": "coinbase", "symbols": ["BTC/USD"], "strategy.name": "momentum"})

if __name__ == "__main__":
    unittest.main()
