import json
from datetime import datetime, timezone

from scripts.research.report_cmc_readiness import report


def test_multiple_captures_do_not_inflate_days(tmp_path):
    data = {"schema_version": 3, "artifact_type": "research_only_forward_log_v3",
            "places_orders": False, "snapshot_utc": "2026-10-09T05:00:00Z",
            "trending_hidden_boost": [{"cmc_id": 42}], "tracked_coinbase": [],
            "majors_coinbase": {}, "trending_status": "OBSERVED", "source_errors": []}
    for name in ("a", "b"):
        (tmp_path/f"{name}.json").write_text(json.dumps(data))
    (tmp_path/"old.json").write_text(json.dumps({"schema_version": 2}))
    result = report(tmp_path, datetime(2026, 10, 9, 6, tzinfo=timezone.utc))
    assert result["v3_envelopes"] == 2
    assert len(result["observed_nonempty_list_utc_days"]) == 1
    assert len(result["excluded_envelopes"]) == 1
    assert result["minimum_90_days_reached"] is False
    assert result["scoring_authorized"] is False


def test_empty_collection_not_ready(tmp_path):
    result = report(tmp_path, datetime(2026, 10, 9, tzinfo=timezone.utc))
    assert result["elapsed_collection_days"] is None
    assert result["minimum_90_days_reached"] is False


def test_bad_timestamp_is_reported_not_abort(tmp_path):
    data = {"schema_version": 3, "artifact_type": "research_only_forward_log_v3",
            "places_orders": False, "snapshot_utc": 123}
    (tmp_path/"bad.json").write_text(json.dumps(data))
    result = report(tmp_path, datetime(2026, 10, 9, tzinfo=timezone.utc))
    assert result["v3_envelopes"] == 0
    assert len(result["excluded_envelopes"]) == 1
