"""Group A Slack-only transport. Importing this module has no side effects."""

import http.client
import json
from pathlib import Path
import re
import ssl
import subprocess
import sys


_HOST = "hooks.slack.com"
_URL = re.compile(r"https://hooks\.slack\.com(/services/[A-Za-z0-9_-]{1,128}/[A-Za-z0-9_-]{1,128}/[A-Za-z0-9_-]{1,128})")
_TOKEN = re.compile(r"[a-z0-9_.-]{1,140}")
_INPUT_CAP = 1024
_WORKER_TIMEOUT_SEC = 8
_SOCKET_TIMEOUT_SEC = 5
_MESSAGE = "CryptKeep Group A paper alert"


def _webhook_path(value):
    if type(value) is str and len(value) <= 420:
        match = _URL.fullmatch(value)
        if match is not None:
            return match[1]
    return None


def _valid_payload(payload):
    if (type(payload) is not dict or not 2 <= len(payload) <= 3
            or any(type(key) is not str or key not in ("scope", "condition", "first_observed_ms")
                   for key in payload)):
        return False
    for key in ("scope", "condition"):
        value = payload.get(key)
        if type(value) is not str or len(value) > 140 or _TOKEN.fullmatch(value) is None:
            return False
    if "first_observed_ms" in payload:
        value = payload["first_observed_ms"]
        if type(value) is not int or not 0 < value <= 253_402_300_799_999:
            return False
    return True


def send_group_a_slack(*, cfg, level, message, payload):
    """Send at most one POST, with a worker timeout and no secondary channel.

    A timeout is ambiguous: Slack may already have accepted the POST. This
    adapter does not retry. The supervisor must separately bound process
    creation/cleanup and supply a protected runtime and trusted configuration.
    """
    alerts = cfg.get("alerts") if type(cfg) is dict else None
    if type(alerts) is not dict or alerts.get("enabled") is not True:
        return {"ok": False, "skipped": True, "reason": "alerts_disabled"}
    webhook = alerts.get("slack_webhook_url")
    if (_webhook_path(webhook) is None or type(level) is not str or level != "error"
            or type(message) is not str or message != _MESSAGE or not _valid_payload(payload)):
        return {"ok": False, "reason": "slack_input_invalid"}
    if type(alerts.get("min_level", "error")) is not str or alerts.get("min_level", "error") not in (
        "info", "warn", "warning", "error",
    ):
        return {"ok": False, "reason": "slack_input_invalid"}
    data = json.dumps([webhook, payload], ensure_ascii=True, separators=(",", ":")).encode("ascii")
    if len(data) > _INPUT_CAP:
        return {"ok": False, "reason": "slack_input_invalid"}
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(Path(__file__).resolve())], input=data,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env={}, check=False,
            timeout=_WORKER_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "slack_timeout_unconfirmed"}
    except (OSError, ValueError):
        return {"ok": False, "reason": "slack_worker_unavailable"}
    if result.returncode == 0 and result.stdout == b"200\n":
        return {"ok": True, "channels": [{"channel": "slack", "ok": True, "status": 200}]}
    return {"ok": False, "reason": "slack_unconfirmed"}


def _post(webhook, payload):
    path = _webhook_path(webhook)
    if path is None or not _valid_payload(payload):
        return False
    text = "[ERROR] " + _MESSAGE + "\n" + json.dumps(payload, ensure_ascii=True, sort_keys=True)
    body = json.dumps({"text": text}, ensure_ascii=True).encode("ascii")
    # HTTPSConnection handles one literal host and never follows redirects.
    connection = http.client.HTTPSConnection(_HOST, timeout=_SOCKET_TIMEOUT_SEC,
                                             context=ssl.create_default_context())
    try:
        connection.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        with connection.getresponse() as response:
            return accepted_response(response)
    finally:
        connection.close()


def accepted_response(response):
    if response.status != 200 or response.headers.get_all("Transfer-Encoding"):
        return False
    # A prefix at EOF is not a complete acknowledgement.
    lengths = response.headers.get_all("Content-Length")
    if lengths == ["2"]:
        return response.read(2) == b"ok"
    if lengths == ["3"]:
        return response.read(3) == b"ok\n"
    return False


def _worker():
    try:
        data = sys.stdin.buffer.read(_INPUT_CAP + 1)
        if len(data) <= _INPUT_CAP:
            value = json.loads(data)
            if type(value) is list and len(value) == 2 and _post(*value):
                sys.stdout.write("200\n")
                return 0
    except Exception:
        # Neither the request nor upstream error text belongs in an alert log.
        pass
    return 1


if __name__ == "__main__":
    sys.exit(_worker())
