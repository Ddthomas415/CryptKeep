from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from services.control.promotion_thresholds import PAPER_MIN_DAYS, PAPER_MIN_ROUND_TRIPS

LEGACY_POLICY_ID = "legacy_round_trip_v1"
SLOW_DAILY_POLICY_ID = "slow_daily_single_symbol_v1"
INTRADAY_POLICY_ID = "intraday_single_symbol_v1"
CONTEXT_EDGE_POLICY_ID = "context_edge_v1"


@dataclass(frozen=True)
class PaperPromotionPolicy:
    policy_id: str
    min_calendar_days: int
    min_qualified_round_trips: int
    min_qualified_bars: int = 0
    cohort_start: str | None = None
    cohort_start_dt: datetime | None = None
    require_archive_walk_forward: bool = False
    require_manual_review: bool = True
    legacy_evidence_policy: str = "diagnostic_only"
    valid: bool = True
    invalid_reasons: tuple[str, ...] = ()
    qualified_bar: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "min_calendar_days": self.min_calendar_days,
            "min_qualified_round_trips": self.min_qualified_round_trips,
            "min_qualified_bars": self.min_qualified_bars,
            "cohort_start": self.cohort_start,
            "require_archive_walk_forward": self.require_archive_walk_forward,
            "require_manual_review": self.require_manual_review,
            "legacy_evidence_policy": self.legacy_evidence_policy,
            "valid": self.valid,
            "invalid_reasons": list(self.invalid_reasons),
            "qualified_bar": dict(self.qualified_bar or {}),
        }


