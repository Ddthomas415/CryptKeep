from __future__ import annotations

import json

import pytest

from services.events.platform_event_journal import (
    PlatformEventJournalError,
    append_platform_event,
    build_platform_event,
    load_platform_events,
    summarize_platform_events,
)


def test_platform_event_journal_appends_loads_and_summarizes(tmp_path):
    path = tmp_path / "platform_events.jsonl"

    event = append_platform_event(
        event_type="StrategySignalProduced",
        producer="paper_strategy_evidence_service",
        source="paper",
        strategy_id="es_daily_trend_v1",
        strategy_version="v1",
        config_hash="sha256:config",
        dataset_id="archive:coinbase:btc-usd:1d",
        evidence_artifact_id="evidence:abc",
        run_id="run-1",
        commit_sha="abc123",
        payload={"signal": "long", "api_token": "sensitive"},
        path=path,
    )

    assert event["path"] == str(path)
    assert event["schema_version"] == "platform_event_v1"
    assert event["payload"]["api_token"] == "<redacted>"

    rows = load_platform_events(path)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "StrategySignalProduced"
    assert rows[0]["provenance"]["strategy_id"] == "es_daily_trend_v1"

    summary = summarize_platform_events(path)
    assert summary["ok"] is True
    assert summary["event_count"] == 1
    assert summary["event_types"] == {"StrategySignalProduced": 1}
    assert summary["producers"] == {"paper_strategy_evidence_service": 1}
    assert summary["latest"]["event_id"] == rows[0]["event_id"]


def test_platform_event_journal_filters_by_event_type(tmp_path):
    path = tmp_path / "platform_events.jsonl"
    append_platform_event(event_type="CampaignStarted", producer="test", path=path)
    append_platform_event(event_type="CampaignEnded", producer="test", path=path)

    rows = load_platform_events(path, event_type="CampaignEnded")

    assert len(rows) == 1
    assert rows[0]["event_type"] == "CampaignEnded"


def test_platform_event_journal_rejects_unknown_event_type():
    with pytest.raises(PlatformEventJournalError, match="unsupported_event_type:UnknownEvent"):
        build_platform_event(event_type="UnknownEvent", producer="test")


def test_platform_event_journal_rejects_missing_producer():
    with pytest.raises(PlatformEventJournalError, match="missing_required_field:producer"):
        build_platform_event(event_type="CampaignStarted", producer="")


def test_platform_event_journal_corrupt_rows_fail_closed(tmp_path):
    path = tmp_path / "platform_events.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")

    report = summarize_platform_events(path)

    assert report["ok"] is False
    assert report["reason"].startswith("platform_event_read_failed:")


def test_platform_event_journal_require_events_marks_empty_as_not_ok(tmp_path):
    path = tmp_path / "platform_events.jsonl"

    report = summarize_platform_events(path, require_events=True)

    assert report["ok"] is False
    assert report["reason"] == "platform_event_journal_empty"


def test_platform_event_rows_are_valid_jsonl(tmp_path):
    path = tmp_path / "platform_events.jsonl"
    append_platform_event(event_type="RiskDecisionMade", producer="risk_gate", path=path)

    raw = path.read_text(encoding="utf-8").strip()

    decoded = json.loads(raw)
    assert decoded["event_type"] == "RiskDecisionMade"

