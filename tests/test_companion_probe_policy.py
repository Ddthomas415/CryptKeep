"""Synthetic offline policy proof: no lifespan, services, credentials or SDK proof."""
from __future__ import annotations

import asyncio
import ast
import copy
import hashlib
import importlib
import importlib.util
import json
import socket
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1] / "phase1_research_copilot"
REAL_CLIENT = httpx.AsyncClient
HEADER = "X-CryptKeep-Probe"
PROFILE = "single-cited-query-v1"
AUTH = {"Authorization": "Bearer fixture-token"}


def run(awaitable):
    return asyncio.run(awaitable)


async def request(app, path, *, payload=None, headers=None, method="POST"):
    async with REAL_CLIENT(transport=httpx.ASGITransport(app=app), base_url="http://fixture",
                           trust_env=False) as client:
        return await client.request(method, path, json=payload, headers=headers or {})


def forbidden(*args, **kwargs):
    raise AssertionError("unexpected offline boundary access")


@pytest.fixture
def loaded(monkeypatch):
    """Import actual service bodies with synthetic settings and storage modules."""
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    prefixes = ("shared", "memory_retrieval")
    saved = {name: module for name, module in sys.modules.items()
             if any(name == p or name.startswith(p + ".") for p in prefixes)}
    for name in saved:
        del sys.modules[name]
    monkeypatch.syspath_prepend(str(ROOT))

    def stub(name, **attrs):
        module = ModuleType(name)
        module.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, name, module)
        return module

    config = importlib.import_module("shared.config")
    # model_construct bypasses BaseSettings environment/dotenv readers entirely.
    monkeypatch.setattr(config.Settings, "__init__", forbidden)
    monkeypatch.setattr(config, "_fallback_env_values", forbidden)
    settings = config.Settings.model_construct(service_token="fixture-token", openai_api_key="")
    monkeypatch.setattr(config, "get_settings", lambda: settings)
    stub("shared.db", Database=lambda dsn: SimpleNamespace(
        fetch_one=forbidden, fetch_all=forbidden, health=forbidden))
    stub("dashboard.services.intelligence", build_opportunity_snapshot=forbidden)
    boto = stub("boto3", client=forbidden)
    stub("botocore")
    stub("botocore.config", Config=lambda **kwargs: SimpleNamespace(**kwargs))
    qdrant = stub("qdrant_client", QdrantClient=forbidden)
    qm = SimpleNamespace(Filter=SimpleNamespace, FieldCondition=SimpleNamespace,
                         MatchAny=SimpleNamespace)
    stub("qdrant_client.http", models=qm)

    result = SimpleNamespace(settings=settings, boto=boto, qdrant=qdrant)
    try:
        result.probe = importlib.import_module("shared.probe")
        result.tools = importlib.import_module("shared.tools")
        result.audit = importlib.import_module("shared.audit")
        for name in ("orchestrator", "memory_retrieval", "risk_stub", "audit_log"):
            spec = importlib.util.spec_from_file_location("probe_test_" + name, ROOT / name / "main.py")
            module = importlib.util.module_from_spec(spec)
            monkeypatch.setitem(sys.modules, spec.name, module)
            spec.loader.exec_module(module)
            assert module.settings is settings
            setattr(result, name, module)
        assert result.tools.settings is settings and result.audit._settings is settings
        yield result
    finally:
        for name in list(sys.modules):
            if any(name == p or name.startswith(p + ".") for p in prefixes):
                del sys.modules[name]
        sys.modules.update(saved)


def probe_app(loaded, operation):
    app = FastAPI()
    app.add_middleware(loaded.probe.ProbePolicyMiddleware)

    @app.post("/run")
    async def call():
        return await operation()

    return app


