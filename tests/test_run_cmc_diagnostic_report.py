import json
from datetime import datetime, timedelta, timezone

from scripts.research.run_cmc_diagnostic_report import run


def save(path, time, coin):
    quote = {"payload": {"bid": "100", "ask": "101"},
             "request_started_utc": time.isoformat(), "received_utc": time.isoformat()}
    row = {"type": "listing", "cmc_id": coin, "identity_eligible": True, "coinbase_product": "X-USD", "coinbase": quote}
    data = {"schema_version": 3, "artifact_type": "research_only_forward_log_v3",
            "places_orders": False, "snapshot_utc": time.isoformat(),
            "trending_status": "OBSERVED", "source_errors": [],
            "trending_hidden_boost": [row], "tracked_coinbase": [], "majors_coinbase": {"BTC": quote}}
    path.write_text(json.dumps(data))


def test_startup_is_uncertain_and_original_unchanged(tmp_path):
    time = datetime(2026, 10, 9, tzinfo=timezone.utc)
    path = tmp_path/"one.json"; save(path, time, 42); before = path.read_bytes()
    result = run(tmp_path, time+timedelta(hours=1))
    assert result["status_counts"] == {"HISTORY_UNCERTAIN": 1}
    assert result["scoring_authorized"] is False
    assert path.read_bytes() == before
    assert result["book_status_counts"] == {"MISSING_BOOK_CAPTURE": 1}


def test_book_diagnostics_visible_without_scoring_or_input_mutation(tmp_path):
    time = datetime(2026, 10, 9, tzinfo=timezone.utc)
    path = tmp_path/"one.json"; save(path, time, 42)
    data = json.loads(path.read_text())
    data["coinbase_level1_books"] = {"BTC-USD": {
        "product_id": "BTC-USD", "request_url": "https://api.exchange.coinbase.com/products/BTC-USD/book?level=1",
        "response": {"response_sha256": "a"*64, "request_started_utc": time.isoformat(),
                     "received_utc": time.isoformat(), "payload": {"auction_mode": False,
                     "bids": [["100", "2", 1]], "asks": [["101", ".01", 1]]}}}}
    path.write_text(json.dumps(data)); original = path.read_bytes()
    report = run(tmp_path, time)
    assert report["book_status_counts"] == {"STRUCTURALLY_VALID": 1, "MISSING_PRODUCT_BOOK": 1}
    btc = next(row for row in report["book_capacity_diagnostics"] if row["product_id"] == "BTC-USD")
    assert btc["displayed_size_covers_buy"] is False
    assert btc["quote_notional_excluding_fees"] == "100"
    assert btc["scoring_authorized"] is False
    assert report["status_counts"] == {"HISTORY_UNCERTAIN": 1}
    assert path.read_bytes() == original


def test_malformed_book_container_does_not_abort_report(tmp_path):
    time = datetime(2026, 10, 9, tzinfo=timezone.utc)
    path = tmp_path/"one.json"; save(path, time, 42)
    data = json.loads(path.read_text()); data["coinbase_level1_books"] = []
    path.write_text(json.dumps(data))
    assert run(tmp_path, time)["book_status_counts"] == {"INVALID_BOOK_CONTAINER": 1}


def test_candidate_without_mature_endpoint_not_scored(tmp_path):
    time = datetime(2026, 11, 9, tzinfo=timezone.utc)
    for n in range(1,31): save(tmp_path/f"prior{n}.json", time-timedelta(days=n), 7)
    save(tmp_path/"event.json", time, 42)
    result = run(tmp_path, time+timedelta(hours=1))
    assert result["status_counts"]["NOT_READY_90_DAYS"] == 3
    assert all("net_return" not in item for item in result["outcomes"])


def test_old_schema_recorded_not_modified(tmp_path):
    path = tmp_path/"old.json"; path.write_text('{"schema_version": 2}')
    result = run(tmp_path, datetime(2026, 10, 9, tzinfo=timezone.utc))
    assert len(result["rejected_envelopes"]) == 1
    assert result["outcomes"] == []


def test_failed_early_capture_does_not_start_collection_clock(tmp_path):
    time = datetime(2026, 11, 9, tzinfo=timezone.utc)
    early = tmp_path/"failed.json"
    save(early, time-timedelta(days=120), 7)
    data = json.loads(early.read_text())
    data["source_errors"] = ["list fetch failed"]
    early.write_text(json.dumps(data))
    for n in range(1, 31):
        save(tmp_path/f"prior{n}.json", time-timedelta(days=n), 7)
    save(tmp_path/"event.json", time, 42)
    result = run(tmp_path, time+timedelta(days=7, hours=12))
    assert result["qualified_collection_start_utc"] == time-timedelta(days=30)
    assert result["status_counts"]["NOT_READY_90_DAYS"] == 3
    assert result["statistics"]["status"] == "NOT_READY_90_DAYS"
    assert all("net_return" not in item for item in result["outcomes"])


def test_malformed_tracked_row_counted_without_abort(tmp_path):
    time = datetime(2026, 11, 9, tzinfo=timezone.utc)
    for n in range(1,31): save(tmp_path/f"prior{n}.json", time-timedelta(days=n), 7)
    path = tmp_path/"event.json"; save(path, time, 42)
    data = json.loads(path.read_text()); data["tracked_coinbase"] = [None]
    path.write_text(json.dumps(data))
    result = run(tmp_path, time+timedelta(days=91))
    assert result["malformed_tracked_rows"] == 1
    assert result["status_counts"]["MISSING"] == 3
