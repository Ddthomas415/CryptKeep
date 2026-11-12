"""Fixed R3 summary/health protocol; no I/O or implicit alert configuration."""

from dataclasses import dataclass
import json
import math
import re

from services.alerts.group_a_watch import _ACCOUNT_RULES, _HOST_RULES, _account_names, _policy


GLOBAL_CODES = ("cursor_near_capacity", "cursor_unavailable", "cursor_capacity")
SOURCE_CODES = ("source_copy_unavailable", "queue_evidence_limit")
MAX_EPOCH = 253_402_300_799_999
ALL_HEALTH = (1 << 21) - 1
TITLE = "CryptKeep Group A paper summary\n"
OUTCOMES = ("idle", "slack_accepted", "unconfirmed", "fault")


def health_keys(release):
    names = tuple(sorted(_account_names(_policy(release))))
    return tuple((code, None) for code in GLOBAL_CODES) + tuple(
        (code, scope) for code in SOURCE_CODES for scope in names
    )


def bit_for(release, code, scope=None):
    try:
        return 1 << health_keys(release).index((code, scope))
    except ValueError:
        raise ValueError("invalid_group_a_health_key") from None


def _mask(value):
    return type(value) is int and 0 <= value <= ALL_HEALTH


def _epoch(value):
    return type(value) is int and 0 < value <= MAX_EPOCH


def _generation(value):
    return type(value) is str and re.fullmatch(r"[a-f0-9]{32}", value) is not None