def test_request_context_is_opt_in_concurrent_and_reset_after_error(loaded):
    async def exercise():
        entered, release = asyncio.Event(), asyncio.Event()

        async def operation():
            active = loaded.probe.probe_active()
            if active:
                entered.set()
                await release.wait()
                assert loaded.probe.probe_active()
            return {"probe": active}

        app = probe_app(loaded, operation)
        probe = asyncio.create_task(request(app, "/run", headers={HEADER: PROFILE}))
        await entered.wait()
        ordinary = await request(app, "/run")
        assert ordinary.json() == {"probe": False}
        assert HEADER not in ordinary.headers
        release.set()
        response = await probe
        assert response.json() == {"probe": True}
        assert response.headers[HEADER] == PROFILE
        assert not loaded.probe.probe_active()

        async def fail():
            assert loaded.probe.probe_active()
            raise RuntimeError("synthetic failure")

        with pytest.raises(RuntimeError, match="synthetic failure"):
            await request(probe_app(loaded, fail), "/run", headers={HEADER: PROFILE})
        assert not loaded.probe.probe_active()

    run(exercise())


@pytest.mark.parametrize("headers", [{HEADER: "unknown"}, [(HEADER, PROFILE), (HEADER, PROFILE)]])
def test_unknown_or_duplicate_profile_cannot_fall_through(loaded, headers):
    response = run(request(probe_app(loaded, forbidden), "/run", headers=headers))
    assert response.status_code == 400


@pytest.mark.parametrize("name,path,payload", [
    ("orchestrator", "/v1/explain", {"asset": "BTC", "question": "regulation"}),
    ("memory_retrieval", "/v1/memory/retrieve", {"asset": "BTC", "question": "regulation"}),
    ("risk_stub", "/v1/risk/status", None),
    ("audit_log", "/v1/audit/events", {"service": "test", "action": "test"}),
])
@pytest.mark.parametrize("probe", [False, True])
def test_all_four_services_preserve_auth(loaded, name, path, payload, probe):
    module = getattr(loaded, name)
    profile_headers = {HEADER: PROFILE} if probe else {}
    for token in ("", "Bearer wrong"):
        response = run(request(module.app, path, payload=payload,
                               headers={**profile_headers, "Authorization": token},
                               method="GET" if name == "risk_stub" else "POST"))
        assert response.status_code == 401
        assert response.headers.get(HEADER) == (PROFILE if probe else None)
    loaded.settings.service_token = ""
    assert run(request(module.app, path, payload=payload, headers={**profile_headers, **AUTH},
                       method="GET" if name == "risk_stub" else "POST")).status_code == 503


