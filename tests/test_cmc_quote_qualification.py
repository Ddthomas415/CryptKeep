import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import quote as enc

from scripts.research.cmc_quote_qualification import ACCEPTED_COLLECTORS, all_ranges_above_zero, qualify_capture
from scripts.research.run_cmc_qualified_report import run_qualified

H = "a" * 64
COLLECTOR = sorted(ACCEPTED_COLLECTORS)[0]
T = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)


def iso(t):
    return t.isoformat().replace("+00:00", "Z")


def ticker(t, bid=100, ask=101, trip=0.05, trade_age=1.0):
    return {"payload": {"bid": str(bid), "ask": str(ask), "time": iso(t - timedelta(seconds=trade_age))},
            "request_started_utc": (t - timedelta(seconds=trip)).isoformat(), "received_utc": t.isoformat(),
            "response_sha256": H}


def book(product, t, bid=100, ask=101, bid_size="5", ask_size="5", age=0.5, trip=0.05, auction=False):
    return {"product_id": product,
            "request_url": "https://api.exchange.coinbase.com/products/" + enc(product, safe="") + "/book?level=1",
            "response": {"payload": {"bids": [[str(bid), bid_size, 1]], "asks": [[str(ask), ask_size, 1]],
                                     "sequence": 1, "auction_mode": auction, "auction": None,
                                     "time": iso(t - timedelta(seconds=age))},
                         "request_started_utc": (t - timedelta(seconds=trip)).isoformat(),
                         "received_utc": t.isoformat(), "response_sha256": H},
            "execution": "NOT_FILL_PROOF"}


def snap(product="X-USD", t=T, **kw):
    return {"collector_sha256": kw.pop("collector", COLLECTOR),
            "coinbase_level1_books": {} if kw.pop("no_book", False) else {product: book(product, t, **kw)}}


def test_fresh_sized_entry_qualifies_with_100usd_quantity():
    r = qualify_capture(snap(), "X-USD", ticker(T), "buy", identity_eligible=True)
    assert r["status"] == "QUALIFIED" and Decimal(r["quantity"]) == Decimal(100) / Decimal(101)


def test_capacity_uses_registered_ticker_quantity_not_later_book_price():
    r = qualify_capture(snap(ask=200, ask_size="0.75"), "X-USD",
                        ticker(T, ask=100), "buy", identity_eligible=True)
    assert Decimal(r["quantity"]) == 1
    assert r["status"] == "EXCLUDED"
    assert "INSUFFICIENT_DISPLAYED_SIZE" in r["reasons"]


def test_invalid_quantities_and_entry_asks_are_excluded_without_raising():
    for value in (True, False, 0, -1, "NaN", "Infinity", "bad"):
        r = qualify_capture(snap(), "X-USD", ticker(T), "sell", value, True)
        assert r["status"] == "EXCLUDED"
        assert "INVALID_QUANTITY" in r["reasons"] and r["quantity"] is None
        t = ticker(T)
        t["payload"]["ask"] = value
        r = qualify_capture(snap(), "X-USD", t, "buy", identity_eligible=True)
        assert r["status"] == "EXCLUDED" and "INVALID_ENTRY_ASK" in r["reasons"]


def test_each_policy_limit_excludes():
    cases = [(dict(), dict(trip=6.0), "STALE_CAPTURE"),
             (dict(age=11.0), dict(), "STALE_BOOK"),
             (dict(ask_size="0.5"), dict(), "INSUFFICIENT_DISPLAYED_SIZE"),
             (dict(no_book=True), dict(), "SIZE_UNVERIFIED_NO_BOOK"),
             (dict(collector="b" * 64), dict(), "EXCLUDED_PROVENANCE_COLLECTOR"),
             (dict(auction=True), dict(), "UNQUALIFIED_AUCTION_STATE"),
             (dict(trip=6.0), dict(), "STALE_CAPTURE_BOOK")]
    for book_kw, tick_kw, reason in cases:
        r = qualify_capture(snap(**book_kw), "X-USD", ticker(T, **tick_kw), "buy", identity_eligible=True)
        assert r["status"] == "EXCLUDED" and reason in r["reasons"], (reason, r)


def test_small_negative_book_age_is_clock_offset_not_stale():
    r = qualify_capture(snap(age=-0.6), "X-USD", ticker(T), "buy", identity_eligible=True)
    assert r["status"] == "QUALIFIED" and r["evidence"]["book_age_seconds"] < 0


def test_old_last_trade_is_flag_only():
    r = qualify_capture(snap(), "X-USD", ticker(T, trade_age=7200), "buy", identity_eligible=True)
    assert r["status"] == "QUALIFIED" and "ILLIQUID_FLAG" in r["flags"]


def test_identity_not_eligible_excludes():
    r = qualify_capture(snap(), "X-USD", ticker(T), "buy", identity_eligible=False)
    assert "EXCLUDED_PROVENANCE_IDENTITY" in r["reasons"]


def test_exit_keeps_entry_quantity_against_bid_size():
    q = str(Decimal(100) / Decimal(101))
    assert qualify_capture(snap(bid_size="1"), "X-USD", ticker(T), "sell", q, True)["status"] == "QUALIFIED"
    r = qualify_capture(snap(bid_size="0.9"), "X-USD", ticker(T), "sell", q, True)
    assert "INSUFFICIENT_DISPLAYED_SIZE" in r["reasons"]
    assert "SIZE_UNVERIFIED_NO_QUANTITY" in qualify_capture(snap(), "X-USD", ticker(T), "sell", None, True)["reasons"]


