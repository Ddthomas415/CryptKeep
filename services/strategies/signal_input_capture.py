"""Opt-in ES signal replay evidence, never an execution authority."""
from __future__ import annotations

import hashlib
import inspect
import json
import logging
import marshal
import os
import platform
import re
import subprocess
import tempfile
import types
from functools import lru_cache
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


def _store(payload: dict, *, directory: Path | None = None) -> str:
    raw = _encode(payload)
    digest = hashlib.sha256(raw).hexdigest()
    directory = data_dir() / "signal_inputs" if directory is None else Path(directory)
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


# Runner v2 is deliberately separate from the frozen ES v1 format above.
_DEFAULT_TRIO = {"ema_cross", "breakout_donchian", "mean_reversion_rsi"}
_STRATEGY_KEYS = frozenset("""
name trade_enabled ema_fast ema_slow filter_window min_volatility_pct
min_volume_ratio min_trend_efficiency min_cross_gap_pct rsi_len rsi_buy rsi_sell
sma_len max_volatility_pct max_trend_efficiency max_sma_distance_pct
require_reversal_confirmation donchian_len min_channel_width_pct breakout_buffer_pct
require_directional_confirmation sma_period atr_period
""".split())
_RUNNER_KEYS = frozenset("""
enabled strategy_id strategy_preset venue symbol symbols fast_n slow_n min_bars
max_bars loop_interval_sec qty order_type allow_first_signal_trade position_aware
sell_full_position signal_source stop_loss_pct take_profit_pct trailing_stop_pct
max_bars_hold min_volatility_pct min_trend_efficiency min_cross_gap_pct
ema_invalidate_on_low_vol ema_invalidate_on_chop ema_invalidate_on_cross_gap_loss
timeframe ohlcv_timeframe window use_ccxt_fallback max_tick_age_sec
auto_select_best_venue switch_only_when_blocked venue_candidates
max_concurrent_positions max_symbol_exposure_pct max_total_exposure_pct
max_strategy_exposure_pct max_open_intents_per_symbol max_adds_per_symbol
min_profit_to_add_pct scale_in_size_multiplier kill_cooldown_loops
max_consecutive_risk_blocks_per_symbol
""".split())
_IND_KEYS = frozenset("""
ema_fast ema_slow avg_range_pct volume_ratio trend_efficiency cross_gap_pct
upper_prev lower_prev close rsi sma sma_distance_pct channel_width_pct price
current_price last_price
""".split())
_SIGNAL_KEYS = frozenset("ok action reason strategy symbol price ind raw_action raw_reason".split())
_PUBLIC_KEYS = frozenset("""
action changed exit_action exit_reason exit_out conditions decision warmed last_action
strategy_id allow_first_signal_trade symbol write_warm
write_warmed write_last_action note reason ok eligible enabled triggered evaluated
applicable active met value threshold observed selected stack_rule entry_price
current_price price qty side strategy pnl_pct pnl_abs bars_held max_bars_hold
stop_loss_pct take_profit_pct trailing_stop_pct trailing_peak_price stop_price
take_profit_price trailing_stop_price raw_action raw_reason signal_action
signal_reason filtered_action filtered_reason intended_action outcome gates
intent_id intentid error_type position_qty pos_qty matched threshold_price
move_pct peak_price cooldown risk performance market_quality preflight startup
intent_pending duplicate kill scale_in queue_write emission pending_exit
ema_low_vol ema_chop ema_cross_gap stop trailing take_profit time strategy_sell pre_filter_sell
observation_error observation_errors
scaling cooldown_protective_exit open_intent_lookup remaining_loops
kill_until_loop loops exposure total_exposure symbol_exposure max_exposure
max_symbol_exposure open_positions max_open_positions notional proposed_notional
current_notional projected_notional max_position_notional max_total_notional
scale_count max_scales max_scale_ins current_qty proposed_qty total_notional
is_scale size_multiplier cooldown_loops
""".split())
_SAFE_ERRORS = {"ValueError", "TypeError", "OSError", "RuntimeError", "KeyError",
                "OverflowError", "TimeoutError", "PermissionError", "FileNotFoundError"}
