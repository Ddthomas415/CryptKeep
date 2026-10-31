from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import subprocess

import pytest

from services.analytics.okx_funding_pair_producer import (
    collect_and_journal_okx_pair, collect_okx_funding_pair,
)
from services.analytics.okx_funding_journal import recent_okx_funding_quotes
from storage import crypto_edge_store_sqlite as storage


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise AssertionError("external/default process boundary forbidden")
    connect = sqlite3.connect
    def temporary(database, *args, **kwargs):
        assert Path(database).resolve().is_relative_to(tmp_path.resolve())
        return connect(database, *args, **kwargs)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(sqlite3, "connect", temporary)
    monkeypatch.setattr(storage, "ensure_dirs", refuse)


@pytest.fixture
def bodies():
    path = ROOT / "docs/review_artifacts/okx_funding_metadata_20261029/20261029T103617Z_2668220f5a85484580a593b0207494d4"
    return [(path / (name + ".body")).read_bytes() for name in ("current", "history")]


class Transport:
    def __init__(self, bodies, action=None):
        self.bodies, self.action, self.calls = bodies, action, []

    def __call__(self, command, **kwargs):
        self.calls.append((deepcopy(command), deepcopy(kwargs)))
        if self.action:
            replacement = self.action(len(self.calls), command, kwargs)
            if replacement is not None:
                return replacement
        return subprocess.CompletedProcess(command, 0, self.bodies[len(self.calls) - 1] + b"\n200", b"")


def options(transport, **changes):
    return {"inst_id": "BTC-USDT-SWAP", "enabled": True, "max_requests": 2,
            "total_timeout_seconds": 30, "request_timeout_seconds": 10,
            "max_response_bytes": 1048576, "run": transport,
            "utc": lambda: "2026-10-29T10:36:19Z", "monotonic": lambda: 0.0} | changes


def test_disabled_default_cannot_launch_transport():
    out = collect_okx_funding_pair(inst_id="BTC-USDT-SWAP")
    assert out["ok"] is False and out["requests_attempted"] == 0 and out["pair"] is None


@pytest.mark.parametrize("field,value", [
    ("enabled", "yes"), ("inst_id", "BTC/USDT:USDT"), ("inst_id", "BTC-USDT-SWAP&x=1"),
    ("max_requests", None), ("max_requests", True), ("max_requests", 3),
    ("total_timeout_seconds", None), ("total_timeout_seconds", True),
    ("total_timeout_seconds", float("nan")), ("total_timeout_seconds", 31),
    ("request_timeout_seconds", 0), ("request_timeout_seconds", 11),
    ("max_response_bytes", 0), ("max_response_bytes", True), ("max_response_bytes", 1048577),
    ("run", False), ("utc", False), ("monotonic", False),
])
def test_invalid_scope_or_limits_refuse_before_transport(bodies, field, value):
    fake = Transport(bodies)
    with pytest.raises(ValueError):
        collect_okx_funding_pair(**options(fake, **{field: value}))
    assert fake.calls == []


def test_two_fixed_gets_preserve_bodies_receipts_and_transport_controls(bodies):
    fake = Transport(bodies)
    out = collect_okx_funding_pair(**options(fake))
    assert out["ok"] is True and out["requests_attempted"] == 2
    for index, (command, kwargs) in enumerate(fake.calls):
        assert command[:2] == ["/usr/bin/curl", "--disable"]
        assert kwargs["env"] == {"PATH": "/usr/bin:/bin"}
        assert 0 < kwargs["timeout"] <= 10 and kwargs["check"] is False
        for flag, value in (("--noproxy", "*"), ("--proto", "=https"), ("--retry", "0"),
                            ("--max-redirs", "0"), ("--request", "GET"), ("--output", "-")):
            assert command[command.index(flag) + 1] == value
        assert "--location" not in command and "--insecure" not in command
        endpoint = "funding-rate" if index == 0 else "funding-rate-history"
        assert command[-1] == "https://www.okx.com/api/v5/public/" + endpoint + "?instId=BTC-USDT-SWAP" + (
            "&limit=5" if index else "")
        capture = out["captures"][index]
        assert capture["body"] == bodies[index]
        assert capture["receipt"]["body_sha256"] == hashlib.sha256(bodies[index]).hexdigest()
        assert capture["complete"] is True and capture["body_truncated"] is False
    assert out["execution_authority"] is False


