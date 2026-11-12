"""Bounded, opt-in OHLCV fetch evidence for a single Group A account."""

from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time


WINDOW_MS = 600_000
_MAX_BYTES = 32_768
_MAX_BUCKETS = 601
_MARKETS = ("BTC/USD", "ETH/USD", "SOL/USD")
_MAX_COUNT = 2**31 - 1
FILENAME = "group_a_candle_health.json"


def _bounded_int(value, low=0, high=2**53 - 1):
    return type(value) is int and low <= value <= high


def valid_writer_id(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{32}", value) is not None


def _unique_checkpoint(pairs):
    obj = dict(pairs)
    if len(obj) != len(pairs):
        raise ValueError("duplicate_checkpoint_key")
    return obj


def _read(path, market, *, dir_fd=None):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                return None
            raw = stream.read(_MAX_BYTES + 1)
        obj = json.loads(raw, object_pairs_hook=_unique_checkpoint) if len(raw) <= _MAX_BYTES else None
        if (not isinstance(obj, dict) or set(obj) - {"writer_id", "attempt_seq"} != {
                "version", "market", "as_of_ms", "unknown_through_ms",
                "failures", "streak_known", "pending", "buckets",
            } or (("writer_id" in obj or "attempt_seq" in obj)
                  and (not valid_writer_id(obj.get("writer_id")) or not _bounded_int(obj.get("attempt_seq"), 1)))
                or not _bounded_int(obj["version"], 1, 1) or obj.get("market") != market
                or not _bounded_int(obj.get("as_of_ms"), 1)
                or not _bounded_int(obj.get("unknown_through_ms"), high=obj["as_of_ms"])
                or not _bounded_int(obj.get("failures"), high=_MAX_COUNT)
                or type(obj.get("streak_known")) is not bool or type(obj.get("pending")) is not bool
                or not isinstance(obj.get("buckets"), list) or len(obj["buckets"]) > _MAX_BUCKETS):
            return None
        previous = -1
        for bucket in obj["buckets"]:
            if (not isinstance(bucket, list) or len(bucket) != 2
                    or not _bounded_int(bucket[0], 1, obj["as_of_ms"] // 1000)
                    or not _bounded_int(bucket[1], 1, _MAX_COUNT) or bucket[0] <= previous):
                return None
            previous = bucket[0]
        return obj
    except (OSError, ValueError, RecursionError):
        return None


def _save(path, obj):
    with tempfile.NamedTemporaryFile(dir=path.parent, mode="w", encoding="ascii", delete=False) as stream:
        tmp = Path(stream.name)
        try:
            json.dump(obj, stream, separators=(",", ":"))
            stream.close()
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)


def watcher_fetch_counts(
    path: Path, market: str, *, now_ms: int, expected_writer: str | None = None,
    expected_sequence: int | None = None, dir_fd=None,
) -> tuple[int | None, int | None]:
    """Supply exact counts, or threshold-proving lower bounds, to R3.

    Unknown coverage below threshold stays unknown. A bucket straddling the
    ten-minute boundary cannot prove exact absence or add a false positive.
    """
    obj = _read(path, market, dir_fd=dir_fd)
    if (obj is None or obj["pending"] or not _bounded_int(now_ms, 1)
            or ((expected_writer is not None or expected_sequence is not None)
                and (not valid_writer_id(expected_writer) or expected_writer != obj.get("writer_id")
                     or not _bounded_int(expected_sequence, 1) or expected_sequence != obj.get("attempt_seq")))
            or not 0 <= now_ms - obj["as_of_ms"] <= WINDOW_MS):
        return None, None
    failures = obj["failures"]
    start = now_ms - WINDOW_MS
    definite = sum(count for second, count in obj["buckets"] if second * 1000 > start)
    edge = any(second * 1000 <= start < second * 1000 + 999 for second, _ in obj["buckets"])
    exact = not edge and start >= obj["unknown_through_ms"]
    return failures if obj["streak_known"] or failures >= 10 else None, definite if exact or definite >= 5 else None


@dataclass
class _Attempt:
    success: bool = False


class CandleFetchHealth:
    def __init__(self, path: Path, market: str, *, clock_ms=None, writer_id=None):
        self.path = path
        self.market = market
        self.clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self.writer_id = writer_id
        self.attempt_seq = 0
        self._write_failed = False
        self._new_writer = True

    @contextmanager
    def attempt(self, exchange):
        """Observe transport without changing fetch results or raising on telemetry I/O."""
        result = _Attempt()
        self.attempt_seq += 1
        try:
            started = self.clock_ms()
            if not _bounded_int(started, 1) or self.market not in _MARKETS:
                raise ValueError("invalid_health_input")
            previous = _read(self.path, self.market)
            if (previous is None or started < previous["as_of_ms"]
                    or started - previous["as_of_ms"] > WINDOW_MS):
                previous = {"failures": 0, "streak_known": False, "buckets": [], "unknown_through_ms": started}
            elif self._new_writer or self._write_failed or previous["pending"]:
                # An earlier writer may have completed a fetch after failing
                # to mark it pending. Keep only the durable 429 lower bound.
                previous.update(failures=0, streak_known=False, unknown_through_ms=started)
            checkpoint = {**previous, "version": 1, "market": self.market, "as_of_ms": started, "pending": True}
            if self.writer_id is not None:
                if not valid_writer_id(self.writer_id):
                    raise ValueError("invalid_health_writer")
                checkpoint["writer_id"] = self.writer_id
                checkpoint["attempt_seq"] = self.attempt_seq
            else:
                checkpoint.pop("writer_id", None)
                checkpoint.pop("attempt_seq", None)
            _save(self.path, checkpoint)
            self._new_writer = False
        except Exception:
            self._write_failed = True
            yield result
            return

        responses = Counter()
        uncertain = False
        latest_seen = started
        original = None
        was_local = False
        installed = False

        def observe(code, *args, **kwargs):
            nonlocal uncertain, latest_seen
            if type(code) is int and code == 429:
                try:
                    stamp = self.clock_ms()
                    if not _bounded_int(stamp, latest_seen) or stamp - started > WINDOW_MS:
                        raise ValueError("invalid_health_clock")
                    second = stamp // 1000
                    if responses[second] >= _MAX_COUNT:
                        raise ValueError("health_count_overflow")
                    responses[second] += 1
                    latest_seen = stamp
                except Exception:
                    uncertain = True
            return original(code, *args, **kwargs)

        try:
            try:
                original = getattr(exchange, "on_rest_response", None)
                if callable(original):
                    was_local = "on_rest_response" in vars(exchange)
                    exchange.on_rest_response = observe
                    installed = True
            except Exception:
                pass
            yield result
        finally:
            if installed:
                try:
                    if was_local:
                        exchange.on_rest_response = original
                    else:
                        del exchange.on_rest_response
                except Exception:
                    uncertain = True
            try:
                finished = self.clock_ms()
                if not _bounded_int(finished, latest_seen) or finished - started > WINDOW_MS:
                    raise ValueError("invalid_health_clock")
                buckets = Counter(dict(checkpoint["buckets"]))
                buckets.update(responses)
                recent = sorted((sec, count) for sec, count in buckets.items()
                                if sec * 1000 + 999 > finished - WINDOW_MS)
                if any(sec * 1000 > finished or count > _MAX_COUNT for sec, count in recent):
                    raise ValueError("invalid_health_bucket")
                checkpoint.update(
                    as_of_ms=finished, pending=False, buckets=recent,
                    failures=0 if result.success else min(_MAX_COUNT, checkpoint["failures"] + 1),
                    streak_known=checkpoint["streak_known"] or result.success,
                )
                if not installed or uncertain:
                    checkpoint["unknown_through_ms"] = finished
                _save(self.path, checkpoint)
                self._write_failed = False
            except Exception:
                self._write_failed = True
