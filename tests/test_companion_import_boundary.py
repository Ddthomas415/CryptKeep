"""Execute actual tools source with synthetic configuration and blocked repo imports."""
import asyncio
import builtins
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "phase1_research_copilot/shared/tools.py"


def load_tools(*, dashboard_available=True):
    attempts, invocations = [], []
    settings = SimpleNamespace(log_level="INFO", memory_service_url="http://memory-retrieval:8007",
                               risk_service_url="http://risk-stub:8008")
    def build(*args, **kwargs):
        invocations.append((args, kwargs))
        return {"status": "synthetic-dashboard-result"}
    def forbidden(*args, **kwargs):
        pytest.fail("unexpected external access")
    modules = {
        "shared.config": SimpleNamespace(get_settings=lambda: settings),
        "shared.logging": SimpleNamespace(configure_logging=lambda *a: SimpleNamespace(warning=forbidden)),
        "shared.retry": SimpleNamespace(retry_async=forbidden),
        "shared.probe": SimpleNamespace(probe_active=lambda: True, probe_headers=forbidden,
                                         require_probe_origin=forbidden),
        "httpx": SimpleNamespace(AsyncClient=forbidden),
        "sys": SimpleNamespace(path=["/app", "/repo"]),
    }
    real_import = builtins.__import__
    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith(("dashboard", "services", "storage")):
            attempts.append(name)
            if dashboard_available and name == "dashboard.services.intelligence":
                return SimpleNamespace(build_opportunity_snapshot=build)
            raise ModuleNotFoundError(name)
        if name in modules:
            return modules[name]
        return real_import(name, globals, locals, fromlist, level)
    namespace = {"__name__": "synthetic_companion_tools", "__file__": "/app/shared/tools.py",
                 "__builtins__": {**vars(builtins), "__import__": guarded}}
    exec(compile(SOURCE.read_bytes(), str(SOURCE), "exec"), namespace)
    return namespace, attempts, invocations


def test_import_and_bounded_retrieval_do_not_load_dashboard_or_repository_services():
    tools, attempts, invocations = load_tools(dashboard_available=False)
    assert attempts == []
    requests = []
    async def request(method, url, **kwargs):
        requests.append((method, url, kwargs))
        if method == "POST":
            return {"ok": True, "synthetic": "stored-retrieval"}
        return {"gate": "NO_TRADING", "allow_trading": False, "execution_mode": "DISABLED"}
    tools["_request_json"] = request
    result = asyncio.run(tools["get_probe_tool_results"]("BTC", "question", 60))
    assert result["get_signal_summary"] == {"ok": True, "synthetic": "stored-retrieval"}
    assert [r[:2] for r in requests] == [
        ("POST", "http://memory-retrieval:8007/v1/memory/retrieve"),
        ("GET", "http://risk-stub:8008/v1/risk/status")]
    assert attempts == invocations == []


def test_ordinary_intelligence_capability_is_still_invoked_with_same_arguments():
    tools, attempts, invocations = load_tools()
    assert attempts == []
    result = tools["build_opportunity_snapshot"]("positional", option="same")
    assert result == {"status": "synthetic-dashboard-result"}
    assert attempts == ["dashboard.services.intelligence"]
    assert invocations == [(("positional",), {"option": "same"})]


def test_ordinary_signal_summary_retains_dashboard_intelligence():
    tools, attempts, invocations = load_tools()
    assert attempts == []
    async def request(method, url, **kwargs):
        return {"market": {"latest_price": 100}} if method == "POST" else None
    tools["_request_json"] = request
    result = asyncio.run(tools["get_signal_summary"]("BTC"))
    assert result["intelligence"] == {"status": "synthetic-dashboard-result"}
    assert result["source"] == "memory-retrieval"
    assert invocations[0][1]["signal_row"]["asset"] == "BTC"
    assert attempts == ["dashboard.services.intelligence"]


def test_missing_dashboard_keeps_existing_explicit_unavailable_result():
    tools, attempts, invocations = load_tools(dashboard_available=False)
    assert attempts == []
    assert tools["build_opportunity_snapshot"](unknown="preserved") == {
        "status": "unavailable", "reason": "dashboard_import_failed", "opportunities": []}
    assert attempts == ["dashboard.services.intelligence"] and invocations == []
