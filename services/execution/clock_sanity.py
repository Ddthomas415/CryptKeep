"""
Clock/venue-time sanity checks (live blocker: window-based safety
mechanisms — intent TTL, resume ceremony window, stale-submitting
threshold, not-found age, reconciler cursor overlap — all assume sane
host and venue clocks).

Skew is measured against the venue's own server time: local midpoint of
the request round-trip vs the venue-reported epoch. The consumer gate
fails closed on a MEASURED skew beyond `CBP_MAX_CLOCK_SKEW_MS`.

Deliberate v1 boundaries (recorded, operator-adjustable):
- venues without a server-time endpoint are recorded as a limitation
  (`venue_time_unsupported`) and never block — per the backlog wording
  "venue server-time query or limitation record";
- measurement errors are recorded but do not block; only an affirmative
  over-threshold measurement blocks. Blocking on unmeasurable time is a
  possible stricter follow-up.
- OK results are cached for `CBP_CLOCK_SKEW_CHECK_INTERVAL_S`; exceeded
  and failed measurements are never cached, so recovery is immediate and
  a single-measurement blip rejects at most one loop iteration's intents.
"""
from __future__ import annotations

import logging
import math
import os
import time
from typing import Any, Callable

_LOG = logging.getLogger("clock_sanity")

MAX_CLOCK_SKEW_MS_ENV = "CBP_MAX_CLOCK_SKEW_MS"
MAX_CLOCK_SKEW_MS_DEFAULT = 5000.0
CLOCK_SKEW_CHECK_INTERVAL_S_ENV = "CBP_CLOCK_SKEW_CHECK_INTERVAL_S"
CLOCK_SKEW_CHECK_INTERVAL_S_DEFAULT = 300.0

_CACHE: dict[str, dict[str, Any]] = {}


def _reset_cache() -> None:
    _CACHE.clear()


def max_clock_skew_ms() -> float:
    raw = os.environ.get(MAX_CLOCK_SKEW_MS_ENV)
    if raw is None or str(raw).strip() == "":
        return MAX_CLOCK_SKEW_MS_DEFAULT
    try:
        value = float(raw)
    except Exception as _err:
        return MAX_CLOCK_SKEW_MS_DEFAULT
    if not math.isfinite(value) or value <= 0.0:
        return MAX_CLOCK_SKEW_MS_DEFAULT
    return value


def clock_skew_check_interval_s() -> float:
    raw = os.environ.get(CLOCK_SKEW_CHECK_INTERVAL_S_ENV)
    if raw is None or str(raw).strip() == "":
        return CLOCK_SKEW_CHECK_INTERVAL_S_DEFAULT
    try:
        value = float(raw)
    except Exception as _err:
        return CLOCK_SKEW_CHECK_INTERVAL_S_DEFAULT
    if not math.isfinite(value) or value <= 0.0:
        return CLOCK_SKEW_CHECK_INTERVAL_S_DEFAULT
    return value


def measure_venue_skew(ex: Any, *, local_ms: Callable[[], float] | None = None) -> dict[str, Any]:
    """
    Measure venue-vs-local clock skew in milliseconds.

    skew_ms = venue_time - midpoint(local before, local after); rtt_ms
    bounds measurement quality (true skew lies within ±rtt/2 of the
    estimate). Fail closed on shape: non-finite or non-positive venue
    times report measured=False.
    """
    now = local_ms or (lambda: time.time() * 1000.0)
    out: dict[str, Any] = {
        "supported": False,
        "measured": False,
        "skew_ms": None,
        "rtt_ms": None,
        "venue_time_ms": None,
        "reason": "venue_time_unsupported",
    }
    has = getattr(ex, "has", None)
    fetch_time = getattr(ex, "fetch_time", None)
    if not callable(fetch_time) or (isinstance(has, dict) and not has.get("fetchTime")):
        return out
    out["supported"] = True
    try:
        t0 = float(now())
        venue_ms = fetch_time()
        t1 = float(now())
    except Exception as exc:
        out["reason"] = f"measure_error:{type(exc).__name__}"
        return out
    try:
        venue_ms_f = float(venue_ms)
    except Exception as _err:
        out["reason"] = "invalid_venue_time"
        return out
    if not math.isfinite(venue_ms_f) or venue_ms_f <= 0.0 or not math.isfinite(t0) or not math.isfinite(t1) or t1 < t0:
        out["reason"] = "invalid_venue_time"
        return out
    midpoint = (t0 + t1) / 2.0
    out.update({
        "measured": True,
        "skew_ms": venue_ms_f - midpoint,
        "rtt_ms": t1 - t0,
        "venue_time_ms": venue_ms_f,
        "reason": "ok",
    })
    return out


def check_venue_clock(
    venue: str,
    exchange_factory: Callable[[], Any],
    *,
    monotonic: Callable[[], float] | None = None,
) -> dict[str, Any]:
    """
    Cached submit gate. Returns a dict whose `ok` field means "submits may
    proceed". `ok=False` only for an affirmative measured skew beyond the
    threshold. OK results are cached for the check interval; exceeded and
    failed measurements are never cached (immediate re-measure next call).
    The factory is invoked only on cache misses and may return either a raw
    ccxt exchange or an adapter exposing `.ex`; a `close()` on the returned
    object is called after measurement when present.
    """
    mono = monotonic or time.monotonic
    threshold = max_clock_skew_ms()
    interval = clock_skew_check_interval_s()
    key = str(venue or "").strip().lower()
    cached = _CACHE.get(key)
    if cached is not None and (mono() - cached["at"]) < interval:
        result = dict(cached["result"])
        result["cached"] = True
        return result

    handle = None
    try:
        handle = exchange_factory()
        ex = getattr(handle, "ex", handle)
        m = measure_venue_skew(ex)
    except Exception as exc:
        m = {
            "supported": True,
            "measured": False,
            "skew_ms": None,
            "rtt_ms": None,
            "venue_time_ms": None,
            "reason": f"factory_error:{type(exc).__name__}",
        }
    finally:
        try:
            if handle is not None and hasattr(handle, "close"):
                handle.close()
        except Exception as _err:
            pass

    exceeded = bool(m.get("measured")) and abs(float(m.get("skew_ms") or 0.0)) > threshold
    result: dict[str, Any] = {
        "ok": not exceeded,
        "venue": key,
        "threshold_ms": threshold,
        "exceeded": exceeded,
        "cached": False,
        **m,
    }
    if exceeded:
        result["reason"] = f"clock_skew_exceeded:{float(m['skew_ms']):.0f}ms"
        _LOG.error(
            "clock_sanity.skew_exceeded venue=%s skew_ms=%.0f rtt_ms=%.0f threshold_ms=%.0f",
            key, float(m["skew_ms"]), float(m.get("rtt_ms") or 0.0), threshold,
        )
    elif not m.get("measured"):
        _LOG.warning("clock_sanity.unmeasured venue=%s reason=%s", key, m.get("reason"))

    # cache only trustworthy-OK results: measured-good or unsupported venues
    if result["ok"] and (m.get("measured") or not m.get("supported")):
        _CACHE[key] = {"at": mono(), "result": dict(result)}
    return result
