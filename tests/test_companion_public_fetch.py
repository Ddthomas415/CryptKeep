import asyncio
import importlib.util
import socket
from pathlib import Path

import httpx
import pytest
import yaml


class ByteStream(httpx.AsyncByteStream):
    def __init__(self, content):
        self.content = content

    async def __aiter__(self):
        yield self.content


@pytest.fixture
def fetcher():
    path = Path(__file__).parents[1] / "phase1_research_copilot/shared/public_fetch.py"
    spec = importlib.util.spec_from_file_location("fetch_proof", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("url", ["file:///etc/passwd", "http://user:pass@example.org", "http://example.org:8080", "https://127.0.0.1", "http://169.254.169.254", "http://[::1]"])
def test_unsafe_destinations(fetcher, monkeypatch, url):
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, *a, **k: [(0, 0, 0, "", (host if host != "example.org" else "127.0.0.1", 80))])
    with pytest.raises(ValueError):
        asyncio.run(fetcher._destination(url))


def install_transport(fetcher, monkeypatch, handler):
    real_client = httpx.AsyncClient
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(0, 0, 0, "", ("93.184.216.34", 443))])
    monkeypatch.setattr(fetcher.httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))


def test_pins_dns_and_preserves_tls_host(fetcher, monkeypatch):
    def handler(req):
        assert req.url.host == "93.184.216.34"
        assert req.headers["host"] == "example.org"
        assert req.extensions["sni_hostname"] == "example.org"
        assert req.headers["accept-encoding"] == "identity"
        return httpx.Response(200, stream=ByteStream(b"fixture"))
    install_transport(fetcher, monkeypatch, handler)
    assert asyncio.run(fetcher.fetch_public_text("https://example.org")) == "fixture"


def test_mixed_dns_is_rejected(fetcher, monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(0, 0, 0, "", (ip, 443)) for ip in ("93.184.216.34", "10.0.0.1")])
    with pytest.raises(ValueError, match="non_public"):
        asyncio.run(fetcher._destination("https://example.org"))


@pytest.mark.parametrize("location", ["http://example.org", "https://user:pass@example.org", "https://example.org:9000"])
def test_redirect_checked(fetcher, monkeypatch, location):
    install_transport(fetcher, monkeypatch, lambda req: httpx.Response(302, headers={"location": location}))
    with pytest.raises(ValueError):
        asyncio.run(fetcher.fetch_public_text("https://example.org"))


def test_body_and_redirect_budgets(fetcher, monkeypatch):
    install_transport(fetcher, monkeypatch, lambda req: httpx.Response(200, stream=ByteStream(b"12345")))
    with pytest.raises(ValueError, match="too_large"):
        asyncio.run(fetcher.fetch_public_text("https://example.org", max_bytes=4))


def test_compressed_response_refused_before_read(fetcher, monkeypatch):
    install_transport(fetcher, monkeypatch, lambda req: httpx.Response(200, headers={"content-encoding": "gzip"}, stream=ByteStream(b"not-read")))
    with pytest.raises(ValueError, match="compressed_public_response_refused"):
        asyncio.run(fetcher.fetch_public_text("https://example.org"))


def test_password_is_encoded_for_database(monkeypatch):
    import sys
    monkeypatch.syspath_prepend(str(Path(__file__).parents[1] / "phase1_research_copilot"))
    from shared.config import Settings
    from urllib.parse import urlsplit, unquote
    settings = Settings(_env_file=None, postgres_password="reserved@:/ password")
    assert unquote(urlsplit(settings.database_url).password) == "reserved@:/ password"
    assert urlsplit(settings.database_url).hostname == "timescaledb"


def test_local_deployment_boundaries():
    root = Path(__file__).parents[1] / "phase1_research_copilot"
    compose = yaml.safe_load((root / "docker-compose.yml").read_text())
    for service in compose["services"].values():
        assert all(port.startswith("127.0.0.1:") for port in service.get("ports", []))
    for name in ("gateway", "orchestrator"):
        assert "../:/repo:ro" in compose["services"][name]["volumes"]
        source = (root / name / "main.py").read_text()
        assert "except ModuleNotFoundError" not in source
    assert "${POSTGRES_PASSWORD:?" in compose["services"]["timescaledb"]["environment"]["POSTGRES_PASSWORD"]
