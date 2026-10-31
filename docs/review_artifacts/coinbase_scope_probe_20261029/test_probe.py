"""Offline, invented credentials and response bodies only."""
import base64
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace

import pytest

PATH = Path(__file__).with_name("probe.py")
spec = importlib.util.spec_from_file_location("scope_probe", PATH)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
UUID = "12345678-1234-4234-8234-123456789abc"
SECRET = "invented-secret-never-a-real-key"
PERMISSIONS = {"can_view": True, "can_trade": False, "can_transfer": False,
               "portfolio_uuid": UUID, "portfolio_type": "DEFAULT"}
PORTFOLIOS = {"portfolios": [{"uuid": UUID, "name": SECRET, "type": "DEFAULT", "deleted": False}]}


@pytest.fixture(autouse=True)
def deny_external(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("offline test attempted external access")
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(socket.socket, "connect", deny)
    def no_process(*args, **kwargs):
        raise FileNotFoundError("offline test forbids subprocesses")
    monkeypatch.setattr(subprocess, "Popen", no_process)
    import keyring
    monkeypatch.setattr(keyring, "get_password", deny)


def envelope(body, status=200):
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    return SimpleNamespace(returncode=0, stdout=json.dumps({"http_status": status,
        "body_bytes": len(raw), "body_base64": base64.b64encode(raw).decode()}).encode())


class Client:
    id = "coinbase"
    urls = {"api": {"rest": "https://api.coinbase.com"}}

    def sign(self, path, api, method, params):
        assert api == ["v3", "private"] and method == "GET" and params == {}
        return {"url": "https://api.coinbase.com/api/v3/" + path, "method": "GET",
                "body": None, "headers": {"Authorization": "Bearer " + SECRET}}


def observe(responses=None, *, clock=lambda: 0, client=None, loader=None):
    calls = []
    responses = iter(responses if responses is not None else [envelope(PERMISSIONS), envelope(PORTFOLIOS)])
    def run(command, **kwargs):
        assert command == [p.sys.executable, "-B", str(PATH.resolve()), "--http-worker"]
        assert SECRET not in repr(command)
        assert kwargs["stdout"] == subprocess.PIPE and kwargs["stderr"] == subprocess.DEVNULL
        assert 0 < kwargs["timeout"] <= 10
        assert set(kwargs["env"]) == {"PATH", "PYTHONDONTWRITEBYTECODE"}
        payload = json.loads(kwargs["input"])
        assert payload["url"] == p.URLS[len(calls)]
        calls.append(payload)
        answer = next(responses)
        if isinstance(answer, BaseException):
            raise answer
        return answer
    result = p.observe(loader=loader or (lambda venue: {"apiKey": SECRET, "secret": SECRET, "source": "keyring"}),
        factory=lambda *a, **k: client or Client(), run=run, clock=clock)
    saved = json.dumps(result)
    assert SECRET not in saved and UUID not in saved and "Bearer" not in saved
    return result, calls


def test_success_two_fixed_requests_and_no_accountwide_claim():
    result, calls = observe()
    assert result["status"] == "METADATA_OBSERVED" and len(calls) == 2
    assert result["portfolio_observation"]["associated_portfolio_returned"] is True
    assert result["portfolio_observation"]["unique_portfolio_count"] == 1
    assert result["account_wide_coverage"] == "UNVERIFIED"
    assert result["execution_authority"] is False


def test_missing_credentials_no_request():
    result, calls = observe(loader=lambda _: {})
    assert result["status"] == "MISSING_EXISTING_CREDENTIALS" and not calls


@pytest.mark.parametrize("status", [301, 401, 403, 429, 500])
def test_rejection_no_second_request_or_retry(status):
    result, calls = observe([envelope({"private": SECRET}, status)])
    assert result["status"] == "READ_ONLY_REQUEST_REJECTED" and len(calls) == 1


def test_view_not_granted_no_portfolio_get():
    result, calls = observe([envelope(PERMISSIONS | {"can_view": False})])
    assert result["status"] == "VIEW_PERMISSION_NOT_GRANTED" and len(calls) == 1


@pytest.mark.parametrize("body", [b'{"can_view":true,"can_view":false}', b'{"x":NaN}',
    b'{"x":1e999}', b'not json', b'[' * 1100 + b']' * 1100,
    PERMISSIONS | {"can_trade": "false"}, PERMISSIONS | {"portfolio_uuid": "invalid"}])
def test_malformed_permission_fails_closed(body):
    result, calls = observe([envelope(body)])
    assert result["status"] == "OBSERVATION_FAILED" and len(calls) == 1


@pytest.mark.parametrize("body", [{}, {"portfolios": None}, {"portfolios": [None]},
    {"portfolios": [{"uuid": "00000000-0000-0000-0000-000000000000"}]}])
def test_bad_portfolios_not_completeness(body):
    result, calls = observe([envelope(PERMISSIONS), envelope(body)])
    assert result["status"] == "OBSERVATION_FAILED" and len(calls) == 2


@pytest.mark.parametrize("where", [0, 1])
def test_timeout_no_retry(where):
    responses = [envelope(PERMISSIONS)] * where + [subprocess.TimeoutExpired("worker", 10)]
    result, calls = observe(responses)
    assert result["status"] == "OBSERVATION_FAILED" and len(calls) == where + 1
    assert result["error_type"] == "TimeoutExpired"


@pytest.mark.parametrize("ticks", [[float("nan")], [2, 1], [0, 31], [0, 0, 31]])
def test_clock_rejection(ticks):
    iterator = iter(ticks)
    result, calls = observe(clock=lambda: next(iterator))
    assert result["status"] == "OBSERVATION_FAILED" and len(calls) <= 1


def test_bad_signed_target_no_request():
    client = Client()
    client.sign = lambda *a: {"url": "https://example.invalid", "method": "GET", "body": None}
    result, calls = observe(client=client)
    assert result["status"] == "OBSERVATION_FAILED" and not calls


@pytest.mark.parametrize("bad", [{"http_status": SECRET, "body_bytes": 0, "body_base64": ""},
    {"http_status": 200, "body_bytes": SECRET, "body_base64": ""}, [],
    {"error_type": SECRET}, {"http_status": 200, "body_bytes": 4, "body_base64": "!!!"}])
def test_bad_worker_envelope_never_persists_raw_fields(bad):
    result, calls = observe([SimpleNamespace(returncode=0, stdout=json.dumps(bad).encode())])
    assert result["status"] == "OBSERVATION_FAILED" and len(calls) == 1


def test_worker_transport_no_redirect_retry_or_proxy():
    class Response:
        status_code = 200
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def iter_content(self, size):
            assert size == 16384
            yield b'{}'
    class Session:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def mount(self, prefix, adapter):
            assert prefix == "https://" and adapter.max_retries.total == 0
        def get(self, url, **kwargs):
            assert url == p.URLS[0] and self.trust_env is False and self.max_redirects == 0
            assert kwargs == {"headers": {"Authorization": "Bearer fake"}, "timeout": 10,
                              "allow_redirects": False, "verify": True, "stream": True}
            return Response()
    answer = p.http_worker({"url": p.URLS[0], "headers": {"Authorization": "Bearer fake"}, "timeout": 10}, Session)
    assert answer["body_bytes"] == 2


@pytest.mark.parametrize("overrides", [{"url": "https://other.invalid"}, {"timeout": 11},
    {"timeout": True}, {"headers": {"Authorization": "Bearer fake\r\nbad"}},
    {"headers": {"X-Other": SECRET}}, {"headers": {"Content-Type": "application/json"}}])
def test_worker_refuses_unsafe_request_before_session(overrides):
    def no_session(): raise AssertionError("session must not be created")
    with pytest.raises(ValueError):
        p.http_worker({"url": p.URLS[0], "headers": {"Authorization": "Bearer fake"}, "timeout": 10} | overrides, no_session)


def test_installed_sdk_signing_only_invented_hmac_credentials():
    import ccxt
    client = ccxt.coinbase({"apiKey": "invented", "secret": SECRET})
    for path, expected in zip(p.ENDPOINTS, p.URLS):
        signed = client.sign(path, ["v3", "private"], "GET", {})
        assert signed["url"] == expected and signed["method"] == "GET" and signed["body"] is None
        assert set(signed["headers"]) <= p.HEADER_NAMES


def test_worker_response_cap(monkeypatch):
    monkeypatch.setattr(p, "BODY_LIMIT", 1)
    class Response:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def iter_content(self, size): yield b'{}'
    class Session:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def mount(self, *a): pass
        def get(self, *a, **k): return Response()
    with pytest.raises(ValueError):
        p.http_worker({"url": p.URLS[0], "headers": {"Authorization": "fake"}, "timeout": 10}, Session)
