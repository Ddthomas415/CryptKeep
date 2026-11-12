import http.client
import io
import json
import ssl

import pytest

from services.alerts import group_a_slack as legacy, group_a_summary_transport as transport
from services.alerts.group_a_summary_protocol import Health, bit_for


RELEASE = "frozen42"
URL = "https://hooks.slack.com/services/Tsynthetic/Bsynthetic/Offline-placeholder"
CFG = {"alerts": {"enabled": True, "slack_webhook_url": URL}}


@pytest.mark.parametrize("status,headers,body,accepted", [
    (200, b"Content-Length: 2\r\n", b"ok", True),
    (200, b"Content-Length: 3\r\n", b"ok\n", True),
    (200, b"Content-Length: 5\r\n", b"ok", False),
    (200, b"Content-Length: 3\r\n", b"ok", False),
    (200, b"Content-Length: 2\r\nContent-Length: 2\r\n", b"ok", False),
    (200, b"Transfer-Encoding: chunked\r\n", b"2\r\nok\r\n0\r\n", False),
    (302, b"Content-Length: 2\r\n", b"ok", False),
    (429, b"Content-Length: 2\r\n", b"ok", False),
])
def test_summary_is_one_direct_verified_post_without_worker(monkeypatch, status, headers, body, accepted):
    calls = []
    class Socket:
        def makefile(self, mode):
            return io.BytesIO(f"HTTP/1.1 {status} Synthetic\r\n".encode() + headers + b"\r\n" + body)
    class Connection:
        def __init__(self, host, *, timeout, context):
            assert host == "hooks.slack.com" and timeout == 5
            assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
        def request(self, method, path, **kwargs):
            assert method == "POST" and path == URL.removeprefix("https://hooks.slack.com")
            assert URL not in repr(json.loads(kwargs["body"]))
            calls.append("post")
        def getresponse(self):
            response = http.client.HTTPResponse(Socket())
            response.begin()
            return response
        def close(self):
            calls.append("close")
    monkeypatch.setattr(transport.http.client, "HTTPSConnection", Connection)
    monkeypatch.setattr(legacy.subprocess, "run", lambda *a, **kw: pytest.fail("nested worker"))
    health = Health().with_state(bit_for(RELEASE, "cursor_unavailable"), "present")
    assert transport.send_summary(RELEASE, 1, (), health, health.present, cfg=CFG, deadline=40, clock=lambda: 0) is accepted
    assert calls == ["post", "close"]


@pytest.mark.parametrize("deadline,url", [(0, URL), (41, URL), (float("nan"), URL), (40, URL + "?leak=1")])
def test_invalid_deadline_and_recipient_never_connect(monkeypatch, deadline, url):
    monkeypatch.setattr(transport.http.client, "HTTPSConnection", lambda *a, **kw: pytest.fail("connected"))
    assert not transport.send_summary(RELEASE, 1, (), Health(), 0, deadline=deadline, clock=lambda: 0,
                                      cfg={"alerts": {"enabled": True, "slack_webhook_url": url}})
