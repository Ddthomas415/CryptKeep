"""Offline tests for the first-candle check (fake Coinbase; synthetic map and selections)."""
import csv
from datetime import date
import hashlib
import json

import pytest

from scripts.research import fetch_coinbase_listing_dates as fetch
from scripts.research import verify_first_candles as v
from tests.test_coinbase_listing_fetch import FakeCoinbase, span

END = date(2026, 10, 19)
# XRP-like: traded 2019-02-25..2021-01-19, suspended, back from 2023-07-13
DAYS = {"X-USD": span("2019-02-25", "2021-01-19") | span("2023-07-13", "2026-10-19"),
        "NEW-USD": span("2024-09-04", "2026-10-19"),
        "OLD-USD": span("2020-09-01", "2026-10-19")}
RECORDS = {"52": {"status": "mapped", "products": [{"id": "X-USD"}]},
           "7": {"status": "mapped", "products": [{"id": "NEW-USD"}]},
           "9": {"status": "mapped", "products": [{"id": "OLD-USD"}]},
           "3": {"status": "never_listed"}}
CONTROL = [{"cmc_id": "52", "first_entry": "2019-01-13"}, {"cmc_id": "7", "first_entry": "2024-08-25"},
           {"cmc_id": "9", "first_entry": "2021-01-10"}, {"cmc_id": "3", "first_entry": "2019-01-13"}]


def fetched(tmp_path):
    """Run the real fetcher on the fake exchange to get a results.json like the saved one."""
    m = tmp_path / "map.json"
    m.write_text(json.dumps({"records": RECORDS}))
    p = tmp_path / "products.json"
    p.write_text(json.dumps([{"id": k, "status": "online"} for k in DAYS]))
    sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    fetch.main(["--map", str(m), "--map-sha256", sha(m), "--products", str(p), "--products-sha256", sha(p),
                "--output-dir", str(tmp_path / "candles")], get=FakeCoinbase(DAYS), sleep=lambda s: None, today=END)
    c = tmp_path / "control.csv"
    with open(c, "w", newline="") as stream:
        w = csv.DictWriter(stream, fieldnames=["cmc_id", "first_entry"])
        w.writeheader()
        w.writerows(CONTROL)
    r = tmp_path / "candles" / "results.json"
    return ["--map", str(m), "--map-sha256", sha(m), "--results", str(r), "--results-sha256", sha(r),
            "--control-ids", str(c), "--control-ids-sha256", sha(c)]


def test_binary_search_misses_the_early_period_and_the_check_repairs_it(tmp_path):
    args = fetched(tmp_path)
    res = json.loads((tmp_path / "candles" / "results.json").read_text())
    assert res["products"]["X-USD"]["first"] == "2023-07-13"  # the documented limit, reproduced
    fake = FakeCoinbase(DAYS)
    s = v.main(args + ["--output-dir", str(tmp_path / "check")], get=fake, sleep=lambda x: None)
    assert s["first_moved_earlier"] == ["X-USD"] and s["errors"] == []
    out = json.loads((tmp_path / "check" / "results_verified.json").read_text())
    x = out["products"]["X-USD"]
    assert x["first"] == "2019-02-25" and x["first_check"]["found_first"] == "2023-07-13"
    assert x["first_check"]["empty_windows_after_verified_first"]  # the suspension shows as empty windows
    assert out["products"]["NEW-USD"]["first"] == "2024-09-04"  # checked, nothing earlier
    assert "first_check" not in out["products"]["OLD-USD"]  # listed before its first selection: not checked
    assert out["map_sha256"] == res["map_sha256"] and out["schema"] == res["schema"]
    assert {u.split("/products/")[1].split("/")[0] for u in fake.urls} == {"X-USD", "NEW-USD"}


def test_check_stops_at_the_first_window_with_candles_and_logs_every_request(tmp_path):
    args = fetched(tmp_path)
    fake = FakeCoinbase(DAYS)
    v.main(args + ["--output-dir", str(tmp_path / "check")], get=fake, sleep=lambda x: None)
    lines = [json.loads(l) for l in (tmp_path / "check" / "requests.jsonl").read_text().splitlines()]
    assert len(lines) == len(fake.urls) and [l["n"] for l in lines] == list(range(1, len(lines) + 1))
    x_requests = [l for l in lines if l["product"] == "X-USD"]
    assert len(x_requests) == 1 and x_requests[0]["window"][0] == "2018-12-15"


def test_resume_cap_and_pins(tmp_path):
    args = fetched(tmp_path)
    s = v.main(args + ["--output-dir", str(tmp_path / "check"), "--max-requests", "1"],
               get=FakeCoinbase(DAYS), sleep=lambda x: None)
    assert s["stopped"] == "request_cap" and not (tmp_path / "check" / "results_verified.json").exists()
    s = v.main(args + ["--output-dir", str(tmp_path / "check")], get=FakeCoinbase(DAYS), sleep=lambda x: None)
    assert s["products_done"] == 2 and (tmp_path / "check" / "results_verified.json").exists()
    bad = list(args)
    bad[bad.index("--results-sha256") + 1] = "0" * 64
    with pytest.raises(SystemExit):
        v.main(bad + ["--output-dir", str(tmp_path / "c2")], get=FakeCoinbase(DAYS))


def test_verified_results_feed_the_listing_builder(tmp_path):
    from scripts.research import build_coinbase_listings as builder
    args = fetched(tmp_path)
    v.main(args + ["--output-dir", str(tmp_path / "check")], get=FakeCoinbase(DAYS), sleep=lambda x: None)
    doc = json.loads((tmp_path / "check" / "results_verified.json").read_text())
    rec = {k: dict(r, reason="x") for k, r in RECORDS.items()}
    listings, report = builder.build({"records": rec}, doc, doc["map_sha256"])
    assert listings["assets"]["52"]["first_candle"] == "2019-02-25"
