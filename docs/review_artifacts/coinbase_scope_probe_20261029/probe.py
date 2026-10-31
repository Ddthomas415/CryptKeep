"""One read-only scope observation; raw headers/responses never saved."""

import argparse
import base64
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
from time import monotonic
from uuid import UUID

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
ENDPOINTS = ("brokerage/key_permissions", "brokerage/portfolios")
URLS = tuple("https://api.coinbase.com/api/v3/" + path for path in ENDPOINTS)
BODY_LIMIT = 1048576
HEADER_NAMES = {"Authorization", "Content-Type", "CB-ACCESS-KEY", "CB-ACCESS-SIGN", "CB-ACCESS-TIMESTAMP"}


def strict_json(body):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    def finite(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("nonfinite_json")
        return result
    def refuse(value):
        raise ValueError("nonfinite_json")
    return json.loads(body, object_pairs_hook=unique, parse_float=finite, parse_constant=refuse)


def uuid_hash(value):
    if type(value) is not str:
        raise ValueError("portfolio_id_required")
    parsed = UUID(value)
    if parsed.int == 0:
        raise ValueError("nil_portfolio_id")
    return hashlib.sha256(str(parsed).encode()).hexdigest()


def permissions_summary(body):
    if type(body) is not dict or any(type(body.get(key)) is not bool for key in ("can_view", "can_trade", "can_transfer")):
        raise ValueError("permission_flags_unknown")
    kind = body.get("portfolio_type")
    return {key: body[key] for key in ("can_view", "can_trade", "can_transfer")} | {
        "portfolio_uuid_sha256": uuid_hash(body.get("portfolio_uuid")),
        "portfolio_type": kind if kind in ("DEFAULT", "CONSUMER", "INTX", "UNDEFINED") else "OTHER_OR_MISSING"}


def portfolios_summary(body, associated_hash):
    if type(body) is not dict or type(body.get("portfolios")) is not list:
        raise ValueError("portfolio_list_missing")
    rows = []
    for item in body["portfolios"]:
        if type(item) is not dict:
            raise ValueError("invalid_portfolio")
        kind = item.get("type")
        rows.append({"uuid_sha256": uuid_hash(item.get("uuid")),
                     "type": kind if kind in ("DEFAULT", "CONSUMER", "INTX", "UNDEFINED") else "OTHER_OR_MISSING",
                     "deleted": item.get("deleted") if type(item.get("deleted")) is bool else None})
    identities = {item["uuid_sha256"] for item in rows}
    return {"returned_portfolio_rows": len(rows), "unique_portfolio_count": len(identities),
            "associated_portfolio_returned": associated_hash in identities, "portfolios": rows,
            "list_exhaustiveness": "UNVERIFIED", "account_wide_coverage": "UNVERIFIED"}


def http_worker(request=None, session_factory=None):
    """Exactly one GET in an isolated process; stdout is a private parent pipe."""
    if request is None:
        data = sys.stdin.buffer.read(32769)
        if len(data) > 32768:
            raise ValueError("request_byte_budget_exceeded")
        request = strict_json(data)
    if (type(request) is not dict or set(request) != {"url", "headers", "timeout"}
            or request["url"] not in URLS or type(request["headers"]) is not dict
            or not request["headers"] or not set(request["headers"]) <= HEADER_NAMES
            or any(type(value) is not str or "\r" in value or "\n" in value for value in request["headers"].values())
            or type(request["timeout"]) not in (int, float) or not 0 < request["timeout"] <= 10):
        raise ValueError("fixed_metadata_request_required")
    headers = request["headers"]
    if not (headers.get("Authorization") or all(headers.get(key) for key in
            ("CB-ACCESS-KEY", "CB-ACCESS-SIGN", "CB-ACCESS-TIMESTAMP"))):
        raise ValueError("signed_headers_required")
    if session_factory is None:
        import requests
        session_factory = requests.Session
    with session_factory() as session:
        session.trust_env = False
        session.max_redirects = 0
        import requests
        session.mount("https://", requests.adapters.HTTPAdapter(max_retries=0))
        with session.get(request["url"], headers=request["headers"], timeout=request["timeout"],
                         allow_redirects=False, verify=True, stream=True) as response:
            chunks = []
            size = 0
            for chunk in response.iter_content(16384):
                size += len(chunk)
                if size > BODY_LIMIT:
                    raise ValueError("response_byte_budget_exceeded")
                chunks.append(chunk)
            return {"http_status": int(response.status_code), "body_bytes": size,
                    "body_base64": base64.b64encode(b"".join(chunks)).decode("ascii")}


def observe(loader=None, factory=None, run=None, clock=monotonic):
    result = {"status": "INCOMPLETE", "stage": "credentials", "observed_at": datetime.now(timezone.utc).isoformat(),
              "requests_attempted": 0, "receipts": [], "orders_submitted": False,
              "raw_responses_saved": False, "account_wide_coverage": "UNVERIFIED", "execution_authority": False}
    try:
        previous = None
        def now():
            nonlocal previous
            value = clock()
            if type(value) not in (int, float) or not math.isfinite(value) or (previous is not None and value < previous):
                raise ValueError("invalid_monotonic_clock")
            previous = value
            return value
        start = now()
        deadline = start + 30
        if loader is None:
            from services.security.credentials_loader import load_exchange_credentials
            loader = load_exchange_credentials
        if factory is None:
            from services.security.exchange_factory import make_exchange
            factory = make_exchange
        creds = loader("coinbase")
        result["credential_source"] = creds.get("source") if creds.get("source") in ("keyring", "env") else "other"
        if not creds.get("apiKey") or not creds.get("secret"):
            result["status"] = "MISSING_EXISTING_CREDENTIALS"
            return result
        result["stage"] = "client"
        client = factory("coinbase", creds, enable_rate_limit=False)
        if client.id != "coinbase" or client.urls.get("api") != {"rest": "https://api.coinbase.com"}:
            raise ValueError("unexpected_api_target")
        client.verbose = False
        client.logger = logging.Logger("private_scope_probe_suppressed")
        client.logger.disabled = True
        client.logger.propagate = False
        transport = subprocess.run if run is None else run
        for path, url in zip(ENDPOINTS, URLS):
            result["stage"] = path.rsplit("/", 1)[-1]
            signed = client.sign(path, ["v3", "private"], "GET", {})
            if signed.get("url") != url or signed.get("method") != "GET" or signed.get("body") not in (None, ""):
                raise ValueError("unexpected_signed_target")
            remaining = deadline - now()
            if not math.isfinite(remaining) or remaining <= 0:
                raise TimeoutError("collection_window_expired")
            timeout = min(10, remaining)
            payload = {"url": url, "headers": signed["headers"], "timeout": timeout}
            result["requests_attempted"] += 1
            receipt = {"endpoint": result["stage"], "started_at": datetime.now(timezone.utc).isoformat()}
            result["receipts"].append(receipt)
            completed = transport([sys.executable, "-B", str(Path(__file__).resolve()), "--http-worker"],
                                  input=json.dumps(payload).encode(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  timeout=timeout, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
            if completed.returncode != 0 or len(completed.stdout) > 1500000:
                raise RuntimeError("metadata_worker_failed")
            answer = strict_json(completed.stdout)
            if type(answer) is not dict:
                raise ValueError("invalid_worker_envelope")
            if answer.get("error_type"):
                result["worker_error_type"] = answer["error_type"] if answer["error_type"] in ("ValueError", "Timeout", "ConnectionError", "SSLError") else "WorkerError"
                raise RuntimeError("metadata_worker_failed")
            if (set(answer) != {"http_status", "body_bytes", "body_base64"}
                    or type(answer["http_status"]) is not int or not 100 <= answer["http_status"] <= 599
                    or type(answer["body_bytes"]) is not int or not 0 <= answer["body_bytes"] <= BODY_LIMIT
                    or type(answer["body_base64"]) is not str):
                raise ValueError("invalid_worker_envelope")
            receipt["http_status"] = answer["http_status"]
            receipt["body_bytes"] = answer["body_bytes"]
            if answer["http_status"] != 200:
                result["status"] = "READ_ONLY_REQUEST_REJECTED"
                return result
            body = base64.b64decode(answer["body_base64"], validate=True)
            if len(body) != answer["body_bytes"] or len(body) > BODY_LIMIT or now() >= deadline:
                raise ValueError("invalid_or_late_metadata_body")
            parsed = strict_json(body)
            if path == ENDPOINTS[0]:
                result["permissions"] = permissions_summary(parsed)
                if not result["permissions"]["can_view"]:
                    result["status"] = "VIEW_PERMISSION_NOT_GRANTED"
                    return result
            else:
                result["portfolio_observation"] = portfolios_summary(parsed, result["permissions"]["portfolio_uuid_sha256"])
        result["status"] = "METADATA_OBSERVED"
    except Exception as error:
        result["status"] = "OBSERVATION_FAILED"
        result["error_type"] = type(error).__name__
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http-worker", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    if args.http_worker:
        try:
            answer = http_worker()
        except BaseException as error:
            answer = {"error_type": type(error).__name__}
        print(json.dumps(answer))
        return
    if args.output is None:
        parser.error("--output required")
    with args.output.open("x") as output:
        # Nothing from credentials, SDK signing or HTTP error bodies reaches logs.
        with open(os.devnull, "w") as sink, redirect_stdout(sink), redirect_stderr(sink):
            def no_network(*args, **kwargs):
                raise AssertionError("network permitted only inside the fixed worker")
            socket.create_connection = no_network
            socket.getaddrinfo = no_network
            socket.socket.connect = no_network
            real_popen = subprocess.Popen
            worker = [sys.executable, "-B", str(Path(__file__).resolve()), "--http-worker"]
            def restricted_popen(command, *popen_args, **kwargs):
                if command != worker:
                    raise FileNotFoundError("only metadata worker permitted")
                return real_popen(command, *popen_args, **kwargs)
            subprocess.Popen = restricted_popen
            def no_sql(event, values):
                if event == "sqlite3.connect":
                    raise AssertionError("application database access forbidden")
            sys.addaudithook(no_sql)
            result = observe()
        json.dump(result, output, indent=2, allow_nan=False)
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
