from configparser import ConfigParser
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import run_group_a_quote_publisher
from services.control.group_a_account_units import render_group_a_account_units
from services.control.group_a_quote_routing import render_group_a_quote_routing
from services.market_data import group_a_quote_publisher as publisher, tick_reader
from services.market_data.paper_snapshot_quote import read_paper_quote


NOW = 1793802000.0
STAMP = int(NOW * 1000) - 500


def _tick(symbol, bid=100, **updates):
    return {
        "venue": "coinbase", "symbol": symbol, "symbol_mapped": symbol, "ticker_symbol": symbol,
        "source": "public_ticker", "bid": bid, "ask": bid + 2, "last": bid + 1,
        "ts_ms": STAMP + 100, **updates,
    }


def test_one_atomic_snapshot_is_read_by_all_three_strict_market_readers(tmp_path, monkeypatch):
    rows = [_tick(market, bid=100 + i * 50) for i, market in enumerate(publisher.MARKETS)]
    target = tmp_path / publisher.SNAPSHOT_NAME
    monkeypatch.setattr(tick_reader, "LATEST", target)
    calls = []

    def fetch():
        calls.append("one")
        return {"ts_ms": STAMP, "ticks": rows}

    assert publisher.publish_once(tmp_path, fetch=fetch, clock=lambda: NOW) == 3
    assert calls == ["one"]
    for row in rows:
        quote, reason = read_paper_quote("coinbase", row["symbol"], clock=lambda: NOW)
        assert reason is None and quote["bid"] == row["bid"] and quote["ts_ms"] == row["ts_ms"]
    assert publisher.publish_once(
        tmp_path, fetch=lambda: {"ts_ms": STAMP, "ticks": []}, clock=lambda: NOW,
    ) == 0
    assert read_paper_quote("coinbase", "BTC/USD", clock=lambda: NOW) == (None, "missing_quote")


def test_projection_preserves_other_markets_but_drops_duplicate_wrong_stale_and_sample():
    for bad in (
        [_tick("BTC/USD"), _tick("btc-usd")],
        [_tick("BTC/USD", symbol_mapped="ETH/USD", ticker_symbol="ETH/USD")],
        [_tick("BTC/USD", source="sample_ohlcv")],
        [_tick("BTC/USD", ts_ms=STAMP - 1)],
        [_tick("BTC/USD", ts_ms=int(NOW * 1000) + 1)],
        [_tick("BTC/USD", ask=float("nan"))],
        [_tick("BTC/USD", venue="kraken")],
    ):
        out = publisher.project_snapshot(
            {"ts_ms": STAMP, "ticks": [*bad, _tick("SOL/USD", last=float("inf"))]}, now=NOW,
        )
        assert [row["symbol"] for row in out["ticks"]] == ["SOL/USD"]
        assert out["ts_ms"] == STAMP and out["ticks"][0]["last"] is None
    assert publisher.project_snapshot(
        {"ts_ms": STAMP - 5000, "ticks": [_tick("SOL/USD")]}, now=NOW,
    ) == {"ts_ms": 0, "ticks": []}


def test_atomic_replace_failure_does_not_touch_old_snapshot(tmp_path, monkeypatch):
    target = tmp_path / publisher.SNAPSHOT_NAME
    target.write_text('{"previous":true}')

    def broken_replace(src, dest):
        assert json.loads(src.read_text())["ticks"][0]["symbol"] == "BTC/USD"
        assert dest == target
        raise OSError("synthetic write failure")

    monkeypatch.setattr(publisher.os, "replace", broken_replace)
    with pytest.raises(OSError, match="synthetic"):
        publisher.publish_once(
            tmp_path, fetch=lambda: {"ts_ms": STAMP, "ticks": [_tick("BTC/USD")]}, clock=lambda: NOW,
        )
    assert target.read_text() == '{"previous":true}'
    assert list(tmp_path.iterdir()) == [target]


