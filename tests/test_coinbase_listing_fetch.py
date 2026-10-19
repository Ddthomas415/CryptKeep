"""Offline tests for the ENTR-CB-1 Step B candle-date fetcher and listing builder (synthetic data, no network)."""
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import re
from urllib.parse import parse_qs, urlparse

import pytest

from scripts.research import build_coinbase_listings as builder
from scripts.research import fetch_coinbase_listing_dates as fetch
from scripts.research.run_coinbase_tradable_entrants import classify, parse_listings

END = date(2026, 10, 19)
WINS = fetch.windows(END)


def span(a, b):
    a, b = date.fromisoformat(a), date.fromisoformat(b)
    return {a + timedelta(days=i) for i in range((b - a).days + 1)}


class FakeCoinbase:
    """Serves daily candles for known products, newest first, like the Exchange API."""

    def __init__(self, days, script=None):
        self.days, self.script, self.urls = days, dict(script or {}), []

    def __call__(self, url):
        self.urls.append(url)
        n = len(self.urls)
        if n in self.script:
            return self.script[n]
        product = re.search(r"/products/([^/]+)/candles", url).group(1)
        if product not in self.days:
            return 404, b'{"message":"NotFound"}'
        q = parse_qs(urlparse(url).query)
        start = datetime.fromisoformat(q["start"][0].replace("Z", "+00:00")).date()
        end = datetime.fromisoformat(q["end"][0].replace("Z", "+00:00")).date()
        assert (end - start).days + 1 <= 300, "window larger than 300 candles"
        rows = [[int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()), 1, 2, 1, 2, 10]
                for d in sorted(self.days[product], reverse=True) if start <= d <= end]
        return 200, json.dumps(rows).encode()


class Clock:
    def __init__(self):
        self.t, self.sleeps = 0.0, []

    def __call__(self):
        self.t += 0.05  # every clock read costs a little time
        return self.t

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


def run_product(tmp_path, days, product="X-USD", script=None, cap=100):
    (tmp_path / "raw").mkdir(exist_ok=True)
    state = {"requests": 0}
    clock = Clock()
    fake = FakeCoinbase(days, script)
    f = fetch.Fetcher(tmp_path, state, cap, get=fake, sleep=clock.sleep, clock=clock)
    return f.product(product, WINS), fake, state, clock


# ---------- windows and URLs ----------

def test_windows_are_back_to_back_300_day_windows_from_search_start_to_end_day():
    assert WINS[0][0] == date(2018, 12, 15) and WINS[-1][1] == END
    for (a, b), (c, _) in zip(WINS, WINS[1:]):
        assert (b - a).days == 299 and c == b + timedelta(days=1)
    assert (WINS[-1][1] - WINS[-1][0]).days <= 299


def test_url_uses_the_step_a_form_with_midnight_end_of_the_300th_day():
    url = fetch.candle_url("GNT-USDC", (date(2019, 1, 1), date(2019, 10, 27)))
    assert url == ("https://api.exchange.coinbase.com/products/GNT-USDC/candles?granularity=86400"
                   "&start=2019-01-01T00:00:00Z&end=2019-10-27T00:00:00Z")


# ---------- search results ----------

def test_online_product_listed_mid_range_gets_exact_first_and_last(tmp_path):
    res, fake, state, _ = run_product(tmp_path, {"X-USD": span("2022-03-07", "2026-10-18")})
    assert res == {"first": "2022-03-07", "last": "2026-10-18", "first_at_search_start": False,
                   "windows_queried": res["windows_queried"], "error": None}
    assert state["requests"] == len(fake.urls) <= 1 + 4  # newest window + binary search over <= 10 windows


def test_first_on_any_day_of_any_window_is_found_exactly(tmp_path):
    for i, start in enumerate([date(2018, 12, 15), date(2019, 10, 10), date(2020, 8, 4), date(2023, 1, 1),
                               date(2025, 9, 1), date(2026, 10, 18)]):
        out = tmp_path / str(i)
        out.mkdir()
        res, *_ = run_product(out, {"X-USD": span(start.isoformat(), "2026-10-19")})
        assert res["first"] == start.isoformat() and res["last"] == "2026-10-19"
        assert res["first_at_search_start"] == (start == date(2018, 12, 15))


