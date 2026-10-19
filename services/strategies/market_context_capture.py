"""Opt-in, bounded research observations; never an execution authority.

Quotes are runner observations, not exchange event/receive timestamps. This
stream alone cannot establish high-frequency coverage or executable returns.
"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import threading
import time
import uuid
from pathlib import Path

from services.os.app_paths import data_dir


class MarketContextCapture:
    def __init__(self, directory: Path, *, config_hash: str, capacity=256, byte_limit=64*1024*1024):
        if capacity <= 0 or byte_limit <= 0:
            raise ValueError("capture budgets must be positive")
        self.path = directory / f"{uuid.uuid4().hex}.jsonl"
        self.config_hash = config_hash
        self.events = queue.Queue(maxsize=capacity)
        self.byte_limit = byte_limit
        self.stop = threading.Event()
        self.failed = threading.Event()
        self.dropped = 0
        self.written = 0
        self.error = None
        self.admission = threading.Lock()
        self.lost = 0
        self.worker_state = "running"
        self.thread = threading.Thread(target=self._write, daemon=True, name="research-context-writer")
        self.thread.start()

    def offer(self, kind: str, **fields):
        if not self.admission.acquire(blocking=False):
            self.dropped += 1
            return None
        try:
            if self.stop.is_set() or self.failed.is_set():
                self.dropped += 1
                return None
            event_id = uuid.uuid4().hex
            event = dict(fields, schema_version=1, kind=kind, event_id=event_id,
                         capture_session_id=self.path.stem,
                         observed_ns=time.time_ns(), monotonic_ns=time.monotonic_ns(),
                         config_sha256=self.config_hash,
                         scope="research_observation_not_fill_or_quote_receipt")
            self.events.put_nowait(event)
            return event_id
        except Exception:
            self.dropped += 1
            return None
        finally:
            self.admission.release()

    def quote(self, venue: str, symbol: str, evidence: dict):
        # Allowlist avoids persisting arbitrary config or credentials.
        return self.offer("quote", venue=venue, symbol=symbol,
                          bid=evidence.get("market_bid"), ask=evidence.get("market_ask"),
                          source_age_sec=evidence.get("market_age_sec"),
                          quality_ok=evidence.get("market_quality_ok"),
                          exchange_event_ns=None, quote_received_ns=None)

    def entry(self, *, side: str, intent_id: str, venue: str, symbol: str,
              strategy: str, qty: float, quote_event_id):
        if side != "buy":
            return None
        return self.offer("admitted_entry", intent_id=intent_id, venue=venue,
                          symbol=symbol, strategy=strategy, qty=qty,
                          quote_event_id=quote_event_id, disposition="queue_upsert_returned",
                          fee_policy="unverified", reporting_conversion="unverified")

    def _write(self):
        in_flight = False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            size = 0
            with self.path.open("x", encoding="utf-8") as out:
                while not self.stop.is_set() or not self.events.empty():
                    try:
                        event = self.events.get(timeout=.05)
                    except queue.Empty:
                        self._persist_status()
                        continue
                    in_flight = True
                    raw = json.dumps(event, sort_keys=True, allow_nan=False)+"\n"
                    size += len(raw.encode())
                    if size > self.byte_limit:
                        raise ValueError("capture_byte_budget_exhausted")
                    out.write(raw)
                    out.flush()
                    self.written += 1
                    in_flight = False
                    self._persist_status()
        except Exception as exc:
            self.lost += int(in_flight)
            self.error = "capture_byte_budget_exhausted" if str(exc) == "capture_byte_budget_exhausted" else type(exc).__name__
            self.failed.set()
        finally:
            self.worker_state = "failed" if self.failed.is_set() else "finished"
            self._persist_status()

    def status(self):
        return {"enabled": True, "path": str(self.path), "written": self.written,
                "dropped": self.dropped, "lost": self.lost, "pending": self.events.qsize(),
                "failed": self.failed.is_set(), "error": self.error,
                "writer_stopped": not self.thread.is_alive(),
                "worker_state": self.worker_state,
                "coverage": "unverified", "stop_requested": self.stop.is_set()}

    def _persist_status(self):
        # Worker-only I/O; missing/stale sidecar must never imply complete capture.
        try:
            target = self.path.with_suffix(".status.json")
            temporary = target.with_suffix(".tmp")
            snapshot = self.status()
            # A worker cannot observe its own thread termination. Persist the
            # processing lifecycle, not a necessarily stale is_alive() value.
            snapshot.pop("writer_stopped")
            temporary.write_text(json.dumps(snapshot), encoding="utf-8")
            temporary.replace(target)
        except Exception:
            self.failed.set()
            self.worker_state = "failed"
            self.error = self.error or "capture_status_write_failed"

    def close(self):
        with self.admission:
            self.stop.set()
        self.thread.join(timeout=.25)
        return self.status()


def capture_call(capture, method, *args, **kwargs):
    """Research instrumentation must not interrupt the runner, including cleanup."""
    try:
        return getattr(capture, method)(*args, **kwargs)
    except Exception:
        return None


def start_capture(cfg: dict):
    if os.environ.get("CBP_CAPTURE_MARKET_CONTEXT") != "1":
        return None
    try:
        digest = hashlib.sha256(json.dumps(cfg, sort_keys=True, allow_nan=False).encode()).hexdigest()
        return MarketContextCapture(data_dir()/"market_context", config_hash=digest)
    except Exception:
        # Caller can expose startup failure without affecting trading.
        return None