def mock_http(monkeypatch, handler):
    options, calls = [], []

    async def dispatch(req):
        calls.append(req)
        return await handler(req)

    def factory(**kwargs):
        options.append(kwargs.copy())
        kwargs["transport"] = httpx.MockTransport(dispatch)
        return REAL_CLIENT(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    return options, calls


@pytest.mark.parametrize("url", [
    "http://market-data:8003/x", "http://parser-normalizer:8006/x",
    "http://news-ingestion:8004/x", "http://archive-lookup:8005/x",
    "https://example.org/x", "https://api.openai.com/v1/responses",
    "http://memory-retrieval:8007.evil/x", "http://memory-retrieval:8008/x",
    "http://user@memory-retrieval:8007/x", "https://risk-stub:8008/x",
])
def test_probe_rejects_every_other_origin_before_client_creation(loaded, monkeypatch, url):
    monkeypatch.setattr(httpx, "AsyncClient", forbidden)

    async def operation():
        with pytest.raises(RuntimeError, match="probe_origin_forbidden"):
            await loaded.tools._request_json("GET", url)
        return {"ok": True}

    assert run(request(probe_app(loaded, operation), "/run", headers={HEADER: PROFILE})).status_code == 200


@pytest.mark.parametrize("status", [503, 302])
def test_probe_tools_single_attempt_no_redirect_proxy_or_retry(loaded, monkeypatch, status):
    retries = []
    actual_retry = loaded.tools.retry_async

    async def retry(fn, **kwargs):
        retries.append(kwargs["retries"])
        return await actual_retry(fn, **kwargs)

    monkeypatch.setattr(loaded.tools, "retry_async", retry)

    async def reply(req):
        return httpx.Response(status, headers={"Location": "https://example.org/forbidden"})

    options, calls = mock_http(monkeypatch, reply)

    async def operation():
        with pytest.raises(httpx.HTTPStatusError):
            await loaded.tools._request_json("GET", "http://risk-stub:8008/v1/risk/status")
        return {"ok": True}

    assert run(request(probe_app(loaded, operation), "/run", headers={HEADER: PROFILE})).status_code == 200
    assert len(calls) == 1 and retries == [0]
    assert calls[0].headers[HEADER] == PROFILE
    assert calls[0].headers["Authorization"] == AUTH["Authorization"]
    assert options[0]["trust_env"] is False and options[0]["follow_redirects"] is False
    assert isinstance(options[0]["transport"], httpx.AsyncHTTPTransport)


def test_default_tool_retry_and_unmarked_request_remain(loaded, monkeypatch):
    retries = []

    async def retry(fn, **kwargs):
        retries.append(kwargs["retries"])
        return await fn()

    async def reply(req):
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(loaded.tools, "retry_async", retry)
    _, calls = mock_http(monkeypatch, reply)
    assert run(loaded.tools._request_json("GET", "http://market-data:8003/x")) == {"ok": True}
    assert retries == [1]
    assert HEADER not in calls[0].headers


def test_probe_explain_uses_actual_service_handlers_and_existing_assembler(loaded, monkeypatch):
    memory, orchestrator = loaded.memory_retrieval, loaded.orchestrator
    row = {"id": 73, "title": "Bitcoin regulation", "url": "https://example.org/article",
           "source": "fixture", "lexical_rank": 0.2}
    sql_calls, persisted_audits = [], []

    def fetch(sql, params):
        sql_calls.append((sql, params))
        return [row] if "AS lexical_rank" in sql else []

    def persist(sql, params):
        persisted_audits.append(params)
        return {"id": len(persisted_audits)}

    monkeypatch.setattr(memory.db, "fetch_all", fetch)
    monkeypatch.setattr(memory, "read_archive", lambda *a, **kw: None)
    monkeypatch.setattr(memory, "_qdrant_client", lambda: SimpleNamespace(search=lambda **kw: []))
    monkeypatch.setattr(loaded.audit_log.db, "fetch_one", persist)
    for name in ("_run_openai_reasoning", "_ensure_core_tool_results", "get_market_snapshot",
                 "get_operations_summary", "get_signal_summary"):
        monkeypatch.setattr(orchestrator, name, forbidden)
    monkeypatch.setattr(orchestrator.llm_client, "create_response", forbidden)
    # Even a configured model must not be used by the probe.
    loaded.settings.openai_api_key = "synthetic-not-a-credential"
    apps = {"memory-retrieval": memory.app, "risk-stub": loaded.risk_stub.app,
            "audit-log": loaded.audit_log.app}

    async def route(req):
        assert req.url.host in apps
        return await httpx.ASGITransport(app=apps[req.url.host]).handle_async_request(req)

    options, calls = mock_http(monkeypatch, route)
    response = run(request(orchestrator.app, "/v1/explain", headers={HEADER: PROFILE, **AUTH},
                           payload={"asset": "BTC", "question": "regulation", "lookback_minutes": 23}))
    assert response.status_code == 200
    result = response.json()
    assert result["asset"] == "BTC"
    assert result["probe_protocol"] == PROFILE
    assert result["assistant_status"]["provider"] == "fallback"
    assert result["assistant_status"]["model"] is None
    citation = next(e for e in result["evidence"] if e.get("document_id") == 73)
    assert citation["url"] == row["url"]
    assert result["risk_posture"]["reason"] == "Phase 1 research copilot mode"
    assert result["risk_posture"]["gate"] == "NO_TRADING"
    assert result["risk_posture"]["allow_trading"] is False
    assert result["risk_posture"]["execution_mode"] == "DISABLED"
    assert result["execution_disabled"] is True
    assert result["execution"]["enabled"] is False
    assert ("regulation", "BTC", "regulation", 3) in [p for _, p in sql_calls]
    retrieval = next(c for c in calls if c.url.path == "/v1/memory/retrieve")
    assert json.loads(retrieval.content)["lookback_minutes"] == 23
    assert len(calls) == 5  # retrieval, risk and three real audit writes
    assert len(persisted_audits) == 3
    assert {p[1] for p in persisted_audits} == {"memory-retrieval", "risk-stub", "orchestrator"}
    assert all(json.loads(p[-1])["probe_protocol"] == PROFILE for p in persisted_audits)
    assert all(c.headers[HEADER] == PROFILE and c.headers["Authorization"] == AUTH["Authorization"] for c in calls)
    assert all(o["trust_env"] is False and o["follow_redirects"] is False for o in options)


@pytest.mark.parametrize("bad", ["retrieval", "risk", "transport"])
def test_probe_context_failure_cannot_become_successful_fallback(loaded, monkeypatch, bad):
    async def reply(req):
        if bad == "transport":
            raise httpx.ConnectError("synthetic", request=req)
        if req.url.host == "memory-retrieval":
            return httpx.Response(200, json={} if bad == "retrieval" else {"ok": True})
        return httpx.Response(200, json={})

    _, calls = mock_http(monkeypatch, reply)
    monkeypatch.setattr(loaded.orchestrator, "_ensure_core_tool_results", forbidden)
    response = run(request(loaded.orchestrator.app, "/v1/explain", headers={HEADER: PROFILE, **AUTH},
                           payload={"asset": "BTC", "question": "regulation"}))
    assert response.status_code == 503
    assert response.json()["detail"] == "probe_context_unavailable"
    assert len(calls) == (2 if bad == "risk" else 1)


@pytest.mark.parametrize("override", [
    {"gate": "OPEN"}, {"allow_trading": True}, {"allow_trading": 0},
    {"execution_mode": "PAPER"}, {"execution_mode": None},
])
def test_probe_refuses_inconsistent_or_missing_no_trading_posture(loaded, monkeypatch, override):
    async def reply(req):
        payload = {"ok": True} if req.url.host == "memory-retrieval" else {
            "gate": "NO_TRADING", "allow_trading": False, "execution_mode": "DISABLED", **override}
        return httpx.Response(200, json=payload)

    _, calls = mock_http(monkeypatch, reply)
    response = run(request(loaded.orchestrator.app, "/v1/explain", headers={HEADER: PROFILE, **AUTH},
                           payload={"asset": "BTC", "question": "regulation"}))
    assert response.status_code == 503 and len(calls) == 2


def test_default_explain_still_uses_original_fallback(loaded, monkeypatch):
    calls = []

    async def core(asset, results, question):
        calls.append((asset, question))
        return {}

    async def audit(*args, **kwargs):
        pass

    monkeypatch.setattr(loaded.orchestrator, "_ensure_core_tool_results", core)
    monkeypatch.setattr(loaded.orchestrator, "emit_audit_event", audit)
    monkeypatch.setattr(loaded.orchestrator, "get_probe_tool_results", forbidden)
    response = run(request(loaded.orchestrator.app, "/v1/explain", headers=AUTH,
                           payload={"asset": "BTC", "question": "regulation"}))
    assert response.status_code == 200 and calls == [("BTC", "regulation")]
    assert "probe_protocol" not in response.json()


def test_probe_audit_forbidden_override_is_not_contacted(loaded, monkeypatch):
    loaded.settings.audit_service_url = "https://example.org"
    monkeypatch.setattr(httpx, "AsyncClient", forbidden)

    async def operation():
        await loaded.audit.emit_audit_event("test", "test")
        return {"ok": True}

    assert run(request(probe_app(loaded, operation), "/run", headers={HEADER: PROFILE})).status_code == 200


@pytest.mark.parametrize("missing", [None, "bucket", "collection"])
def test_read_only_startup_requires_existing_resources_and_health_proves_mode(loaded, monkeypatch, missing):
    memory = loaded.memory_retrieval
    assert loaded.settings.memory_read_only_startup is False
    loaded.settings.memory_read_only_startup = True
    monkeypatch.setattr(memory, "_s3_client", lambda: SimpleNamespace(
        list_buckets=lambda: {"Buckets": [] if missing == "bucket" else [{"Name": "raw-docs"}]},
        create_bucket=forbidden))
    monkeypatch.setattr(memory, "_qdrant_client", lambda: SimpleNamespace(
        get_collections=lambda: SimpleNamespace(collections=[] if missing == "collection"
                                               else [SimpleNamespace(name="documents")]),
        create_collection=forbidden))
    monkeypatch.setattr(memory.db, "health", lambda: {"ok": True})
    if missing:
        with pytest.raises(RuntimeError, match=f"read_only_{missing}_missing"):
            memory._startup()
    else:
        memory._startup()
    response = run(request(memory.app, "/healthz", method="GET", headers={HEADER: PROFILE}))
    assert response.json()["memory_read_only_startup"] is True
    assert response.json()["ok"] is (missing is None)


def test_default_startup_retains_resource_creation(loaded, monkeypatch):
    created = []
    monkeypatch.setattr(loaded.memory_retrieval, "_s3_client", lambda: SimpleNamespace(
        list_buckets=lambda: {"Buckets": []}, create_bucket=lambda **kw: created.append("bucket")))
    monkeypatch.setattr(loaded.memory_retrieval, "_qdrant_client", lambda: SimpleNamespace(
        get_collections=lambda: SimpleNamespace(collections=[]),
        create_collection=lambda **kw: created.append("collection")))
    monkeypatch.setattr(loaded.memory_retrieval.qm, "VectorParams", SimpleNamespace, raising=False)
    monkeypatch.setattr(loaded.memory_retrieval.qm, "Distance", SimpleNamespace(COSINE="cosine"), raising=False)
    loaded.memory_retrieval._startup()
    assert created == ["bucket", "collection"]


@pytest.mark.parametrize("read_only,probe", [(True, False), (False, True)])
def test_ingestion_rejected_before_sql_object_or_index_access(loaded, read_only, probe):
    loaded.settings.memory_read_only_startup = read_only
    payload = {"source": "fixture", "url": "https://example.org/article", "title": "fixture",
               "content_text": "fixture", "content_hash": "fixture", "fetched_at": "2026-01-01T00:00:00Z"}
    response = run(request(loaded.memory_retrieval.app, "/v1/memory/documents", payload=payload,
                           headers={**AUTH, **({HEADER: PROFILE} if probe else {})}))
    assert response.status_code == 403 and response.json()["detail"] == "memory_read_only"


@pytest.mark.parametrize("profile", ["read_only", "request_probe"])
def test_restricted_sdk_constructor_contracts_not_installed_sdk_proof(loaded, monkeypatch, profile):
    memory = loaded.memory_retrieval
    q_options, s_options, transports = [], [], []
    monkeypatch.setattr(memory, "QdrantClient", lambda **kw: q_options.append(kw) or object())
    monkeypatch.setattr(loaded.boto, "client", lambda *a, **kw: s_options.append(kw) or object())
    monkeypatch.setattr(httpx, "HTTPTransport", lambda **kw: transports.append(kw) or object())
    ordinary_q, ordinary_s = memory._qdrant_client(), memory._s3_client()
    loaded.settings.memory_read_only_startup = profile == "read_only"

    async def operation():
        assert memory._qdrant_client() is not ordinary_q
        assert memory._s3_client() is not ordinary_s
        memory._qdrant_client()
        memory._s3_client()
        return {"ok": True}

    assert run(request(probe_app(loaded, operation), "/run",
                       headers={HEADER: PROFILE} if profile == "request_probe" else {})).status_code == 200
    assert len(q_options) == len(s_options) == 2
    assert q_options[-1]["timeout"] == loaded.settings.request_timeout_seconds
    assert q_options[-1]["trust_env"] is False and q_options[-1]["follow_redirects"] is False
    assert q_options[-1]["prefer_grpc"] is False
    assert transports == []
    assert "transport" not in q_options[-1]
    config = s_options[-1]["config"]
    assert config.connect_timeout == config.read_timeout == loaded.settings.request_timeout_seconds
    assert config.proxies == {} and config.retries == {"total_max_attempts": 1, "mode": "standard"}


def test_restricted_qdrant_survives_captured_constructor_deepcopy(loaded, monkeypatch):
    """Captured SDK constructor + real host HTTPX; no installed imports or network."""
    evidence = ROOT.parent / "docs/review_artifacts/companion_installed_policy_20261016"
    source = evidence / "phase1-memory__usr__local__lib__python3.11__site-packages__qdrant_client__qdrant_client.py.source.txt"
    tree = ast.parse(source.read_text())
    sdk_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "QdrantClient")
    constructor = next(node for node in sdk_class.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
    report = json.loads((evidence / "report.json").read_text())
    expected = next(row["sha256"] for row in report["files"] if row["path"].endswith("qdrant_client/qdrant_client.py"))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
    import httpx._transports.default as transport_module
    expected_transport = next(row["sha256"] for row in report["files"] if row["path"].endswith("httpx/_transports/default.py"))
    assert hashlib.sha256(Path(transport_module.__file__).read_bytes()).hexdigest() == expected_transport

    class Base:
        def __init__(self, **kwargs):
            pass

    clients = []
    def remote(**kwargs):
        # Mirrors captured QdrantRemote's forwarding of these HTTPX controls.
        forwarded = {key: kwargs[key] for key in ("trust_env", "follow_redirects", "transport") if key in kwargs}
        client = httpx.Client(base_url=kwargs["url"], **forwarded)
        clients.append(client)
        return client

    captured = ast.ClassDef(name="Captured", bases=[ast.Name(id="Base", ctx=ast.Load())], keywords=[], body=[constructor], decorator_list=[])
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), captured], type_ignores=[])
    namespace = {"Base": Base, "deepcopy": copy.deepcopy, "QdrantRemote": remote}
    exec(compile(ast.fix_missing_locations(module), str(source), "exec"), namespace)
    monkeypatch.setattr(loaded.memory_retrieval, "QdrantClient", namespace["Captured"])
    loaded.settings.memory_read_only_startup = True
    try:
        instance = loaded.memory_retrieval._qdrant_client()
        assert instance is loaded.memory_retrieval._qdrant_client()
        assert "transport" not in instance._init_options
        assert instance._init_options["trust_env"] is False
        assert instance._init_options["follow_redirects"] is False
        assert len(clients) == 1 and clients[0]._transport._pool._retries == 0
        assert clients[0].trust_env is False and clients[0].follow_redirects is False
    finally:
        for client in clients:
            client.close()


