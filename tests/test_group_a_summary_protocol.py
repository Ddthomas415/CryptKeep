import json

import pytest

from services.alerts import group_a_summary_protocol as protocol
from services.alerts.group_a_watch import _ACCOUNT_RULES, _HOST_RULES, _account_names, _policy


RELEASE = "frozen42"
GENERATION = "a" * 32


def request(suppressed=0):
    return protocol.control(RELEASE, GENERATION, suppressed)


def test_account_specific_suppression_unknown_and_recovery():
    state = protocol.Suppression()
    a, b = (1 << 3), (1 << 4)
    first = protocol.Health().with_state(a, "present")
    state.accept(protocol.cycle_result(request(), 1, "slack_accepted", first, a), request(), 10)
    assert state.mask(20) == a
    both = first.with_state(b, "present")
    next_request = request(state.mask(20))
    state.accept(protocol.cycle_result(next_request, 2, "slack_accepted", both, b), next_request, 20)
    state.accept(protocol.cycle_result(request(), 3, "idle", protocol.Health()), request(), 25)
    assert state.mask(30) == a | b
    clear = protocol.Health().with_state(a, "known_clear")
    state.accept(protocol.cycle_result(request(), 4, "idle", clear), request(), 30)
    assert state.mask(31) == b and state.mask(1821) == 0


@pytest.mark.parametrize("damage", ["generation", "overlap", "incomplete", "ack_unknown", "ack_suppressed", "bool", "extra", "duplicate", "oversize"])
def test_bad_result_never_mutates_suppression(damage):
    state = protocol.Suppression()
    control = request(1)
    value = protocol.cycle_result(control, 1, "idle", protocol.Health())
    if damage == "generation":
        value["generation"] = "b" * 32
    elif damage == "overlap":
        value["present"] = 1
    elif damage == "incomplete":
        value["unknown"] = 0
    elif damage == "ack_unknown":
        value["acknowledged"] = 2
    elif damage == "ack_suppressed":
        value.update(present=1, unknown=protocol.ALL_HEALTH ^ 1, acknowledged=1, outcome="slack_accepted")
    elif damage == "bool":
        value["known_clear"] = False
    elif damage == "extra":
        value["private"] = "not allowed"
    raw = json.dumps(value).encode()
    if damage == "duplicate":
        raw = b'{"schema":1,' + raw[1:]
    elif damage == "oversize":
        raw += b" " * 1025
    with pytest.raises(ValueError):
        parsed = protocol.decode_result(raw, control)
        state.accept(parsed, control, 1)
    assert state.mask(1) == 0


def test_maximum_valid_summary_and_ipc_round_trip():
    release = "z" * 40
    policy = _policy(release)
    epoch = protocol.MAX_EPOCH
    findings = tuple((scope, rule[1], epoch) for scope in _account_names(policy) for rule in _ACCOUNT_RULES)
    findings += tuple((policy.target, rule[1], epoch) for rule in _HOST_RULES)
    health = protocol.Health(protocol.ALL_HEALTH, 0, 0)
    body = protocol.summary_body(release, epoch, findings, health, protocol.ALL_HEALTH)
    payload = json.loads(json.loads(body)["text"].split("\n", 1)[1])
    assert len(payload["findings"]) == 93 and len(payload["health"]) == 5
    assert len(body) <= 24576
    control = protocol.control(release, GENERATION, 0)
    assert protocol.decode_control(protocol.encode_control(control), release, GENERATION) == control
    result = protocol.cycle_result(control, epoch, "slack_accepted", health, protocol.ALL_HEALTH)
    assert protocol.decode_result(protocol.encode_result(result, control), control) == result


def test_summary_rejects_unrostered_duplicate_future_and_bool_findings():
    row = (_policy(RELEASE).target, "disk_high", 1)
    for findings in ((row, row), (("elsewhere", "disk_high", 1),), ((row[0], row[1], 3),), ((row[0], row[1], True),)):
        with pytest.raises(ValueError):
            protocol.summary_body(RELEASE, 2, findings, protocol.Health(), 0)


def test_unknown_and_unconfirmed_do_not_acknowledge():
    with pytest.raises(ValueError):
        protocol.cycle_result(request(), 1, "unconfirmed", protocol.Health().with_state(1, "present"), 1)
    with pytest.raises(ValueError):
        protocol.decode_control(protocol.encode_control(request()), RELEASE, "b" * 32)
