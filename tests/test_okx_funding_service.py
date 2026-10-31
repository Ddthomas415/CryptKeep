import base64
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import socket
import sqlite3
import subprocess

import pytest

from services.analytics import crypto_edge_collector_service as svc
from storage import crypto_edge_store_sqlite as storage


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise AssertionError("external/default boundary forbidden")
    connect = sqlite3.connect
    def temporary(database, *args, **kwargs):
        assert Path(database).resolve().is_relative_to(tmp_path.resolve())
        return connect(database, *args, **kwargs)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(storage, "ensure_dirs", refuse)
    monkeypatch.setattr(sqlite3, "connect", temporary)
    monkeypatch.setattr(svc, "_now_iso", lambda: "2026-10-29T14:59:37Z")


@pytest.fixture
def bodies():
    path = ROOT / "docs/review_artifacts/okx_funding_pair_transport_20261029/20261029T145936Z_eddbeac2a3134ea68bc7f2b649d64b1a"
    return [json.loads((path / (name + ".body")).read_bytes()) for name in ("current", "history")]


def setup(monkeypatch, tmp_path, count=2):
    plan = {"funding": [{"venue": "okx", "symbol": f"COIN{i}/USDT:USDT", "inst_id": f"COIN{i}-USDT-SWAP"}
                        for i in range(count)],
            "quotes": [{"venue": "coinbase", "symbol": "OTHER/USD"}]}
    options = {"max_requests": count * 2, "total_timeout_seconds": 30,
               "request_timeout_seconds": 10, "max_response_bytes": 1048576}
    cfg = svc.CryptoEdgeCollectorServiceCfg(
        plan_file="not-opened", db_path=str(tmp_path / "service.sqlite"), source="fixture",
        raw_funding_only=True, raw_funding_max_rows=count, raw_funding_max_bytes=2000000,
        okx_pair_options=options)
    monkeypatch.setattr(svc, "_load_plan", lambda path: deepcopy(plan))
    other_calls = []
    def other(data, **kwargs):
        other_calls.append((deepcopy(data), kwargs))
        assert data["funding"] == [] and kwargs == {"raw_funding_only": True}
        return {"funding_rows": [], "funding_observations": [], "checks": [],
                "quote_rows": [{"symbol": "OTHER/USD", "venue": "coinbase", "bid": 10, "ask": 11}]}
    monkeypatch.setattr(svc, "collect_live_crypto_edge_snapshot", other)
    return cfg, plan, options, other_calls


class Transport:
    def __init__(self, bodies, action=None):
        self.bodies, self.action, self.calls = bodies, action, []

    def __call__(self, command, **kwargs):
        self.calls.append((list(command), dict(kwargs)))
        if self.action:
            replacement = self.action(len(self.calls), command, kwargs)
            if replacement is not None:
                return replacement
        inst_id = command[-1].split("instId=")[1].split("&")[0]
        payload = deepcopy(self.bodies[1 if "funding-rate-history?" in command[-1] else 0])
        for row in payload["data"]:
            row["instId"] = inst_id
        return subprocess.CompletedProcess(command, 0, json.dumps(payload).encode() + b"\n200", b"")


@pytest.mark.parametrize("count", [1, 2, 25])
def test_explicit_service_batch_roundtrip_preserves_other_streams(monkeypatch, tmp_path, bodies, count):
    cfg, plan, options, other_calls = setup(monkeypatch, tmp_path, count)
    original = deepcopy(plan), deepcopy(options)
    fake = Transport(bodies)
    out = svc.collect_once(cfg, pair_run=fake)
    assert out["ok"] is True and len(fake.calls) == count * 2
    assert out["funding_count"] == 0 and out["raw_funding_count"] == count
    assert out["funding_pair_capture"]["successful_pairs"] == count
    assert out["funding_pair_capture"]["request_budget"] == count * 2
    assert out["quote_count"] == 1 and len(other_calls) == 1
    assert other_calls[0][0]["quotes"] == plan["quotes"]
    assert (plan, options) == original
    assert len(out["report"]["funding_pair_quotes"]["quotes"]) == count
    assert out["report"]["funding_pair_quotes"]["strategy_eligible"] is False
    assert out["report"]["funding"]["annualized_carry_pct"] is None
    assert out["report"]["funding_meta"] is None
    assert out["execution_enabled"] is False
    json.dumps(out, allow_nan=False)
    reopened = storage.CryptoEdgeStoreSQLite(path=cfg.db_path)
    assert reopened.latest_funding_rows() == []
    assert len(reopened.recent_raw_funding_observations(source="fixture", limit=count)["observations"]) == count


