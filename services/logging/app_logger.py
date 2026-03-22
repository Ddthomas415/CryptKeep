from __future__ import annotations

import logging
import re
from services.os import app_paths


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

class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact_text(str(record.msg))
        if record.args:
            record.args = tuple(_redact_text(str(a)) for a in record.args)
        return True

def log_path() -> str:
    p = app_paths.runtime_dir() / "logs" / "app.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)

def get_logger(name: str = "cbp") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path())
    fh.addFilter(RedactingFilter())
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger
