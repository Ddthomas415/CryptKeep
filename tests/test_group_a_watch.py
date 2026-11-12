from dataclasses import replace

import pytest

from services.alerts.group_a_watch import (
    AccountObservation, HostObservation, WatchFinding, assess_group_a_watch,
    dispatch_group_a_alert, terminal_failure,
)


RELEASE = "frozen42"
TARGET = "cbp-group-a-frozen42.target"
ACCOUNT = "cbp-group-a-frozen42-ema-cross-default-btc"
HEALTHY = AccountObservation(0, 0, False, 0, 0, True, False, False, 0, 0)
HOST = HostObservation(0, 0, False)


@pytest.mark.parametrize(("field", "quiet", "fires", "code"), [
    ("strategy_status_age_sec", 600, 601, "strategy_status_stale"),
    ("paper_status_age_sec", 600, 601, "paper_status_stale"),
    ("kill_cooldown", False, True, "kill_cooldown"),
    ("consecutive_candle_failures", 9, 10, "candle_fetch_failures"),
    ("http_429_last_10_min", 4, 5, "http_429_burst"),
    ("quote_fresh", True, False, "quote_stale"),
    ("order_refused", False, True, "order_refused"),
    ("order_expired", False, True, "order_expired"),
    ("oldest_pending_exit_sec", 120, 121, "exit_delayed"),
    ("oldest_submitting_sec", 60, 61, "submitting_delayed"),
])
def test_all_frozen_account_triggers(field, quiet, fires, code):
    def evaluate(value):
        return assess_group_a_watch(RELEASE, accounts={ACCOUNT: replace(HEALTHY, **{field: value})}, host=HOST)

    assert evaluate(quiet).alerts == ()
    assert evaluate(fires).alerts == (WatchFinding(ACCOUNT, code),)
    assert WatchFinding(ACCOUNT, code) in evaluate(None).missing


@pytest.mark.parametrize(("field", "quiet", "fires", "code"), [
    ("disk_pct", 80, 81, "disk_high"),
    ("memory_pct", 85, 86, "memory_high"),
    ("backup_failed", False, True, "backup_failed"),
])
def test_all_frozen_host_triggers(field, quiet, fires, code):
    def evaluate(value):
        return assess_group_a_watch(RELEASE, accounts={}, host=replace(HOST, **{field: value}))

    assert evaluate(quiet).alerts == ()
    assert evaluate(fires).alerts == (WatchFinding(TARGET, code),)
    assert WatchFinding(TARGET, code) in evaluate(None).missing


def test_missing_or_bad_evidence_does_not_pass_for_healthy():
    report = assess_group_a_watch(RELEASE, accounts={}, host=HostObservation())
    assert report.alerts == ()
    assert len(report.missing) == 9 * 10 + 3
    assert len({item.scope for item in report.missing}) == 10
    account = replace(HEALTHY, http_429_last_10_min=True, oldest_submitting_sec=float("inf"), quote_fresh="false")
    report = assess_group_a_watch(RELEASE, accounts={ACCOUNT: account}, host=HostObservation(101, -1, 1))
    assert report.alerts == ()
    assert {item.code for item in report.missing if item.scope == ACCOUNT} == {
        "http_429_burst", "submitting_delayed", "quote_stale",
    }
    assert len([item for item in report.missing if item.scope == TARGET]) == 3
    with pytest.raises(ValueError, match="unknown_group_a_account"):
        assess_group_a_watch(RELEASE, accounts={"cbp-old": HEALTHY}, host=HOST)


def test_exact_failure_hook_instance_and_sanitized_dispatch():
    failure = terminal_failure(RELEASE, ACCOUNT + "-paper")
    assert failure == WatchFinding(ACCOUNT + "-paper.service", "terminal_service_failure")
    cfg = {"test": "must not appear in the alert payload"}

    def send(**kwargs):
        assert kwargs == {
            "cfg": cfg, "level": "error", "message": "CryptKeep Group A paper alert",
            "payload": {"scope": failure.scope, "condition": failure.code},
        }
        return {"ok": True, "channels": [{"ok": True, "channel": "slack", "status": 200}]}

    assert dispatch_group_a_alert(RELEASE, failure, cfg=cfg, send_alert=send) == "slack_accepted"
    for invalid in ("cbp-collector", "cbp-group-a-frozen43-watcher", ACCOUNT + "-paper.service"):
        with pytest.raises(ValueError, match="unknown_group_a_failure_instance"):
            terminal_failure(RELEASE, invalid)
    with pytest.raises(ValueError, match="unknown_group_a_finding"):
        dispatch_group_a_alert(RELEASE, WatchFinding(ACCOUNT, "arbitrary"), cfg=cfg, send_alert=send)


@pytest.mark.parametrize("receipt", [
    None, {"ok": True, "skipped": True},
    {"ok": True, "local_written": True},
    {"ok": False, "channels": [{"ok": True, "channel": "slack", "status": 200}]},
    {"ok": True, "channels": [{"ok": True, "channel": "email", "status": 200}]},
    {"ok": True, "channels": [{"ok": True, "channel": "slack", "status": 403}]},
    {"ok": True, "channels": [{"ok": True, "channel": "slack"}]},
])
def test_dispatch_never_converts_non_slack_receipts_to_delivery(receipt):
    finding = WatchFinding(ACCOUNT, "quote_stale")
    assert dispatch_group_a_alert(RELEASE, finding, cfg={}, send_alert=lambda **_: receipt) == "external_unverified"


def test_dispatch_exception_does_not_return_the_exception_text():
    def broken(**kwargs):
        raise OSError("synthetic secret")

    assert dispatch_group_a_alert(
        RELEASE, WatchFinding(TARGET, "backup_failed"), cfg={}, send_alert=broken,
    ) == "dispatch_failed"


class _Impersonator(str):
    def __eq__(self, other):
        return True

    def __hash__(self):
        return hash(ACCOUNT)


def test_roster_rejects_account_key_with_custom_equality():
    with pytest.raises(ValueError, match="unknown_group_a_account"):
        assess_group_a_watch(
            RELEASE, accounts={_Impersonator("cbp-old-account"): replace(HEALTHY, kill_cooldown=True)}, host=HOST,
        )


def test_hook_rejects_instance_with_custom_equality():
    with pytest.raises(ValueError, match="unknown_group_a_failure_instance"):
        terminal_failure(RELEASE, _Impersonator("cbp-old-collector"))


def test_release_rejects_custom_formatting():
    class Alias(str):
        def __format__(self, spec):
            return "frozen43"

    with pytest.raises(ValueError, match="invalid_group_a_release"):
        terminal_failure(Alias(RELEASE), "cbp-group-a-frozen43-watcher")