def test_delisted_product_gets_exact_first_and_last(tmp_path):
    res, fake, *_ = run_product(tmp_path, {"X-USDT": span("2021-04-09", "2023-10-16")}, "X-USDT")
    assert (res["first"], res["last"], res["error"]) == ("2021-04-09", "2023-10-16", None)


def test_product_without_any_candle_reports_none_without_error(tmp_path):
    res, fake, *_ = run_product(tmp_path, {"X-USD": set()})
    assert (res["first"], res["last"], res["error"]) == (None, None, None)
    assert len(fake.urls) == len(WINS)


def test_last_is_exact_even_with_a_gap_but_a_window_long_gap_can_move_first_later(tmp_path):
    # KNOWN LIMIT, documented in the module: binary search assumes trading in every window after listing.
    days = span("2019-01-01", "2020-12-31") | span("2023-06-07", "2026-10-19")
    res, *_ = run_product(tmp_path, {"X-USD": days})
    assert res["last"] == "2026-10-19"
    assert res["first"] == "2023-06-07"  # true first is 2019-01-01: the search lands in the gap
    assert ["2022-03-29", 0] in res["windows_queried"], "the empty window queried is recorded"


# ---------- request handling ----------

def test_raw_bodies_are_saved_byte_for_byte_and_logged_with_sha256(tmp_path):
    res, fake, state, _ = run_product(tmp_path, {"X-USD": span("2024-01-01", "2026-10-19")})
    lines = [json.loads(l) for l in (tmp_path / "requests.jsonl").read_text().splitlines()]
    assert [l["n"] for l in lines] == list(range(1, len(fake.urls) + 1))
    for line, url in zip(lines, fake.urls):
        body = (tmp_path / line["file"]).read_bytes()
        assert line["url"] == url and line["http_status"] == 200
        assert line["sha256"] == hashlib.sha256(body).hexdigest() and line["bytes"] == len(body)


def test_requests_are_spaced_to_under_three_per_second(tmp_path):
    stamps = []
    clock = Clock()

    def get(url):
        stamps.append(clock.t)
        return 200, b"[]"
    (tmp_path / "raw").mkdir()
    f = fetch.Fetcher(tmp_path, {"requests": 0}, 100, get=get, sleep=clock.sleep, clock=clock)
    f.product("X-USD", WINS)
    assert len(stamps) == len(WINS)
    assert all(b - a >= fetch.MIN_INTERVAL for a, b in zip(stamps, stamps[1:]))


def test_transient_failures_are_retried_and_each_attempt_counted(tmp_path):
    script = {1: (429, b"slow down"), 2: (None, b"NETWORK_ERROR: x")}
    res, fake, state, clock = run_product(tmp_path, {"X-USD": span("2024-01-01", "2026-10-19")}, script=script)
    assert res["error"] is None and res["first"] == "2024-01-01"
    assert fetch.RETRY_WAITS[0] in clock.sleeps and fetch.RETRY_WAITS[1] in clock.sleeps
    assert state["requests"] == len(fake.urls) == len((tmp_path / "requests.jsonl").read_text().splitlines())


def test_three_transient_failures_in_a_row_fail_the_product(tmp_path):
    script = {1: (503, b""), 2: (503, b""), 3: (503, b"")}
    res, fake, *_ = run_product(tmp_path, {"X-USD": span("2024-01-01", "2026-10-19")}, script=script)
    assert res["error"] == "http_503_after_retries" and res["first"] is None and len(fake.urls) == 3


def test_not_found_fails_the_product_without_retry(tmp_path):
    res, fake, *_ = run_product(tmp_path, {}, "GONE-USD")
    assert res["error"] == "http_404" and len(fake.urls) == 1


@pytest.mark.parametrize("body", [b"not json", b'{"message":"x"}', b"[1, 2]", b"[[]]"])
def test_a_200_body_that_is_not_candle_rows_fails_the_product(tmp_path, body):
    res, *_ = run_product(tmp_path, {"X-USD": set()}, script={1: (200, body)})
    assert res["error"] == "bad_body"


def test_a_candle_outside_the_requested_window_fails_the_product(tmp_path):
    ts = int(datetime(2010, 1, 1, tzinfo=timezone.utc).timestamp())
    res, *_ = run_product(tmp_path, {"X-USD": set()}, script={1: (200, json.dumps([[ts, 1, 1, 1, 1, 1]]).encode())})
    assert res["error"] == "candle_outside_window"


