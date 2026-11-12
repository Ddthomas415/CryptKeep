"""Render offline R2 lifecycle policy; never install or operate units."""

from dataclasses import dataclass
import re


_STRATEGIES = ("breakout-default", "ema-cross-default", "mean-reversion-default")
_ASSETS = ("btc", "eth", "sol")
_ACCOUNT_COMPONENTS = ("strategy", "paper")
_SUPPORT_COMPONENTS = ("publisher", "watcher", "backup")


@dataclass(frozen=True)
class GroupAPolicy:
    target: str
    services: tuple[str, ...]
    failure_services: tuple[str, ...]
    # Review metadata only. Execute neither this argv nor the rendered policy
    # without verifying the host's effective graph and ownership.
    stop_argv: tuple[str, ...]
    files: tuple[tuple[str, str], ...]


def render_group_a_policy(release: str) -> GroupAPolicy:
    """Return the frozen Group A membership and its systemd 254+ policy overlay.

    The matching foreground service definitions and failure hook are separate
    release inputs. A drop-in is not proof of what a base unit executes.
    """
    if not isinstance(release, str) or not re.fullmatch(r"[a-z0-9]{8,40}", release):
        raise ValueError("release must be 8-40 lowercase ASCII letters or digits")

    prefix = f"cbp-group-a-{release}"
    target = f"{prefix}.target"
    services = tuple(
        f"{prefix}-{strategy}-{asset}-{component}.service"
        for strategy in _STRATEGIES
        for asset in _ASSETS
        for component in _ACCOUNT_COMPONENTS
    ) + tuple(f"{prefix}-{component}.service" for component in _SUPPORT_COMPONENTS)

    failure_template = f"{prefix}-failed@.service"
    failure_services = tuple(
        f"{prefix}-failed@{unit.removesuffix('.service')}.service" for unit in services
    )
    target_text = (
        "[Unit]\n"
        "Description=CryptKeep Group A paper simulation\n"
        f"Wants={' '.join(services)}\n"
        "JobTimeoutSec=50s\n"
        "\n[Install]\n"
        "WantedBy=multi-user.target\n"
    )
    stop_policy = (
        "[Unit]\n"
        f"PartOf={target}\n"
        "JobTimeoutSec=50s\n"
    )
    restart_policy = (
        "StartLimitIntervalSec=300s\n"
        "StartLimitBurst=4\n"
        "\n[Service]\n"
        "Restart=on-failure\n"
        "RestartMode=direct\n"
        "RestartSec=2s\n"
        "RestartSteps=3\n"
        "RestartMaxDelaySec=12s\n"
        "KillMode=control-group\n"
        "TimeoutStopSec=20s\n"
        "SendSIGKILL=yes\n"
    )
    # Requisite verifies the target without starting it. Do not let an
    # OnFailure transaction replace a stop already queued for the group.
    hook_policy = (
        stop_policy
        + f"Requisite={target}\nAfter={target}\n"
        + "\n[Service]\nKillMode=control-group\nTimeoutStopSec=20s\nSendSIGKILL=yes\n"
    )
    files = (
        (target, target_text),
        (f"{failure_template}.d/50-group-a-lifecycle.conf", hook_policy),
    ) + tuple(
        (f"{unit}.d/50-group-a-lifecycle.conf",
         stop_policy + f"OnFailure={failure}\nOnFailureJobMode=fail\n" + restart_policy)
        for unit, failure in zip(services, failure_services, strict=True)
    )
    return GroupAPolicy(
        target=target,
        services=services,
        failure_services=failure_services,
        stop_argv=("systemctl", "--system", "stop", "--", target, *services, *failure_services),
        files=files,
    )
