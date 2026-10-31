"""Opt-in, one-shot public capture. No SDK, accounts, loop or store creation."""

from datetime import datetime, timezone
import hashlib
import math
import re
from sqlite3 import Error as SQLiteError
import subprocess
import time

from services.analytics.okx_funding_contract import _response
from services.analytics.okx_funding_journal import append_okx_funding_pairs, pair_journal_inputs


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _seconds(value, ceiling):
    return (type(value) in (int, float) and math.isfinite(value)
            and 0 < value <= ceiling)


def collect_okx_funding_pair(*, inst_id, enabled=False, max_requests=None,
                             total_timeout_seconds=None, request_timeout_seconds=None,
                             max_response_bytes=None, run=None, utc=None, monotonic=None):
    """Capture at most two GETs; deadline covers capture, not caller persistence.

    Injected dependencies must honor subprocess.run's timeout and bytes contract.
    No live authority is implied by enabling a source function.
    """
    if type(enabled) is not bool:
        raise ValueError("explicit_boolean_enable_required")
    if not enabled:
        return {"ok": False, "reason": "okx_pair_capture_disabled", "captures": [], "pair": None,
                "requests_attempted": 0, "execution_authority": False}
    if (type(inst_id) is not str or re.fullmatch(r"[A-Z0-9]+-[A-Z0-9]+-SWAP", inst_id) is None
            or type(max_requests) is not int or max_requests != 2
            or not _seconds(total_timeout_seconds, 30) or not _seconds(request_timeout_seconds, 10)
            or type(max_response_bytes) is not int or not 0 < max_response_bytes <= 1048576):
        raise ValueError("explicit_pair_identity_and_budgets_required")
    run = subprocess.run if run is None else run
    utc = _utc if utc is None else utc
    monotonic = time.monotonic if monotonic is None else monotonic
    if not all(callable(value) for value in (run, utc, monotonic)):
        raise ValueError("transport_and_clocks_must_be_callable")
    started = monotonic()
    deadline = started + total_timeout_seconds
    captures = []
    result = {"ok": False, "reason": "okx_pair_capture_incomplete", "captures": captures,
              "pair": None, "requests_attempted": 0, "execution_authority": False}
    pair = {"requested_inst_id": inst_id}
    for name, endpoint in (("current", "funding-rate"), ("history", "funding-rate-history")):
        remaining = deadline - monotonic()
        if remaining <= 0:
            result["reason"] = "okx_pair_deadline_exhausted"
            return result
        timeout = min(request_timeout_seconds, remaining)
        url = "https://www.okx.com/api/v5/public/" + endpoint + "?instId=" + inst_id
        if name == "history":
            url += "&limit=5"
        receipt = {"url": url, "request_started_at": utc()}
        result["requests_attempted"] += 1
        command = [
            "/usr/bin/curl", "--disable", "--silent", "--show-error",
            "--noproxy", "*", "--proto", "=https", "--max-redirs", "0", "--retry", "0",
            "--connect-timeout", str(min(5, timeout)), "--max-time", str(timeout),
            "--max-filesize", str(max_response_bytes), "--request", "GET", "--output", "-",
            "--write-out", "\n%{http_code}", url,
        ]
        body = b""
        try:
            completed = run(command, env={"PATH": "/usr/bin:/bin"}, capture_output=True,
                            timeout=timeout, check=False)
            if type(completed.stdout) is not bytes:
                raise ValueError("transport_bytes_required")
            body, separator, status = completed.stdout.rpartition(b"\n")
            if not separator or len(status) != 3 or not status.isdigit():
                body = completed.stdout
                raise ValueError("transport_status_trailer_invalid")
            receipt.update(curl_exit_code=completed.returncode, http_status=status.decode("ascii"))
            if len(body) > max_response_bytes:
                raise ValueError("response_byte_budget_exceeded")
            receipt["received_at"] = utc()
            receipt.update(body_bytes=len(body), body_sha256=hashlib.sha256(body).hexdigest())
            payload, _ = _response(body, receipt, endpoint, inst_id)
            if name == "current" and len(payload["data"]) != 1:
                raise ValueError("current_row_count_invalid")
        except (OSError, subprocess.SubprocessError, ValueError, TypeError, RecursionError, OverflowError) as exc:
            if isinstance(exc, subprocess.TimeoutExpired) and type(exc.output) is bytes:
                body = exc.output
            truncated = len(body) > max_response_bytes
            body = body[:max_response_bytes]
            receipt.update(received_at=receipt.get("received_at") or utc(),
                           body_bytes=len(body), body_sha256=hashlib.sha256(body).hexdigest())
            captures.append({"name": name, "body": body, "receipt": receipt, "complete": False,
                             "body_truncated": truncated, "error_type": type(exc).__name__})
            result["reason"] = "okx_pair_request_failed"
            return result
        captures.append({"name": name, "body": body, "receipt": receipt, "complete": True,
                         "body_truncated": False})
        pair[name + "_body"], pair[name + "_receipt"] = body, receipt
    if monotonic() >= deadline:
        result["reason"] = "okx_pair_deadline_exhausted"
        return result
    try:
        pair_journal_inputs(**pair)
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        result.update(reason="okx_pair_contract_invalid", error_type=type(exc).__name__)
        return result
    finished = monotonic()
    if finished >= deadline:
        result["reason"] = "okx_pair_deadline_exhausted"
        return result
    result.update(ok=True, reason="okx_pair_captured", pair=pair,
                  elapsed_capture_seconds=finished - started)
    return result


def collect_and_journal_okx_pair(store, *, source, max_journal_bytes, **capture_options):
    """Use an explicitly supplied store only after a valid opt-in capture."""
    if (type(source) is not str or not source or source != source.strip()
            or type(max_journal_bytes) is not int or max_journal_bytes <= 0):
        raise ValueError("explicit_journal_source_and_byte_budget_required")
    if capture_options.get("enabled") is True and not callable(
            getattr(store, "append_raw_funding_observations", None)):
        raise ValueError("explicit_caller_owned_journal_required")
    result = collect_okx_funding_pair(**capture_options)
    if not result["ok"]:
        result["journal_state"] = "not_attempted"
        return result
    try:
        result["journal_write"] = append_okx_funding_pairs(
            store, [result["pair"]], source=source, max_rows=1, max_bytes=max_journal_bytes)
    except (OSError, ValueError, TypeError, RuntimeError, SQLiteError, OverflowError) as exc:
        result.update(ok=False, reason="okx_pair_persistence_failed",
                      journal_state="unknown", error_type=type(exc).__name__)
        return result
    result["journal_state"] = "confirmed"
    return result
