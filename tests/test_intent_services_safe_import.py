from __future__ import annotations
import importlib

def test_intent_executor_safe_imports():
    importlib.import_module("scripts.run_intent_executor_safe")

def test_intent_reconciler_safe_imports():
    importlib.import_module("scripts.run_intent_reconciler_safe")


def test_intent_consumer_safe_imports():
    importlib.import_module("scripts.run_intent_consumer_safe")


def test_live_reconciler_safe_imports():
    importlib.import_module("scripts.run_live_reconciler_safe")