_NUMERIC_SETTINGS = (_STRATEGY_KEYS | _RUNNER_KEYS) - frozenset("""
name strategy_id strategy_preset venue symbol symbols order_type signal_source
timeframe ohlcv_timeframe venue_candidates enabled trade_enabled
allow_first_signal_trade position_aware sell_full_position use_ccxt_fallback
auto_select_best_venue switch_only_when_blocked require_reversal_confirmation
require_directional_confirmation ema_invalidate_on_low_vol ema_invalidate_on_chop
ema_invalidate_on_cross_gap_loss
""".split())
_BOOL_SETTINGS = frozenset("""
enabled trade_enabled allow_first_signal_trade position_aware sell_full_position
use_ccxt_fallback auto_select_best_venue switch_only_when_blocked
require_reversal_confirmation require_directional_confirmation
ema_invalidate_on_low_vol ema_invalidate_on_chop ema_invalidate_on_cross_gap_loss
""".split())


def runner_capture_enabled() -> bool:
    return os.environ.get("CBP_CAPTURE_RUNNER_DECISIONS") == "1"


def _number(value):
    import math

    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("invalid_number")
    return value


def _tag(value, *, nullable=False):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:/+\-]{1,160}", value):
        raise ValueError("invalid_public_tag")
    return value


def _settings(value, keys):
    if not isinstance(value, dict):
        raise ValueError("invalid_settings")
    result = {}
    for key in sorted(keys & value.keys()):
        item = value[key]
        if item is None:
            result[key] = None
        elif key in _BOOL_SETTINGS:
            if type(item) is not bool:
                raise ValueError("invalid_setting_boolean")
            result[key] = item
        elif key in _NUMERIC_SETTINGS:
            result[key] = _number(item)
        elif key in {"symbols", "venue_candidates"}:
            if not isinstance(item, list):
                raise ValueError("invalid_setting_list")
            result[key] = [_tag(v) for v in item]
        else:
            result[key] = _tag(item)
    if "strategy" in value and keys == _RUNNER_KEYS:
        result["strategy"] = _settings(value["strategy"], _STRATEGY_KEYS)
    if "risk" in value and keys == _RUNNER_KEYS:
        result["risk"] = _settings(value["risk"], frozenset({
            "stop_loss_pct", "take_profit_pct", "trailing_stop_pct", "max_bars_hold",
            "max_concurrent_positions", "max_symbol_exposure_pct", "max_total_exposure_pct",
            "max_strategy_exposure_pct", "max_open_intents_per_symbol", "max_adds_per_symbol",
            "min_profit_to_add_pct", "scale_in_size_multiplier", "kill_cooldown_loops",
            "max_consecutive_risk_blocks_per_symbol"}))
    return result


