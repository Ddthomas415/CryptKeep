import pytest

from scripts.research.report_market_context_markouts import summarize


def row(kind, ident, sec, **kwargs):
    return dict(schema_version=1, kind=kind, event_id=ident, monotonic_ns=int(sec*1e9),
                venue="coinbase", symbol="BTC/USD", config_sha256="x",
                capture_session_id="session-a", **kwargs)


def quote(ident, sec, price=100):
    return row("quote", ident, sec, bid=price, ask=price, source_age_sec=0,
               quality_ok=True)


def sample():
    return [quote("q", 0), row("admitted_entry", "e", .1, quote_event_id="q"),
            quote("later", 5.1, 101)]


def test_observed_label_not_net_profit():
    result = summarize(sample(), horizons=[5])
    assert result["entries"][0]["labels"][0]["gross_mid_return_bps"] == pytest.approx(100)
    assert result["entries"][0]["net_profit"] is None


@pytest.mark.parametrize("field,value", [("quality_ok", False), ("bid", float("nan")),
                                          ("source_age_sec", None), ("source_age_sec", 2)])
def test_bad_entry_quote_unavailable(field, value):
    rows = sample()
    rows[0][field] = value
    assert summarize(rows)["entries"][0]["labels"][0]["gross_mid_return_bps"] is None


@pytest.mark.parametrize("time", [5.0, 6.2])
def test_no_early_or_overdue_horizon_quote(time):
    rows = sample()
    rows[-1]["monotonic_ns"] = int(time*1e9)
    assert summarize(rows, horizons=[5])["entries"][0]["labels"][0]["gross_mid_return_bps"] is None


def test_no_entry_and_duplicate_fail_closed():
    assert summarize([quote("q", 0)])["status"] == "NO_ENTRY_EVIDENCE"
    with pytest.raises(ValueError, match="duplicate"):
        summarize([quote("q", 0), quote("q", 1)])


def test_other_symbol_not_joined():
    rows = sample()
    rows[-1]["symbol"] = "ETH/USD"
    assert summarize(rows)["entries"][0]["labels"][0]["gross_mid_return_bps"] is None


def test_session_provenance_and_clock_reset_rejected():
    rows = sample()
    rows[-1]["capture_session_id"] = "session-b"
    with pytest.raises(ValueError, match="mixed capture sessions"):
        summarize(rows)
    rows[-1].pop("capture_session_id")
    with pytest.raises(ValueError, match="missing capture session"):
        summarize(rows)
    with pytest.raises(ValueError, match="clock order reset"):
        summarize(list(reversed(sample())))


@pytest.mark.parametrize("case", ["stale_future", "missing_link", "future_entry"])
def test_unavailable_labels_and_truthful_counts(case):
    rows = sample()
    if case == "stale_future":
        rows[-1]["source_age_sec"] = 10
    elif case == "missing_link":
        rows[1]["quote_event_id"] = "absent"
    else:
        rows[1]["quote_event_id"] = "later"
    result = summarize(rows, horizons=[5])
    assert result["admitted_entry_count"] == 1
    assert result["available_label_count"] == 0
    assert result["valid_entry_quote_count"] == int(case == "stale_future")