def test_request_cap_is_hard(tmp_path):
    with pytest.raises(fetch.RequestCapReached):
        run_product(tmp_path, {"X-USD": set()}, cap=3)
    assert len((tmp_path / "requests.jsonl").read_text().splitlines()) == 3


# ---------- main: pinning, targets, resume, budget ----------

def make_inputs(tmp_path, records, products):
    m = tmp_path / "map.json"
    m.write_text(json.dumps({"records": records}))
    p = tmp_path / "products.json"
    p.write_text(json.dumps(products))
    sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    return ["--map", str(m), "--map-sha256", sha(m), "--products", str(p), "--products-sha256", sha(p)]


RECORDS = {
    "1": {"status": "mapped", "products": [{"id": "A-USD"}, {"id": "A-USDT"}]},
    "2": {"status": "mapped", "products": [{"id": "B-USD"}]},
    "3": {"status": "never_listed", "reason": "absent_from_products"},
    "4": {"status": "unknown", "reason": "x", "products": [{"id": "C-USD"}]},
    "5": {"status": "mapped", "products": [{"id": "A-USD"}]},
}
PRODUCTS = [{"id": "A-USD", "status": "online"}, {"id": "A-USDT", "status": "delisted"},
            {"id": "B-USD", "status": "delisted"}, {"id": "C-USD", "status": "online"},
            {"id": "D-USD", "status": "online"}]
DAYS = {"A-USD": span("2020-01-05", "2026-10-19"), "A-USDT": span("2021-04-01", "2023-10-16"),
        "B-USD": span("2019-06-01", "2022-02-02")}


def test_main_fetches_only_products_of_mapped_records_and_writes_results(tmp_path):
    args = make_inputs(tmp_path, RECORDS, PRODUCTS)
    out = tmp_path / "out"
    fake, clock = FakeCoinbase(DAYS), Clock()
    summary = fetch.main(args + ["--output-dir", str(out)], get=fake, sleep=clock.sleep, clock=clock, today=END)
    assert summary["products_remaining"] == 0 and summary["failed"] == []
    assert {re.search(r"/products/([^/]+)/", u).group(1) for u in fake.urls} == {"A-USD", "A-USDT", "B-USD"}
    res = json.loads((out / "results.json").read_text())
    assert res["products"]["A-USDT"]["first"] == "2021-04-01" and res["products"]["A-USDT"]["product_status"] == "delisted"
    assert res["requests"] == len(fake.urls) and res["end_day"] == "2026-10-19"


def test_main_refuses_changed_inputs_and_unexpected_output_dir(tmp_path):
    args = make_inputs(tmp_path, RECORDS, PRODUCTS)
    bad = list(args)
    bad[3] = "0" * 64
    with pytest.raises(SystemExit):
        fetch.main(bad + ["--output-dir", str(tmp_path / "o1")], get=FakeCoinbase(DAYS), today=END)
    (tmp_path / "o2").mkdir()
    (tmp_path / "o2" / "stray.txt").write_text("x")
    with pytest.raises(SystemExit):
        fetch.main(args + ["--output-dir", str(tmp_path / "o2")], get=FakeCoinbase(DAYS), today=END)


def test_main_refuses_a_mapped_product_missing_from_products_list(tmp_path):
    args = make_inputs(tmp_path, {"1": {"status": "mapped", "products": [{"id": "Z-USD"}]}}, PRODUCTS)
    with pytest.raises(SystemExit):
        fetch.main(args + ["--output-dir", str(tmp_path / "o")], get=FakeCoinbase(DAYS), today=END)


