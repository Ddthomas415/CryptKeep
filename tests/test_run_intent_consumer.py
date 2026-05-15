from __future__ import annotations

from scripts import run_intent_consumer as script


def test_run_intent_consumer_uses_live_module():
    assert script.run_forever.__module__ == "services.execution.live_intent_consumer"
    assert script.request_stop.__module__ == "services.execution.live_intent_consumer"