def test_explicit_falsey_transport_is_not_replaced_with_live_transport(bodies):
    class Falsey(Transport):
        def __bool__(self):
            return False
    fake = Falsey(bodies)
    assert collect_okx_funding_pair(**options(fake))["ok"] is True
    assert len(fake.calls) == 2


@pytest.mark.parametrize("failure_at", [1, 2])
def test_timeout_retains_partial_evidence_without_retry_or_pair(bodies, failure_at):
    def action(number, command, kwargs):
        if number == failure_at:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"], output=b"PARTIAL")
    fake = Transport(bodies, action)
    out = collect_okx_funding_pair(**options(fake))
    assert out["ok"] is False and out["pair"] is None
    assert len(fake.calls) == failure_at and out["requests_attempted"] == failure_at
    assert out["captures"][-1]["body"] == b"PARTIAL"
    assert out["captures"][-1]["error_type"] == "TimeoutExpired"
    assert out["captures"][-1]["complete"] is False


@pytest.mark.parametrize("status,code", [(b"301", 0), (b"429", 0), (b"000", 6)])
def test_http_or_curl_failure_stops_without_followup_or_error_text(bodies, status, code):
    def action(number, command, kwargs):
        return subprocess.CompletedProcess(command, code, b'{"code":"error"}\n' + status,
                                           b"private-looking transport diagnostic")
    fake = Transport(bodies, action)
    out = collect_okx_funding_pair(**options(fake))
    assert len(fake.calls) == 1 and out["pair"] is None
    assert "private-looking" not in str(out)


def test_byte_limit_marks_partial_body_not_complete_original(bodies):
    fake = Transport(bodies)
    out = collect_okx_funding_pair(**options(fake, max_response_bytes=8))
    assert len(fake.calls) == 1 and out["ok"] is False
    capture = out["captures"][0]
    assert capture["body"] == bodies[0][:8] and capture["body_truncated"] is True
    assert capture["complete"] is False and capture["receipt"]["body_bytes"] == 8


@pytest.mark.parametrize("bad", [
    b'{"code":"50000","data":[]}', b'{"code":"0","data":[]}', b'not json',
    b'{"code":"0","data":[{"instId":"ETH-USDT-SWAP","instType":"SWAP"}]}',
    b'{"code":"0","data":[],"extra":1e309}',
    b'{"code":"0","data":[],"extra":' + b'[' * 2000 + b'0' + b']' * 2000 + b'}',
])
def test_invalid_first_response_is_not_followed_by_history_request(bodies, bad):
    fake = Transport([bad, bodies[1]])
    out = collect_okx_funding_pair(**options(fake))
    assert out["ok"] is False and len(fake.calls) == 1 and out["pair"] is None
    assert out["captures"][0]["body"] == bad


def test_deadline_prevents_second_dispatch(bodies):
    clock = [0.0]
    def action(number, command, kwargs):
        assert kwargs["timeout"] == pytest.approx(0.25)
        clock[0] = 31
    fake = Transport(bodies, action)
    ticks = iter([0.0, 29.75])
    def monotonic():
        return next(ticks, clock[0])
    out = collect_okx_funding_pair(**options(fake, monotonic=monotonic))
    assert len(fake.calls) == 1 and out["reason"] == "okx_pair_deadline_exhausted"
    assert out["captures"][0]["complete"] is True and out["pair"] is None


