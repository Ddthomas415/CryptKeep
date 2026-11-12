import json
import os
from types import SimpleNamespace

import pytest

from scripts import run_group_a_alert as runtime
from services.alerts import group_a_alert_entrypoints as entrypoints
from services.alerts.group_a_cursor_image import EMPTY_IMAGE, IMAGE_NAME
from services.alerts.group_a_watch import HostObservation, assess_group_a_watch
from services.alerts.group_a_watch_cycle import QueueEventEvidence, WatchCycleResult
from services.control.group_a_alert_units import render_group_a_alert_units
from services.control.group_a_systemd_policy import render_group_a_policy


RELEASE = "frozen42"
URL = "https://hooks.slack.com/services/Tsynthetic/Bsynthetic/Offline-placeholder"


def _document():
    return {"release": RELEASE, "root": [1, 1], "since_ms": 42, "queues": {
        unit.removesuffix("-strategy.service"): [[1, i * 2 + 2], [1, i * 2 + 3]]
        for i, unit in enumerate(render_group_a_policy(RELEASE).services) if unit.endswith("-strategy.service")
    }}


def test_fragments_do_not_start_and_separate_alert_user_state_and_secrets():
    with pytest.raises(ValueError, match="distinct"):
        render_group_a_alert_units(RELEASE, service_user="cbp-ga-paper", alert_user="cbp-ga-paper")
    units = render_group_a_alert_units(RELEASE, service_user="cbp-ga-paper", alert_user="cbp-ga-alert")
    (_, watch), (_, terminal) = units.fragments
    assert "ExecStart=" not in watch + terminal and "User=cbp-ga-alert\n" in watch and "User=cbp-ga-alert\n" in terminal
    assert f"ReadOnlyPaths=/srv/cryptkeep/state/{RELEASE}\n" in watch
    assert f"ReadWritePaths=/srv/cryptkeep/alert-state/{RELEASE}\n" in watch
    assert "ReadWritePaths=" not in terminal and "queue-receipt" not in terminal
    assert "LoadCredentialEncrypted=slack-webhook:" in watch and "LoadCredentialEncrypted=slack-webhook:" in terminal
    assert units.launch_args[0][1][-2:] == ("watch", RELEASE)
    assert units.launch_args[1][1][-3:] == ("terminal", RELEASE, "%i")


def test_receipt_has_fixed_roster_cutoff_and_exact_identity():
    data = _document()
    receipt, since = runtime._receipt(json.dumps(data).encode(), RELEASE)
    assert receipt.root == (1, 1) and since == 42 and len(receipt.queues) == 9
    raw = json.dumps(data).encode()
    with pytest.raises(ValueError, match="duplicate"):
        runtime._receipt(b'{"release":"another42",' + raw[1:], RELEASE)
    with pytest.raises(ValueError, match="identity"):
        runtime._receipt(json.dumps({**data, "root": [1, True]}).encode(), RELEASE)
    data["queues"].pop(next(iter(data["queues"])))
    with pytest.raises(ValueError, match="scope"):
        runtime._receipt(json.dumps(data).encode(), RELEASE)


def test_credential_reader_refuses_symlink_writable_and_oversized(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime.os, "fstatvfs", lambda fd: SimpleNamespace(f_flag=os.ST_RDONLY))
    target = tmp_path / "webhook"
    target.write_text(URL)
    with runtime._directory(tmp_path.resolve().parts) as fd:
        with pytest.raises(ValueError, match="unsafe"):
            runtime._read_credential(fd, "webhook", 421)
        target.chmod(0o400)
        assert runtime._read_credential(fd, "webhook", 421) == URL.encode()
        with pytest.raises(ValueError, match="unsafe"):
            runtime._read_credential(fd, "webhook", 12)
        (tmp_path / "alias").symlink_to(target)
        with pytest.raises(OSError):
            runtime._read_credential(fd, "alias", 421)


@pytest.mark.parametrize("credential_readonly", [True, False])
def test_terminal_uses_exact_instance_and_checks_both_mounts(tmp_path, monkeypatch, credential_readonly):
    policy = render_group_a_policy(RELEASE)
    terminal = policy.services[0].removesuffix(".service")
    directory = tmp_path / f"cbp-group-a-{RELEASE}-failed@{terminal}.service"
    directory.mkdir()
    credential = directory / "slack-webhook"
    credential.write_text(URL + "\n")
    credential.chmod(0o400)
    inode = directory.stat().st_ino
    monkeypatch.setattr(runtime.os, "fstatvfs", lambda fd: SimpleNamespace(
        f_flag=os.ST_RDONLY if credential_readonly or os.fstat(fd).st_ino == inode else 0,
    ))
    sent = []

    def send(release, instance, *, cfg):
        assert release == RELEASE and instance == terminal
        assert cfg["alerts"]["slack_webhook_url"] == URL
        sent.append(instance)
        return "slack_accepted"

    monkeypatch.setattr(runtime, "deliver_terminal_alert", send)
    kwargs = dict(credential_root=tmp_path.resolve())
    with pytest.raises(ValueError, match="unknown_group_a_failure_instance"):
        runtime._run("terminal", RELEASE, "../escape", **kwargs)
    if credential_readonly:
        assert runtime._run("terminal", RELEASE, terminal, **kwargs) == "slack_accepted"
        assert sent == [terminal]
    else:
        with pytest.raises(ValueError, match="unsafe_alert_credential"):
            runtime._run("terminal", RELEASE, terminal, **kwargs)
        assert not sent


