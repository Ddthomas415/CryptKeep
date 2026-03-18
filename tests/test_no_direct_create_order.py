from __future__ import annotations
import unittest
from pathlib import Path

from scripts.verify_no_direct_create_order import scan

class TestNoDirectCreateOrder(unittest.TestCase):
    def test_no_direct_create_order_outside_place_order(self):
        root = Path(__file__).resolve().parents[1]
        hits = [
            f"{row['file']}:{row['line']}  {row['text']}"
            for row in scan(root)
        ]

        if hits:
            msg = "Direct create_order usage found outside place_order.py:\n" + "\n".join(hits[:200])
            self.fail(msg)

if __name__ == "__main__":
    unittest.main()
