from configparser import ConfigParser

import pytest

from services.control.group_a_account_units import render_group_a_account_units
from services.control.group_a_systemd_policy import render_group_a_policy
from services.strategies.presets import get_preset


def _parse(text):
    config = ConfigParser(interpolation=None)
    config.read_string(text)
    return config


def test_partial_composition_does_not_expose_target_or_executable_unit():
    draft = render_group_a_account_units("frozen42", service_user="cbp-ga-test")
    assert not hasattr(draft, "policy")
    assert all(name.endswith(".service") for name, _ in draft.account_files)
    for _, text in draft.account_files:
        unit = _parse(text)
        assert "Install" not in unit
        assert not any(key.startswith("exec") for key in unit["Service"])


def test_manager_unsets_loader_variables_before_the_env_wrapper():
    draft = render_group_a_account_units("frozen42", service_user="cbp-ga-test")
    for _, text in draft.account_files:
        names = _parse(text)["Service"].get("UnsetEnvironment", "").split()
        assert {"LD_PRELOAD", "LD_LIBRARY_PATH", "LD_AUDIT", "LD_TRACE_LOADED_OBJECTS",
                "LD_DEBUG", "LD_DEBUG_OUTPUT", "GLIBC_TUNABLES", "GCONV_PATH"} <= set(names)
        assert all(name.isascii() and name.replace("_", "").isalnum() for name in names)


def test_account_base_units_match_the_reviewed_lifecycle_and_report_missing_roles():
    composition = render_group_a_account_units("frozen42", service_user="cbp-ga-test")
    policy = render_group_a_policy("frozen42")
    accounts = dict(composition.account_files)
    missing = composition.missing_base_units
    assert composition.target_name == policy.target
    assert len(accounts) == len(composition.account_files) == 18
    assert len(composition.launch_args) == 18
    assert set(dict(composition.launch_args)) == set(accounts)
    assert set(accounts) == set(policy.services) - set(missing)
    assert all(f"{name}.d/50-group-a-lifecycle.conf" in dict(policy.files) for name in accounts)
    assert missing == (
        "cbp-group-a-frozen42-publisher.service", "cbp-group-a-frozen42-watcher.service",
        "cbp-group-a-frozen42-backup.service", "cbp-group-a-frozen42-failed@.service",
    )
    assert set(accounts).isdisjoint(missing)


def test_account_pairs_share_only_their_own_release_state_and_paper_launchers():
    release = "frozen42"
    user = "cbp-ga-test"
    composition = render_group_a_account_units(release, service_user=user)
    files = dict(composition.account_files)
    launch_args = dict(composition.launch_args)
    source = "/srv/cryptkeep/releases/frozen42"
    states = set()
    for preset in ("breakout_default", "ema_cross_default", "mean_reversion_default"):
        for asset in ("BTC", "ETH", "SOL"):
            account = f"{preset.replace('_', '-')}-{asset.lower()}"
            state = f"/srv/cryptkeep/state/{release}/{account}"
            config = f"{state}/runtime/config/user.yaml"
            states.add(state)
            for role, script in (("strategy", "run_strategy_runner.py"), ("paper", "run_paper_engine.py")):
                name = f"cbp-group-a-{release}-{account}-{role}.service"
                unit = _parse(files[name])
                assert set(unit) == {"DEFAULT", "Unit", "Service"}
                assert unit["Unit"]["AssertPathIsDirectory"] == state
                assert unit["Unit"]["AssertPathExists"] == config
                service = unit["Service"]
                assert dict(service.items()).keys() == {
                    "type", "user", "workingdirectory", "nonewprivileges", "protectsystem",
                    "protecthome", "privatetmp", "umask", "readwritepaths", "readonlypaths", "unsetenvironment",
                }
                assert service["User"] == user
                assert service["Type"] == "exec"
                assert service["WorkingDirectory"] == source
                assert service["ProtectSystem"] == "strict"
                assert service["ProtectHome"] == service["NoNewPrivileges"] == service["PrivateTmp"] == "yes"
                assert service["UMask"] == "0077"
                assert service["ReadWritePaths"] == state
                assert service["ReadOnlyPaths"] == config
                argv = launch_args[name]
                assert argv[:2] == ("/usr/bin/env", "-i")
                assert argv[-4:] == (f"{source}/.venv/bin/python", "-B", f"{source}/scripts/{script}", "run")
                expected = {
                    "PATH": "/usr/bin:/bin", "CBP_STATE_DIR": state, "CBP_COMPONENT_VENUE": "coinbase",
                    "CBP_COMPONENT_SYMBOLS": f"{asset}/USD", "CBP_LOG_COMPONENT": role,
                }
                if role == "strategy":
                    strategy = get_preset(preset)["strategy"]["name"]
                    expected.update(
                        CBP_STRATEGY_NAME=strategy, CBP_STRATEGY_ID=strategy, CBP_STRATEGY_PRESET=preset,
                        CBP_STRATEGY_SIGNAL_SOURCE="public_ohlcv_1h", CBP_CAPTURE_RUNNER_DECISIONS="1",
                        CBP_CAPTURE_GROUP_A_FETCH_HEALTH="1",
                    )
                assert len(argv[2:-4]) == len(expected)
                assert dict(item.split("=", 1) for item in argv[2:-4]) == expected
    assert len(states) == 9


def test_second_release_cannot_share_account_names_or_declared_roots():
    first, second = (render_group_a_account_units(r, service_user="cbp-ga-test") for r in ("frozen42", "frozen43"))
    assert dict(first.account_files).keys().isdisjoint(dict(second.account_files))
    first_paths = {_parse(text)["Service"]["ReadWritePaths"] for _, text in first.account_files}
    second_paths = {_parse(text)["Service"]["ReadWritePaths"] for _, text in second.account_files}
    assert first_paths.isdisjoint(second_paths)


@pytest.mark.parametrize("user", ["root", "cbp", "cbp-ga-", "cbp-ga-root\nUser=root", "cbp-ga-%i", "", None])
def test_unit_user_requires_a_safe_dedicated_name(user):
    with pytest.raises(ValueError, match="dedicated"):
        render_group_a_account_units("frozen42", service_user=user)


def test_rejects_injected_release_path():
    with pytest.raises(ValueError, match="release must be"):
        render_group_a_account_units("frozen42/../../app", service_user="cbp-ga-test")