def test_writable_credential_file_mount_is_refused_before_read(tmp_path, monkeypatch):
    target = tmp_path / "webhook"
    target.write_text(URL)
    target.chmod(0o400)
    monkeypatch.setattr(runtime.os, "fstatvfs", lambda fd: SimpleNamespace(f_flag=0))
    with runtime._directory(tmp_path.resolve().parts) as fd:
        with pytest.raises(ValueError, match="unsafe_alert_credential"):
            runtime._read_credential(fd, "webhook", 421)


def test_watcher_without_protected_directory_is_refused_before_file_access(tmp_path, monkeypatch):
    def must_not_open(*args, **kwargs):
        pytest.fail("unprotected watcher attempted a file open")

    monkeypatch.setattr(runtime, "_directory", must_not_open)
    with pytest.raises(ValueError, match="protected_alert_cursor_required"):
        runtime._run("watch-once", RELEASE, None, credential_root=tmp_path)


def test_watcher_launcher_uses_pinned_cursor_with_no_sqlite_disk_open(tmp_path, monkeypatch):
    credential_root = tmp_path / "credentials"
    credentials = credential_root / f"cbp-group-a-{RELEASE}-watcher.service"
    credentials.mkdir(parents=True)
    for name, raw in (("slack-webhook", URL), ("queue-receipt", json.dumps(_document()))):
        path = credentials / name
        path.write_text(raw)
        path.chmod(0o400)
    parent = tmp_path / "owned"
    parent.mkdir()
    cursor = parent / RELEASE
    cursor.mkdir(mode=0o700)
    (cursor / IMAGE_NAME).write_bytes(EMPTY_IMAGE)
    (cursor / IMAGE_NAME).chmod(0o600)
    original = os.fstat
    parent_inode = parent.stat().st_ino

    def synthetic_parent(fd):
        info = original(fd)
        return SimpleNamespace(st_uid=0, st_mode=info.st_mode) if info.st_ino == parent_inode else info

    monkeypatch.setattr(runtime.os, "fstat", synthetic_parent)
    monkeypatch.setattr(runtime.os, "fstatvfs", lambda fd: SimpleNamespace(f_flag=os.ST_RDONLY))
    stamp = [43]

    def observe(release, receipt, *, since_ms, proc_fd, track_events):
        assert release == RELEASE and receipt.root == (1, 1) and since_ms == 42 and track_events
        report = assess_group_a_watch(release, accounts={}, host=HostObservation(disk_pct=81))
        return WatchCycleResult(report, (), QueueEventEvidence(since_ms, stamp[0], ()))

    sent = []

    def sender(**kwargs):
        sent.append(kwargs["payload"])
        return {"ok": True, "channels": [{"channel": "slack", "ok": True, "status": 200}]}

    monkeypatch.setattr(runtime, "observe_owned_group_a_queues", observe)
    monkeypatch.setattr(entrypoints, "send_group_a_slack", sender)
    args = dict(credential_root=credential_root.resolve(), cursor_root=cursor.resolve(), proc_root=tmp_path.resolve())
    assert runtime._run("watch-once", RELEASE, None, **args) == "slack_accepted"
    stamp[0] += 1
    assert runtime._run("watch-once", RELEASE, None, **args) == "idle"
    assert len(sent) == 1 and {p.name for p in cursor.iterdir()} == {IMAGE_NAME}


def test_supervised_launcher_defers_credentials_until_cycle_gate(tmp_path, monkeypatch):
    from services.alerts.group_a_summary_protocol import control
    credentials = tmp_path / "credentials" / f"cbp-group-a-{RELEASE}-watcher.service"
    credentials.mkdir(parents=True)
    for name, value in (("slack-webhook", URL), ("queue-receipt", json.dumps(_document()))):
        path = credentials / name
        path.write_text(value)
        path.chmod(0o400)
    parent = tmp_path / "owned"
    parent.mkdir()
    cursor = parent / RELEASE
    cursor.mkdir(mode=0o700)
    (cursor / IMAGE_NAME).write_bytes(EMPTY_IMAGE)
    (cursor / IMAGE_NAME).chmod(0o600)
    original_stat = os.fstat
    parent_inode = parent.stat().st_ino
    monkeypatch.setattr(runtime.os, "fstat", lambda fd: SimpleNamespace(st_uid=0, st_mode=original_stat(fd).st_mode)
                        if original_stat(fd).st_ino == parent_inode else original_stat(fd))
    monkeypatch.setattr(runtime.os, "fstatvfs", lambda fd: SimpleNamespace(f_flag=os.ST_RDONLY))
    read_credential = runtime._read_credential
    reads = []
    def read(*args):
        reads.append(args[1])
        return read_credential(*args)
    monkeypatch.setattr(runtime, "_read_credential", read)
    observed = WatchCycleResult(assess_group_a_watch(RELEASE, accounts={}, host=HostObservation(disk_pct=81)),
                                (), QueueEventEvidence(42, 43, ()))
    monkeypatch.setattr(runtime, "observe_owned_group_a_queues", lambda *a, **kw: observed)
    from services.alerts.group_a_summary_delivery import deliver_summary
    sent = []
    def deliver(request, directory, value, **kwargs):
        assert kwargs["cfg"]["alerts"]["slack_webhook_url"] == URL
        return deliver_summary(request, directory, value, **kwargs,
                               send=lambda *a, **kw: sent.append(a[2]) or True)
    monkeypatch.setattr(runtime, "deliver_summary", deliver)
    def supervise(release, directory, cycle):
        assert reads == []
        result = cycle(control(release, "a" * 32, 0), 40)
        assert result["outcome"] == "slack_accepted"
        return 0
    monkeypatch.setattr(runtime, "supervise", supervise)
    assert runtime._watch(RELEASE, credential_root=tmp_path / "credentials", cursor_root=cursor,
                          proc_root=tmp_path) == 0
    assert reads == ["slack-webhook", "queue-receipt"] and len(sent) == 1
