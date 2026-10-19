"""Read-only, lineage-checked projection of a versioned article archive."""
import hashlib
import json
from datetime import datetime
from pathlib import Path


COLUMNS = "id, source_type, source, url, title, timeline_tag, asset_tags, confidence, published_at, fetched_at, content_text"
APPROVED_MANIFEST_SHA256 = "94af84ec1096fc2edfb3757bbb49ee264a0f27f519709398f1b942253e12ab77"
CTE = """WITH repair AS (
    SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(
        id bigint, source_type text, source text, url text, title text, timeline_tag text,
        asset_tags text[], confidence double precision, published_at timestamptz,
        fetched_at timestamptz, content_text text, raw_object_key text,
        original_content_hash text, body_verified boolean)
), lineage_ok AS (
    SELECT COUNT(*)=(SELECT COUNT(*) FROM repair) AS ok
    FROM repair r JOIN public.documents p ON p.id=r.id
      AND p.content_hash=r.original_content_hash AND p.source_type=r.source_type
      AND p.source=r.source AND p.url=r.url AND p.fetched_at=r.fetched_at
      AND p.published_at IS NOT DISTINCT FROM r.published_at
      AND p.raw_object_key IS NOT DISTINCT FROM r.raw_object_key
), documents AS (
    SELECT r.id, r.source_type, r.source, r.url, r.title, r.timeline_tag, r.asset_tags,
           r.confidence, r.published_at, r.fetched_at, r.content_text
    FROM repair r JOIN public.documents p ON p.id=r.id AND p.content_hash=r.original_content_hash
    WHERE r.body_verified AND r.fetched_at<=NOW()
      AND (r.published_at IS NULL OR r.published_at<=NOW())
    UNION ALL
    SELECT p.id, p.source_type, p.source, p.url, p.title, p.timeline_tag, p.asset_tags,
           p.confidence, p.published_at, p.fetched_at, p.content_text
    FROM public.documents p
    WHERE NOT EXISTS (SELECT 1 FROM repair r WHERE r.id=p.id)
      AND (p.source_type <> 'news' OR COALESCE(p.metadata->>'ingested_by', '') <> 'news-ingestion'
           OR p.metadata->>'article_body_boundary_verified'='true')
      AND p.fetched_at<=NOW() AND (p.published_at IS NULL OR p.published_at<=NOW())
) """


def read_archive(root: Path, *, required=False, expected_manifest_sha256=None):
    if not root.exists():
        if required:
            raise ValueError("required_archive_missing")
        return None
    def read(name):
        path = root / name
        if path.stat().st_size > 2_000_000:
            raise ValueError("archive_file_size_exceeded")
        with path.open("rb") as stream:
            data = stream.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError("archive_file_size_exceeded")
        return data
    manifest_bytes = read("manifest.json")
    if expected_manifest_sha256 and hashlib.sha256(manifest_bytes).hexdigest() != expected_manifest_sha256:
        raise ValueError("unapproved_archive_manifest")
    manifest = json.loads(manifest_bytes)
    files = {}
    for name in ("original_snapshot.json", "derived_article_body_v1.json"):
        data = read(name)
        if hashlib.sha256(data).hexdigest() != manifest["file_sha256"][name]:
            raise ValueError("archive_hash_mismatch")
        files[name] = json.loads(data)
    original, derived = files["original_snapshot.json"], files["derived_article_body_v1.json"]
    source = {row["id"]: row for row in original}
    if (not original or len(original) > 500 or len(source) != len(original)
            or len(derived) != len(original) or len({row["id"] for row in derived}) != len(derived)):
        raise ValueError("archive_identity_invalid")
    rows, diagnostics = [], []
    for row in derived:
        prior = source[row["id"]]
        meta = row["metadata"]
        if (meta.get("original_document_id") != row["id"]
                or meta.get("original_content_hash") != prior["content_hash"]
                or meta.get("extraction_version") != "article_body_v1"):
            raise ValueError("archive_lineage_invalid")
        for key in ("source_type", "source", "url", "published_at", "fetched_at", "raw_object_key"):
            if row[key] != prior[key]:
                raise ValueError("archive_source_or_time_changed")
        verified = (meta.get("article_body_boundary_verified") is True
                    and meta.get("extraction_method") == "observed_article_body_v1")
        item = {key: row[key] for key in COLUMNS.split(", ")}
        item.update(original_content_hash=prior["content_hash"], raw_object_key=prior["raw_object_key"],
                    body_verified=verified)
        rows.append(item)
        if not verified:
            diagnostics.append({"document_id": row["id"], "title": prior["title"],
                                "url": prior["url"], "status": "UNVERIFIED_ARTICLE_BOUNDARY"})
    return {"rows": rows, "original": source, "diagnostics": diagnostics,
            "sha256": manifest["file_sha256"]["derived_article_body_v1.json"]}


def check_source_rows(view, actual):
    expected = view["original"]
    if len(actual) != len(expected) or len({row["id"] for row in actual}) != len(actual):
        raise ValueError("live_source_set_changed")
    for row in actual:
        prior = expected[row["id"]]
        for key in ("content_hash", "url", "source", "source_type", "raw_object_key"):
            if row[key] != prior[key]:
                raise ValueError("live_source_lineage_changed")
        for key in ("published_at", "fetched_at"):
            # JSON export uses PostgreSQL datetime string representation.
            current = datetime.fromisoformat(str(row[key])) if row[key] is not None else None
            archived = datetime.fromisoformat(str(prior[key])) if prior[key] is not None else None
            if current != archived:
                raise ValueError("live_source_time_changed")


def fetch_from_view(db, view, sql, params):
    # One SQL statement validates the frozen lineage and retrieves its projection
    # from the same PostgreSQL snapshot, including when the result is empty.
    wrapped = CTE + ", requested AS (" + sql + ") SELECT (SELECT ok FROM lineage_ok) AS source_valid, "
    wrapped += "COALESCE((SELECT jsonb_agg(row_to_json(q)) FROM requested q), '[]'::jsonb) AS rows"
    result = db.fetch_all(wrapped, (json.dumps(view["rows"]),) + params)
    if len(result) != 1 or result[0].get("source_valid") is not True:
        raise ValueError("live_source_lineage_changed")
    return result[0]["rows"]