STORAGE_CASES = [
    ("qdrant", "qdrant_url", "_qdrant_client", "_restricted_qdrant", "_qdrant", "http://qdrant:6333"),
    ("minio", "minio_endpoint", "_s3_client", "_restricted_s3", "_s3", "http://minio:9000"),
]


@pytest.mark.parametrize("profile", ["read_only", "request_probe"])
@pytest.mark.parametrize("service,setting,factory,restricted_cache,normal_cache,base", STORAGE_CASES)
@pytest.mark.parametrize("suffix", ["", "/"])
def test_restricted_storage_accepts_only_its_named_endpoint(
        loaded, monkeypatch, profile, service, setting, factory, restricted_cache, normal_cache, base, suffix):
    memory = loaded.memory_retrieval
    loaded.settings.memory_read_only_startup = profile == "read_only"
    setattr(loaded.settings, setting, base + suffix)
    marker, calls = object(), []

    def construct(*args, **kwargs):
        calls.append(kwargs)
        return marker

    monkeypatch.setattr(memory, "QdrantClient", construct)
    monkeypatch.setattr(loaded.boto, "client", construct)
    monkeypatch.setattr(httpx, "HTTPTransport", lambda **kw: object())
    monkeypatch.setattr(loaded.probe, "require_probe_origin", forbidden)

    async def operation():
        get_client = getattr(memory, factory)
        assert get_client() is marker
        assert get_client() is marker
        return {"ok": True}

    response = run(request(probe_app(loaded, operation), "/run",
                           headers={HEADER: PROFILE} if profile == "request_probe" else {}))
    assert response.status_code == 200 and len(calls) == 1
    assert calls[0]["url" if service == "qdrant" else "endpoint_url"] == base + suffix


