"""Synthetic continuation/receipt-readiness checks; no external work or returns."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import socket
import subprocess
from urllib.parse import urlencode

import pytest
import yaml

from scripts.research import capture_descriptive_inputs as cap
from services.backtest import descriptive_readiness as ready


H, A = cap.candles.HOUR, 2000*cap.candles.HOUR
UNIVERSE = (cap.ROOT/"config/candidate_universe.yaml").read_bytes()
CONFIG = yaml.safe_load(UNIVERSE)["universe"]
SYMBOLS = sorted(s.split("/")[0] for t in ("tier1", "tier2", "watchlist") for s in CONFIG[t])
IDS = {s: {"product_id": s+"-USD", "base_currency": s, "quote_currency": "USD",
           "identity_evidence_sha256": hashlib.sha256(("invented "+s).encode()).hexdigest()} for s in SYMBOLS}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("test attempted external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, refuse)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, refuse)


def spec():
    return {"schema": cap.CONTINUATION_SCHEMA, "universe_sha256": cap.sha(UNIVERSE),
            "identities": deepcopy(IDS), "start_ms": A-24*H, "end_ms": A}


def products(excluded="MATIC"):
    return [{"id": s+"-USD", "base_currency": s, "quote_currency": "USD",
             "status": "delisted" if s == excluded else "online", "base_increment": ".001",
             **dict.fromkeys(cap.metadata.FLAGS, False)} for s in SYMBOLS]


def url(symbol, first, end):
    params = urlencode({"granularity": 3600,
        "start": datetime.fromtimestamp(first/1000, timezone.utc).isoformat(),
        "end": datetime.fromtimestamp((end-1000)/1000, timezone.utc).isoformat()})
    return cap.BASE+"/products/"+symbol+"-USD/candles?"+params


def receipt(route, data, received, *, status=200, truncated=False):
    raw = json.dumps(data).encode()
    return {"method": "GET", "url": route, "request_started_ms": received-1,
            "received_at_ms": received, "http_status": status, "response_bytes": raw,
            "sha256": hashlib.sha256(raw).hexdigest(), "truncated": truncated}


@pytest.fixture
def receipts():
    records = [receipt(cap.BASE+"/products", products(), A-H//2),
               receipt(cap.BASE+"/products", products(), A+H//2)]
    for s in SYMBOLS:
        if s == "MATIC":
            continue
        first = A-(1464 if s in ("BTC", "ETH") else 300)*H
        for page in range(first, A, 300*H):
            end = min(A,page+300*H)
            records.append(receipt(url(s,page,end),
                [[t//1000,90,110,100,105,5] for t in range(page,end,H)], A+5*60000))
    return records


def merge(records, *, cutoff=A+H, identities=None):
    return ready.merge_receipts(records, symbols=SYMBOLS, identities=identities or IDS,
        start_ms=A-1464*H, end_ms=A, as_of_ms=cutoff)


def report(records, *, checked=A+H, identities=None):
    return ready.first_batch_readiness(merge(records,cutoff=min(checked,A+H),identities=identities),
        signal_close_ms=A, checked_at_ms=checked)


@pytest.mark.parametrize("excluded",[None,"MATIC"])
def test_pinned_24_hour_capture_all25_and_no_authority(tmp_path,excluded):
    calls = []
    def fake_get(route, timeout, limit):
        calls.append(route)
        if route.endswith("/products"):
            data = products(excluded)
        elif route.endswith("/currencies"):
            data = [{"id": s} for s in ["USD",*SYMBOLS]]
        else:
            data = [[t//1000,90,110,100,105,5] for t in range(A-24*H,A,H)]
        return 200,json.dumps(data).encode(),{}
    preview = cap.validate_plan(spec(),UNIVERSE)
    assert preview["planned_max_requests"] == 27
    assert set(preview["history_hours_by_symbol"].values()) == {24}
    result = cap.capture_once(spec(),tmp_path,get=fake_get,monotonic=lambda: 0,wall_ms=lambda: A+H//2)
    cap.verify_result(result,tmp_path,spec())
    assert result["status"] == "COMPLETE" and len(calls) == (27 if excluded is None else 26)
    assert len(result["symbols"]) == 25 and not result["scoring_authorized"]
    normal = json.loads((tmp_path/"observations.json").read_bytes())
    assert sum(map(len,normal["observations"].values())) == (25 if excluded is None else 24)*24
    assert all(r["known_at_ms"] == A+H//2 for rows in normal["observations"].values() for r in rows)


@pytest.mark.parametrize("field,value",[("start_ms",A-25*H),("start_ms",A),
    ("start_ms",A+H),("start_ms",True),("start_ms",-H),("end_ms",A+1),
    ("end_ms",float(A)),("schema","ed002-auto-catchup"),("universe_sha256","bad")])
def test_continuation_refuses_unbounded_unaligned_or_changed_scope(field,value):
    plan=spec();plan[field]=value
    with pytest.raises(ValueError):cap.validate_plan(plan,UNIVERSE)


def test_future_pinned_window_refused_before_transport_or_file_write(tmp_path):
    def forbidden(*args):raise AssertionError("transport called")
    with pytest.raises(ValueError,match="completed_window"):
        cap.capture_once(spec(),tmp_path,get=forbidden,wall_ms=lambda:A-1,monotonic=lambda:0)
    assert not list(tmp_path.iterdir())


def test_first_batch_ready_with_cash_exclusion_no_fills_or_activation(receipts):
    merged=merge(receipts)
    result=ready.first_batch_readiness(merged,signal_close_ms=A,checked_at_ms=A+H)
    assert result["status"] == "COMPLETE" and len(result["rows"]) == 25
    assert merged["physical_window_status"] == "INCOMPLETE"
    rows={r["symbol"]:r for r in result["rows"]}
    assert rows["MATIC"]["signal_eligible"] is False and rows["MATIC"]["required_signal_hours"] == 0
    assert rows["BTC"]["required_signal_hours"] == rows["ETH"]["required_signal_hours"] == 1464
    assert rows["SOL"]["required_signal_hours"] == 300
    assert not any(result[k] for k in ("activation_authorized","execution_open_verified","scoring_authorized"))


def test_overlap_is_deduplicated_and_earliest_receipt_preserved(receipts):
    source=deepcopy(receipts)
    candle=next(r for r in receipts if "/SOL-USD/" in r["url"])
    later=deepcopy(candle);later["received_at_ms"]+=60000
    numeric=receipt(later["url"],[[float(v) if i else v for i,v in enumerate(row)]
        for row in json.loads(later["response_bytes"])],later["received_at_ms"])
    merged=merge(receipts+[deepcopy(candle),numeric])
    assert len(merged["observations"]["SOL"]) == 300
    assert all(r["known_at_ms"] == A+5*60000 for r in merged["observations"]["SOL"])
    assert receipts == source


def test_conflicting_completed_version_withholds_hour_not_winner(receipts):
    candle=next(r for r in receipts if "/SOL-USD/" in r["url"])
    rows=json.loads(candle["response_bytes"]);rows[-1][4]=106
    revised=receipt(candle["url"],rows,A+10*60000)
    result=report(receipts+[revised])
    sol=next(r for r in result["rows"] if r["symbol"] == "SOL")
    assert result["status"] == "INCOMPLETE" and sol["conflicting_hours"] == [A-H]
    assert sol["missing_or_late_hours"] == [A-H]


def test_late_and_future_corrupt_receipts_do_not_repair_past_deadline(receipts):
    first=report(receipts)
    later=deepcopy(receipts)
    for r in later:
        if "/SOL-USD/" in r["url"]:r["received_at_ms"]=A+H+1
    later.append({"received_at_ms":A+2*H})
    result=report(later,checked=A+3*H)
    assert first["status"] == "COMPLETE" and result["status"] == "INCOMPLETE"
    assert result["execution_ms"] == A+H and result["deadline_passed"]


@pytest.mark.parametrize("change",["hash","clock","truncated_flag","host","method","undeclared"])
def test_untrusted_or_misrouted_receipt_refused(receipts,change):
    records=deepcopy(receipts)
    item=records[-1]
    if change=="hash":item["sha256"]="0"*64
    elif change=="clock":item["request_started_ms"]=item["received_at_ms"]+1
    elif change=="truncated_flag":item["truncated"]=0
    elif change=="host":item["url"]=item["url"].replace("api.exchange.coinbase.com","unapproved.example")
    elif change=="method":item["method"]="POST"
    else:item["url"]=item["url"].replace("/XRP-USD/","/UNKNOWN-USD/")
    with pytest.raises(ValueError):merge(records)


@pytest.mark.parametrize("failure",["http","truncated","unreadable","ambiguous"])
def test_new_bad_products_shadows_prior_permission(receipts,failure):
    kwargs={"status":503} if failure=="http" else {"truncated":True} if failure=="truncated" else {}
    bad=receipt(cap.BASE+"/products",{} if failure=="unreadable" else products(),A+40*60000,**kwargs)
    records=receipts+[bad]
    if failure=="ambiguous":records.append(receipt(cap.BASE+"/products",[],A+40*60000))
    result=report(records)
    assert result["status"] == "INCOMPLETE"
    assert all("unknown_execution_eligible" in r["reasons"] for r in result["rows"])
    if failure in ("http","truncated","ambiguous"):
        latest=merge(records)["rules"]["SOL"][-1]
        assert latest["eligible"] is None and latest["original_source_sha256"]


def test_missing_products_and_expired_rules_do_not_grant_permission(receipts):
    none=[r for r in receipts if not r["url"].endswith("/products")]
    assert report(none)["status"] == "INCOMPLETE"
    expired=[r for r in receipts if r["received_at_ms"] != A+H//2]
    result=report(expired)
    assert all(r["execution_eligible"] is None for r in result["rows"])


def test_metadata_observed_after_A_cannot_grant_signal_permission(receipts):
    result=report([r for r in receipts if r["received_at_ms"] != A-H//2])
    assert all(r["signal_eligible"] is None and r["execution_eligible"] is not None for r in result["rows"])


def test_unknown_identity_not_treated_as_excluded_or_removed(receipts):
    identities=deepcopy(IDS);identities["MATIC"]=None
    result=report(receipts,identities=identities)
    matic=next(r for r in result["rows"] if r["symbol"]=="MATIC")
    assert result["status"]=="INCOMPLETE" and matic["signal_eligible"] is None


def test_control_ineligible_invalidates_initial_comparison(receipts):
    records=[r for r in receipts if not r["url"].endswith("/products")]
    for t in (A-H//2,A+H//2):records.append(receipt(cap.BASE+"/products",products("BTC"),t))
    result=report(records)
    btc=next(r for r in result["rows"] if r["symbol"]=="BTC")
    assert result["status"]=="INCOMPLETE" and "required_control_ineligible" in btc["reasons"]


def test_failed_candle_does_not_erase_good_observation(receipts):
    c=next(r for r in receipts if "/SOL-USD/" in r["url"])
    failed=receipt(c["url"],[],A+20*60000,status=503)
    assert report(receipts+[failed])["status"]=="COMPLETE"
    records=[r for r in receipts if "/SOL-USD/" not in r["url"]]+[failed]
    assert report(records)["status"]=="INCOMPLETE"


def test_unanswered_call_is_diagnostic_not_delivery_or_loss_of_good_data(receipts):
    source=next(r for r in receipts if "/SOL-USD/" in r["url"])
    failed={"method":"GET","url":source["url"],"request_started_ms":A+20*60000,
            "received_at_ms":None,"http_status":None,"error_class":"TimeoutError"}
    assert report(receipts+[failed])["status"]=="COMPLETE"
    item=merge(receipts+[failed])["receipt_evidence"][-1]
    assert item["qualification"]=="UNANSWERED_NOT_OBSERVATION" and "source_sha256" not in item
    intent=deepcopy(failed);del intent["error_class"]
    with pytest.raises(ValueError,match="diagnostic"):merge(receipts+[intent])


def test_truncated_candle_cannot_supply_a_missing_hour(receipts):
    records=deepcopy(receipts)
    for row in records:
        if "/SOL-USD/" in row["url"]:row["truncated"]=True
    assert report(records)["status"]=="INCOMPLETE"


def test_declared_scope_cannot_silently_shrink(receipts):
    with pytest.raises(ValueError,match="25_symbol"):
        ready.merge_receipts(receipts,symbols=SYMBOLS[:-1],identities=IDS,
            start_ms=A-1464*H,end_ms=A,as_of_ms=A+H)


def test_check_requires_the_fixed_E_prefix_and_initial_close(receipts):
    with pytest.raises(ValueError,match="fixed_first_batch"):
        ready.first_batch_readiness(merge(receipts),signal_close_ms=A,checked_at_ms=A+10*60000)
    with pytest.raises(ValueError,match="initial_signal"):
        ready.first_batch_readiness(merge(receipts),signal_close_ms=A+H,checked_at_ms=A+H)
    assert report(receipts,checked=A+45*60000)["status"] == "COMPLETE"
