import http.client
import io
import json
from pathlib import Path
import ssl
import subprocess
import sys
from types import SimpleNamespace

import pytest

from services.alerts import group_a_alert_entrypoints as entrypoints, group_a_slack as slack
from services.alerts.group_a_watch import HostObservation, assess_group_a_watch
from services.alerts.group_a_watch_cycle import QueueEventEvidence, WatchCycleResult
from services.control.group_a_systemd_policy import render_group_a_policy


URL = "https://hooks.slack.com/services/Tsynthetic/Bsynthetic/Synthetic-placeholder"
CFG = {"alerts": {"enabled": True, "slack_webhook_url": URL}}
PAYLOAD = {"scope": "cbp-group-a-frozen42.target", "condition": "disk_high"}
ACCEPTED = {"ok": True, "channels": [{"channel": "slack", "ok": True, "status": 200}]}


def _send(cfg=CFG, payload=PAYLOAD):
    return slack.send_group_a_slack(cfg=cfg, payload=payload, level="error", message=slack._MESSAGE)


@pytest.mark.parametrize("suffix", ["?x=1", "#tag", "\n", "/extra"])
def test_wrong_webhook_never_starts_worker(monkeypatch, suffix):
    monkeypatch.setattr(slack.subprocess, "run", lambda *a, **kw: pytest.fail("started worker"))
    for url in (URL + suffix, URL.replace("hooks.slack.com", "hooks.slack.com.invalid"),
                URL.replace("https://", "http://"), URL.replace("hooks.slack.com", "user@hooks.slack.com")):
        assert _send({"alerts": {"enabled": True, "slack_webhook_url": url}})["reason"] == "slack_input_invalid"
    assert _send({"alerts": {"enabled": "true", "slack_webhook_url": URL}})["skipped"]
    assert not _send(payload={**PAYLOAD, "first_observed_ms": True})["ok"]


def test_parent_launch_does_not_export_secret_and_reports_only_fixed_ack(monkeypatch):
    def run(argv, **kwargs):
        assert URL not in repr(argv) and Path(argv[-1]).name == "group_a_slack.py"
        assert kwargs["env"] == {} and kwargs["stderr"] == subprocess.DEVNULL
        assert kwargs["timeout"] == 8 and json.loads(kwargs["input"]) == [URL, PAYLOAD]
        return SimpleNamespace(returncode=0, stdout=b"200\n")

    monkeypatch.setattr(slack.subprocess, "run", run)
    assert _send() == ACCEPTED


def test_real_isolated_child_rejects_invalid_request_without_echo():
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(Path(slack.__file__).resolve())],
        input=json.dumps(["https://invalid.example/services/synthetic/no/send", PAYLOAD]).encode(),
        capture_output=True, check=False, env={}, timeout=5,
    )
    assert (result.returncode, result.stdout, result.stderr) == (1, b"", b"")


@pytest.mark.parametrize("failure", ["timeout", "unavailable", "bad_ack", "nonzero"])
def test_uncertain_worker_does_not_retry_or_expose_error(monkeypatch, failure):
    calls = []

    def run(argv, **kwargs):
        calls.append(1)
        if failure == "timeout":
            raise subprocess.TimeoutExpired(argv, 8, output=URL.encode())
        if failure == "unavailable":
            raise OSError(URL)
        return SimpleNamespace(returncode=int(failure == "nonzero"),
                               stdout=b"200\n" if failure == "nonzero" else URL.encode())

    monkeypatch.setattr(slack.subprocess, "run", run)
    result = _send()
    assert not result["ok"] and calls == [1] and URL not in repr(result)


@pytest.mark.parametrize("status,headers,body,expected", [
    (200, b"Content-Length: 2\r\n", b"ok", True),
    (200, b"Content-Length: 3\r\n", b"ok\n", True),
    (302, b"Content-Length: 2\r\n", b"ok", False),
    (429, b"Content-Length: 2\r\n", b"ok", False),
    (200, b"Content-Length: 2\r\n", b"no", False),
    (200, b"Content-Length: 5\r\n", b"ok", False),
    (200, b"Content-Length: 3\r\n", b"ok", False),
    (200, b"Content-Length: 2\r\nContent-Length: 5\r\n", b"ok", False),
    (200, b"", b"ok", False),
    (200, b"Transfer-Encoding: chunked\r\n", b"2\r\nok\r\n0\r\n", False),
])
def test_worker_uses_one_verified_tls_post_and_never_follows_response(monkeypatch, status, headers, body, expected):
    calls = []

    class Socket:
        def makefile(self, mode):
            assert mode == "rb"
            return io.BytesIO(f"HTTP/1.1 {status} Synthetic\r\n".encode() + headers + b"\r\n" + body)

    class Connection:
        def __init__(self, host, *, timeout, context):
            assert host == "hooks.slack.com" and timeout == 5
            assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED

        def request(self, method, path, **kwargs):
            assert method == "POST" and path == URL.removeprefix("https://hooks.slack.com")
            assert URL not in json.loads(kwargs["body"])["text"]
            calls.append("post")

        def getresponse(self):
            response = http.client.HTTPResponse(Socket())
            response.begin()
            return response

        def close(self):
            calls.append("closed")

    monkeypatch.setattr(slack.http.client, "HTTPSConnection", Connection)
    assert slack._post(URL, PAYLOAD) is expected
    assert calls == ["post", "closed"]


def test_exact_terminal_instance_and_tracked_watcher_share_sender(tmp_path, monkeypatch):
    sent = []

    def sender(**kwargs):
        sent.append(kwargs["payload"])
        return ACCEPTED

    monkeypatch.setattr(entrypoints, "send_group_a_slack", sender)
    release = "frozen42"
    unit = render_group_a_policy(release).services[0]
    with pytest.raises(ValueError, match="unknown_group_a_failure_instance"):
        entrypoints.deliver_terminal_alert(release, unit, cfg=CFG)
    assert entrypoints.deliver_terminal_alert(release, unit.removesuffix(".service"), cfg=CFG) == "slack_accepted"
    cursor = tmp_path.resolve() / "group_a_delivery.sqlite"
    report = assess_group_a_watch(release, accounts={}, host=HostObservation(disk_pct=81))
    with pytest.raises(ValueError, match="tracked_group_a_observation_required"):
        entrypoints.deliver_watcher_alert(release, cursor, WatchCycleResult(report, ()), cfg=CFG)
    assert not cursor.exists()
    obs = WatchCycleResult(report, (), QueueEventEvidence(0, 42, ()))
    assert entrypoints.deliver_watcher_alert(release, cursor, obs, cfg=CFG).outcome == "slack_accepted"
    assert sent == [{"scope": unit, "condition": "terminal_service_failure"}, {**PAYLOAD, "first_observed_ms": 42}]
