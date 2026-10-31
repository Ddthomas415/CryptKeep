"""Prepare/perform one supervised public feasibility capture; default is offline."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlencode, urlsplit
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml
from services.backtest import descriptive_candles as candles
from services.backtest import descriptive_metadata as metadata


BASE = "https://api.exchange.coinbase.com"
NAMESPACE = ROOT / "research/ed002_public_inputs"
MAX_REQUESTS, WORKER_SECONDS, SOCKET_SECONDS = 27, 120, 5
PER_BODY, TOTAL_BODY = 2*1024*1024, 16*1024*1024
WARMUP_SCHEMA = "ed002-public-warmup-plan-v1"
CONTINUATION_SCHEMA = "ed002-public-continuation-plan-v1"
DAY = 24*candles.HOUR


def request_cap(plan):
    return 35 if plan.get("schema") == WARMUP_SCHEMA else MAX_REQUESTS


def history_hours(plan, symbol):
    if plan.get("schema") == WARMUP_SCHEMA:
        return 1464 if symbol in ("BTC", "ETH") else 300
    if plan.get("schema") == CONTINUATION_SCHEMA:
        return (plan["end_ms"]-plan["start_ms"])//candles.HOUR
    return 2


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def validate_plan(plan, universe_bytes):
    if not isinstance(plan, dict) or plan.get("universe_sha256") != sha(universe_bytes):
        raise ValueError("invalid_public_capture_plan")
    if plan.get("schema") == WARMUP_SCHEMA:
        expected = {"schema", "universe_sha256", "identities", "default_warmup_hours", "incumbent_warmup_hours", "anchor"}
        if (set(plan) != expected or type(plan["default_warmup_hours"]) is not int
                or type(plan["incumbent_warmup_hours"]) is not int
                or plan["default_warmup_hours"] != 300 or plan["incumbent_warmup_hours"] != 1464
                or plan["anchor"] != "last_completed_utc_day_at_worker_start"):
            raise ValueError("fixed_warmup_profile_required")
    elif plan.get("schema") == CONTINUATION_SCHEMA:
        if (set(plan) != {"schema", "universe_sha256", "identities", "start_ms", "end_ms"}
                or any(type(plan[k]) is not int or plan[k] < 0 or plan[k] % candles.HOUR
                       for k in ("start_ms", "end_ms"))
                or not candles.HOUR <= plan["end_ms"]-plan["start_ms"] <= DAY):
            raise ValueError("pinned_one_to_24_completed_hours_required")
    elif (set(plan) != {"schema", "universe_sha256", "identities", "lookback_completed_hours"}
            or plan.get("schema") != "ed002-public-capture-plan-v1"
            or type(plan["lookback_completed_hours"]) is not int or plan["lookback_completed_hours"] != 2):
        raise ValueError("invalid_public_capture_plan")
    config = yaml.safe_load(universe_bytes)["universe"]
    assets = [s.split("/")[0] for tier in ("tier1", "tier2", "watchlist") for s in config[tier]]
    identities = plan["identities"]
    if len(assets) != 25 or len(set(assets)) != 25 or not isinstance(identities, dict) or set(identities) != set(assets):
        raise ValueError("declared_25_identity_rows_required")
    for asset, identity in identities.items():
        if identity is None:
            continue
        if (not metadata._identity(identity)
                or set(identity) != {"product_id", "base_currency", "quote_currency", "identity_evidence_sha256"}
                or not re.fullmatch(r"[A-Z0-9]+", asset)
                or identity["base_currency"] != asset or identity["product_id"] != asset + "-USD"):
            raise ValueError("invalid_explicit_product_identity")
    return {"planned_max_requests": request_cap(plan), "symbols_considered": sorted(assets),
            "unresolved_identity_rows": sum(v is None for v in identities.values()),
            "worker_wait_seconds": WORKER_SECONDS, "socket_timeout_seconds": SOCKET_SECONDS,
            "body_bytes_cap": TOTAL_BODY,
            "history_hours_by_symbol": {s: history_hours(plan, s) for s in sorted(assets)},
            "lookback_completed_hours": 2 if plan["schema"] == "ed002-public-capture-plan-v1" else None,
            "pinned_window": {k: plan[k] for k in ("start_ms", "end_ms")}
                if plan["schema"] == CONTINUATION_SCHEMA else None,
            "market_run_authorized": False, "scoring_authorized": False}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def allowed_url(value):
    try:
        url = urlsplit(value)
        if (url.scheme != "https" or url.hostname != "api.exchange.coinbase.com"
                or url.port not in (None, 443) or url.username is not None or url.password is not None or url.fragment):
            return False
        if url.path in ("/products", "/currencies"):
            return not url.query
        params = parse_qs(url.query, keep_blank_values=True)
        return (re.fullmatch(r"/products/[A-Z0-9]+-USD/candles", url.path) is not None
                and set(params) == {"granularity", "start", "end"}
                and params["granularity"] == ["3600"] and all(len(v) == 1 and v[0] for v in params.values()))
    except (TypeError, ValueError):
        return False


def public_getter():
    import certifi
    context = ssl.create_default_context(cafile=certifi.where())
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=context), NoRedirect())

    def get(url, timeout, limit):
        if not allowed_url(url) or not 0 < timeout <= SOCKET_SECONDS or not 0 < limit <= PER_BODY:
            raise ValueError("public_request_bounds_required")
        request = urllib.request.Request(url, method="GET", headers={
            "User-Agent": "CryptKeep-public-feasibility/1", "Accept": "application/json",
            "Accept-Encoding": "identity"})
        try:
            response = opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            response = error  # Keep error body/status; never follow or retry it.
        with response:
            body = response.read(limit + 1)
            return response.code, body, {k: response.headers.get(k) for k in ("Date", "Content-Type")}
    return get


def capture_once(plan, output, *, get, monotonic=time.monotonic,
                 wall_ms=lambda: time.time_ns()//1_000_000):
    """Fake-injectable worker core; supported live entry is the supervisor only."""
    output = Path(output)
    began = monotonic()
    warmup = plan["schema"] == WARMUP_SCHEMA
    continuation = plan["schema"] == CONTINUATION_SCHEMA
    now = wall_ms()
    end = plan["end_ms"] if continuation else now // (DAY if warmup else candles.HOUR) * (DAY if warmup else candles.HOUR)
    starts = {s: end-history_hours(plan, s)*candles.HOUR for s in plan["identities"]}
    start = min(starts.values())
    if start < 0 or end > now//candles.HOUR*candles.HOUR:
        raise ValueError("completed_window_unavailable")
    records, captures, stored, products_body = [], [], 0, None
    result = {"status": "INCOMPLETE", "qualification": "PUBLIC_CAPTURE_NOT_STUDY_OR_IDENTITY_APPROVAL",
              "window_start_ms": start, "window_end_ms": end, "records": records,
              "symbols": {s: {"metadata_eligible_under_model": None, "metadata_reason": "not_observed",
                              "candle_capture_required": None} for s in plan["identities"]},
              "scoring_authorized": False, "identity_authenticity_verified": False}
    window = {"start_ms": start, "end_ms": end,
              "resolution": "pinned_completed_interval" if continuation else
                  "last_completed_utc_day_at_worker_start" if warmup else "two_completed_hours_at_worker_start"}
    if warmup:
        window["start_ms_by_symbol"] = starts
    write_json(output/"window.json", window)

    def request(path, label):
        nonlocal stored
        remaining = 110 - (monotonic() - began)
        if len(records) >= request_cap(plan) or remaining <= 0 or stored >= TOTAL_BODY:
            raise ValueError("capture_budget_exhausted")
        url, number = BASE+path, len(records)+1
        sent = wall_ms()
        write_json(output/f"{number:02d}_intent.json", {"phase": "ABOUT_TO_CALL_TRANSPORT_NOT_SENT_PROOF",
            "method": "GET", "url": url, "sent_clock_ms": sent})
        record = {"method": "GET", "url": url, "request_started_ms": sent,
                  "http_status": None, "received_at_ms": None, "error_class": None}
        records.append(record)
        limit = min(PER_BODY, TOTAL_BODY-stored)
        try:
            status, body, headers = get(url, min(SOCKET_SECONDS, remaining), limit)
        except Exception as error:
            record["error_class"] = type(error).__name__
            write_json(output/f"{number:02d}_receipt.json", record)
            raise ValueError("public_transport_failure") from None
        received = wall_ms()
        if not isinstance(body, bytes) or type(status) is not int or not isinstance(headers, dict):
            raise ValueError("invalid_transport_result")
        truncated = len(body) > limit
        saved = body[:limit]
        name = f"{number:02d}_{label}.bin"
        with (output/name).open("xb") as handle:
            handle.write(saved)
        stored += len(saved)
        record.update({"http_status": status, "received_at_ms": received, "file": name,
                       "sha256": sha(saved), "bytes": len(saved), "truncated": truncated,
                       "http_date": headers.get("Date"), "content_type": headers.get("Content-Type")})
        write_json(output/f"{number:02d}_receipt.json", record)
        if truncated or received < sent or monotonic()-began > 110 or status != 200:
            raise ValueError("truncated_clock_budget_or_http_failure")
        return saved, record

    try:
        products_body, products_receipt = request("/products", "products")
        currencies_body, _ = request("/currencies", "currencies")
        currency_rows = json.loads(currencies_body)
        if not isinstance(currency_rows, list) or not all(isinstance(r, dict) for r in currency_rows):
            raise ValueError("invalid_currency_response")
        if sum(r.get("id") == "USD" for r in currency_rows) != 1:
            raise ValueError("missing_or_duplicate_usd_currency")
        mapped = metadata.map_public_metadata([{"received_at_ms": products_receipt["received_at_ms"],
            "products_bytes": products_body}], identities=plan["identities"])
        observed = {r["symbol"]: r for r in mapped["observations"]}
        for symbol in sorted(plan["identities"]):
            identity = plan["identities"][symbol]
            info = observed[symbol]
            result["symbols"][symbol] = {"metadata_eligible_under_model": info["eligible"],
                "metadata_reason": info["reason"], "candle_capture_required": info["eligible"] is True}
            if warmup:
                result["symbols"][symbol].update({"history_hours_required": history_hours(plan, symbol),
                                                  "window_start_ms": starts[symbol]})
            if info["eligible"] is not True:
                continue
            if sum(r.get("id") == identity["base_currency"] for r in currency_rows) != 1:
                raise ValueError("missing_or_duplicate_base_currency")
            pages = [(start, end)] if not warmup else [(t, min(t+300*candles.HOUR, end))
                     for t in range(starts[symbol], end, 300*candles.HOUR)]
            for page, (lower, upper) in enumerate(pages):
                params = urlencode({"granularity": 3600,
                    "start": datetime.fromtimestamp(lower/1000, timezone.utc).isoformat(),
                    "end": datetime.fromtimestamp((upper-1000 if warmup or continuation else upper)/1000, timezone.utc).isoformat()})
                label = symbol+"p"+str(page) if warmup else symbol
                body, receipt = request("/products/"+identity["product_id"]+"/candles?"+params, label)
                captures.append({"product_id": identity["product_id"], "method": "GET",
                    "url": receipt["url"], "received_at_ms": receipt["received_at_ms"],
                    "http_status": receipt["http_status"], "response_bytes": body})
        if warmup:
            normal = {"observations": {}, "coverage": [], "scoring_authorized": False,
                      "qualification": "PER_SYMBOL_WARMUP_SEED_NOT_CONFIRMATION",
                      "start_ms_by_symbol": starts, "end_ms": end}
            cutoff = max(end, wall_ms())
            for symbol, identity in plan["identities"].items():
                selected = [c for c in captures if identity is not None and c["product_id"] == identity["product_id"]]
                panel = candles.map_candle_captures(selected, identities={symbol: identity},
                    start_ms=starts[symbol], end_ms=end, as_of_ms=cutoff)
                normal["observations"][symbol] = panel["observations"][symbol]
                normal["coverage"].extend(panel["coverage"])
            normal["status"] = "COMPLETE" if all(r["status"] == "COMPLETE" for r in normal["coverage"]) else "INCOMPLETE"
        else:
            normal = candles.map_candle_captures(captures, identities=plan["identities"],
                start_ms=start, end_ms=end, as_of_ms=max(end, wall_ms()))
        coverage = {r["symbol"]: r for r in normal["coverage"]}
        ready = True
        for symbol, info in result["symbols"].items():
            info["window_coverage"] = coverage[symbol]
            latest = next((r for r in normal["observations"][symbol] if r["row"][0] == end-candles.HOUR), None)
            info["latest_bar_received_within_one_hour"] = bool(latest and latest["known_at_ms"] <= end+candles.HOUR)
            ready &= (info["metadata_eligible_under_model"] is False or
                      info["metadata_eligible_under_model"] is True and coverage[symbol]["status"] == "COMPLETE")
        write_json(output/"observations.json", normal)
        result["status"] = "COMPLETE" if ready else "INCOMPLETE"
    except (ValueError, KeyError, TypeError) as error:
        result["reason_class"] = type(error).__name__
        result["reason"] = str(error) if type(error) is ValueError else "capture_processing_failure"
    result["transport_calls_started"] = len(records)
    result["stored_payload_bytes"] = stored
    return result


def code_inputs():
    return {name: sha((ROOT/name).read_bytes()) for name in (
        "scripts/research/capture_descriptive_inputs.py", "services/backtest/descriptive_candles.py",
        "services/backtest/descriptive_metadata.py", "services/backtest/shared_cash_research.py",
        "config/candidate_universe.yaml")}


def _worker(output):
    output = Path(output)
    stage = "preflight"
    try:
        attempt = json.loads((output/"ATTEMPT.json").read_bytes())
        raw = (output/"plan.json").read_bytes()
        if attempt["code_inputs"] != code_inputs() or attempt["plan_sha256"] != sha(raw):
            raise ValueError("prepared_inputs_changed")
        plan = json.loads(raw)
        validate_plan(plan, (ROOT/"config/candidate_universe.yaml").read_bytes())
        stage = "client_initialization"
        get = public_getter()
        stage = "capture"
        result = capture_once(plan, output, get=get)
        stage = "result_write"
        write_json(output/"worker_result.json", result)
    except Exception as error:
        write_json(output/"worker_failure.json", {"stage": stage, "error_class": type(error).__name__})
        raise


def verify_result(result, output, plan):
    if (not isinstance(result, dict) or result.get("status") not in ("COMPLETE", "INCOMPLETE")
            or result.get("scoring_authorized") is not False
            or result.get("identity_authenticity_verified") is not False
            or set(result.get("symbols", {})) != set(plan["identities"])):
        raise ValueError("invalid_worker_receipt")
    records = result.get("records")
    if not isinstance(records, list) or len(records) > request_cap(plan) or result.get("transport_calls_started") != len(records):
        raise ValueError("invalid_transport_count")
    total = 0
    for record in records:
        if record.get("method") != "GET" or not allowed_url(record.get("url")):
            raise ValueError("invalid_public_request_receipt")
        if "file" not in record:
            if result["status"] == "COMPLETE":
                raise ValueError("complete_without_payload")
            continue
        name = record["file"]
        if not isinstance(name, str) or not re.fullmatch(r"[0-9]{2}_[A-Za-z0-9]+\.bin", name):
            raise ValueError("invalid_payload_path")
        raw = (Path(output)/name).read_bytes()
        if len(raw) != record["bytes"] or sha(raw) != record["sha256"] or len(raw) > PER_BODY:
            raise ValueError("payload_receipt_mismatch")
        total += len(raw)
        if result["status"] == "COMPLETE" and (record.get("truncated") is not False or record["http_status"] != 200):
            raise ValueError("complete_with_failed_payload")
    if total != result.get("stored_payload_bytes") or total > TOTAL_BODY:
        raise ValueError("invalid_payload_total")
    if result["status"] == "COMPLETE":
        if len(records) < 2 or any(i["metadata_eligible_under_model"] is None or
            i["metadata_eligible_under_model"] is True and i.get("window_coverage", {}).get("status") != "COMPLETE"
            for i in result["symbols"].values()):
            raise ValueError("complete_without_required_coverage")


def supervise(plan, output, *, popen=subprocess.Popen):
    validate_plan(plan, (ROOT/"config/candidate_universe.yaml").read_bytes())
    output = Path(output).resolve()
    if not output.is_relative_to(NAMESPACE.resolve()) or output == NAMESPACE.resolve():
        raise ValueError("new_public_capture_namespace_required")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/"plan.json", plan)
    write_json(output/"ATTEMPT.json", {"phase": "PREPARED_NOT_REQUEST_PROOF",
        "plan_sha256": sha((output/"plan.json").read_bytes()), "code_inputs": code_inputs(),
        "worker_wait_seconds": WORKER_SECONDS, "recovery_wait_seconds": 5})
    command = [sys.executable, "-B", "-c",
        "from scripts.research.capture_descriptive_inputs import _worker; import sys; _worker(sys.argv[1])", str(output)]
    clean_env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                 "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}
    process, reason, cleanup_failed = None, None, False
    try:
        process = popen(command, cwd=str(ROOT), env=clean_env, stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        code = process.wait(timeout=WORKER_SECONDS)
        if code != 0:
            reason = "worker_exit_nonzero"
    except subprocess.TimeoutExpired:
        reason = "worker_timeout"
    except KeyboardInterrupt:
        reason = "operator_interrupt"
    except Exception:
        reason = "supervisor_failure"
    finally:
        if process is not None and process.poll() is None:
            try:
                process.kill()
                process.wait(timeout=5)
            except Exception:
                cleanup_failed = True
    result = {"status": "INCOMPLETE", "reason": reason or "missing_worker_receipt"}
    if reason is None:
        try:
            result = json.loads((output/"worker_result.json").read_bytes())
            verify_result(result, output, plan)
        except (OSError, ValueError, TypeError, KeyError):
            result = {"status": "INCOMPLETE", "reason": "unreadable_worker_receipt"}
    result["owned_worker_cleanup_failed"] = cleanup_failed
    write_json(output/"manifest.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true", help="Live acquisition needs separate authorization.")
    args = parser.parse_args()
    try:
        plan_path = args.plan.resolve()
        if not plan_path.is_relative_to(NAMESPACE.resolve()):
            raise ValueError("public_plan_namespace_required")
        plan = json.loads(plan_path.read_bytes())
        preview = validate_plan(plan, (ROOT/"config/candidate_universe.yaml").read_bytes())
        result = supervise(plan, args.output) if args.execute else {"dry_run": True, **preview}
        print(json.dumps({k: result.get(k) for k in ("status", "dry_run", "planned_max_requests",
            "transport_calls_started", "stored_payload_bytes", "reason", "owned_worker_cleanup_failed")}, sort_keys=True))
        return 0 if not args.execute or result.get("status") == "COMPLETE" else 2
    except Exception:
        print('{"status":"INCOMPLETE","reason":"capture_preflight_failed"}')
        return 2


if __name__ == "__main__":
    sys.exit(main())
