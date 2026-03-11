from __future__ import annotations

import importlib


def test_data_collector_module_is_import_safe_without_optional_adapters():
    mod = importlib.import_module("services.data_collector.main")
    assert mod is not None

