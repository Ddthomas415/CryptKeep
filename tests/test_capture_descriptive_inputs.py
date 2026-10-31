"""Bounded capture with fake transport/processes only; no live acquisition."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import socket
import ssl
import subprocess
from urllib.parse import urlsplit
import urllib.error

import pytest
import yaml

from scripts.research import capture_descriptive_inputs as cap


H = 3_600_000
UNIVERSE = (cap.ROOT/"config/candidate_universe.yaml").read_bytes()
CONFIG = yaml.safe_load(UNIVERSE)["universe"]
ASSETS = sorted(s.split("/")[0] for tier in ("tier1", "tier2", "watchlist") for s in CONFIG[tier])


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("capture test attempted real external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, refuse)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, refuse)


def plan():
    return {"schema": "ed002-public-capture-plan-v1", "universe_sha256": cap.sha(UNIVERSE),
        "lookback_completed_hours": 2, "identities": {s: {"product_id": s+"-USD",
            "base_currency": s, "quote_currency": "USD",
            "identity_evidence_sha256": hashlib.sha256(("invented "+s).encode()).hexdigest()} for s in ASSETS}}


class FakeGet:
    def __init__(self, *, excluded=None, missing=None, failure=None):
        self.calls, self.excluded, self.missing, self.failure = [], excluded, missing, failure

    def __call__(self, url, timeout, limit):
        assert cap.allowed_url(url) and 0 < timeout <= 5 and limit <= cap.PER_BODY
        self.calls.append(url)
        if self.failure and len(self.calls) == self.failure:
            return 429, b"rate limited", {}
        path = urlsplit(url).path
        if path == "/products":
            data = [{"id": s+"-USD", "base_currency": s, "quote_currency": "USD",
                "base_increment": ".001", "status": "delisted" if s == self.excluded else "online",
                **dict.fromkeys(cap.metadata.FLAGS, False)} for s in ASSETS]
        elif path == "/currencies":
            data = [{"id": s} for s in ["USD", *ASSETS]]
        else:
            symbol = path.split("/")[2][:-4]
            data = [] if symbol == self.missing else [[0,90,110,100,105,500], [3600,90,110,100,105,500]]
        return 200, json.dumps(data).encode(), {"Date": "synthetic"}


def capture(tmp_path, get=None, spec=None):
    return cap.capture_once(spec or plan(), tmp_path, get=get or FakeGet(),
        monotonic=lambda: 0, wall_ms=lambda: 2*H+123)


def test_all_25_capture_manifest_hashes_and_adapter_compatibility(tmp_path):
    get = FakeGet()
    spec, original = plan(), deepcopy(plan())
    assert cap.validate_plan(spec, UNIVERSE)["planned_max_requests"] == 27
    result = capture(tmp_path, get, spec)
    assert result["status"] == "COMPLETE" and not result["scoring_authorized"]
    assert len(get.calls) == result["transport_calls_started"] == 27
    assert len(result["symbols"]) == 25 and spec == original
    assert all(i["latest_bar_received_within_one_hour"] for i in result["symbols"].values())
    cap.verify_result(result, tmp_path, spec)
    normal = json.loads((tmp_path/"observations.json").read_bytes())
    assert len(normal["observations"]) == 25 and normal["status"] == "COMPLETE"
    assert normal["observations"]["BTC"][0]["known_at_ms"] == 2*H+123
    with pytest.raises(FileExistsError):
        capture(tmp_path, get, spec)
    assert len(get.calls) == 27


def test_known_ineligible_row_is_retained_without_demanding_its_candles(tmp_path):
    get = FakeGet(excluded="MATIC")
    result = capture(tmp_path, get)
    assert result["status"] == "COMPLETE" and len(get.calls) == 26
    assert not result["symbols"]["MATIC"]["candle_capture_required"]
    assert result["symbols"]["MATIC"]["window_coverage"]["status"] == "INCOMPLETE"
    assert not any("MATIC-USD/candles" in u for u in get.calls)


def test_unknown_identity_is_not_dropped_or_treated_as_excluded(tmp_path):
    spec = plan()
    spec["identities"]["MATIC"] = None
    result = capture(tmp_path, spec=spec)
    assert result["status"] == "INCOMPLETE" and len(result["symbols"]) == 25
    assert result["symbols"]["MATIC"]["metadata_eligible_under_model"] is None


def test_missing_hour_is_not_a_complete_capture(tmp_path):
    result = capture(tmp_path, FakeGet(missing="BTC"))
    assert result["status"] == "INCOMPLETE" and result["transport_calls_started"] == 27
    assert result["symbols"]["BTC"]["window_coverage"]["missing_or_conflicting_hours"] == [0,H]


@pytest.mark.parametrize("failure", [1, 2, 3, 7])
def test_http_failure_stops_without_retry_and_retains_receipts(tmp_path, failure):
    get = FakeGet(failure=failure)
    result = capture(tmp_path, get)
    assert result["status"] == "INCOMPLETE" and len(get.calls) == failure
    assert len(result["symbols"]) == 25
    assert result["records"][-1]["http_status"] == 429
    assert (tmp_path/f"{failure:02d}_receipt.json").exists()


def test_transport_exception_does_not_write_its_sensitive_message(tmp_path):
    def bad(*args):
        raise TimeoutError("DONT_LOG_THIS_PRIVATE_VALUE")
    result = capture(tmp_path, bad)
    assert result["status"] == "INCOMPLETE" and result["records"][0]["error_class"] == "TimeoutError"
    assert "DONT_LOG" not in json.dumps(result)
    assert all("DONT_LOG" not in p.read_text() for p in tmp_path.iterdir())


def test_payload_overflow_is_truncated_labelled_and_stops(tmp_path):
    calls = []
    def huge(url, timeout, limit):
        calls.append(url)
        return 200, b"x"*(limit+1), {}
    result = capture(tmp_path, huge)
    assert len(calls) == 1 and result["status"] == "INCOMPLETE"
    assert result["stored_payload_bytes"] == cap.PER_BODY
    assert result["records"][0]["truncated"] is True


def test_global_payload_cap_is_used_as_next_read_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(cap, "TOTAL_BODY", 300)
    budgets = []
    def full(url, timeout, limit):
        budgets.append(limit)
        return 200, b"[]"+b" "*(limit-2), {}
    result = capture(tmp_path, full)
    assert budgets == [300] and result["stored_payload_bytes"] == 300
    assert result["status"] == "INCOMPLETE"


def test_exhausted_cooperative_budget_refuses_first_request(tmp_path):
    clock = iter((0, 111))
    result = cap.capture_once(plan(), tmp_path, get=lambda *args: pytest.fail("transport"),
        monotonic=lambda: next(clock), wall_ms=lambda: 2*H+123)
    assert result["status"] == "INCOMPLETE" and result["transport_calls_started"] == 0


def test_wall_clock_rollback_is_not_backdated_into_a_valid_receipt(tmp_path):
    clock = iter((2*H+123, 2*H+125, 2*H+124))
    result = cap.capture_once(plan(), tmp_path, get=FakeGet(), monotonic=lambda: 0,
        wall_ms=lambda: next(clock))
    assert result["status"] == "INCOMPLETE" and result["transport_calls_started"] == 1


@pytest.mark.parametrize("fault", ["hash", "scope", "window", "extra", "wrong_quote", "path_injection"])
def test_invalid_plan_is_rejected_before_any_capture(fault):
    spec = plan()
    if fault == "hash": spec["universe_sha256"] = "0"*64
    elif fault == "scope": del spec["identities"]["MATIC"]
    elif fault == "window": spec["lookback_completed_hours"] = 24
    elif fault == "extra": spec["api_key"] = "not allowed"
    elif fault == "wrong_quote": spec["identities"]["BTC"]["quote_currency"] = "EUR"
    else: spec["identities"]["BTC"]["product_id"] = "../../accounts"
    with pytest.raises(ValueError): cap.validate_plan(spec, UNIVERSE)


@pytest.mark.parametrize("url", ["http://api.exchange.coinbase.com/products", "https://example.com/products",
    "https://user:password@api.exchange.coinbase.com/products", "https://api.exchange.coinbase.com/accounts",
    "https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400&start=x&end=y",
    "https://api.exchange.coinbase.com/products#fragment"])
def test_private_or_unapproved_url_cannot_reach_transport(url):
    assert not cap.allowed_url(url)


def test_https_policy_no_proxies_redirects_credentials_or_hidden_retry(monkeypatch):
    handlers, requests = [], []
    class Opener:
        def open(self, request, timeout):
            requests.append(request)
            raise urllib.error.HTTPError(request.full_url, 302, "redirect", {}, io.BytesIO(b"redirect"))
    def build(*supplied):
        handlers.extend(supplied)
        return Opener()
    monkeypatch.setattr(cap.urllib.request, "build_opener", build)
    get = cap.public_getter()
    status, body, _ = get(cap.BASE+"/products", 5, 100)
    assert status == 302 and body == b"redirect" and len(requests) == 1
    assert requests[0].get_header("Authorization") is None and requests[0].get_header("Cookie") is None
    assert any(isinstance(h, cap.NoRedirect) and h.redirect_request(None) is None for h in handlers)
    assert next(h for h in handlers if isinstance(h, cap.urllib.request.ProxyHandler)).proxies == {}
    context = next(h for h in handlers if isinstance(h, cap.urllib.request.HTTPSHandler))._context
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname


class FakeProcess:
    def __init__(self, mode="success"):
        self.mode, self.kills, self.waits, self.done = mode, 0, [], False
    def wait(self, timeout):
        self.waits.append(timeout)
        if self.mode == "interrupt" and not self.kills:
            raise KeyboardInterrupt()
        if self.mode in ("timeout", "cleanup_failed") and not self.kills:
            raise subprocess.TimeoutExpired("fake", timeout)
        if self.mode == "cleanup_failed":
            raise subprocess.TimeoutExpired("fake cleanup", timeout)
        self.done = True
        return 0
    def poll(self): return 0 if self.done else None
    def kill(self): self.kills += 1


@pytest.mark.parametrize("mode", ["success", "timeout", "cleanup_failed", "tampered", "interrupt", "forged"])
def test_supervisor_owned_worker_environment_and_failure_receipts(tmp_path, monkeypatch, mode):
    monkeypatch.setattr(cap, "NAMESPACE", tmp_path/"public")
    proc = FakeProcess(mode)
    invoked = []
    def launch(command, **kwargs):
        invoked.append((command, kwargs))
        assert set(kwargs["env"]) == {"PATH", "PYTHONDONTWRITEBYTECODE", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"}
        out = Path(command[-1])
        result = capture(out)
        if mode == "forged":
            result["scoring_authorized"] = True
        cap.write_json(out/"worker_result.json", result)
        if mode == "tampered":
            (out/result["records"][0]["file"]).write_bytes(b"changed")
        return proc
    out = cap.NAMESPACE/"attempt"
    result = cap.supervise(plan(), out, popen=launch)
    assert len(invoked) == 1 and (out/"ATTEMPT.json").exists() and (out/"manifest.json").exists()
    assert result["status"] == ("COMPLETE" if mode == "success" else "INCOMPLETE")
    if mode in ("timeout", "cleanup_failed", "interrupt"):
        assert proc.kills == 1 and proc.waits == [120,5]
    assert result["owned_worker_cleanup_failed"] == (mode == "cleanup_failed")
    with pytest.raises(FileExistsError): cap.supervise(plan(), out, popen=launch)
    assert len(invoked) == 1


def test_outside_output_and_input_drift_are_refused_without_transport(tmp_path, monkeypatch):
    monkeypatch.setattr(cap, "NAMESPACE", tmp_path/"public")
    with pytest.raises(ValueError): cap.supervise(plan(), tmp_path/"elsewhere", popen=lambda *a, **k: pytest.fail("spawn"))
    out = tmp_path/"worker"
    out.mkdir()
    cap.write_json(out/"plan.json", plan())
    cap.write_json(out/"ATTEMPT.json", {"code_inputs": {}, "plan_sha256": "wrong"})
    monkeypatch.setattr(cap, "public_getter", lambda: pytest.fail("client creation"))
    with pytest.raises(ValueError, match="prepared_inputs_changed"): cap._worker(out)
    assert json.loads((out/"worker_failure.json").read_bytes()) == {"stage": "preflight", "error_class": "ValueError"}


def test_cli_is_read_only_without_execute(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cap, "NAMESPACE", tmp_path/"public")
    cap.NAMESPACE.mkdir()
    source = cap.NAMESPACE/"plan.json"
    cap.write_json(source, plan())
    destination = cap.NAMESPACE/"not-created"
    monkeypatch.setattr(cap.sys, "argv", ["capture", "--plan", str(source), "--output", str(destination)])
    monkeypatch.setattr(cap, "supervise", lambda *args, **kwargs: pytest.fail("execution"))
    assert cap.main() == 0 and not destination.exists()
    assert json.loads(capsys.readouterr().out)["dry_run"] is True
