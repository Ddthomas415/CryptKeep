"""Archival-only exclusion over synthetic transport/DB; prior diagnosis archived."""
from copy import deepcopy
import ast
import json
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace

import httpx
import pytest

from scripts.research import companion_evidence_checks as checks
from tests.test_companion_archive_probe_scope import ROOT, retrieval
from tests.test_companion_probe_policy import AUTH, HEADER, PROFILE, loaded, request, run


@pytest.fixture(autouse=True)
def no_native(monkeypatch, loaded):
    attempted = []

    def forbidden(*args, **kwargs):
        attempted.append("native_or_socket")
        raise AssertionError("strict diagnosis attempted external operation")

    async def forbidden_http(*args, **kwargs):
        attempted.append("non_ASGI_HTTP")
        raise AssertionError("strict diagnosis attempted non-ASGI transport")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden_http)
    yield {"native": forbidden, "http": forbidden_http}
    assert attempted == [], "production code swallowed a forbidden operation"


def test_counting_hooks_survive_fixture_composition(no_native):
    assert socket.socket.connect is no_native["native"]
    assert socket.socket.connect_ex is no_native["native"]
    assert socket.getaddrinfo is no_native["native"]
    assert subprocess.Popen is no_native["native"]
    assert subprocess.run is no_native["native"]
    assert httpx.AsyncHTTPTransport.handle_async_request is no_native["http"]


def test_composed_guard_detects_swallowed_socket_error_on_synthetic_objects():
    tree = ast.parse(Path(__file__).read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "no_native")
    node.decorator_list = []
    fake_socket = SimpleNamespace(connect=None, connect_ex=None)
    ns = {"socket": SimpleNamespace(socket=fake_socket, getaddrinfo=None),
          "subprocess": SimpleNamespace(Popen=None, run=None),
          "httpx": SimpleNamespace(AsyncHTTPTransport=SimpleNamespace(handle_async_request=None))}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "synthetic_guard_only", "exec"), ns)
    fixture = ns["no_native"](SimpleNamespace(setattr=setattr), object())
    next(fixture)
    try:
        fake_socket.connect()
    except AssertionError:
        pass
    with pytest.raises(AssertionError, match="production code swallowed"):
        next(fixture)


@pytest.mark.parametrize("mode", ["absent", "positive", "zero"])
def test_strict_signal_to_bundle_with_synthetic_market_rows(loaded, monkeypatch, mode):
    memory, view, sql_calls = retrieval(loaded, monkeypatch)
    original_fetch = memory.db.fetch_all
    market_rows = [] if mode == "absent" else [{
        "price": 100.0 if mode == "positive" else 0.0,
        "event_ts": "2026-10-26T00:00:00+00:00", "source": "SYNTHETIC_ONLY",
        "symbol": "BTC/USDT", "bid": None, "ask": None, "volume": None,
    }]

    def fetch(sql, params):
        if "FROM market_ticks" in sql:
            sql_calls.append(sql)
            return deepcopy(market_rows)
        return original_fetch(sql, params)

    monkeypatch.setattr(memory.db, "fetch_all", fetch)
    calls = []

    async def transport(method, url, *, payload=None, **kwargs):
        assert loaded.probe.probe_active()
        calls.append((method, url))
        if method == "POST" and url.endswith("/v1/memory/retrieve"):
            response = await request(memory.app, "/v1/memory/retrieve",
                headers={**AUTH, HEADER: PROFILE}, payload=payload)
        elif method == "GET" and url.endswith("/v1/risk/status"):
            response = await request(loaded.risk_stub.app, "/v1/risk/status",
                headers={**AUTH, HEADER: PROFILE}, method="GET")
        else:
            pytest.fail("probe issued an unexpected tool request")
        assert response.status_code == 200
        return response.json()

    def forbidden(*args, **kwargs):
        pytest.fail("strict probe must not call standalone market/default/ordinary reasoning")

    audit_calls = []

    async def audit(service, action, **kwargs):
        audit_calls.append((service, action))
        return None

    monkeypatch.setattr(loaded.tools, "_request_json", transport)
    monkeypatch.setattr(loaded.tools, "_default_market_snapshot", forbidden)
    monkeypatch.setattr(loaded.tools, "get_market_snapshot", forbidden)
    monkeypatch.setattr(loaded.orchestrator, "get_market_snapshot", forbidden)
    monkeypatch.setattr(loaded.orchestrator, "_ensure_core_tool_results", forbidden)
    monkeypatch.setattr(loaded.orchestrator, "_run_openai_reasoning", forbidden)
    monkeypatch.setattr(loaded.orchestrator, "emit_audit_event", audit)
    monkeypatch.setattr(loaded.risk_stub, "emit_audit_event", audit)
    response = run(request(loaded.orchestrator.app, "/v1/explain",
        headers={**AUTH, HEADER: PROFILE}, payload={"asset": "BTC", "question": checks.QUESTION}))
    assert response.status_code == 200
    raw = response.json()
    assert raw["probe_protocol"] == PROFILE and raw["execution_disabled"] is True
    assert raw["assistant_status"]["provider"] == "fallback"
    assert len(calls) == 2 and [method for method, _ in calls] == ["POST", "GET"]
    assert audit_calls == [("risk-stub", "risk_status"), ("orchestrator", "explain")]
    assert sum("FROM market_ticks" in sql for sql in sql_calls) == 0
    assert raw["evidence_bundle"]["market_snapshot"] == {}
    market = raw["evidence_bundle"]["market"]
    assert market == {"ok": False, "reason": "excluded_by_archival_probe", "latest_price": None,
                      "change_pct": 0.0, "window_samples": 0}
    approvals = json.loads((ROOT / "docs/review_artifacts/companion_evidence_packet_v2_20261024/topical_candidates.json").read_bytes())
    result = checks.evaluate_diagnostic(raw, view, deepcopy(list(view["original"].values())), approvals)
    assert result["diagnostic"] == {"stage": "complete", "code": "ok"}
    assert all(result["checks"].values())


@pytest.mark.parametrize("mode", ["absent", "positive", "zero"])
def test_ordinary_memory_still_reads_and_reports_market(loaded, monkeypatch, mode):
    memory, _, _ = retrieval(loaded, monkeypatch)
    original_fetch = memory.db.fetch_all
    rows = [] if mode == "absent" else [{
        "price": 100.0 if mode == "positive" else 0.0,
        "event_ts": "2026-10-26T00:00:00+00:00", "source": "SYNTHETIC_ONLY",
        "symbol": "BTC/USDT", "bid": None, "ask": None, "volume": None,
    }]
    calls = []

    def fetch(sql, params):
        if "FROM market_ticks" in sql:
            calls.append((sql, params))
            return deepcopy(rows)
        return original_fetch(sql, params)

    monkeypatch.setattr(memory.db, "fetch_all", fetch)
    response = run(request(memory.app, "/v1/memory/retrieve", headers=AUTH,
        payload={"asset": "BTC", "question": checks.QUESTION, "lookback_minutes": 60, "limit": 3}))
    assert response.status_code == 200 and len(calls) == 1
    assert calls[0][1] == ("BTC/%", 60)
    assert response.json()["market"] == memory._compute_market_summary(rows)
    if rows:
        assert response.json()["market"]["ok"] is True
    else:
        assert response.json()["market"]["reason"] == "no_market_data"