def _nested_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _parse_ts(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _configured_contract(config: dict[str, Any]) -> dict[str, str]:
    strategy = _nested_dict(config.get("strategy"))
    signal = _nested_dict(strategy.get("signal"))
    timeframe = str(signal.get("timeframe") or "").strip().lower()
    configured_source = str(config.get("signal_source") or "").strip().lower()
    suffix = f"_{timeframe}" if timeframe else ""
    source = (
        configured_source[: -len(suffix)]
        if suffix and configured_source.endswith(suffix)
        else configured_source
    )
    return {
        "source": source,
        "timeframe": timeframe,
        "venue": str(strategy.get("venue") or "").strip().lower(),
        "symbol": str(strategy.get("symbol") or "").strip().upper(),
    }


def _policy_defaults(policy_id: str) -> dict[str, Any] | None:
    if policy_id == LEGACY_POLICY_ID:
        return {
            "min_calendar_days": PAPER_MIN_DAYS,
            "min_qualified_round_trips": PAPER_MIN_ROUND_TRIPS,
            "min_qualified_bars": 0,
            "require_archive_walk_forward": False,
            "require_manual_review": True,
        }
    if policy_id == SLOW_DAILY_POLICY_ID:
        return {
            "min_calendar_days": 45,
            "min_qualified_round_trips": 5,
            "min_qualified_bars": 60,
            "require_archive_walk_forward": True,
            "require_manual_review": True,
        }
    if policy_id == INTRADAY_POLICY_ID:
        return {
            "min_calendar_days": PAPER_MIN_DAYS,
            "min_qualified_round_trips": PAPER_MIN_ROUND_TRIPS,
            "min_qualified_bars": 0,
            "require_archive_walk_forward": True,
            "require_manual_review": True,
        }
    if policy_id == CONTEXT_EDGE_POLICY_ID:
        return {
            "min_calendar_days": PAPER_MIN_DAYS,
            "min_qualified_round_trips": PAPER_MIN_ROUND_TRIPS,
            "min_qualified_bars": 0,
            "require_archive_walk_forward": True,
            "require_manual_review": True,
        }
    return None


def _int_at_least(
    value: Any,
    *,
    default: int,
    floor: int,
    field: str,
    invalid: list[str],
) -> int:
    try:
        out = int(value)
    except Exception:
        invalid.append(f"invalid_{field}")
        return int(default)
    if out < floor:
        invalid.append(f"{field}_below_floor")
        return int(floor)
    return int(out)


def resolve_paper_promotion_policy(config: dict[str, Any]) -> PaperPromotionPolicy:
    promotion = _nested_dict(config.get("promotion"))
    paper = _nested_dict(promotion.get("paper"))
    raw_policy = paper.get("policy")
    explicit_policy = isinstance(raw_policy, dict)
    policy_cfg = _nested_dict(raw_policy)
    policy_id = str(policy_cfg.get("id") or LEGACY_POLICY_ID).strip()
    defaults = _policy_defaults(policy_id)
    invalid: list[str] = []
    if defaults is None:
        invalid.append(f"unknown_policy_id:{policy_id}")
        policy_id = LEGACY_POLICY_ID
        defaults = _policy_defaults(policy_id) or {}

    if explicit_policy:
        days_raw = policy_cfg.get("min_calendar_days", defaults["min_calendar_days"])
        trips_raw = policy_cfg.get("min_qualified_round_trips", defaults["min_qualified_round_trips"])
        bars_raw = policy_cfg.get("min_qualified_bars", defaults["min_qualified_bars"])
    else:
        days_raw = paper.get("min_days", PAPER_MIN_DAYS)
        trips_raw = paper.get("min_round_trips", PAPER_MIN_ROUND_TRIPS)
        bars_raw = 0

    min_days = _int_at_least(
        days_raw,
        default=int(defaults["min_calendar_days"]),
        floor=int(defaults["min_calendar_days"]),
        field="min_calendar_days",
        invalid=invalid,
    )
    min_trips = _int_at_least(
        trips_raw,
        default=int(defaults["min_qualified_round_trips"]),
        floor=int(defaults["min_qualified_round_trips"]),
        field="min_qualified_round_trips",
        invalid=invalid,
    )
    min_bars = _int_at_least(
        bars_raw,
        default=int(defaults["min_qualified_bars"]),
        floor=int(defaults["min_qualified_bars"]),
        field="min_qualified_bars",
        invalid=invalid,
    )

    cohort_start = None
    cohort_start_dt = None
    if explicit_policy and str(policy_cfg.get("cohort_start") or "").strip():
        cohort_start = str(policy_cfg.get("cohort_start")).strip()
        cohort_start_dt = _parse_ts(cohort_start)
        if cohort_start_dt is None:
            invalid.append("invalid_cohort_start")
            cohort_start = None

    qbar = _configured_contract(config)
    qbar.update(_nested_dict(policy_cfg.get("qualified_bar")))

    return PaperPromotionPolicy(
        policy_id=policy_id,
        min_calendar_days=min_days,
        min_qualified_round_trips=min_trips,
        min_qualified_bars=min_bars,
        cohort_start=cohort_start,
        cohort_start_dt=cohort_start_dt,
        require_archive_walk_forward=bool(
            policy_cfg.get(
                "require_archive_walk_forward",
                defaults.get("require_archive_walk_forward", False),
            )
        ),
        require_manual_review=bool(
            policy_cfg.get("require_manual_review", defaults.get("require_manual_review", True))
        ),
        legacy_evidence_policy=str(
            policy_cfg.get("legacy_evidence_policy") or "diagnostic_only"
        ).strip()
        or "diagnostic_only",
        valid=not invalid,
        invalid_reasons=tuple(invalid),
        qualified_bar=qbar,
    )


def record_timestamp(record: dict[str, Any]) -> datetime | None:
    return _parse_ts(record.get("timestamp") or record.get("_logged_at"))


def before_policy_cohort(record: dict[str, Any], policy: PaperPromotionPolicy) -> bool:
    if policy.cohort_start_dt is None:
        return False
    ts = record_timestamp(record)
    return ts is not None and ts < policy.cohort_start_dt


def _record_date(record: dict[str, Any]) -> str:
    ts = record_timestamp(record)
    if ts is None:
        return ""
    return ts.date().isoformat()


def _bar_timestamp(record: dict[str, Any]) -> str:
    for key in ("ohlcv_bar_ts", "ohlcv_last_bar_ts", "source_bar_ts", "market_data_bar_ts"):
        raw = str(record.get(key) or "").strip()
        if raw:
            return raw
    return ""


def count_qualified_signal_bars(
    signals: list[dict[str, Any]],
    *,
    config: dict[str, Any],
    strategy_id: str = "",
) -> dict[str, Any]:
    policy = resolve_paper_promotion_policy(config)
    required = int(policy.min_qualified_bars)
    contract = dict(policy.qualified_bar or {})
    keys: set[tuple[str, str, str, str, str, str]] = set()
    sources: set[str] = set()
    rejected: dict[str, int] = {}
    excluded_before_cohort = 0
    total = 0

    def reject(reason: str) -> None:
        rejected[reason] = rejected.get(reason, 0) + 1

    for raw in list(signals or []):
        if not isinstance(raw, dict):
            continue
        total += 1
        row = dict(raw)
        if before_policy_cohort(row, policy):
            excluded_before_cohort += 1
            continue
        sid = str(strategy_id or "").strip()
        if sid:
            row_sid = str(row.get("strategy_id") or row.get("_strategy_id") or "").strip()
            if row_sid and row_sid != sid:
                reject("strategy_id_mismatch")
                continue
        source = str(row.get("market_data_source") or "").strip().lower()
        if source != str(contract.get("source") or "").strip().lower():
            reject("market_data_source_mismatch")
            continue
        if row.get("ohlcv_sample_mode") is not False:
            reject("sample_mode_not_explicit_false")
            continue
        if bool(row.get("ohlcv_source_mismatch")):
            reject("ohlcv_source_mismatch")
            continue
        timeframe = str(row.get("ohlcv_timeframe") or "").strip().lower()
        if timeframe != str(contract.get("timeframe") or "").strip().lower():
            reject("ohlcv_timeframe_mismatch")
            continue
        venue = str(row.get("ohlcv_venue") or "").strip().lower()
        if venue != str(contract.get("venue") or "").strip().lower():
            reject("ohlcv_venue_mismatch")
            continue
        symbol = str(row.get("ohlcv_symbol") or "").strip().upper()
        if symbol != str(contract.get("symbol") or "").strip().upper():
            reject("ohlcv_symbol_mismatch")
            continue

        bar_ts = _bar_timestamp(row)
        source_kind = "ohlcv_bar_ts"
        if not bar_ts:
            if policy.policy_id == SLOW_DAILY_POLICY_ID and timeframe == "1d":
                bar_ts = _record_date(row)
                source_kind = "legacy_signal_date"
            if not bar_ts:
                reject("missing_ohlcv_bar_ts")
                continue
        sources.add(source_kind)
        keys.add((sid, source, timeframe, venue, symbol, bar_ts))

    count = len(keys)
    if not sources:
        source_label = "none"
    elif len(sources) == 1:
        source_label = next(iter(sources))
    else:
        source_label = "mixed"
    return {
        "enabled": required > 0,
        "policy_id": policy.policy_id,
        "qualified_bars_recorded": count,
        "qualified_bars_required": required,
        "qualified_bars_remaining": max(0, required - count),
        "qualified_bars_ready": (count >= required) if required > 0 else True,
        "bar_count_source": source_label,
        "total_signal_records": total,
        "excluded_before_cohort_signals": excluded_before_cohort,
        "rejected_signal_records": sum(rejected.values()),
        "rejection_reason_counts": dict(sorted(rejected.items())),
        "rule": "count unique provenance-qualified source bars, not runner loops",
    }
