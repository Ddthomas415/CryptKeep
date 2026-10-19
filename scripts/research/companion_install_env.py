"""Pure encoder for a separately bounded child's Docker --env-file /dev/stdin.

No I/O, subprocesses, pipe opens, logging, or installed-parser verification.
The returned bytes contain credentials: keep them only in the child caller and
pass them through private subprocess stdin. Never log, repr, persist, or return
them to the parent. The parent owns subprocess bounds and lifecycle policy.
"""
from __future__ import annotations

import json
import re

from scripts.research import companion_existing_controller as core

_MAX_BYTES = 65_536
_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*", re.ASCII)
_REQUIRED = frozenset({"SERVICE_TOKEN", "POSTGRES_PASSWORD", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY"})
# Mirror runtime_adapter.ENV_EXPECTED except database identity defaults, which
# must not be injected into applications. Tests bind this independent copy.
_OVERRIDES = {
    "NO_TRADING": "true", "OPENAI_API_KEY": "", "MEMORY_READ_ONLY_STARTUP": "true",
    "AUDIT_SERVICE_URL": "http://audit-log:8009", "MEMORY_SERVICE_URL": "http://memory-retrieval:8007",
    "RISK_SERVICE_URL": "http://risk-stub:8008", "QDRANT_URL": "http://qdrant:6333",
    "MINIO_ENDPOINT": "http://minio:9000", "QDRANT_COLLECTION": "documents", "MINIO_BUCKET": "raw-docs",
    "REQUEST_TIMEOUT_SECONDS": "2", "PYTHONDONTWRITEBYTECODE": "1",
}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("invalid")
        result[key] = value
    return result


def _reject_constant(_value):
    raise ValueError("invalid")


def encode_environment(raw: bytes) -> bytes:
    """Encode one <=65536-byte UTF-8 JSON list, or refuse with a fixed code.

    Keys are ASCII identifiers; values are strict UTF-8 without NUL/CR/LF.
    Values are not shell-quoted, stripped, normalized, or interpolated. Unpaired
    Unicode surrogates and non-UTF-8/BOM JSON are refused rather than repaired.
    Only the returned bytes carry secrets; exceptions have no raw diagnostics.
    """
    if type(raw) is not bytes or not raw or len(raw) > _MAX_BYTES:
        raise core.Refused("install_environment_refused") from None
    try:
        entries = json.loads(raw.decode("utf-8", errors="strict"),
                             object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant)
        if type(entries) is not list:
            raise ValueError("invalid")
        environment = {}
        for entry in entries:
            if type(entry) is not str or any(c in entry for c in "\0\r\n"):
                raise ValueError("invalid")
            key, separator, value = entry.partition("=")
            if not separator or _KEY.fullmatch(key) is None or key in environment:
                raise ValueError("invalid")
            # Validate even fields that will be overridden; no silent repairs.
            value.encode("utf-8", errors="strict")
            environment[key] = value
        if any(not environment.get(key) for key in _REQUIRED):
            raise ValueError("invalid")
        environment.update(_OVERRIDES)
        return "".join(key + "=" + value + "\n" for key, value in environment.items()).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError):
        pass
    # Raise outside the handler so even __context__ cannot retain decoder data.
    raise core.Refused("install_environment_refused") from None


def encode_labels(raw: bytes) -> bytes:
    """Opaque original labels for a private descriptor, never argv/logs/files."""
    try:
        if type(raw) is not bytes or not raw or len(raw) > _MAX_BYTES:
            raise ValueError("invalid")
        labels = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                            parse_constant=_reject_constant)
        if labels is None:
            labels = {}
        if type(labels) is not dict:
            raise ValueError("invalid")
        for key, value in labels.items():
            if (type(key) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]*", key)
                    or type(value) is not str or any(c in value for c in "\0\r\n")):
                raise ValueError("invalid")
            value.encode("utf-8", errors="strict")
        result = "".join(key + "=" + value + "\n" for key, value in labels.items()).encode("utf-8")
        if len(result) > _MAX_BYTES:
            raise ValueError("invalid")
        return result
    except (ValueError, TypeError, UnicodeError, RecursionError):
        pass
    raise core.Refused("install_labels_refused") from None