def test_interrupted_runs_resume_to_the_same_results_with_a_contiguous_log(tmp_path):
    args = make_inputs(tmp_path, RECORDS, PRODUCTS)
    clean = tmp_path / "clean"
    fetch.main(args + ["--output-dir", str(clean)], get=FakeCoinbase(DAYS), sleep=Clock().sleep, clock=Clock(), today=END)
    out = tmp_path / "out"
    calls = {"n": 0}
    real = FakeCoinbase(DAYS)

    def dying(url):
        calls["n"] += 1
        if calls["n"] == 7:
            raise KeyboardInterrupt  # killed mid-product, like a shell timeout
        return real(url)
    with pytest.raises(KeyboardInterrupt):
        fetch.main(args + ["--output-dir", str(out)], get=dying, sleep=Clock().sleep, clock=Clock(), today=END)
    assert not (out / "results.json").exists()
    # a body saved without its log line (stopped between the two writes), named exactly like the next request
    n = len((out / "requests.jsonl").read_text().splitlines())
    st = json.loads((out / "state.json").read_text())
    nxt = next(p for p in st["todo"] if p not in st["done"])
    orphan = f"{n + 1:05d}_{nxt}_{WINS[-1][0].isoformat()}.json"
    (out / "raw" / orphan).write_bytes(b"orphan")
    fetch.main(args + ["--output-dir", str(out)], get=real, sleep=Clock().sleep, clock=Clock(), today=END)
    a = json.loads((clean / "results.json").read_text())
    b = json.loads((out / "results.json").read_text())
    strip = lambda d: {p: {k: v for k, v in r.items()} for p, r in d["products"].items()}
    assert strip(a) == strip(b)
    lines = [json.loads(l) for l in (out / "requests.jsonl").read_text().splitlines()]
    assert [l["n"] for l in lines] == list(range(1, len(lines) + 1)) and b["requests"] == len(lines)
    assert b["requests"] > a["requests"]  # the interrupted product's requests stay counted
    state = json.loads((out / "state.json").read_text())
    assert state["unlogged_files"] == [f"raw/unlogged_{orphan}"]
    assert (out / "raw" / f"unlogged_{orphan}").read_bytes() == b"orphan"
    assert hashlib.sha256((out / "raw" / orphan).read_bytes()).hexdigest() == lines[n]["sha256"]


def test_budget_stops_between_products_and_results_wait_for_the_last_product(tmp_path):
    args = make_inputs(tmp_path, RECORDS, PRODUCTS)
    out = tmp_path / "out"
    s1 = fetch.main(args + ["--output-dir", str(out), "--budget-seconds", "0"], get=FakeCoinbase(DAYS),
                    sleep=Clock().sleep, clock=Clock(), today=END)
    assert s1["stopped"] == "budget" and s1["products_done"] == 0 and not (out / "results.json").exists()
    s2 = fetch.main(args + ["--output-dir", str(out)], get=FakeCoinbase(DAYS), sleep=Clock().sleep,
                    clock=Clock(), today=date(2030, 1, 1))
    assert s2["products_remaining"] == 0
    assert json.loads((out / "results.json").read_text())["end_day"] == "2026-10-19"  # first run's day kept


def test_cap_stops_the_run_cleanly_and_a_later_run_with_a_higher_cap_finishes(tmp_path):
    args = make_inputs(tmp_path, RECORDS, PRODUCTS)
    out = tmp_path / "out"
    s1 = fetch.main(args + ["--output-dir", str(out), "--max-requests", "4"], get=FakeCoinbase(DAYS),
                    sleep=Clock().sleep, clock=Clock(), today=END)
    assert s1["stopped"] == "request_cap" and s1["requests_total"] == 4 and not (out / "results.json").exists()
    s2 = fetch.main(args + ["--output-dir", str(out)], get=FakeCoinbase(DAYS), sleep=Clock().sleep,
                    clock=Clock(), today=END)
    assert s2["products_remaining"] == 0


# ---------- listing builder ----------

def results_doc(products, map_sha="m" * 64):
    return {"schema": builder.RESULTS_SCHEMA, "map_sha256": map_sha, "end_day": "2026-10-19",
            "search_start": "2018-12-15", "products": products}


def pr(first, last, error=None):
    return {"first": first, "last": last, "error": error, "first_at_search_start": first == "2018-12-15",
            "windows_queried": []}


