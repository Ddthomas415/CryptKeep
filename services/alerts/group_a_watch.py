"""Offline Group A alert decisions; no state, network, or service access."""

from dataclasses import dataclass
import math

from services.control.group_a_systemd_policy import render_group_a_policy


@dataclass(frozen=True)
class AccountObservation:
    strategy_status_age_sec: float | None = None
    paper_status_age_sec: float | None = None
    kill_cooldown: bool | None = None
    consecutive_candle_failures: int | None = None
    http_429_last_10_min: int | None = None
    quote_fresh: bool | None = None
    order_refused: bool | None = None
    order_expired: bool | None = None
    oldest_pending_exit_sec: float | None = None
    oldest_submitting_sec: float | None = None


@dataclass(frozen=True)
class HostObservation:
    disk_pct: float | None = None
    memory_pct: float | None = None
    backup_failed: bool | None = None


@dataclass(frozen=True)
class WatchFinding:
    scope: str
    code: str


@dataclass(frozen=True)
class WatchReport:
    alerts: tuple[WatchFinding, ...]
    missing: tuple[WatchFinding, ...]


# Field, finding code, operator, threshold. Numeric thresholds retain the
# strict/inclusive distinction in R3; zero means a measured empty backlog.
_ACCOUNT_RULES = (
    ("strategy_status_age_sec", "strategy_status_stale", "gt", 600),
    ("paper_status_age_sec", "paper_status_stale", "gt", 600),
    ("kill_cooldown", "kill_cooldown", "bool", True),
    ("consecutive_candle_failures", "candle_fetch_failures", "count", 10),
    ("http_429_last_10_min", "http_429_burst", "count", 5),
    ("quote_fresh", "quote_stale", "bool", False),
    ("order_refused", "order_refused", "bool", True),
    ("order_expired", "order_expired", "bool", True),
    ("oldest_pending_exit_sec", "exit_delayed", "gt", 120),
    ("oldest_submitting_sec", "submitting_delayed", "gt", 60),
)
_HOST_RULES = (
    ("disk_pct", "disk_high", "pct", 80),
    ("memory_pct", "memory_high", "pct", 85),
    ("backup_failed", "backup_failed", "bool", True),
)


def _policy(release):
    if type(release) is not str:
        raise ValueError("invalid_group_a_release")
    return render_group_a_policy(release)


def _account_names(policy):
    return tuple(unit.removesuffix("-strategy.service") for unit in policy.services
                 if unit.endswith("-strategy.service"))


def _decision(value, operator, threshold):
    if operator == "bool":
        return value is threshold if type(value) is bool else None
    if operator == "count":
        return value >= threshold if type(value) is int and value >= 0 else None
    if type(value) not in (int, float) or value < 0:
        return None
    if type(value) is float and not math.isfinite(value):
        return None
    if operator == "pct" and value > 100:
        return None
    return value > threshold


def assess_group_a_watch(
    release: str, *, accounts: dict[str, AccountObservation], host: HostObservation,
) -> WatchReport:
    """Classify precomputed observations, not inferred counts from status polling."""
    policy = _policy(release)
    names = _account_names(policy)
    if type(accounts) is not dict or any(type(name) is not str or name not in names for name in accounts):
        raise ValueError("unknown_group_a_account")
    if not isinstance(host, HostObservation):
        raise ValueError("invalid_host_observation")
    alerts = []
    missing = []

    def evaluate(scope, observation, rules):
        for field, code, operator, threshold in rules:
            verdict = _decision(getattr(observation, field), operator, threshold)
            if verdict is True:
                alerts.append(WatchFinding(scope, code))
            elif verdict is None:
                missing.append(WatchFinding(scope, code))

    for name in names:
        observation = accounts.get(name, AccountObservation())
        if not isinstance(observation, AccountObservation):
            raise ValueError("invalid_account_observation")
        evaluate(name, observation, _ACCOUNT_RULES)
    evaluate(policy.target, host, _HOST_RULES)
    return WatchReport(tuple(alerts), tuple(missing))


def terminal_failure(release: str, instance: str) -> WatchFinding:
    """Validate the exact systemd failure-hook instance, not a unit prefix."""
    policy = _policy(release)
    if type(instance) is not str:
        raise ValueError("unknown_group_a_failure_instance")
    for unit in policy.services:
        if instance == unit.removesuffix(".service"):
            return WatchFinding(unit, "terminal_service_failure")
    raise ValueError("unknown_group_a_failure_instance")


def dispatch_group_a_alert(release: str, finding: WatchFinding, *, cfg, send_alert) -> str:
    """Use the injected existing dispatcher; never report owner receipt."""
    policy = _policy(release)
    if not isinstance(finding, WatchFinding) or type(finding.scope) is not str or type(finding.code) is not str:
        raise ValueError("unknown_group_a_finding")
    account_codes = {rule[1] for rule in _ACCOUNT_RULES}
    host_codes = {rule[1] for rule in _HOST_RULES}
    allowed = (
        (finding.scope in _account_names(policy) and finding.code in account_codes)
        or (finding.scope == policy.target and finding.code in host_codes)
        or (finding.scope in policy.services and finding.code == "terminal_service_failure")
    )
    if not allowed:
        raise ValueError("unknown_group_a_finding")
    try:
        result = send_alert(
            cfg=cfg, level="error", message="CryptKeep Group A paper alert",
            payload={"scope": finding.scope, "condition": finding.code},
        )
    except Exception:
        return "dispatch_failed"
    if not isinstance(result, dict) or result.get("ok") is not True or result.get("skipped", False) is not False:
        return "external_unverified"
    channels = result.get("channels")
    if isinstance(channels, list) and any(
        isinstance(channel, dict) and channel.get("channel") == "slack" and channel.get("ok") is True
        and type(channel.get("status")) is int and 200 <= channel["status"] < 300
        for channel in channels
    ):
        return "slack_accepted"
    return "external_unverified"
