"""Warm-up paging with invented bytes only; never acquires or scores market data."""
import hashlib
import json
from pathlib import Path
import socket
import subprocess
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

from scripts.research import capture_descriptive_inputs as cap


H, DAY = cap.candles.HOUR, cap.DAY
UNIVERSE = (cap.ROOT/"config/candidate_universe.yaml").read_bytes()
CONFIG = yaml.safe_load(UNIVERSE)["universe"]
ASSETS = sorted(s.split("/")[0] for tier in ("tier1", "tier2", "watchlist") for s in CONFIG[tier])
NOW = 2000*H+123
END = NOW//DAY*DAY


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("warmup test attempted external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, refuse)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, refuse)


def plan():
    return {"schema": cap.WARMUP_SCHEMA, "universe_sha256": cap.sha(UNIVERSE),
        "default_warmup_hours": 300, "incumbent_warmup_hours": 1464,
        "anchor": "last_completed_utc_day_at_worker_start",
        "identities": {s: {"product_id": s+"-USD", "base_currency": s, "quote_currency": "USD",
            "identity_evidence_sha256": hashlib.sha256(("invented "+s).encode()).hexdigest()} for s in ASSETS}}


class FakeWarmGet:
    def __init__(self, excluded=None, missing=None, failure=None):
        self.excluded, self.missing, self.failure = excluded, missing, failure
        self.calls, self.pages = [], []

    def __call__(self, url, timeout, limit):
        assert cap.allowed_url(url) and 0 < timeout <= 5 and limit <= cap.PER_BODY
        self.calls.append(url)
        if len(self.calls) == self.failure:
            return 503, b"unavailable", {}
        parsed = urlsplit(url)
        if parsed.path == "/products":
            data = [{"id": s+"-USD", "base_currency": s, "quote_currency": "USD", "base_increment": ".001",
                     "status": "delisted" if s == self.excluded else "online",
                     **dict.fromkeys(cap.metadata.FLAGS, False)} for s in ASSETS]
        elif parsed.path == "/currencies":
            data = [{"id": s} for s in ["USD", *ASSETS]]
        else:
            symbol = parsed.path.split("/")[2][:-4]
            query = parse_qs(parsed.query)
            first = int(datetime.fromisoformat(query["start"][0]).timestamp()*1000)
            last = int(datetime.fromisoformat(query["end"][0]).timestamp()*1000)
            timestamps = list(range(first, last+1, H))
            assert 1 <= len(timestamps) <= 300 and last % H == H-1000
            self.pages.append((symbol, first, last, len(timestamps)))
            data = [[t//1000,90,110,100,105,500] for t in reversed(timestamps)
                    if (symbol,t) != self.missing]
        return 200, json.dumps(data).encode(), {}


def run(tmp_path, get, spec=None):
    return cap.capture_once(spec or plan(), tmp_path, get=get, monotonic=lambda: 0, wall_ms=lambda: NOW)


def test_exact_25_scope_61_complete_days_300_hours_and_35_call_max(tmp_path):
    spec, get = plan(), FakeWarmGet()
    preview = cap.validate_plan(spec, UNIVERSE)
    assert preview["planned_max_requests"] == 35
    assert preview["history_hours_by_symbol"] == {s:1464 if s in ("BTC","ETH") else 300 for s in ASSETS}
    result = run(tmp_path, get, spec)
    assert result["status"] == "COMPLETE" and result["transport_calls_started"] == len(get.calls) == 35
    cap.verify_result(result, tmp_path, spec)
    assert result["window_end_ms"] == END and END % DAY == 0
    normal = json.loads((tmp_path/"observations.json").read_bytes())
    assert len(normal["observations"]) == 25 and normal["status"] == "COMPLETE"
    for symbol in ASSETS:
        records = normal["observations"][symbol]
        hours = 1464 if symbol in ("BTC","ETH") else 300
        assert len(records) == hours
        assert [r["row"][0] for r in records] == list(range(END-hours*H,END,H))
        assert all(r["known_at_ms"] == NOW for r in records)  # Seed knowledge, never historical availability.
    assert [n for s,_,_,n in get.pages if s == "BTC"] == [300,300,300,300,264]
    assert len({u for u in get.calls}) == 35 and not result["scoring_authorized"]


def test_known_exclusion_retained_34_requests_and_9528_actual_seed_rows(tmp_path):
    get = FakeWarmGet(excluded="MATIC")
    result = run(tmp_path, get)
    assert result["status"] == "COMPLETE" and len(get.calls) == 34
    normal = json.loads((tmp_path/"observations.json").read_bytes())
    assert len(normal["observations"]) == 25 and not normal["observations"]["MATIC"]
    assert sum(len(rows) for rows in normal["observations"].values()) == 9528
    assert normal["status"] == "INCOMPLETE"  # Physical all-25 coverage, not required flat-excluded inputs.


def test_missing_warmup_hour_is_unknown_not_imputed_or_retried(tmp_path):
    get = FakeWarmGet(missing=("BTC",END-100*H))
    result = run(tmp_path, get)
    assert result["status"] == "INCOMPLETE" and len(get.calls) == 35
    assert result["symbols"]["BTC"]["window_coverage"]["missing_or_conflicting_hours"] == [END-100*H]


def test_mid_paging_http_failure_stops_and_preserves_all_identity_rows(tmp_path):
    get = FakeWarmGet(failure=12)
    result = run(tmp_path, get)
    assert result["status"] == "INCOMPLETE" and len(get.calls) == 12
    assert len(result["symbols"]) == 25 and result["records"][-1]["http_status"] == 503
    assert (tmp_path/"12_receipt.json").exists()


@pytest.mark.parametrize("field,value", [("default_warmup_hours",299),("default_warmup_hours",301),
    ("incumbent_warmup_hours",1440),("incumbent_warmup_hours",True),
    ("anchor","last_completed_hour"),("universe_sha256","bad")])
def test_different_horizon_anchor_or_scope_needs_a_different_reviewed_plan(field,value):
    spec = plan();spec[field] = value
    with pytest.raises(ValueError): cap.validate_plan(spec,UNIVERSE)


def test_legacy_preflight_still_has_27_call_and_two_hour_limits():
    spec = plan()
    for field in ("default_warmup_hours","incumbent_warmup_hours","anchor"): del spec[field]
    spec.update(schema="ed002-public-capture-plan-v1",lookback_completed_hours=2)
    preview = cap.validate_plan(spec,UNIVERSE)
    assert preview["planned_max_requests"] == 27
    assert set(preview["history_hours_by_symbol"].values()) == {2}


def test_unknown_identity_stays_unresolved_instead_of_disappearing(tmp_path):
    spec = plan();spec["identities"]["MATIC"] = None
    result = run(tmp_path,FakeWarmGet(),spec)
    assert result["status"] == "INCOMPLETE" and len(result["symbols"]) == 25
    assert result["symbols"]["MATIC"]["metadata_eligible_under_model"] is None


def test_future_seed_does_not_claim_retrospective_hourly_availability(tmp_path):
    result = run(tmp_path,FakeWarmGet())
    assert result["status"] == "COMPLETE"
    assert all(not i["latest_bar_received_within_one_hour"] for i in result["symbols"].values())
    assert not result["identity_authenticity_verified"]