def test_builder_maps_statuses_and_dates_and_output_parses_with_the_runner():
    records = {"1": {"status": "mapped", "reason": "exact", "products": [{"id": "A-USD"}, {"id": "A-USDT"}]},
               "2": {"status": "mapped", "reason": "exact", "products": [{"id": "B-USD"}]},
               "3": {"status": "never_listed", "reason": "absent_from_products"},
               "4": {"status": "unknown", "reason": "name_slug_mismatch_unadjudicated"},
               "5": {"status": "mapped", "reason": "exact", "products": [{"id": "C-USD"}]},
               "6": {"status": "mapped", "reason": "exact", "products": [{"id": "D-USD"}]},
               "7": {"status": "mapped", "reason": "exact", "products": [{"id": "E-USD"}]}}
    results = results_doc({"A-USD": pr("2021-05-01", "2026-10-18"), "A-USDT": pr("2021-04-01", "2023-10-16"),
                           "B-USD": pr("2018-12-15", "2022-02-02"), "C-USD": pr(None, None, "http_404"),
                           "D-USD": pr(None, None), "E-USD": pr("2020-01-01", "2026-10-11")})
    listings, report = builder.build({"records": records}, results, "m" * 64)
    a = listings["assets"]
    assert a["1"] == {"status": "mapped", "product": "A-USDT", "first_candle": "2021-04-01", "last_candle": None}
    assert a["2"] == {"status": "mapped", "product": "B-USD", "first_candle": "2018-12-15", "last_candle": "2022-02-02"}
    assert a["3"] == {"status": "never_listed"} and a["4"] == {"status": "unknown"}
    assert a["5"] == {"status": "unknown"} and report["5"]["reason"].startswith("candle_fetch_failed")
    assert a["6"] == {"status": "unknown"} and report["6"]["reason"] == "no_candles_on_any_product"
    assert a["7"]["last_candle"] == "2026-10-11"  # 8 days before the end day: not "still trading"
    assert report["2"]["first_at_search_start"] is True and report["1"]["product_interval_gaps"] == []
    parsed = parse_listings(json.dumps(listings).encode())
    assert classify(parsed, 1, date(2021, 4, 2)) == "tradable"
    assert classify(parsed, 1, date(2021, 4, 1)) == "not_yet_listed"
    assert classify(parsed, 2, date(2022, 2, 3)) == "delisted_before_entry"
    assert classify(parsed, 5, date(2024, 1, 1)) == "unknown"


def test_builder_reports_gaps_between_product_intervals():
    records = {"1": {"status": "mapped", "reason": "exact",
                     "products": [{"id": "A-USD"}, {"id": "A-USDC"}, {"id": "A-USDT"}]}}
    results = results_doc({"A-USDT": pr("2019-01-01", "2020-12-31"), "A-USDC": pr("2020-06-01", "2021-01-01"),
                           "A-USD": pr("2023-06-07", "2026-10-19")})
    listings, report = builder.build({"records": records}, results, "m" * 64)
    assert listings["assets"]["1"]["first_candle"] == "2019-01-01" and listings["assets"]["1"]["last_candle"] is None
    assert report["1"]["product_interval_gaps"] == [{"from": "2021-01-02", "to": "2023-06-06", "resumed_on": "A-USD"}]


def test_builder_refuses_results_for_another_map_or_a_missing_product():
    records = {"1": {"status": "mapped", "reason": "exact", "products": [{"id": "A-USD"}]}}
    with pytest.raises(ValueError):
        builder.build({"records": records}, results_doc({"A-USD": pr("2020-01-01", "2026-10-19")}, "x" * 64), "m" * 64)
    with pytest.raises(ValueError):
        builder.build({"records": records}, results_doc({}), "m" * 64)


def test_builder_main_pins_inputs_and_writes_exclusively(tmp_path):
    m = tmp_path / "map.json"
    m.write_text(json.dumps({"records": {"3": {"status": "never_listed", "reason": "absent_from_products"}}}))
    msha = hashlib.sha256(m.read_bytes()).hexdigest()
    r = tmp_path / "results.json"
    r.write_text(json.dumps(results_doc({}, msha)))
    rsha = hashlib.sha256(r.read_bytes()).hexdigest()
    args = ["--map", str(m), "--map-sha256", msha, "--results", str(r), "--results-sha256", rsha,
            "--output-dir", str(tmp_path / "out")]
    summary = builder.main(args)
    assert summary["status"] == {"never_listed": 1}
    assert summary["listings_sha256"] == hashlib.sha256((tmp_path / "out" / "listings.json").read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        builder.main(args)
    with pytest.raises(SystemExit):
        builder.main(args[:3] + ["0" * 64] + args[4:])
