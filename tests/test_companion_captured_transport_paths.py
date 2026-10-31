"""Offline probes of hash-bound installed methods; never import the live SDK."""
import ast
import asyncio
import hashlib
import itertools
import json
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1] / "docs/review_artifacts/companion_continuation_20261021"


def captured(folder, suffix):
    base = ROOT / folder
    report = json.loads((base / "report.json").read_bytes())
    entries = [r for r in report["files"] if r["path"].endswith(suffix)]
    assert len(entries) == 4
    assert len({r["sha256"] for r in entries}) == 1
    for row in entries:
        raw = (base / row["saved_file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]
        assert len(raw) == row["bytes"]
    return ast.parse(raw)


def extract(tree, name):
    return next(n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)


def compile_functions(nodes, namespace):
    module = ast.Module(body=[ast.ImportFrom(module="__future__",
        names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "<captured-installed-method>", "exec"), namespace)
    return namespace


class ConnectFailure(Exception):
    pass


class Trace:
    def __init__(self, *args, **kwargs):
        self.return_value = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


@pytest.mark.parametrize("retries,failures,expected_calls", [(0, 1, 1), (1, 1, 2), (1, 2, 2)])
def test_installed_async_connect_retry_boundary(retries, failures, expected_calls):
    tree = captured("missing_runtime_sources_authorized", "httpcore/_async/connection.py")
    namespace = compile_functions([extract(tree, "exponential_backoff"), extract(tree, "_connect")],
        {"itertools": itertools, "Trace": Trace, "logger": None, "RETRIES_BACKOFF_FACTOR": 0.5,
         "ConnectError": ConnectFailure, "ConnectTimeout": ConnectFailure})
    calls = []
    failure = ConnectFailure("synthetic; no network")

    async def connect_tcp(**kwargs):
        calls.append(kwargs)
        if len(calls) <= failures:
            raise failure
        return "synthetic-stream"

    async def sleep(delay):
        pass

    client = SimpleNamespace(_retries=retries, _uds=None, _local_address=None, _socket_options=None,
        _origin=SimpleNamespace(host=b"audit-log", port=8009, scheme=b"http"),
        _network_backend=SimpleNamespace(connect_tcp=connect_tcp, sleep=sleep))
    if failures > retries:
        with pytest.raises(ConnectFailure) as caught:
            asyncio.run(namespace["_connect"](client, SimpleNamespace(extensions={})))
        assert caught.value is failure
    else:
        assert asyncio.run(namespace["_connect"](client, SimpleNamespace(extensions={}))) == "synthetic-stream"
    assert len(calls) == expected_calls


@pytest.mark.parametrize("hostaddr,expected", [(None, 2), ("192.0.2.1", 1)])
def test_installed_psycopg_dns_attempt_expansion(hostaddr, expected):
    tree = captured("missing_psycopg_attempt_sources", "psycopg/_conninfo_attempts.py")
    dns_calls = []

    def lookup(*args, **kwargs):
        dns_calls.append(args)
        return [(None, None, None, None, ("192.0.2.1", 5432)),
                (None, None, None, None, ("192.0.2.2", 5432))]

    namespace = compile_functions([extract(tree, "_resolve_hostnames")],
        {"get_param": lambda p, k: p.get(k), "is_ip_address": lambda host: False,
         "get_param_def": lambda key: None,
         "socket": SimpleNamespace(getaddrinfo=lookup, IPPROTO_TCP=socket.IPPROTO_TCP,
                                   SOCK_STREAM=socket.SOCK_STREAM)})
    params = {"host": "timescaledb", "port": "5432"}
    if hostaddr:
        params["hostaddr"] = hostaddr
    attempts = namespace["_resolve_hostnames"](params)
    assert len(attempts) == expected
    assert len(dns_calls) == (0 if hostaddr else 1)
