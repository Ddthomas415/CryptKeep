"""Non-startable Group A alert unit fragments and review-only launcher argv."""

from dataclasses import dataclass

from services.control.group_a_account_units import _STARTUP_ENV, render_group_a_account_units


def alert_cursor_dir(release):
    return f"/srv/cryptkeep/alert-state/{release}"


@dataclass(frozen=True)
class GroupAAlertUnits:
    fragments: tuple[tuple[str, str], ...]
    launch_args: tuple[tuple[str, tuple[str, ...]], ...]


def render_group_a_alert_units(release: str, *, service_user: str, alert_user: str) -> GroupAAlertUnits:
    if type(release) is not str or type(service_user) is not str or type(alert_user) is not str:
        raise ValueError("invalid_group_a_alert_unit_input")
    accounts = render_group_a_account_units(release, service_user=service_user)
    render_group_a_account_units(release, service_user=alert_user)
    if service_user == alert_user:
        raise ValueError("group_a_alert_user_must_be_distinct")
    prefix = accounts.target_name.removesuffix(".target")
    watcher = f"{prefix}-watcher.service"
    failure = f"{prefix}-failed@.service"
    state = f"/srv/cryptkeep/state/{release}"
    cursor = alert_cursor_dir(release)
    source = f"/srv/cryptkeep/releases/{release}"
    cred = f"/etc/cryptkeep/group-a/{release}"
    common = (
        "[Service]\n" f"User={alert_user}\nWorkingDirectory={source}\n"
        "NoNewPrivileges=yes\nProtectSystem=strict\nProtectHome=yes\nPrivateTmp=yes\n"
        "UMask=0077\nLimitCORE=0\nCapabilityBoundingSet=\nRestrictSUIDSGID=yes\n"
        "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6\n"
        f"UnsetEnvironment={_STARTUP_ENV}\n"
        f"LoadCredentialEncrypted=slack-webhook:{cred}/slack-webhook.cred\n"
    )
    fragments = (
        (watcher, "[Unit]\n" f"AssertPathIsDirectory={state}\nAssertPathIsDirectory={cursor}\n\n"
         + common + f"ReadOnlyPaths={state}\nReadWritePaths={cursor}\n"
         f"LoadCredential=queue-receipt:{cred}/queue-receipt.json\n"),
        (failure, common + "Type=oneshot\nTimeoutStartSec=15s\n" + f"InaccessiblePaths={state} {cursor}\n"),
    )
    argv = ("/usr/bin/env", "-i", "PATH=/usr/bin:/bin", f"{source}/.venv/bin/python", "-I", "-B",
            f"{source}/scripts/run_group_a_alert.py")
    return GroupAAlertUnits(fragments, (
        (watcher, (*argv, "watch", release)),
        (failure, (*argv, "terminal", release, "%i")),
    ))
