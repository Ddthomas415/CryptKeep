from __future__ import annotations
TOKEN1 = ".create_" + "order("
TOKEN2 = ".create" + "Order("


import unittest
from pathlib import Path

ALLOWED = {
    "services/execution/place_order.py",
}

SKIP_DIRS = {'tools', 'attic', ".venv", "venv", "__pycache__", ".git", "data", "docs", "dist", "build", ".pytest_cache"}

class TestNoDirectCreateOrder(unittest.TestCase):
    def test_no_direct_create_order_outside_place_order(self):
        root = Path(__file__).resolve().parents[1]
        hits = []
        for p in root.rglob("*.py"):
            rel = p.relative_to(root).as_posix()
            parts = set(p.parts)
            if any(part.startswith(".venv") for part in p.parts):
                continue
            if any(s in parts for s in SKIP_DIRS):
                continue
            if rel in ALLOWED:
                continue

            txt = p.read_text(encoding="utf-8", errors="replace")
            if TOKEN1 in txt or TOKEN2 in txt:
                for i, line in enumerate(txt.splitlines(), start=1):
                    if TOKEN1 in line or TOKEN2 in line:
                        hits.append(f"{rel}:{i}  {line.strip()[:240]}")

        if hits:
            msg = "Direct create_order usage found outside place_order.py:\n" + "\n".join(hits[:200])
            self.fail(msg)

if __name__ == "__main__":
    unittest.main()