def test_gate_condition_requires_every_interval_above_zero():
    up = {"status": "DESCRIPTIVE", "p05": 0.01, "p95": 0.05}
    stats = {"status": "DIAGNOSTIC", "registered_entry_day_bootstrap": up,
             "serial_dependence_sensitivities_not_replacement_gate": {"7": up, "14": up, "28": up}}
    assert all_ranges_above_zero(stats) is True
    stats["serial_dependence_sensitivities_not_replacement_gate"]["28"] = {"status": "INCOMPLETE"}
    assert all_ranges_above_zero(stats) is False
    stats["serial_dependence_sensitivities_not_replacement_gate"]["28"] = {**up, "p05": -0.001}
    assert all_ranges_above_zero(stats) is False
    assert all_ranges_above_zero({"status": "NOT_READY_90_DAYS"}) == "NOT_EVALUABLE"


def test_gate_refuses_missing_blocks_and_invalid_bounds():
    up = {"status": "DESCRIPTIVE", "p05": 0.01, "p95": 0.05}
    def stats(blocks):
        return {"status": "DIAGNOSTIC", "registered_entry_day_bootstrap": up,
                "serial_dependence_sensitivities_not_replacement_gate": blocks}
    for blocks in ({}, {"7": up, "14": up}, {"7": up, "14": up, "28": up, "56": up}):
        assert all_ranges_above_zero(stats(blocks)) is False
    for invalid in ({"p05": True}, {"p05": "NaN"}, {"p95": "Infinity"},
                    {"p05": -1}, {"p95": 0.001}, {"p95": None}):
        assert all_ranges_above_zero(stats({"7": up, "14": up, "28": {**up, **invalid}})) is False


def build(tmp_path, exit_bid_size="5"):
    t0 = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    for day in range(0, 101):
        t = t0 + timedelta(days=day)
        coins = [1] + ([42] if day >= 40 else [])
        size = exit_bid_size if day == 47 else "5"
        bid = 120 if day == 47 else 110
        data = {"schema_version": 3, "artifact_type": "research_only_forward_log_v3", "places_orders": False,
                "snapshot_utc": t.isoformat(), "trending_status": "OBSERVED", "source_errors": [],
                "collector_sha256": COLLECTOR,
                "trending_hidden_boost": [{"type": "listing", "cmc_id": c, "identity_eligible": True,
                                           "coinbase_product": f"C{c}-USD", "coinbase": ticker(t)} for c in coins],
                "tracked_coinbase": ([{"cmc_id": 42, "coinbase_product": "C42-USD", "identity_eligible": True,
                                       "quote": ticker(t, bid, bid + 1)}] if day >= 40 else []),
                "majors_coinbase": {"BTC": ticker(t)},
                "coinbase_level1_books": {f"C{c}-USD": book(f"C{c}-USD", t, bid=bid if c == 42 and day > 40 else 100,
                                                            ask=(bid + 1) if c == 42 and day > 40 else 101,
                                                            bid_size=size) for c in coins}}
        (tmp_path / f"s{day:03d}.json").write_text(json.dumps(data))
    return run_qualified(tmp_path, t0 + timedelta(days=101))


def test_end_to_end_registered_and_qualified_views(tmp_path):
    r = build(tmp_path)
    assert r["qualified_view"]["seven_day_diagnostic_outcomes"] == 1
    assert r["qualified_view"]["seven_day_qualified_outcomes"] == 1
    assert r["primary_gate"] == "BLOCKED_STATISTICAL_METHOD_NOT_CERTIFIED" and r["scoring_authorized"] is False


def test_end_to_end_exit_size_failure_is_counted(tmp_path):
    r = build(tmp_path, exit_bid_size="0.5")
    assert r["qualified_view"]["seven_day_qualified_outcomes"] == 0
    assert {"horizon_days": 7, "leg": "exit", "reason": "INSUFFICIENT_DISPLAYED_SIZE", "count": 1} in r["exclusions_by_horizon_leg_reason"]


def test_future_rejected_snapshot_cannot_change_endpoint_linkage(tmp_path):
    baseline = build(tmp_path)
    future = json.loads((tmp_path / "s047.json").read_text())
    future["snapshot_utc"] = iso(datetime(2028, 1, 1, tzinfo=timezone.utc))
    (tmp_path / "future.json").write_text(json.dumps(future))
    now = datetime(2026, 10, 1, 12, tzinfo=timezone.utc) + timedelta(days=101)
    result = run_qualified(tmp_path, now)
    assert result["qualified_view"] == baseline["qualified_view"]
    assert result["qualification_rows"] == baseline["qualification_rows"]
    assert any(r["reason"] == "future snapshot" for r in result["source_report_rejected_envelopes"])


def test_changed_accepted_snapshot_is_refused(tmp_path, monkeypatch):
    import pytest
    from scripts.research import run_cmc_qualified_report as wrapper
    build(tmp_path)
    original = wrapper.load_snapshot
    def changed(path):
        item = original(path)
        item["sha256"] = "changed"
        return item
    monkeypatch.setattr(wrapper, "load_snapshot", changed)
    with pytest.raises(ValueError, match="changed_during_qualification"):
        wrapper.run_qualified(tmp_path, datetime(2027, 1, 10, tzinfo=timezone.utc))


def test_exchange_timestamp_precisions_parse():
    from scripts.research.cmc_quote_qualification import _time
    for value in ("2026-10-09T10:59:34.747268020Z", "2026-10-09T10:59:36.5Z", "2026-10-09T10:59:36Z",
                  "2026-10-09T10:59:36.658147+00:00"):
        assert _time(value).tzinfo is not None