def test_expiration_after_validation_is_not_success(bodies):
    ticks = iter([0.0, 0.0, 0.0, 0.0, 30.0])
    fake = Transport(bodies)
    out = collect_okx_funding_pair(**options(fake, monotonic=lambda: next(ticks)))
    assert len(fake.calls) == 2 and out["ok"] is False and out["pair"] is None
    assert out["reason"] == "okx_pair_deadline_exhausted"


@pytest.mark.parametrize("exception", [KeyboardInterrupt, MemoryError])
def test_systemic_failures_are_not_silently_converted(bodies, exception):
    def action(number, command, kwargs):
        raise exception()
    fake = Transport(bodies, action)
    with pytest.raises(exception):
        collect_okx_funding_pair(**options(fake))
    assert len(fake.calls) == 1


def test_one_shot_capture_to_disposable_journal_and_readback(bodies, tmp_path):
    store = storage.CryptoEdgeStoreSQLite(path=str(tmp_path / "capture.sqlite"))
    fake = Transport(bodies)
    out = collect_and_journal_okx_pair(store, source="fixture", max_journal_bytes=131072, **options(fake))
    assert out["ok"] is True and out["journal_state"] == "confirmed"
    assert out["journal_write"]["inserted"] == 1 and len(fake.calls) == 2
    reopened = storage.CryptoEdgeStoreSQLite(path=store.path)
    report = recent_okx_funding_quotes(reopened, source="fixture", limit=1)
    assert len(report["quotes"]) == 1
    assert report["quotes"][0]["policy"]["forecast_cash_cost"]["forecast_rate_per_8h"] == "0.0000436849743302"
    assert report["strategy_eligible"] is False and reopened.latest_funding_rows() == []


def test_failure_or_disable_never_calls_store(bodies):
    class NoWrite:
        def append_raw_funding_observations(self, *args, **kwargs):
            raise AssertionError("must not write")
    for enabled, data in ((False, bodies), (True, [b"invalid", bodies[1]])):
        fake = Transport(data)
        out = collect_and_journal_okx_pair(NoWrite(), source="fixture", max_journal_bytes=131072,
                                          **options(fake, enabled=enabled))
        assert out["journal_state"] == "not_attempted"


def test_postcommit_error_is_unknown_and_never_recaptures(bodies, tmp_path):
    store = storage.CryptoEdgeStoreSQLite(path=str(tmp_path / "postcommit.sqlite"))
    class PostCommit:
        def append_raw_funding_observations(self, *args, **kwargs):
            store.append_raw_funding_observations(*args, **kwargs)
            raise RuntimeError("private-looking persistence detail")
    fake = Transport(bodies)
    out = collect_and_journal_okx_pair(PostCommit(), source="fixture", max_journal_bytes=131072, **options(fake))
    assert out["ok"] is False and out["journal_state"] == "unknown"
    assert out["pair"] is not None and len(fake.calls) == 2
    assert "private-looking" not in str(out)
    assert len(recent_okx_funding_quotes(store, source="fixture", limit=1)["quotes"]) == 1


@pytest.mark.parametrize("source,budget", [("", 100), (" padded ", 100), ("fixture", 0), ("fixture", True)])
def test_bad_journal_inputs_refuse_before_capture(bodies, source, budget):
    fake = Transport(bodies)
    with pytest.raises(ValueError):
        collect_and_journal_okx_pair(None, source=source, max_journal_bytes=budget, **options(fake))
    assert fake.calls == []


def test_missing_store_refuses_enabled_capture_but_disabled_is_noop(bodies):
    fake = Transport(bodies)
    with pytest.raises(ValueError, match="explicit_caller_owned_journal_required"):
        collect_and_journal_okx_pair(None, source="fixture", max_journal_bytes=131072, **options(fake))
    assert fake.calls == []
    out = collect_and_journal_okx_pair(None, source="fixture", max_journal_bytes=131072,
                                      **options(fake, enabled=False))
    assert out["journal_state"] == "not_attempted" and fake.calls == []