def test_lock_refuses_duplicate_and_releases_after_abrupt_child_exit(tmp_path):
    with publisher.publisher_lock(tmp_path):
        with pytest.raises(BlockingIOError), publisher.publisher_lock(tmp_path):
            pytest.fail("duplicate lock")
    absent_state = tmp_path / "unused-state"
    child = subprocess.run(
        [sys.executable, "-B", "-c", "import os, sys; from pathlib import Path; "
         "from services.market_data.group_a_quote_publisher import publisher_lock; "
         "lock = publisher_lock(Path(sys.argv[1])); lock.__enter__(); os._exit(0)", str(tmp_path)],
        env={"PATH": os.defpath, "CBP_STATE_DIR": str(absent_state)},
        cwd=Path(__file__).resolve().parents[1], timeout=10, check=True,
    )
    assert child.returncode == 0
    assert not absent_state.exists()
    with publisher.publisher_lock(tmp_path):
        assert (tmp_path / "publisher.flock").is_file()


def test_lock_does_not_follow_another_filesystem_entry(tmp_path):
    other = tmp_path / "other"
    other.write_text("keep")
    (tmp_path / "publisher.flock").symlink_to(other)
    with pytest.raises(OSError), publisher.publisher_lock(tmp_path):
        pytest.fail("followed lock symlink")
    assert other.read_text() == "keep"


def test_entrypoint_refuses_unscoped_state_before_launch(monkeypatch, capsys):
    monkeypatch.setenv("CBP_STATE_DIR", "/srv/cryptkeep/app/.cbp_state")
    assert run_group_a_quote_publisher.main(["frozen42"]) == 1
    assert capsys.readouterr().err == "group_a_quote_publisher_failed\n"


@pytest.mark.parametrize(("argv", "exit_code", "stderr"), [
    (["scripts/run_group_a_quote_publisher.py", "frozen42"], 1, "group_a_quote_publisher_failed\n"),
    (["-c", "from services.control.group_a_quote_routing import render_group_a_quote_routing; "
      "render_group_a_quote_routing('frozen42', service_user='cbp-ga-test')"], 0, ""),
])
def test_fresh_process_leaves_unowned_state_absent(tmp_path, argv, exit_code, stderr):
    absent = tmp_path / "never-create"
    child = subprocess.run(
        [sys.executable, "-B", *argv], cwd=Path(__file__).resolve().parents[1],
        env={"PATH": os.defpath, "CBP_STATE_DIR": str(absent)}, timeout=10,
        capture_output=True, text=True, check=False,
    )
    assert child.returncode == exit_code and child.stderr == stderr and child.stdout == ""
    assert not absent.exists()


def test_draft_only_binds_quote_directory_from_same_release_into_every_account():
    release = "frozen42"
    base = render_group_a_account_units(release, service_user="cbp-ga-test")
    draft = render_group_a_quote_routing(release, service_user="cbp-ga-test")
    root = f"/srv/cryptkeep/state/{release}/support/publisher"
    quotes = f"{root}/runtime/snapshots"
    publisher_name = "cbp-group-a-frozen42-publisher.service"
    units = dict(draft.fragments)
    args = dict(draft.launch_args)
    assert draft.target_name == base.target_name
    assert len(units) == len(args) == 19
    assert draft.missing_base_units == tuple(name for name in base.missing_base_units if name != publisher_name)
    for name, text in base.account_files:
        assert args[name] == dict(base.launch_args)[name]
        state, = [arg.split("=", 1)[1] for arg in args[name] if arg.startswith("CBP_STATE_DIR=")]
        assert units[name] == text + f"BindReadOnlyPaths={quotes}:{state}/runtime/snapshots:norbind\n"
    for text in units.values():
        unit = ConfigParser(strict=False, interpolation=None)
        unit.read_string(text)
        assert "Install" not in unit
        assert not any(key.startswith("exec") for key in unit["Service"])
    assert f"ReadWritePaths={quotes} {root}/runtime/locks\n" in units[publisher_name]
    assert "CBP_COMPONENT_SYMBOLS=BTC/USD,ETH/USD,SOL/USD" in args[publisher_name]
    assert args[publisher_name][-2:] == (
        "/srv/cryptkeep/releases/frozen42/scripts/run_group_a_quote_publisher.py", release,
    )