def _public(value, *, depth=0):
    if depth > 12:
        raise ValueError("public_value_too_deep")
    if value is None or type(value) is bool:
        return value
    if type(value) in (int, float):
        return _number(value)
    if isinstance(value, str):
        return _tag(value)
    if isinstance(value, list):
        return [_public(v, depth=depth + 1) for v in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key not in _PUBLIC_KEYS:
                continue
            if key == "error_type":
                result[key] = item if item in _SAFE_ERRORS else "Error"
            else:
                result[key] = _public(item, depth=depth + 1)
        return result
    raise ValueError("invalid_public_value")


def _signal(value):
    if not isinstance(value, dict):
        raise ValueError("invalid_signal")
    for key in ("action", "raw_action"):
        if key in value and value[key] not in {"buy", "sell", "hold"}:
            raise ValueError("invalid_signal_action")
    if "ok" in value and type(value["ok"]) is not bool:
        raise ValueError("invalid_signal_boolean")
    if "price" in value:
        _number(value["price"])
    for key in ("reason", "raw_reason", "strategy", "symbol"):
        if key in value:
            _tag(value[key])
    out = _public({k: v for k, v in value.items() if k in _SIGNAL_KEYS and k != "ind"})
    if "ind" in value:
        if not isinstance(value["ind"], dict):
            raise ValueError("invalid_indicators")
        out["ind"] = {k: _number(v) for k, v in value["ind"].items() if k in _IND_KEYS}
    return out


@lru_cache(maxsize=1)
def _runner_commit_identity():
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2, check=True,
            env={"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
        )
        commit = proc.stdout.decode("ascii").strip()
        return commit if re.fullmatch(r"[0-9a-f]{40,64}", commit) else None
    except Exception:
        return None


def _fingerprint_value(value, seen=None):
    """Hash loaded objects including aliases/defaults, without serializing their text."""
    seen = set() if seen is None else seen
    if value is None or value is Ellipsis or type(value) in (str, int, float, bool, bytes, complex):
        # marshal records interning/object sharing, not just equal code content.
        scalar = (value.hex() if type(value) in (float, bytes) else
                  [value.real.hex(), value.imag.hex()] if type(value) is complex else
                  str(value) if type(value) is int else
                  "ellipsis" if value is Ellipsis else value)
        return hashlib.sha256(_encode({"type": type(value).__name__, "value": scalar})).hexdigest()
    if id(value) in seen:
        return {"cycle": getattr(value, "__qualname__", type(value).__qualname__)}
    seen = seen | {id(value)}
    if isinstance(value, types.CodeType):
        fields = {name: getattr(value, name) for name in (
            "co_argcount", "co_posonlyargcount", "co_kwonlyargcount", "co_nlocals", "co_stacksize",
            "co_flags", "co_filename", "co_name", "co_qualname", "co_firstlineno")}
        fields.update(bytecode=value.co_code.hex(), line_table=value.co_linetable.hex(),
                      exception_table=value.co_exceptiontable.hex(),
                      constants=_fingerprint_value(value.co_consts, seen),
                      names=list(value.co_names), varnames=list(value.co_varnames),
                      freevars=list(value.co_freevars), cellvars=list(value.co_cellvars))
        return hashlib.sha256(_encode(fields)).hexdigest()
    if inspect.isfunction(value):
        return {
            "code": _fingerprint_value(value.__code__, seen),
            "defaults": _fingerprint_value(value.__defaults__, seen),
            "kwdefaults": _fingerprint_value(value.__kwdefaults__, seen),
            "closure": [_fingerprint_value(c.cell_contents, seen) for c in (value.__closure__ or ())],
        }
    if isinstance(value, (staticmethod, classmethod)):
        return _fingerprint_value(value.__func__, seen)
    if isinstance(value, property):
        return [_fingerprint_value(v, seen) for v in (value.fget, value.fset, value.fdel)]
    if isinstance(value, dict):
        return {str(k): _fingerprint_value(v, seen) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return {"type": type(value).__name__, "values": [_fingerprint_value(v, seen) for v in value]}
    if isinstance(value, (set, frozenset)):
        return sorted((_fingerprint_value(v, seen) for v in value), key=lambda v: _encode(v))
    if inspect.isclass(value) and value.__module__.startswith(("services.", "storage.")):
        return {k: _fingerprint_value(v, seen) for k, v in sorted(vars(value).items())
                if k not in {"__dict__", "__weakref__", "__doc__", "__module__"}}
    return {"type": type(value).__qualname__, "module": getattr(value, "__module__", None),
            "name": getattr(value, "__qualname__", None)}


_RUNNER_BINDING_NAMES = (
    "run_forever", "_strategy_signal", "_registry_signal_with_context", "_synth_ohlcv",
    "_position_aware_signal_action", "position_aware_signal_action", "signal_transition",
    "select_exit_decision", "evaluate_strategy_exit_stack", "compute_signal",
    "PaperExitAccounting", "make_event", "scope_for", "assess_hourly_candles", "observe_paper_quote",
)


def _runner_code_identity(*, runner_bindings=None):
    import importlib

    names = ("services.strategies.ema_cross", "services.strategies.breakout_donchian",
             "services.strategies.mean_reversion_rsi", "services.strategies.strategy_registry",
             "services.strategies.market_filters", "services.strategies.indicators",
             "services.execution.runner_decision", "services.risk.exit_controls",
             "services.execution.paper_exit_accounting", "storage.exit_event_journal",
             "services.market_data.hourly_candle_quality", "services.market_data.paper_snapshot_quote")
    modules = {}
    for name in names:
        module = importlib.import_module(name)
        modules[name] = {k: _fingerprint_value(v) for k, v in sorted(vars(module).items())
                         if not k.startswith("__") and not isinstance(v, types.ModuleType)}
    runner = importlib.import_module("services.execution.strategy_runner")
    if runner_bindings is None:
        runner_bindings = {name: getattr(runner, name) for name in _RUNNER_BINDING_NAMES}
    if not isinstance(runner_bindings, dict) or set(runner_bindings) != set(_RUNNER_BINDING_NAMES):
        raise ValueError("invalid_runner_bindings")
    modules[runner.__name__] = {name: _fingerprint_value(runner_bindings[name])
                              for name in _RUNNER_BINDING_NAMES}
    return {"version": 2, "type": "runner_code", "python": platform.python_version(),
            "implementation": platform.python_implementation(), "modules": modules}


def _runner_store(payload):
    raw = _encode(payload)
    digest = hashlib.sha256(raw).hexdigest()
    directory = _runner_object_directory()
    target = directory / f"{digest}.json"
    if target.exists() or target.is_symlink():
        if target.is_symlink() or target.read_bytes() != raw:
            raise ValueError("existing_capture_corrupt")
        return digest
    return _store(payload, directory=directory)


def _runner_object_directory():
    configured = os.environ.get("CBP_RUNNER_DECISION_OBJECT_DIR")
    if not configured:
        return data_dir() / "signal_inputs"
    directory = Path(configured)
    if not directory.is_absolute():
        raise ValueError("shared_object_directory_not_absolute")
    return directory


def _checked_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate_json_key")
            out[key] = value
        return out

    def invalid(_value):
        raise ValueError("nonfinite_json")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def _digest(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("invalid_digest")
    return value


def _verify_envelope(envelope):
    if not isinstance(envelope, dict) or not isinstance(envelope.get("payload"), dict):
        raise ValueError("invalid_envelope")
    if hashlib.sha256(_encode(envelope["payload"])).hexdigest() != _digest(envelope.get("sha256")):
        raise ValueError("runner_record_hash_mismatch")
    if envelope["payload"].get("version") != 2:
        raise ValueError("unsupported_runner_schema")
    return envelope["payload"]


def _observed(value):
    if not isinstance(value, str):
        raise ValueError("invalid_observed_at")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("observed_at_not_utc")
    return stamp


def _bar_layout(rows, observed, runner):
    if not isinstance(rows, list):
        raise ValueError("invalid_ohlcv")
    timeframe = runner.get("ohlcv_timeframe", runner.get("timeframe"))
    match = re.fullmatch(r"([1-9][0-9]*)([smhdw])", timeframe or "")
    duration = int(match[1]) * {"s": 1000, "m": 60000, "h": 3600000,
                               "d": 86400000, "w": 604800000}[match[2]] if match else None
    layout, completed = [], []
    for row in rows:
        if not isinstance(row, list) or len(row) < 6:
            raise ValueError("invalid_ohlcv_row")
        for number in row:
            _number(number)
        complete = duration is not None and row[0] + duration <= observed.timestamp() * 1000
        if complete:
            completed.append({"version": 2, "type": "completed_bar", "row": row})
            layout.append({"complete": True, "timestamp": row[0], "index": len(completed) - 1})
        else:
            layout.append({"complete": False, "timestamp": row[0], "row": row})
    return layout, completed


def _project_quote_quality(quality):
    from services.market_data.paper_snapshot_quote import QUOTE_REASONS, QUOTE_SOURCES, MAX_UTC_MS

    if not isinstance(quality, dict):
        return None
    reason, source = quality.get("reason"), quality.get("source")
    if type(reason) is not str or reason not in QUOTE_REASONS:
        return None
    out = {"ok": reason == "ok", "reason": reason,
           "source": source if type(source) is str and source in QUOTE_SOURCES else "unknown"}
    for key in ("bid_present", "ask_present", "zero_price", "invalid_price"):
        value = quality.get(key)
        out[key] = value if type(value) is bool else None
    for key in ("quote_age_ms", "snapshot_age_ms"):
        value = quality.get(key)
        out[key] = value if type(value) in (int, float) and -MAX_UTC_MS <= value <= MAX_UTC_MS else None
    return out


def _project_record(record):
    if not isinstance(record, dict) or type(record.get("version")) is not int or record["version"] != 2:
        raise ValueError("unsupported_runner_schema")
    session = record.get("session_id")
    account = record.get("account_id")
    if account is None:
        account = hashlib.sha256(str(data_dir().resolve()).encode()).hexdigest()
    if not isinstance(session, str) or not re.fullmatch(r"[0-9a-f]{32}", session):
        raise ValueError("invalid_session_id")
    if not isinstance(account, str) or not re.fullmatch(r"[0-9a-f]{32,64}", account):
        raise ValueError("invalid_account_id")
    if type(record.get("loop")) is not int or record["loop"] < 0:
        raise ValueError("invalid_loop")
    if record.get("kind") not in {"decision", "skipped", "error"}:
        raise ValueError("invalid_kind")
    if type(record.get("signal_computed")) is not bool:
        raise ValueError("invalid_signal_computed")
    _observed(record.get("observed_at"))
    settings = record.get("settings")
    if not isinstance(settings, dict) or not {"runner", "strategy"} <= settings.keys():
        raise ValueError("missing_settings")
    out = {key: record[key] for key in ("version", "session_id", "account_id", "loop", "kind",
                                      "observed_at", "signal_computed") if key != "account_id"}
    out["account_id"] = account
    out["timeframe"] = _tag(record.get("timeframe"), nullable=True)
    for key in ("symbol", "venue", "pipeline_stage"):
        out[key] = _tag(record.get(key))
    out["reason"] = _tag(record.get("reason", "not_evaluated"), nullable=True)
    if isinstance(record.get("candle_quality"), dict):
        out["candle_quality"] = {key: _public(value) for key, value in record["candle_quality"].items()
            if key in {"ok", "reason", "policy_version", "timeframe", "checked_epoch",
                       "last_candle_open_ms", "last_candle_complete", "missing_hours",
                       "current_hour_present", "window_hours"}}
    quote_quality = _project_quote_quality(record.get("quote_quality"))
    if quote_quality is not None:
        out["quote_quality"] = quote_quality
    for key in ("observation_error", "error_type"):
        if key in record:
            out[key] = record[key] if record[key] in _SAFE_ERRORS else "Error"
    out["settings"] = {"runner": _settings(settings["runner"], _RUNNER_KEYS),
                       "strategy": _settings(settings["strategy"], _STRATEGY_KEYS)}
    out["raw_signal"] = _signal(record.get("raw_signal", {}))
    out["signal"] = _signal(record.get("signal", {}))
    transition = record.get("transition_inputs", {})
    exits = record.get("exit_inputs", {})
    if not isinstance(transition, dict) or not isinstance(exits, dict):
        raise ValueError("invalid_decision_inputs")
    for group in (transition, exits):
        for key in ("pos_qty", "entry_price", "trailing_peak_price", "bars_held", "current_price"):
            if key in group:
                _number(group[key])
        for key in ("changed", "warmed", "allow_first_signal_trade"):
            if key in group and type(group[key]) is not bool:
                raise ValueError("invalid_input_boolean")
    if record["kind"] == "decision":
        if not {"strategy_id", "decision", "pos_qty", "warmed", "last_action", "allow_first_signal_trade"} <= transition.keys():
            raise ValueError("incomplete_transition_inputs")
        if not {"cfg", "signal", "decision", "changed", "pos_qty", "entry_price", "trailing_peak_price", "bars_held", "current_price"} <= exits.keys():
            raise ValueError("incomplete_exit_inputs")
        if not {"transition", "exit"} <= record.get("decision", {}).keys():
            raise ValueError("incomplete_decision")
    out["transition_inputs"] = _public({k: v for k, v in transition.items() if k in {
        "strategy_id", "decision", "pos_qty", "warmed", "last_action", "allow_first_signal_trade"}})
    # The input schema is fixed; no config extras can enter through exit inputs.
    for key in ("strategy_id", "allow_first_signal_trade"):
        if key in transition:
            out["transition_inputs"][key] = (_tag(transition[key]) if key == "strategy_id"
                                              else transition[key])
    out["exit_inputs"] = {}
    for key in ("decision", "changed", "pos_qty", "entry_price", "trailing_peak_price", "bars_held", "current_price"):
        if key in exits:
            out["exit_inputs"][key] = _public(exits[key])
    if "cfg" in exits:
        out["exit_inputs"]["cfg"] = _settings(exits["cfg"], _RUNNER_KEYS)
    if "signal" in exits:
        out["exit_inputs"]["signal"] = _signal(exits["signal"])
    decision = record.get("decision", {})
    if not isinstance(decision, dict):
        raise ValueError("invalid_decision")
    out["decision"] = {k: _public(decision[k]) for k in ("transition", "exit") if k in decision}
    if not isinstance(record.get("actual", {}), dict):
        raise ValueError("invalid_actual")
    out["actual"] = _public(record.get("actual", {}))
    return out


def _append_runner(path, envelope):
    import fcntl

    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        size = os.fstat(fd).st_size
        if size:
            if os.pread(fd, 1, size - 1) != b"\n":
                raise ValueError("partial_journal_tail")
        line = _encode(envelope) + b"\n"
        if os.write(fd, line) != len(line):
            raise OSError("incomplete_journal_append")
        os.fsync(fd)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        os.close(fd)


def _retain_candle_capture_diagnostic(record, error_type):
    """Retain a non-replayable observation, never the invalid inputs or decision."""
    if not isinstance(record, dict) or type(record.get("version")) is not int or record["version"] != 2:
        return {}
    quality = record.get("candle_quality")
    if not isinstance(quality, dict) or quality.get("ok") is not False:
        return {}
    reason = quality.get("reason")
    policy_version = quality.get("policy_version")
    if (type(reason) is not str or reason not in {
            "invalid_candles", "invalid_clock", "no_candles",
            "current_hour_stale", "missing_hours", "invalid_ohlcv",
    } or type(policy_version) is not int or policy_version != 1
            or quality.get("timeframe") != "1h" or record.get("timeframe") != "1h"):
        return {}
    try:
        session = record.get("session_id")
        account = record.get("account_id")
        if account is None:
            account = hashlib.sha256(str(data_dir().resolve()).encode()).hexdigest()
        loop = record.get("loop")
        if (type(session) is not str or not re.fullmatch(r"[0-9a-f]{32}", session)
                or type(account) is not str or not re.fullmatch(r"[0-9a-f]{32,64}", account)
                or type(loop) is not int or loop < 0):
            return {}
        observed = _observed(record.get("observed_at"))
        symbol = _tag(record.get("symbol"))
        venue = _tag(record.get("venue"))
    except (ValueError, TypeError, OverflowError):
        return {}
    # Projection can fail before examining the bars. Require a separate raw-bar
    # failure before attributing any part of the failed capture to candle inputs.
    try:
        _bar_layout(record.get("ohlcv"), observed, {"timeframe": "1h"})
    except (ValueError, TypeError, OverflowError):
        pass
    else:
        return {}
    source = record.get("observed_ohlcv_source")
    if type(source) is not str or source not in {"public_ohlcv", "sample_ohlcv"}:
        source = "unknown"
    payload = {
        "version": 1, "type": "candle_capture_diagnostic", "account_id": account,
        "session_id": session, "loop": loop, "venue": venue, "symbol": symbol,
        "timeframe": "1h", "observed_at": observed.isoformat(), "reason": reason,
        "policy_version": policy_version, "capture_error_type": error_type, "source": source,
    }
    quote_quality = _project_quote_quality(record.get("quote_quality"))
    if quote_quality is not None:
        payload["quote_quality"] = quote_quality
    relative = Path("runner_candle_diagnostics") / account / f"{session}.jsonl"
    digest = hashlib.sha256(_encode(payload)).hexdigest()
    _append_runner(data_dir() / relative, {"sha256": digest, "payload": payload})
    return {"diagnostic_status": "captured", "diagnostic_relativepath": str(relative),
            "diagnostic_sha256": digest}


def capture_runner_decision(record, *, runner_bindings=None) -> dict:
    """Append one sanitized receipt. Capture failure is never trading authority."""
    if not runner_capture_enabled():
        return {"ok": True, "status": "disabled"}
    validating = True
    try:
        payload = _project_record(record)
        bar_settings = dict(payload["settings"]["runner"])
        if payload["timeframe"] is not None:
            bar_settings["ohlcv_timeframe"] = payload["timeframe"]
        layout, completed = _bar_layout(record.get("ohlcv"), _observed(payload["observed_at"]), bar_settings)
        validating = False
        settings = payload.pop("settings")
        payload["settings_sha256"] = _runner_store({"version": 2, "type": "runner_settings", **settings})
        payload["code_sha256"] = _runner_store(_runner_code_identity(runner_bindings=runner_bindings))
        payload["commit"] = _runner_commit_identity()
        shared = bool(os.environ.get("CBP_RUNNER_DECISION_OBJECT_DIR"))
        payload["object_scope"] = "shared" if shared else "local"
        refs = [_runner_store(bar) for bar in completed]
        payload["completed_prefix_sha256"] = _runner_store({
            "version": 2, "type": "completed_prefix", "bar_refs": refs})
        payload["ohlcv"] = layout
        envelope = {"sha256": hashlib.sha256(_encode(payload)).hexdigest(), "payload": payload}
        relative = Path("runner_decisions") / payload["account_id"] / f"{payload['session_id']}.jsonl"
        _append_runner(data_dir() / relative, envelope)
        return {"ok": True, "status": "captured", "sha256": envelope["sha256"],
                "relativepath": str(relative), "object_directory": None if shared else "signal_inputs",
                "shared_objects": shared}
    except Exception as exc:
        error_type = type(exc).__name__ if type(exc).__name__ in _SAFE_ERRORS else "Error"
        failure = {"ok": False, "status": "failed", "error_type": error_type}
        if validating and isinstance(exc, (ValueError, TypeError, OverflowError)):
            try:
                failure.update(_retain_candle_capture_diagnostic(record, error_type))
            except Exception:
                failure["diagnostic_status"] = "failed"
        return failure


def iter_runner_records(path, *, expected_sha256=None, object_directory=None):
    """Stream verified envelopes; a trailing partial write is never repaired."""
    path = Path(path)
    import fcntl

    objects = Path(object_directory) if object_directory is not None else path.parent.parent.parent / "signal_inputs"
    count = 0
    with path.open("rb") as source:
        fcntl.flock(source.fileno(), fcntl.LOCK_SH)
        if expected_sha256 is not None:
            _digest(expected_sha256)
            digest = hashlib.sha256()
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
            if digest.hexdigest() != expected_sha256:
                raise ValueError("runner_journal_hash_mismatch")
            source.seek(0)
        for line in source:
            if not line.endswith(b"\n"):
                raise ValueError("partial_journal_tail")
            envelope = _checked_json(line)
            _verify_envelope(envelope)
            if object_directory is not None or envelope["payload"].get("object_scope") == "local":
                envelope["object_directory"] = str(objects)
            count += 1
            yield envelope
    if not count:
        raise ValueError("empty_runner_journal")


def read_runner_records(path, *, expected_sha256=None) -> list:
    return list(iter_runner_records(path, expected_sha256=expected_sha256))


def _load_runner_object(directory, digest, kind):
    path = directory / f"{_digest(digest)}.json"
    if path.is_symlink():
        raise ValueError("symlink_runner_object")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("runner_object_hash_mismatch")
    value = _checked_json(raw)
    if not isinstance(value, dict) or value.get("version") != 2 or value.get("type") != kind:
        raise ValueError("invalid_runner_object")
    return value


def replay_runner_decision(envelope, *, object_directory=None) -> dict:
    """Offline decision proof, never an order/fill replay or a profit claim."""
    from services.execution.runner_decision import (
        position_aware_signal_action, select_exit_decision, signal_transition,
    )
    from services.strategies.strategy_registry import compute_signal

    payload = _verify_envelope(envelope)
    if payload.get("observation_error"):
        raise ValueError("runner_observation_incomplete")
    directory = object_directory if object_directory is not None else envelope.get("object_directory")
    if directory is None:
        raise ValueError("missing_object_directory")
    directory = Path(directory)
    code = _load_runner_object(directory, payload.get("code_sha256"), "runner_code")
    if code != _runner_code_identity():
        raise ValueError("runner_code_mismatch")
    settings = _load_runner_object(directory, payload.get("settings_sha256"), "runner_settings")
    prefix = _load_runner_object(directory, payload.get("completed_prefix_sha256"), "completed_prefix")
    bars = [_load_runner_object(directory, ref, "completed_bar")["row"] for ref in prefix["bar_refs"]]
    rows = []
    for slot in payload.get("ohlcv", []):
        if type(slot.get("complete")) is not bool:
            raise ValueError("invalid_bar_completion")
        if slot["complete"]:
            if type(slot.get("index")) is not int or not 0 <= slot["index"] < len(bars):
                raise ValueError("invalid_bar_index")
            row = bars[slot["index"]]
        else:
            row = slot["row"]
        if row[0] != slot["timestamp"]:
            raise ValueError("bar_timestamp_mismatch")
        rows.append(row)
    record = dict(payload, settings={k: settings[k] for k in ("runner", "strategy")}, ohlcv=rows)
    projected = _project_record(record)
    for key, value in projected.items():
        if key != "settings" and payload.get(key) != value:
            raise ValueError("noncanonical_runner_record")
    bar_settings = dict(settings["runner"])
    if payload.get("timeframe") is not None:
        bar_settings["ohlcv_timeframe"] = payload["timeframe"]
    layout, _ = _bar_layout(rows, _observed(payload["observed_at"]), bar_settings)
    if layout != payload["ohlcv"]:
        raise ValueError("bar_layout_mismatch")
    if settings["runner"] != _settings(settings["runner"], _RUNNER_KEYS) or settings["strategy"] != _settings(settings["strategy"], _STRATEGY_KEYS):
        raise ValueError("noncanonical_settings")
    if payload["kind"] != "decision":
        return {"status": "diagnostic_verified", "sha256": envelope["sha256"],
                "kind": payload["kind"], "recomputed": False, "decision_match": None,
                "signal_recomputed": False,
                "reason": "signal_not_computed" if not payload["signal_computed"] else "nondecision_record"}
    if payload["signal_computed"] and settings["strategy"].get("name", "ema_cross") not in _DEFAULT_TRIO:
        raise ValueError("unsupported_runner_replay_strategy")
    observed_raw = {}

    def observe(*args, **fields):
        if args:
            if len(args) != 1 or not isinstance(args[0], dict):
                raise ValueError("invalid_observer_payload")
            observed_raw.update(args[0])
        observed_raw.update(fields)

    if payload["signal_computed"]:
        signal = compute_signal(cfg={"strategy": settings["strategy"]}, symbol=payload["symbol"],
                                ohlcv=rows, observer=observe)
    else:
        signal = {"ok": True, "action": "hold", "reason": "no_signal"}
    signal = _signal(signal)
    raw = _signal(observed_raw)
    transition_inputs = payload["transition_inputs"]
    expected_decision = position_aware_signal_action(
        signal, strategy_id=transition_inputs["strategy_id"], position_qty=transition_inputs["pos_qty"])
    transition = signal_transition(**dict(transition_inputs, decision=expected_decision))
    exit_inputs = dict(payload["exit_inputs"], signal=signal, decision=expected_decision,
                       changed=transition["changed"])
    exits = select_exit_decision(**exit_inputs, observe=True, raw_signal=raw)
    if exits.get("observation_error") or exits.get("observation_errors"):
        raise ValueError("runner_observation_error")
    matches = {
        "signal": signal == payload["signal"], "raw_signal": raw == payload["raw_signal"],
        "transition_inputs": transition_inputs.get("decision") == expected_decision,
        "exit_inputs": payload["exit_inputs"].get("signal") == signal
            and payload["exit_inputs"].get("decision") == expected_decision
            and payload["exit_inputs"].get("changed") == transition["changed"]
            and payload["exit_inputs"].get("cfg") == settings["runner"],
        "transition": _public(transition) == payload["decision"].get("transition"),
        "exit": _public(exits) == payload["decision"].get("exit"),
        "intended_action": payload["actual"].get("intended_action") == exits["action"],
    }
    return {"status": "decision_match" if all(matches.values()) else "decision_mismatch",
            "sha256": envelope["sha256"], "kind": payload["kind"], "recomputed": True,
            "signal_recomputed": payload["signal_computed"],
            "reason": "signal_computed" if payload["signal_computed"] else "default_no_signal_replayed",
            "decision_match": all(matches.values()), "matches": matches}
