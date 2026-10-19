"""Disposable integration adapters, not production service wiring."""
import ast
import hashlib
import importlib.util
import re
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


def parsed_fixture():
    import feedparser
    from bs4 import BeautifulSoup
    root = Path(__file__).parents[1] / "research/companion_recovery"
    source = root / "parser_normalizer.py"
    tree = ast.parse(source.read_text())
    functions = {"_extract_text_and_title", "_infer_timeline", "_extract_assets",
                 "_confidence", "_hash_content", "_build_doc"}
    constants = {"ASSET_PATTERNS", "FUTURE_HINTS", "PAST_HINTS"}
    nodes = [n for n in tree.body if
             (isinstance(n, ast.FunctionDef) and n.name in functions) or
             (isinstance(n, ast.AnnAssign) and getattr(n.target, "id", None) in constants) or
             (isinstance(n, ast.Assign) and any(getattr(t, "id", None) in constants for t in n.targets))]
    ns = dict(Any=object, BeautifulSoup=BeautifulSoup, re=re, hashlib=hashlib,
              datetime=datetime, timezone=timezone)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), ns)
    feed = feedparser.parse(b'<rss version="2.0"><channel><title>Fixture</title><item>'
                            b'<title>Original</title><link>https://example.org/original</link>'
                            b'</item></channel></rss>')
    assert not feed.bozo and len(feed.entries) == 1
    entry = feed.entries[0]
    doc = ns["_build_doc"](
        url=entry.link, source="example.org", source_type="news",
        html="<html><title>Original</title><body>Bitcoin was volatile.</body></html>",
        timeline_hint=None, asset_hint=[], published_at=None,
        metadata={"updated_at": "2026-01-02T00:00:00Z"})
    spec = importlib.util.spec_from_file_location("pipeline_models", root / "models.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.NormalizedDocument.model_rebuild(_types_namespace=vars(module))
    model = module.NormalizedDocument(**doc)
    # Object-store persistence is outside this proof; do not fake a raw-object receipt.
    model.raw_html = None
    return model


def http_boundary(h):
    import httpx
    from fastapi import FastAPI, Header, HTTPException
    from fastapi.encoders import jsonable_encoder
    app = FastAPI()
    h.ns["HTTPException"] = HTTPException

    @app.post("/v1/memory/documents")
    async def store(payload: dict, authorization: str = Header(default="")):
        doc = parsed_fixture().model_validate(payload)
        result = await h.ns["ingest_document"](doc, authorization)
        return jsonable_encoder(vars(result))

    @app.post("/v1/memory/retrieve")
    async def retrieve(payload: dict, authorization: str = Header(default="")):
        return jsonable_encoder(await h.ns["retrieve_context"](
            SimpleNamespace(**payload), authorization))

    async def request(path, payload, token="Bearer fixture-token"):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://disposable") as client:
            return await client.post(path, json=payload, headers={"Authorization": token})
    return request