@pytest.mark.parametrize("profile", ["read_only", "request_probe"])
@pytest.mark.parametrize("service,setting,factory,restricted_cache,normal_cache,base", STORAGE_CASES)
@pytest.mark.parametrize("cached", [False, True])
def test_restricted_storage_rejects_bad_endpoint_before_construction_or_cache_return(
        loaded, monkeypatch, profile, service, setting, factory, restricted_cache, normal_cache, base, cached):
    memory = loaded.memory_retrieval
    loaded.settings.memory_read_only_startup = profile == "read_only"
    marker = object() if cached else None
    monkeypatch.setattr(memory, restricted_cache, marker)
    monkeypatch.setattr(memory, "QdrantClient", forbidden)
    monkeypatch.setattr(loaded.boto, "client", forbidden)
    monkeypatch.setattr(httpx, "HTTPTransport", forbidden)
    monkeypatch.setattr(loaded.probe, "require_probe_origin", forbidden)
    rejected = [
        base + "?x=1", base + "?", base + "#x", base + "#",
        base + "/extra", base + "//", base + "/./", base + "/%2e",
        base.replace("http://", "http://user:pass@"),
        base.replace("http://", "http://user@"),
        base.replace("http://", "http://@"),
        base.replace("http://", "https://"), base.replace("http://", "HTTP://"),
        base.replace(service + ":", service + ".evil:"), base + "0",
        "http://127.0.0.1:" + base.rsplit(":", 1)[1],
        "http://memory-retrieval:8007", "https://example.org", "",
        "http://minio:9000" if service == "qdrant" else "http://qdrant:6333",
        " " + base, base + "\n",
    ]

    async def operation():
        for endpoint in rejected:
            setattr(loaded.settings, setting, endpoint)
            with pytest.raises(RuntimeError, match="restricted_storage_endpoint_forbidden"):
                getattr(memory, factory)()
            assert getattr(memory, restricted_cache) is marker
        return {"ok": True}

    response = run(request(probe_app(loaded, operation), "/run",
                           headers={HEADER: PROFILE} if profile == "request_probe" else {}))
    assert response.status_code == 200


@pytest.mark.parametrize("service,setting,factory,restricted_cache,normal_cache,base", STORAGE_CASES)
@pytest.mark.parametrize("cached", [False, True])
def test_normal_storage_does_not_apply_restricted_endpoint_policy(
        loaded, monkeypatch, service, setting, factory, restricted_cache, normal_cache, base, cached):
    memory = loaded.memory_retrieval
    endpoint = "http://custom-storage:1234/path?x=1#fragment"
    setattr(loaded.settings, setting, endpoint)
    marker, calls = object(), []
    monkeypatch.setattr(memory, normal_cache, marker if cached else None)
    monkeypatch.setattr(memory, "require_storage_endpoint", forbidden)

    def construct(*args, **kwargs):
        calls.append(kwargs)
        return marker

    monkeypatch.setattr(memory, "QdrantClient", construct)
    monkeypatch.setattr(loaded.boto, "client", construct)
    assert getattr(memory, factory)() is marker
    assert getattr(memory, factory)() is marker
    assert len(calls) == (0 if cached else 1)
    if calls:
        assert calls[0]["url" if service == "qdrant" else "endpoint_url"] == endpoint
