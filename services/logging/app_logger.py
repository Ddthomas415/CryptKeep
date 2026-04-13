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
import os
import re
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


def get_logger(name: str = "cbp") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(log_path())
    fh.addFilter(RedactingFilter())

    if _json_mode:
        fh.setFormatter(StructuredJsonFormatter())
    else:
        fh.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ))

    logger.addHandler(fh)
    return logger


def configure_json_logging(*, enable: bool = True) -> None:
    """Switch all cbp loggers to JSON mode at runtime (e.g. from CLI flag)."""
    global _json_mode
    _json_mode = enable
    fmt = StructuredJsonFormatter() if enable else logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    for name, lgr in logging.Logger.manager.loggerDict.items():
        if isinstance(lgr, logging.Logger):
            for handler in lgr.handlers:
                handler.setFormatter(fmt)