def _json(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def _decode(raw, cap):
    if type(raw) is not bytes or not 0 < len(raw) <= cap:
        raise ValueError("invalid_group_a_control_size")

    def unique(pairs):
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError("duplicate_group_a_control_key")
        return result

    try:
        return json.loads(raw.decode("ascii"), object_pairs_hook=unique)
    except (UnicodeError, RecursionError, json.JSONDecodeError):
        raise ValueError("invalid_group_a_control_json") from None


def control(release, generation, suppressed):
    _policy(release)
    if not _generation(generation) or not _mask(suppressed):
        raise ValueError("invalid_group_a_control")
    return {"schema": 1, "release": release, "generation": generation, "suppressed": suppressed}


def encode_control(value):
    if type(value) is not dict or set(value) != {"schema", "release", "generation", "suppressed"}:
        raise ValueError("invalid_group_a_control")
    if type(value["schema"]) is not int or value["schema"] != 1:
        raise ValueError("invalid_group_a_control")
    canonical = control(value["release"], value["generation"], value["suppressed"])
    raw = _json(canonical)
    if len(raw) > 2048:
        raise ValueError("invalid_group_a_control_size")
    return raw


def decode_control(raw, release, generation):
    value = _decode(raw, 2048)
    encode_control(value)
    if value["release"] != release or value["generation"] != generation:
        raise ValueError("wrong_group_a_control_generation")
    return value


@dataclass(frozen=True)
class Health:
    present: int = 0
    known_clear: int = 0
    unknown: int = ALL_HEALTH

    def validate(self):
        if (any(not _mask(n) for n in (self.present, self.known_clear, self.unknown))
                or self.present & self.known_clear or self.present & self.unknown
                or self.known_clear & self.unknown
                or self.present | self.known_clear | self.unknown != ALL_HEALTH):
            raise ValueError("invalid_group_a_health_partition")
        return self

    def with_state(self, mask, state):
        self.validate()
        if not _mask(mask) or state not in ("present", "known_clear", "unknown"):
            raise ValueError("invalid_group_a_health_state")
        values = {key: getattr(self, key) & ~mask for key in ("present", "known_clear", "unknown")}
        values[state] |= mask
        return Health(**values).validate()


def cycle_result(request, observed_ms, outcome, health, acknowledged=0):
    encode_control(request)
    if (not _epoch(observed_ms) or type(outcome) is not str or outcome not in OUTCOMES
            or type(health) is not Health or not _mask(acknowledged)):
        raise ValueError("invalid_group_a_cycle_result")
    health.validate()
    if (acknowledged & ~health.present or acknowledged & request["suppressed"]
            or (outcome != "slack_accepted" and acknowledged)):
        raise ValueError("invalid_group_a_health_acknowledgement")
    return {"schema": 1, "release": request["release"], "generation": request["generation"],
            "observed_ms": observed_ms, "outcome": outcome, "present": health.present,
            "known_clear": health.known_clear, "unknown": health.unknown, "acknowledged": acknowledged}


def encode_result(value, request):
    fields = {"schema", "release", "generation", "observed_ms", "outcome", "present",
              "known_clear", "unknown", "acknowledged"}
    if (type(value) is not dict or set(value) != fields or type(value["schema"]) is not int
            or value["schema"] != 1 or value["release"] != request["release"]
            or value["generation"] != request["generation"]):
        raise ValueError("invalid_group_a_cycle_result")
    canonical = cycle_result(request, value["observed_ms"], value["outcome"],
                             Health(value["present"], value["known_clear"], value["unknown"]),
                             value["acknowledged"])
    raw = _json(canonical)
    if len(raw) > 1024:
        raise ValueError("invalid_group_a_result_size")
    return raw


def decode_result(raw, request):
    value = _decode(raw, 1024)
    encode_result(value, request)
    return value


class Suppression:
    def __init__(self):
        self.deadlines = [0.0] * 21

    @staticmethod
    def _clock(now):
        if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
            raise ValueError("invalid_group_a_monotonic_clock")

    def mask(self, now):
        self._clock(now)
        return sum(1 << i for i, deadline in enumerate(self.deadlines) if deadline > now)

    def accept(self, result, request, now):
        self._clock(now)
        encode_result(result, request)
        for i in range(21):
            if result["known_clear"] & (1 << i):
                self.deadlines[i] = 0.0
            elif result["acknowledged"] & (1 << i):
                self.deadlines[i] = now + 1800


def summary_body(release, observed_ms, findings, health, health_mask):
    policy = _policy(release)
    if (not _epoch(observed_ms) or type(findings) is not tuple or len(findings) > 93
            or type(health) is not Health or not _mask(health_mask)):
        raise ValueError("invalid_group_a_summary")
    health.validate()
    if health_mask & ~health.present:
        raise ValueError("invalid_group_a_summary_health")
    names = _account_names(policy)
    allowed = {(name, rule[1]) for name in names for rule in _ACCOUNT_RULES}
    allowed.update((policy.target, rule[1]) for rule in _HOST_RULES)
    seen, rows = set(), []
    for row in findings:
        if type(row) is not tuple or len(row) != 3:
            raise ValueError("invalid_group_a_summary_finding")
        scope, code, first = row
        if (type(scope) is not str or type(code) is not str or (scope, code) not in allowed
                or (scope, code) in seen or not _epoch(first) or first > observed_ms):
            raise ValueError("invalid_group_a_summary_finding")
        seen.add((scope, code))
        rows.append({"scope": scope, "condition": code, "first_observed_ms": first})
    rows.sort(key=lambda row: (row["scope"], row["condition"]))
    groups = {}
    for i, (code, scope) in enumerate(health_keys(release)):
        if health_mask & (1 << i):
            groups.setdefault(code, [])
            if scope is not None:
                groups[code].append(scope)
    payload = {"schema": 1, "release": release, "observed_ms": observed_ms, "findings": rows,
               "health": [{"condition": code, "observed_ms": observed_ms, "affected": sorted(scopes)}
                          for code, scopes in sorted(groups.items())]}
    text = TITLE.encode("ascii") + _json(payload)
    body = _json({"text": text.decode("ascii")})
    if len(text) > 20_000 or len(body) > 24_576:
        raise ValueError("group_a_summary_capacity")
    return body
