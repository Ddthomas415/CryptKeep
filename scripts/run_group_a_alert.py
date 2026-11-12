"""Group A alert entrypoint for a separately provisioned Linux namespace."""

import json
import os
from pathlib import Path
import stat
import sys


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.alerts.group_a_alert_entrypoints import deliver_terminal_alert, deliver_watcher_image_alert
from services.alerts.group_a_observations import _directory
from services.alerts.group_a_queue_readers import QueueIdentity, ReleaseIdentity, observe_owned_group_a_queues
from services.alerts.group_a_slack import _webhook_path
from services.alerts.group_a_summary_delivery import deliver_summary
from services.alerts.group_a_supervisor import supervise
from services.alerts.group_a_watch import terminal_failure
from services.control.group_a_alert_units import alert_cursor_dir
from services.control.group_a_systemd_policy import render_group_a_policy


def _read_credential(directory_fd, name, cap):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_mode & 0o222 or not 0 < info.st_size <= cap
                or not os.fstatvfs(stream.fileno()).f_flag & os.ST_RDONLY):
            raise ValueError("unsafe_alert_credential")
        raw = stream.read(cap + 1)
        if len(raw) != info.st_size:
            raise ValueError("unsafe_alert_credential")
        return raw


def _receipt(raw, release):
    def unique(pairs):
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError("duplicate_alert_receipt_key")
        return result

    def identity(value):
        if (type(value) is not list or len(value) != 2 or any(type(n) is not int or not 0 <= n < 2**64 for n in value)
                or not value[1]):
            raise ValueError("invalid_alert_receipt_identity")
        return tuple(value)

    data = json.loads(raw, object_pairs_hook=unique)
    if (type(data) is not dict or set(data) != {"release", "root", "queues", "since_ms"}
            or data["release"] != release or type(data["since_ms"]) is not int
            or not 0 <= data["since_ms"] < 253_402_300_799_999 or type(data["queues"]) is not dict):
        raise ValueError("invalid_alert_receipt")
    policy = render_group_a_policy(release)
    scopes = {unit.removesuffix("-strategy.service") for unit in policy.services if unit.endswith("-strategy.service")}
    if set(data["queues"]) != scopes:
        raise ValueError("invalid_alert_receipt_scope")
    queues = {}
    for scope, entry in data["queues"].items():
        if type(entry) is not list or len(entry) != 2:
            raise ValueError("invalid_alert_receipt_queue")
        queues[scope] = QueueIdentity(identity(entry[0]), identity(entry[1]))
    return ReleaseIdentity(identity(data["root"]), queues), data["since_ms"]


def _run(role, release, instance, *, credential_root, cursor_root=None, proc_root=None):
    policy = render_group_a_policy(release)
    prefix = policy.target.removesuffix(".target")
    if role == "terminal":
        terminal_failure(release, instance)
        unit = f"{prefix}-failed@{instance}.service"
    elif role == "watch-once" and instance is None:
        unit = f"{prefix}-watcher.service"
        if cursor_root is None or proc_root is None:
            raise ValueError("protected_alert_cursor_required")
    else:
        raise ValueError("invalid_alert_role")
    with _directory((credential_root / unit).parts) as credentials:
        if not os.fstatvfs(credentials).f_flag & os.ST_RDONLY:
            raise ValueError("unsafe_alert_credential_mount")
        webhook = _read_credential(credentials, "slack-webhook", 421).decode("ascii").removesuffix("\n")
        if _webhook_path(webhook) is None:
            raise ValueError("invalid_alert_webhook")
        cfg = {"alerts": {"enabled": True, "slack_webhook_url": webhook}}
        if role == "terminal":
            return deliver_terminal_alert(release, instance, cfg=cfg)
        receipt, since_ms = _receipt(_read_credential(credentials, "queue-receipt", 8192), release)
        with _directory(cursor_root.parent.parts) as parent:
            info = os.fstat(parent)
            if info.st_uid != 0 or info.st_mode & 0o022:
                raise ValueError("unsafe_alert_cursor_parent")
            with _directory((cursor_root.name,), parent=parent) as directory, _directory(proc_root.parts) as proc_fd:
                observation = observe_owned_group_a_queues(release, receipt, since_ms=since_ms,
                                                           proc_fd=proc_fd, track_events=True)
                return deliver_watcher_image_alert(release, directory, observation, cfg=cfg).outcome


def _summary_once(request, deadline, directory, *, credential_root, proc_root):
    release = request["release"]
    policy = render_group_a_policy(release)
    unit = policy.target.removesuffix(".target") + "-watcher.service"
    with _directory((credential_root / unit).parts) as credentials:
        if not os.fstatvfs(credentials).f_flag & os.ST_RDONLY:
            raise ValueError("unsafe_alert_credential_mount")
        webhook = _read_credential(credentials, "slack-webhook", 421).decode("ascii").removesuffix("\n")
        if _webhook_path(webhook) is None:
            raise ValueError("invalid_alert_webhook")
        receipt, since_ms = _receipt(_read_credential(credentials, "queue-receipt", 8192), release)
        cfg = {"alerts": {"enabled": True, "slack_webhook_url": webhook}}
        with _directory(proc_root.parts) as proc_fd:
            observation = observe_owned_group_a_queues(release, receipt, since_ms=since_ms,
                                                       proc_fd=proc_fd, track_events=True)
        return deliver_summary(request, directory, observation, cfg=cfg, deadline=deadline)


def _watch(release, *, credential_root, cursor_root, proc_root):
    render_group_a_policy(release)
    with _directory(cursor_root.parent.parts) as parent:
        info = os.fstat(parent)
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError("unsafe_alert_cursor_parent")
        with _directory((cursor_root.name,), parent=parent) as directory:
            return supervise(release, directory, lambda request, deadline: _summary_once(
                request, deadline, directory, credential_root=credential_root, proc_root=proc_root,
            ))


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if sys.platform != "linux" or os.geteuid() == 0 or len(args) not in (2, 3):
            raise ValueError("invalid_group_a_alert_environment")
        role, release = args[:2]
        render_group_a_policy(release)
        if role == "watch" and len(args) == 2:
            result = _watch(release, credential_root=Path("/run/credentials"),
                            cursor_root=Path(alert_cursor_dir(release)), proc_root=Path("/proc"))
            if result:
                print("group_a_alert_supervisor_failed", file=sys.stderr)
            return result
        outcome = _run(role, release, args[2] if len(args) == 3 else None,
                       credential_root=Path("/run/credentials"), cursor_root=Path(alert_cursor_dir(release)),
                       proc_root=Path("/proc"))
        if outcome in ("idle", "superseded", "slack_accepted"):
            print(f"group_a_alert_{outcome}")
            return 0
        print("group_a_alert_delivery_unconfirmed", file=sys.stderr)
        return 1
    except Exception:
        print("group_a_alert_runtime_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