@pytest.mark.parametrize("change", [
    lambda plan, options: plan["funding"][1].pop("inst_id"),
    lambda plan, options: plan["funding"][1].update(venue="binance"),
    lambda plan, options: plan["funding"][1].update(inst_id=plan["funding"][0]["inst_id"]),
    lambda plan, options: options.update(max_requests=2),
    lambda plan, options: options.update(max_requests=True),
    lambda plan, options: options.update(total_timeout_seconds=float("nan")),
    lambda plan, options: options.update(request_timeout_seconds=11),
    lambda plan, options: options.update(max_response_bytes=0),
    lambda plan, options: options.update(run="not-configurable"),
])
def test_invalid_later_plan_or_options_refuse_before_any_capture(monkeypatch, tmp_path, bodies, change):
    cfg, plan, options, other_calls = setup(monkeypatch, tmp_path)
    change(plan, options)
    fake = Transport(bodies)
    with pytest.raises(ValueError):
        svc.collect_once(cfg, pair_run=fake)
    assert fake.calls == [] and other_calls == []
    assert not Path(cfg.db_path).exists()


@pytest.mark.parametrize("changes", [
    {"raw_funding_only": False}, {"db_path": ""}, {"source": " padded "},
    {"raw_funding_max_rows": 1}, {"raw_funding_max_bytes": None},
])
def test_pair_mode_requires_explicit_raw_store_and_budgets(monkeypatch, tmp_path, bodies, changes):
    cfg, plan, options, other_calls = setup(monkeypatch, tmp_path)
    from dataclasses import replace
    cfg = replace(cfg, **changes)
    fake = Transport(bodies)
    with pytest.raises(ValueError):
        svc.collect_once(cfg, pair_run=fake)
    assert fake.calls == [] and other_calls == []


def test_partial_failure_retains_bytes_reports_incomplete_and_keeps_valid_neighbor(monkeypatch, tmp_path, bodies):
    cfg, plan, options, other_calls = setup(monkeypatch, tmp_path)
    def fail(number, command, kwargs):
        if number == 1:
            return subprocess.CompletedProcess(command, 0, b"rate limited\n429", b"private error text")
    fake = Transport(bodies, fail)
    out = svc.collect_once(cfg, pair_run=fake)
    assert out["ok"] is False and out["reason"] == "partial_funding_pair_capture"
    assert out["funding_pair_capture"]["successful_pairs"] == 1
    assert out["funding_pair_capture"]["failed_pairs"] == 1 and len(fake.calls) == 3
    assert out["quote_count"] == 1 and len(out["report"]["funding_pair_quotes"]["quotes"]) == 1
    raw = out["report"]["raw_funding"]["observations"]
    attempt = next(row["observation"]["raw_payload"] for row in raw
                   if row["observation"]["raw_payload"]["contract"] == "okx_public_pair_attempt_v1")
    assert base64.b64decode(attempt["captures"][0]["body_base64"]) == b"rate limited"
    assert "private error text" not in json.dumps(out)
    json.dumps(out, allow_nan=False)


def test_shared_deadline_stops_remaining_symbols_without_new_dispatch(monkeypatch, tmp_path, bodies):
    cfg, plan, options, other_calls = setup(monkeypatch, tmp_path)
    clock = [0.0]
    monkeypatch.setattr(svc, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    def expire(number, command, kwargs):
        clock[0] = 31
    fake = Transport(bodies, expire)
    out = svc.collect_once(cfg, pair_run=fake)
    assert len(fake.calls) == 1 and out["ok"] is False
    assert out["reason"] == "funding_pair_capture_failed"
    assert out["funding_pair_capture"]["failed_pairs"] == 2
    assert out["funding_pair_capture"]["requests_attempted"] == 1
    assert len(out["report"]["raw_funding"]["observations"]) == 2
    assert out["report"]["funding_pair_quotes"]["quotes"] == []


def test_mutated_external_options_cannot_expand_frozen_batch_limits(monkeypatch, tmp_path, bodies):
    cfg, plan, options, other_calls = setup(monkeypatch, tmp_path)
    def mutate(number, command, kwargs):
        options["max_requests"] = 999
        options["request_timeout_seconds"] = 999
        assert kwargs["timeout"] <= 10
    fake = Transport(bodies, mutate)
    out = svc.collect_once(cfg, pair_run=fake)
    assert out["funding_pair_capture"]["request_budget"] == 4 and len(fake.calls) == 4


def test_no_options_keeps_legacy_call_signature_and_never_uses_producer(monkeypatch, tmp_path):
    def old(plan):
        return {"funding_rows": [], "checks": []}
    monkeypatch.setattr(svc, "collect_live_crypto_edge_snapshot", old)
    monkeypatch.setattr(svc, "_load_plan", lambda path: {"funding": []})
    def refuse(*args, **kwargs):
        raise AssertionError("opt-in producer used by default")
    monkeypatch.setattr(svc, "collect_okx_pair_batch", refuse)
    out = svc.collect_once(svc.CryptoEdgeCollectorServiceCfg(plan_file="not-opened", db_path=str(tmp_path / "none")))
    assert out["reason"] == "no_live_rows_collected" and "funding_pair_capture" not in out
