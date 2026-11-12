"""Compose the account side of the offline Group A systemd candidate."""

from dataclasses import dataclass
import re

from services.control.group_a_systemd_policy import render_group_a_policy


_STRATEGIES = (
    ("breakout_default", "breakout_donchian"),
    ("ema_cross_default", "ema_cross"),
    ("mean_reversion_default", "mean_reversion_rsi"),
)
_ASSETS = ("BTC", "ETH", "SOL")
_ENTRYPOINTS = {"strategy": "run_strategy_runner.py", "paper": "run_paper_engine.py"}
# glibc startup controls, including legacy and diagnostic loader switches.
# A future compositor must verify the actual loader and manager environment.
_STARTUP_ENV = (
    "GCONV_PATH GETCONF_DIR GLIBC_TUNABLES HOSTALIASES "
    "LD_ASSUME_KERNEL LD_AUDIT LD_BIND_NOT LD_BIND_NOW LD_DEBUG LD_DEBUG_OUTPUT "
    "LD_DYNAMIC_WEAK LD_HWCAP_MASK LD_LIBRARY_PATH LD_ORIGIN_PATH LD_PRELOAD "
    "LD_PROFILE LD_PROFILE_OUTPUT LD_SHOW_AUXV LD_TRACE_LOADED_OBJECTS "
    "LD_TRACE_PRELINKING LD_USE_LOAD_BIAS LD_VERBOSE LD_WARN LD_PREFER_MAP_32BIT_EXEC "
    "LOCALDOMAIN LOCPATH MALLOC_ARENA_MAX MALLOC_ARENA_TEST MALLOC_CHECK_ "
    "MALLOC_MMAP_MAX_ MALLOC_MMAP_THRESHOLD_ MALLOC_PERTURB_ MALLOC_TOP_PAD_ "
    "MALLOC_TRACE MALLOC_TRIM_THRESHOLD_ NIS_PATH NLSPATH RESOLV_HOST_CONF RES_OPTIONS TMPDIR TZDIR"
)


@dataclass(frozen=True)
class GroupAAccountUnits:
    target_name: str
    # Fragments lack executable directives. Argv is review metadata, not a
    # generated ExecStart or approval to run.
    account_files: tuple[tuple[str, str], ...]
    launch_args: tuple[tuple[str, tuple[str, ...]], ...]
    missing_base_units: tuple[str, ...]


def render_group_a_account_units(release: str, *, service_user: str) -> GroupAAccountUnits:
    """Return non-startable account fragments and separate intended argv.

    The user, physical paths, source/config bytes and effective Linux unit
    graph still require verification. No target file, installer or promotion
    path is emitted.
    """
    policy = render_group_a_policy(release)
    if not isinstance(service_user, str) or not re.fullmatch(r"cbp-ga-[a-z0-9][a-z0-9-]{0,24}", service_user):
        raise ValueError("a dedicated cbp-ga-* service user is required")

    prefix = policy.target.removesuffix(".target")
    source = f"/srv/cryptkeep/releases/{release}"
    files = []
    launch_args = []
    for preset, strategy in _STRATEGIES:
        for asset in _ASSETS:
            account = f"{preset.replace('_', '-')}-{asset.lower()}"
            state = f"/srv/cryptkeep/state/{release}/{account}"
            config = f"{state}/runtime/config/user.yaml"
            for role, entrypoint in _ENTRYPOINTS.items():
                env = [
                    "PATH=/usr/bin:/bin",
                    f"CBP_STATE_DIR={state}",
                    "CBP_COMPONENT_VENUE=coinbase",
                    f"CBP_COMPONENT_SYMBOLS={asset}/USD",
                    f"CBP_LOG_COMPONENT={role}",
                ]
                if role == "strategy":
                    env.extend((
                        f"CBP_STRATEGY_NAME={strategy}",
                        f"CBP_STRATEGY_ID={strategy}",
                        f"CBP_STRATEGY_PRESET={preset}",
                        "CBP_STRATEGY_SIGNAL_SOURCE=public_ohlcv_1h",
                        "CBP_CAPTURE_RUNNER_DECISIONS=1",
                        "CBP_CAPTURE_GROUP_A_FETCH_HEALTH=1",
                    ))
                name = f"{prefix}-{account}-{role}.service"
                launch_args.append((name, (
                    "/usr/bin/env", "-i", *env, f"{source}/.venv/bin/python", "-B",
                    f"{source}/scripts/{entrypoint}", "run",
                )))
                files.append((
                    name,
                    "[Unit]\n"
                    f"Description=CryptKeep Group A {account} {role}\n"
                    f"AssertPathIsDirectory={state}\n"
                    f"AssertPathExists={config}\n"
                    "\n[Service]\n"
                    "Type=exec\n"
                    f"User={service_user}\n"
                    f"WorkingDirectory={source}\n"
                    "NoNewPrivileges=yes\n"
                    "ProtectSystem=strict\n"
                    "ProtectHome=yes\n"
                    "PrivateTmp=yes\n"
                    "UMask=0077\n"
                    f"ReadWritePaths={state}\n"
                    f"ReadOnlyPaths={config}\n"
                    f"UnsetEnvironment={_STARTUP_ENV}\n",
                ))
    names = {name for name, _ in files}
    missing = (
        f"{prefix}-publisher.service",
        f"{prefix}-watcher.service",
        f"{prefix}-backup.service",
    )
    if len(names) != len(files) or names != set(policy.services) - set(missing):
        raise ValueError("account base units do not match the Group A lifecycle roster")
    return GroupAAccountUnits(
        policy.target, tuple(files), tuple(launch_args), (*missing, f"{prefix}-failed@.service"),
    )
