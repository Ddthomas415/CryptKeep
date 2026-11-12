"""Non-startable Group A quote publisher and consumer routing draft."""

from dataclasses import dataclass

from services.control.group_a_account_units import _STARTUP_ENV, render_group_a_account_units
from services.market_data.group_a_quote_publisher import MARKETS


@dataclass(frozen=True)
class GroupAQuoteRouting:
    target_name: str
    fragments: tuple[tuple[str, str], ...]
    launch_args: tuple[tuple[str, tuple[str, ...]], ...]
    missing_base_units: tuple[str, ...]


def render_group_a_quote_routing(release: str, *, service_user: str) -> GroupAQuoteRouting:
    accounts = render_group_a_account_units(release, service_user=service_user)
    publisher = f"{accounts.target_name.removesuffix('.target')}-publisher.service"
    if publisher not in accounts.missing_base_units:
        raise ValueError("publisher is not an open Group A base role")
    root = f"/srv/cryptkeep/state/{release}/support/publisher"
    snapshots = f"{root}/runtime/snapshots"
    locks = f"{root}/runtime/locks"
    source = f"/srv/cryptkeep/releases/{release}"
    fragments = []
    for (name, text), (launch_name, args) in zip(accounts.account_files, accounts.launch_args, strict=True):
        if name != launch_name:
            raise ValueError("account fragment and launch identity mismatch")
        state, = (arg.removeprefix("CBP_STATE_DIR=") for arg in args if arg.startswith("CBP_STATE_DIR="))
        # Bind the directory, not the file inode: atomic replacements must be visible.
        fragments.append((name, text + f"BindReadOnlyPaths={snapshots}:{state}/runtime/snapshots:norbind\n"))
    fragments.append((
        publisher,
        "[Unit]\n"
        "Description=CryptKeep Group A public quote publisher\n"
        f"AssertPathIsDirectory={snapshots}\n"
        f"AssertPathIsDirectory={locks}\n"
        "\n[Service]\n"
        "Type=exec\n"
        f"User={service_user}\n"
        f"WorkingDirectory={source}\n"
        "NoNewPrivileges=yes\n"
        "ProtectSystem=strict\n"
        "ProtectHome=yes\n"
        "PrivateTmp=yes\n"
        "UMask=0077\n"
        "StandardOutput=null\n"
        f"ReadWritePaths={snapshots} {locks}\n"
        f"UnsetEnvironment={_STARTUP_ENV}\n",
    ))
    publisher_args = (
        "/usr/bin/env", "-i", "PATH=/usr/bin:/bin", f"CBP_STATE_DIR={root}",
        "CBP_COMPONENT_VENUE=coinbase", f"CBP_COMPONENT_SYMBOLS={','.join(MARKETS)}",
        f"{source}/.venv/bin/python", "-B", f"{source}/scripts/run_group_a_quote_publisher.py", release,
    )
    return GroupAQuoteRouting(
        accounts.target_name, tuple(fragments), (*accounts.launch_args, (publisher, publisher_args)),
        tuple(name for name in accounts.missing_base_units if name != publisher),
    )
