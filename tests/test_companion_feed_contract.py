"""Real offline feed/HTML parsing; no HTTP, persistence or semantic-quality claim."""
import ast
import asyncio
import hashlib
import re
import runpy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_companion_news_recovery import recovered


@pytest.mark.parametrize("date_tag,publication", [("pubDate", True), ("updated", False)])
@pytest.mark.parametrize("sentence,timeline", [("Bitcoin was volatile", "past"),
                                              ("Bitcoin will change", "future")])
def test_real_feed_html_and_document_contract(date_tag, publication, sentence, timeline):
    feedparser = pytest.importorskip("feedparser")
    bs4 = pytest.importorskip("bs4")
    root = Path(__file__).resolve().parents[1] / "research/companion_recovery"
    tree = ast.parse((root / "parser_normalizer.py").read_text())
    names = {"_extract_text_and_title", "_infer_timeline", "_extract_assets",
             "_confidence", "_hash_content", "_build_doc"}
    constants = {"ASSET_PATTERNS", "PAST_HINTS", "FUTURE_HINTS"}
    nodes = [n for n in tree.body if
             (isinstance(n, ast.FunctionDef) and n.name in names) or
             (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and
                 t.id in constants for t in n.targets)) or
             (isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                 and n.target.id in constants)]
    parser = dict(BeautifulSoup=bs4.BeautifulSoup, re=re, hashlib=hashlib,
                  datetime=datetime, timezone=timezone, Any=object)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "recovered-parser", "exec"), parser)
    model_ns = runpy.run_path(str(root / "models.py"))
    model = model_ns["NormalizedDocument"]
    model.model_rebuild(_types_namespace=model_ns)
    xml = f"""<rss version="2.0"><channel><title>Offline fixture</title>
      <item><title>Bitcoin event</title><link>https://example.org/event</link>
      <{date_tag}>Tue, 29 Sep 2026 08:00:00 -0400</{date_tag}>
      </item></channel></rss>"""
    feed = feedparser.parse(xml)
    assert not feed.bozo and len(feed.entries) == 1
    html = f"<html><title>Bitcoin event</title><body><p>{sentence}</p>" \
           "<script>Ethereum poison</script><style>Solana poison</style></body></html>"
    stored = []
    errors = []
    async def parse(**payload):
        updated = payload.pop("updated_at")
        payload.update(asset_hint=[], metadata={"ingested_by": "news-ingestion",
                                               "updated_at": updated})
        built = parser["_build_doc"](**payload, html=html,
                                      timeline_hint=payload.get("timeline_hint"))
        return {"document": model.model_validate(built).model_dump(mode="json")}
    async def store(doc):
        stored.append(doc)
        return {"ok": True}
    async def audit(*args, **kwargs):
        pass
    ns = recovered()
    ns.update(settings=SimpleNamespace(news_rss_list=["offline-fixture"]),
              feedparser=SimpleNamespace(parse=lambda _: feed),
              _parse_via_service=parse, _store_document=store,
              emit_audit_event=audit, _seen=set(),
              state=SimpleNamespace(errors=0, polls=0, ingested=0, skipped=0),
              logger=SimpleNamespace(error=lambda *args, **kwargs: errors.append((args, kwargs))))
    assert asyncio.run(ns["_poll_once"]())["poll_ingested"] == 1, errors
    doc = stored[0]
    assert doc["timeline_tag"] == timeline and doc["asset_tags"] == ["BTC"]
    assert "poison" not in doc["content_text"]
    if publication:
        assert datetime.fromisoformat(doc["published_at"]) == datetime(2026, 9, 29, 12, tzinfo=timezone.utc)
        assert doc["metadata"]["updated_at"] is None
    else:
        assert doc["published_at"] is None
        assert doc["metadata"]["updated_at"] == "2026-09-29T12:00:00+00:00"
    assert asyncio.run(ns["_poll_once"]())["poll_skipped"] == 1
    assert len(stored) == 1
