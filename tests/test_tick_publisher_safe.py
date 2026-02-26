from __future__ import annotations

import importlib

def test_tick_publisher_imports():
    importlib.import_module("scripts.run_tick_publisher")
