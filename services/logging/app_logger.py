"""
services/logging/app_logger.py

Logging with:
  - Secret redaction (bearer tokens, API keys, passwords, etc.)
  - Optional JSON structured mode (CBP_LOG_JSON=1)
  - Correlation ID support (set_correlation_id / get_correlation_id)
"""
from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
import os
import re
import sys
import threading
import time
from typing import Any

from services.os import app_paths

# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

REDACT_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s]+)"),
    re.compile(r"(?i)(token\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(password\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(secret\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(cookie\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(jwt\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(session\s*[=:]\s*)([^\s,;]+)"),
]


def _redact_text(text: str) -> str:
    out = str(text)
    for pat in REDACT_PATTERNS:
        out = pat.sub(r"\1***REDACTED***", out)
    return out


# ---------------------------------------------------------------------------
# Correlation ID (thread-local)
# ---------------------------------------------------------------------------

_local = threading.local()


def set_correlation_id(cid: str) -> None:
    """Set a correlation ID on the current thread (e.g. per-tick, per-order)."""
    _local.correlation_id = str(cid or "")


def get_correlation_id() -> str:
    return str(getattr(_local, "correlation_id", "") or "")


def clear_correlation_id() -> None:
    _local.correlation_id = ""


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact_text(str(record.msg))
        if record.args:
            record.args = tuple(_redact_text(str(a)) for a in record.args)
        return True


class StructuredJsonFormatter(logging.Formatter):
    """Emit one JSON object per log line with correlation ID and service name."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        # Apply redaction to the fully-rendered message
        message = _redact_text(message)

        obj: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": message,
        }

        cid = get_correlation_id()
        if cid:
            obj["cid"] = cid

        if record.exc_info:
            obj["exc"] = self.formatException(record.exc_info)

        # Attach any extra fields the caller passed
        skip = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        for k, v in record.__dict__.items():
            if k not in skip and not k.startswith("_"):
                try:
                    json.dumps(v)
                    obj[k] = v
                except (TypeError, ValueError):
                    obj[k] = str(v)

        return json.dumps(obj, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Log path
# ---------------------------------------------------------------------------

def log_path() -> str:
    p = app_paths.runtime_dir() / "logs" / "app.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_json_mode = str(os.environ.get("CBP_LOG_JSON", "")).strip().lower() in {"1", "true", "yes", "on"}
COMPONENT_LOG_MAX_BYTES = 2 * 1024 * 1024
COMPONENT_LOG_BACKUPS = 3
_component_handlers = {}
_component_handler_lock = threading.Lock()


def _formatter(json_mode: bool) -> logging.Formatter:
    return StructuredJsonFormatter() if json_mode else logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )


class _BoundedLogFormatter(logging.Formatter):
    def __init__(self, *, json_mode: bool):
        super().__init__()
        self.json_mode = json_mode
        self.omitted = '{"msg":"log_record_omitted_size_limit"}' if json_mode else "log_record_omitted_size_limit"

    def format(self, record):
        # No exception text, stack trace, arbitrary extras or correlation data.
        message = _redact_text(record.getMessage())
        name = _redact_text(record.name)
        level = _redact_text(record.levelname)
        stamp = self.formatTime(record)
        if self.json_mode:
            return json.dumps({"ts": stamp, "level": level, "logger": name, "msg": message},
                              ensure_ascii=False)
        return f"{stamp} {level} {name}: {message}"


class _ComponentLogHandler(RotatingFileHandler):
    def _open(self):
        return open(self.baseFilename, "ab")

    def emit(self, record):
        try:
            formatter = self.formatter
            payload = (formatter.format(record) + "\n").encode("utf-8", errors="backslashreplace")
            if len(payload) > self.maxBytes:
                payload = (formatter.omitted + "\n").encode("ascii")
            if len(payload) > self.maxBytes:
                raise ValueError("component_log_limit_too_small")
            if self.stream is None:
                self.stream = self._open()
            self.stream.seek(0, os.SEEK_END)
            if self.stream.tell() + len(payload) > self.maxBytes:
                self.doRollover()
                if self.stream is None:
                    self.stream = self._open()
                self.stream.seek(0, os.SEEK_END)
                if self.stream.tell() + len(payload) > self.maxBytes:
                    raise OSError("component_log_rollover_incomplete")
            if self.stream.write(payload) != len(payload):
                raise OSError("component_log_short_write")
            self.flush()
        except Exception:
            self.handleError(record)

    def handleError(self, _record):
        # logging.Handler.handleError can print the original template and args.
        try:
            sys.stderr.write("component_log_write_failed\n")
        except Exception:
            pass


def _component_handler(component: str):
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,39}", component):
        raise ValueError("invalid_log_component")
    target = app_paths.runtime_dir() / "logs" / f"{component}.bounded.log"
    with _component_handler_lock:
        handler = _component_handlers.get(target)
        if handler is None:
            target.parent.mkdir(parents=True, exist_ok=True)
            # One process owns this component path; its loggers share one writer.
            handler = _ComponentLogHandler(
                target, maxBytes=COMPONENT_LOG_MAX_BYTES, backupCount=COMPONENT_LOG_BACKUPS,
                delay=True,
            )
            handler.setFormatter(_BoundedLogFormatter(json_mode=_json_mode))
            _component_handlers[target] = handler
        return handler


def get_logger(name: str = "cbp") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    component = os.environ.get("CBP_LOG_COMPONENT")
    if component is not None:
        logger.addHandler(_component_handler(component))
        logger.propagate = False
        return logger

    fh = logging.FileHandler(log_path())
    fh.addFilter(RedactingFilter())
    fh.setFormatter(_formatter(_json_mode))
    logger.addHandler(fh)
    return logger


def configure_json_logging(*, enable: bool = True) -> None:
    """Switch all cbp loggers to JSON mode at runtime (e.g. from CLI flag)."""
    global _json_mode
    _json_mode = enable
    fmt = _formatter(enable)
    for name, lgr in logging.Logger.manager.loggerDict.items():
        if isinstance(lgr, logging.Logger):
            for handler in lgr.handlers:
                if isinstance(handler, _ComponentLogHandler):
                    handler.setFormatter(_BoundedLogFormatter(json_mode=enable))
                else:
                    handler.setFormatter(fmt)
