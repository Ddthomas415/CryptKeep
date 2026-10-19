"""Parsing and ASGI serialization proof; storage here remains in-memory."""
import asyncio

import pytest


def test_feed_parser_and_authenticated_boundary():
    pytest.importorskip("feedparser")
    pytest.importorskip("bs4")
    from tests.companion_pipeline_support import parsed_fixture, http_boundary
    from tests.test_companion_memory_recovery import harness, completed
    doc = parsed_fixture()
    assert doc.asset_tags == ["BTC"]
    assert doc.published_at is None
    assert doc.timeline_tag == "past"
    assert doc.metadata["updated_at"] == "2026-01-02T00:00:00Z"
    h = harness([completed()])
    request = http_boundary(h)
    denied = asyncio.run(request("/v1/memory/documents", doc.model_dump(mode="json"), "Bearer wrong"))
    assert denied.status_code == 401 and not h.rows
    response = asyncio.run(request("/v1/memory/documents", doc.model_dump(mode="json")))
    assert response.status_code == 200 and response.json()["ok"]
    stored = h.rows[doc.content_hash]
    assert stored["published_at"] is None
    assert stored["url"] == doc.url
    assert stored["content_text"] == doc.content_text
