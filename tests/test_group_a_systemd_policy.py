from configparser import ConfigParser
from itertools import product

import pytest

from services.control.group_a_systemd_policy import render_group_a_policy


def _parse(text):
    config = ConfigParser(interpolation=None)
    config.read_string(text)
    return config


def test_frozen_membership_is_reused_for_boot_and_stop():
    policy = render_group_a_policy("frozen42")
    expected = {
        f"cbp-group-a-frozen42-{strategy}-{coin}-{role}.service"
        for strategy, coin, role in product(
            ("breakout-default", "ema-cross-default", "mean-reversion-default"),
            ("btc", "eth", "sol"),
            ("strategy", "paper"),
        )
    } | {f"cbp-group-a-frozen42-{role}.service" for role in ("publisher", "watcher", "backup")}
    target = _parse(dict(policy.files)[policy.target])
    assert policy.target == "cbp-group-a-frozen42.target"
    assert set(target["Unit"]["Wants"].split()) == expected
    assert set(target["Unit"]) == {"description", "wants", "jobtimeoutsec"}
    assert target["Unit"]["JobTimeoutSec"] == "50s"
    assert target["Install"]["WantedBy"] == "multi-user.target"
    assert len(policy.services) == len(expected) == 21
    assert set(policy.services) == expected
    assert policy.stop_argv == (
        "systemctl", "--system", "stop", "--", policy.target,
        *policy.services, *policy.failure_services,
    )
    assert len(set(policy.stop_argv[4:])) == 43
    assert render_group_a_policy("frozen42") == policy


def test_every_member_has_bounded_restart_stop_and_its_own_failure_route():
    policy = render_group_a_policy("frozen42")
    files = dict(policy.files)
    stop = {"killmode": "control-group", "timeoutstopsec": "20s", "sendsigkill": "yes"}
    for unit, hook in zip(policy.services, policy.failure_services, strict=True):
        assert hook == f"cbp-group-a-frozen42-failed@{unit[:-8]}.service"
        drop_in = _parse(files[f"{unit}.d/50-group-a-lifecycle.conf"])
        assert dict(drop_in["Unit"]) == {
            "partof": policy.target, "jobtimeoutsec": "50s", "onfailure": hook,
            "onfailurejobmode": "fail",
            "startlimitintervalsec": "300s", "startlimitburst": "4",
        }
        assert dict(drop_in["Service"]) == {
            **stop, "restart": "on-failure", "restartmode": "direct", "restartsec": "2s",
            "restartsteps": "3", "restartmaxdelaysec": "12s",
        }
    failure = _parse(files["cbp-group-a-frozen42-failed@.service.d/50-group-a-lifecycle.conf"])
    assert dict(failure["Unit"]) == {
        "partof": policy.target, "jobtimeoutsec": "50s",
        "requisite": policy.target, "after": policy.target,
    }
    assert dict(failure["Service"]) == stop
    assert len(files) == len(policy.files) == 23


def test_other_release_and_legacy_units_are_not_in_stop_scope():
    first = render_group_a_policy("frozen42")
    second = render_group_a_policy("frozen43")
    assert set(first.stop_argv[4:]).isdisjoint(second.stop_argv[4:])
    assert dict(first.files).keys().isdisjoint(dict(second.files))
    assert all(name.startswith("cbp-group-a-frozen42") for name in first.stop_argv[4:])
    assert all(not any(c in name for c in "*?[]%/\n") for name in first.stop_argv[4:])


@pytest.mark.parametrize(("target_state", "stop_queued", "expected"), [
    ("active", False, "allow"),
    ("starting", False, "wait"),
    ("active", True, "deny"),
    ("inactive", False, "deny"),
])
def test_failure_hook_admission_contract(target_state, stop_queued, expected):
    """Check rendered admission constraints, not systemd execution."""
    policy = render_group_a_policy("frozen42")
    files = dict(policy.files)
    hook = _parse(files["cbp-group-a-frozen42-failed@.service.d/50-group-a-lifecycle.conf"])["Unit"]
    for unit in policy.services:
        member = _parse(files[f"{unit}.d/50-group-a-lifecycle.conf"])["Unit"]
        if stop_queued and member.get("OnFailureJobMode", "replace") == "fail":
            admission = "deny"
        elif hook.get("Requisite") == policy.target and target_state == "inactive":
            admission = "deny"
        elif hook.get("After") == policy.target and target_state == "starting":
            admission = "wait"
        else:
            admission = "allow"
        assert admission == expected, unit


@pytest.mark.parametrize("release", [
    "", "a" * 7, "a" * 41, "CAPITAL42", "frozen42\n", "../escape", "frozen*", "frozen%N",
    "--all-units", "a" * 7 + "\u00e9", None,
])
def test_invalid_release_ids_are_rejected(release):
    with pytest.raises(ValueError, match="release must be"):
        render_group_a_policy(release)
