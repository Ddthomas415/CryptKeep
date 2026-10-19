import io
import urllib.error

import pytest

from dashboard.services.views import _shared_http as client


def test_missing_token_does_not_transmit(monkeypatch):
    monkeypatch.setattr(client, "PHASE1_SERVICE_TOKEN", "")
    monkeypatch.setattr(client.urllib.request, "build_opener", lambda *args: pytest.fail("transmitted"))
    assert client._request_envelope_from_base(client.PHASE1_ORCHESTRATOR_URL, "/v1/explain") is None


def test_authenticated_request_has_bounded_timeout_and_no_redirect(monkeypatch):
    monkeypatch.setattr(client, "PHASE1_SERVICE_TOKEN", "fixture")
    monkeypatch.setenv("CK_PHASE1_API_TIMEOUT_SECONDS", "45")

    class Opener:
        def open(self, request, timeout):
            assert request.get_header("Authorization") == "Bearer fixture"
            assert timeout == 45
            return io.BytesIO(b'{"ok": true}')

    def build(*handlers):
        proxy = [h for h in handlers if isinstance(h, client.urllib.request.ProxyHandler)]
        assert len(proxy) == 1 and proxy[0].proxies == {}
        redirect = [h for h in handlers if isinstance(h, client._NoCompanionRedirect)]
        assert redirect[0].redirect_request(None, None, 302, "", {}, "https://other.test") is None
        return Opener()

    monkeypatch.setattr(client.urllib.request, "build_opener", build)
    assert client._request_envelope_from_base(client.PHASE1_ORCHESTRATOR_URL, "/v1/explain") == {"ok": True}


@pytest.mark.parametrize("value", ["bad", "nan", "inf", "0", "-1", "91"])
def test_invalid_timeout_is_safe(monkeypatch, value):
    monkeypatch.setenv("CK_PHASE1_API_TIMEOUT_SECONDS", value)
    assert client._companion_timeout() == 30


def test_redirect_failure_returns_unavailable(monkeypatch):
    monkeypatch.setattr(client, "PHASE1_SERVICE_TOKEN", "fixture")

    class Opener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(request.full_url, 302, "redirect refused", {}, None)

    monkeypatch.setattr(client.urllib.request, "build_opener", lambda *args: Opener())
    assert client._request_envelope_from_base(client.PHASE1_ORCHESTRATOR_URL, "/v1/explain") is None


def test_environment_proxy_never_receives_companion_bearer(monkeypatch):
    import http.server, json, threading
    seen = []

    class Capture(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            seen.append((self.server.role, self.headers.get("Authorization")))
            body = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    servers = {}
    for role in ("orchestrator", "proxy"):
        server = http.server.HTTPServer(("127.0.0.1", 0), Capture)
        server.role = role
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers[role] = server
    try:
        base = f"http://127.0.0.1:{servers['orchestrator'].server_port}"
        for name in ("no_proxy", "NO_PROXY"):
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setenv("http_proxy", f"http://127.0.0.1:{servers['proxy'].server_port}")
        monkeypatch.setattr(client, "PHASE1_ORCHESTRATOR_URL", base)
        monkeypatch.setattr(client, "PHASE1_SERVICE_TOKEN", "fixture")
        assert client._request_envelope_from_base(base, "/v1/explain", method="POST", payload={"asset": "BTC"}) == {"ok": True}
        assert seen == [("orchestrator", "Bearer fixture")]
    finally:
        for server in servers.values():
            server.shutdown()
            server.server_close()
