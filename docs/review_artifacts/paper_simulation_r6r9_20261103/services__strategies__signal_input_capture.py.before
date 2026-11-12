"""Opt-in ES signal replay evidence, never an execution authority."""
from __future__ import annotations

import hashlib
import inspect
import json
import logging
import marshal
import os
import platform
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from services.os.app_paths import data_dir

_LOG = logging.getLogger(__name__)


def _encode(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _code_identity() -> dict:
    # Fingerprint loaded functions, not a checkout that may change mid-process.
    from services.strategies import es_daily_trend, strategy_registry

    functions = {
        name: hashlib.sha256(marshal.dumps(fn.__code__)).hexdigest()
        for name, fn in vars(es_daily_trend).items()
        if inspect.isfunction(fn) and fn.__module__ == es_daily_trend.__name__
    }
    functions["registry.compute_signal"] = hashlib.sha256(
        marshal.dumps(strategy_registry.compute_signal.__code__)
    ).hexdigest()
    constants = {
        name: value for name, value in vars(es_daily_trend).items()
        if name.isupper() and isinstance(value, (str, int, float, bool))
    }
    return {"python": platform.python_version(), "functions": functions, "constants": constants}


def _store(payload: dict) -> str:
    raw = _encode(payload)
    digest = hashlib.sha256(raw).hexdigest()
    directory = data_dir() / "signal_inputs"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{digest}.json"
    # Hard-link publication exposes only complete files and never replaces one.
    fd, temporary = tempfile.mkstemp(prefix=".capture-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            if target.is_symlink() or target.read_bytes() != raw:
                raise ValueError("existing_capture_corrupt")
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return digest


def capture_es_inputs(*, strategy: dict, symbol: str, venue: str, ohlcv: list) -> dict:
    """Return evidence fields only. Failure never suppresses a signal."""
    if os.environ.get("CBP_CAPTURE_ES_SIGNAL_INPUTS") != "1":
        return {}
    if strategy.get("name") != "sma_200_trend":
        return {}
    try:
        observed_at = datetime.now(timezone.utc).isoformat()
        extra = strategy.get("evidence_extra") or {}
        payload = {
            "version": 1,
            "scope": "es_signal_only_not_execution_replay",
            "strategy": {
                "name": "sma_200_trend",
                "trade_enabled": bool(strategy.get("trade_enabled", True)),
                "sma_period": int(strategy.get("sma_period", 200)),
                "atr_period": int(strategy.get("atr_period", 20)),
            },
            "symbol": symbol,
            "venue": venue,
            "timeframe": extra.get("ohlcv_timeframe"),
            "source": extra.get("market_data_source", "unknown"),
            "ohlcv": ohlcv,
            "code_identity": _code_identity(),
        }
        digest = _store(payload)
        return {
            "signal_input_capture_status": "captured",
            "signal_input_sha256": digest,
            "signal_input_observed_at": observed_at,
        }
    except Exception as exc:
        # Never persist exception text: it can contain configuration or paths.
        _LOG.warning("signal_input_capture_failed type=%s", type(exc).__name__)
        return {"signal_input_capture_status": "failed", "signal_input_capture_error": type(exc).__name__}


def replay_es_inputs(path: Path, *, expected_sha256: str) -> dict:
    """Verify bytes and loaded code, then recompute without writing evidence."""
    from services.strategies.strategy_registry import compute_signal

    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("signal_input_hash_mismatch")
    payload = json.loads(raw)
    if payload.get("version") != 1 or payload.get("scope") != "es_signal_only_not_execution_replay":
        raise ValueError("unsupported_signal_input_schema")
    if payload["code_identity"] != _code_identity():
        raise ValueError("signal_input_code_mismatch")
    strategy = dict(payload["strategy"], emit_evidence=False)
    if strategy.get("name") != "sma_200_trend":
        raise ValueError("unsupported_signal_input_strategy")
    return compute_signal(cfg={"strategy": strategy}, symbol=payload["symbol"], ohlcv=payload["ohlcv"])
