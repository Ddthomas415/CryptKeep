"""Pin opt-in trial supervision and manifest identity without launching units."""
import configparser
import json
import shlex
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("venue", ["gateio", "binance"])
def test_trial_unit_matches_manifest_and_bounds(venue):
    path = ROOT / "packaging/systemd/trials" / f"cbp-{venue}-observation.service"
    text = path.read_text()
    # Environment is repeatable in systemd; parse it separately.
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string("\n".join(line for line in text.splitlines()
                                 if not line.startswith("Environment=")))
    service = parser["Service"]
    assert service["WorkingDirectory"] == "/srv/cryptkeep/app"
    assert service["Type"] == "exec"
    assert service["RuntimeMaxSec"] == "25h"
    assert service["TimeoutStopSec"] == "30s"
    assert service["KillMode"] == "control-group"
    assert service["Restart"] == "no"
    assert service["NoNewPrivileges"] == "true"
    assert service["UMask"] == "0077"
    assert "Install" not in parser
    assert "EnvironmentFile" not in service
    args = shlex.split(service["ExecStart"])
    assert "--daily-loop" in args
    assert "--detach" not in args
    assert "--allow-first-signal-trade" not in args
    assert args[:2] == ["/srv/cryptkeep/app/.venv/bin/python",
                        "scripts/run_paper_strategy_evidence_collector.py"]
    campaigns = json.loads((ROOT / "configs/paper_evidence_campaigns.hetzner.extended_observation.json").read_text())["campaigns"]
    spec = next(c for c in campaigns if c["venue"] == venue)
    assert ("--no-desktop-notify" in args) == (not spec["desktop_notify"])
    for flag, field in [("--venue", "venue"), ("--symbol", "symbol"),
                        ("--strategies", "strategy"), ("--signal-source", "signal_source"),
                        ("--runtime-sec", "runtime_sec"), ("--max-loops", "max_loops"),
                        ("--session-strategy-id", "session_strategy_id"),
                        ("--max-daily-attempts", "max_daily_attempts"),
                        ("--poll-interval-sec", "poll_interval_sec"),
                        ("--strategy-drain-sec", "strategy_drain_sec")]:
        assert args[args.index(flag) + 1] == str(spec[field])
    env = dict(line.removeprefix("Environment=").split("=", 1)
               for line in text.splitlines() if line.startswith("Environment="))
    assert env == {"CBP_STATE_DIR": "/srv/cryptkeep/app/" + spec["state_dir"],
                   "CBP_VENUE": venue, "CBP_ALLOW_BINANCE": "1" if venue == "binance" else "0"}
