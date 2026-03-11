import asyncio
import importlib

import pytest


HEALTH_TARGETS = [
    "services.gateway.routes.health:health",
    "services.orchestrator.app:health",
    "services.market_data.app:health",
    "services.news_ingestion.app:health",
    "services.archive_lookup.app:health",
    "services.parser_normalizer.app:health",
    "services.memory.app:health",
    "services.risk_stub.app:health",
    "services.execution_sim.app:health",
    "services.audit_log.app:health",
]


def _maybe_await(value):
    if asyncio.iscoroutine(value):
        return asyncio.run(value)
    return value


@pytest.mark.parametrize("target", HEALTH_TARGETS)
def test_health_endpoints_return_ok_payload(target: str):
    module_name, fn_name = target.split(":", 1)
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        pytest.skip(f"skipping {target}: missing dependency ({exc})")

    fn = getattr(module, fn_name)
    assert _maybe_await(fn()) == {"status": "ok"}
