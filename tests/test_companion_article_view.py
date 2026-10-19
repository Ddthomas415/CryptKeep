import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "phase1_research_copilot"))
from memory_retrieval.article_view import read_archive, check_source_rows, fetch_from_view


def archive(tmp_path, change=None):
    original = [{"id": 1, "content_hash": "old-hash", "source_type": "news", "source": "fixture",
                 "url": "https://example.test/story", "title": "Bitcoin", "content_text": "old page",
                 "timeline_tag": "present", "asset_tags": ["BTC"], "confidence": 0.5,
                 "published_at": None, "fetched_at": "2026-01-01 00:00:00+00:00", "raw_object_key": "raw/1"}]
    derived = deepcopy(original)
    derived[0].update(content_text="article body", metadata={"original_document_id": 1,
        "original_content_hash": "old-hash", "extraction_version": "article_body_v1",
        "article_body_boundary_verified": True, "extraction_method": "observed_article_body_v1"})
    if change:
        change(derived)
    hashes = {}
    for name, rows in [("original_snapshot.json", original), ("derived_article_body_v1.json", derived)]:
        raw = json.dumps(rows).encode()
        (tmp_path / name).write_bytes(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    (tmp_path / "manifest.json").write_text(json.dumps({"file_sha256": hashes}))
    return original


def test_versioned_view_preserves_lineage_and_parameterization(tmp_path):
    source = archive(tmp_path)
    view = read_archive(tmp_path, required=True)
    check_source_rows(view, source)
    class DB:
        def fetch_all(self, sql, params):
            assert "public.documents" in sql and "UNION ALL" in sql
            assert "r.body_verified" in sql and "article_body_boundary_verified" in sql
            assert "fixture question" not in sql
            assert params[1:] == ("fixture question",)
            assert "lineage_ok" in sql and "source_valid" in sql
            return [{"source_valid": True, "rows": []}]
    assert fetch_from_view(DB(), view, "SELECT * FROM documents WHERE title=%s", ("fixture question",)) == []


@pytest.mark.parametrize("change", [
    lambda rows: rows[0].update(fetched_at="2026-02-01 00:00:00+00:00"),
    lambda rows: rows[0].update(url="https://different.test"),
    lambda rows: rows.append(deepcopy(rows[0])),
    lambda rows: rows[0]["metadata"].update(original_content_hash="wrong"),
])
def test_archive_rejects_changed_time_source_duplicates_or_lineage(tmp_path, change):
    archive(tmp_path, change)
    with pytest.raises((ValueError, KeyError)):
        read_archive(tmp_path, required=True)


def test_hash_corruption_and_missing_required_archive_fail_closed(tmp_path):
    archive(tmp_path)
    (tmp_path / "derived_article_body_v1.json").write_text("[]")
    with pytest.raises(ValueError, match="hash"):
        read_archive(tmp_path)
    with pytest.raises(ValueError, match="required_archive_missing"):
        read_archive(tmp_path / "absent", required=True)
    assert read_archive(tmp_path / "absent") is None


def test_live_source_drift_fails_closed_but_equivalent_timezones_pass(tmp_path):
    source = archive(tmp_path)
    view = read_archive(tmp_path)
    equivalent = deepcopy(source)
    equivalent[0]["fetched_at"] = "2025-12-31 19:00:00-05:00"
    check_source_rows(view, equivalent)
    equivalent[0]["content_hash"] = "changed"
    with pytest.raises(ValueError):
        check_source_rows(view, equivalent)
    with pytest.raises(ValueError):
        check_source_rows(view, [])


def test_unknown_body_retained_as_diagnostic_not_verified_primary(tmp_path):
    archive(tmp_path, lambda rows: rows[0]["metadata"].update(
        article_body_boundary_verified=False, extraction_method="whole_page_fallback_unverified"))
    view = read_archive(tmp_path)
    assert view["rows"][0]["body_verified"] is False
    assert view["diagnostics"][0]["document_id"] == 1


def test_coordinated_body_and_manifest_change_is_rejected_by_pin(tmp_path):
    archive(tmp_path)
    pin = hashlib.sha256((tmp_path / "manifest.json").read_bytes()).hexdigest()
    rows = json.loads((tmp_path / "derived_article_body_v1.json").read_text())
    rows[0]["content_text"] = "Invented headline body"
    data = json.dumps(rows).encode()
    (tmp_path / "derived_article_body_v1.json").write_bytes(data)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    manifest["file_sha256"]["derived_article_body_v1.json"] = hashlib.sha256(data).hexdigest()
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="unapproved_archive_manifest"):
        read_archive(tmp_path, required=True, expected_manifest_sha256=pin)


def test_intervening_source_drift_is_rejected_even_with_empty_query(tmp_path):
    source = archive(tmp_path)
    view = read_archive(tmp_path)
    check_source_rows(view, source)
    class DriftDB:
        def fetch_all(self, sql, params):
            assert "p.fetched_at=r.fetched_at" in sql
            return [{"source_valid": False, "rows": []}]
    with pytest.raises(ValueError, match="live_source_lineage_changed"):
        fetch_from_view(DriftDB(), view, "SELECT * FROM documents WHERE false", ())


def test_manual_news_lineage_is_not_downgraded():
    from memory_retrieval.article_view import CTE
    assert "COALESCE(p.metadata->>'ingested_by', '') <> 'news-ingestion'" in CTE
