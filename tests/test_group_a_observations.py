from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from services.alerts.group_a_fetch_health import CandleFetchHealth, FILENAME
from services.alerts.group_a_observations import observe_group_a_status
from services.alerts.group_a_watch import WatchFinding


NOW = 1_790_000_000_010
WRITER = "b" * 32
SCOPE = "cbp-group-a-frozen42-breakout-default-btc"


def _flags(tmp_path):
    root = tmp_path.resolve() / "frozen42"
    flags = root / "breakout-default-btc" / "runtime" / "flags"
    flags.mkdir(parents=True)
    return root, flags


def _status(path, stamp=NOW, **fields):
    path.write_text(json.dumps({
        "ok": True, "status": "running",
        "ts": datetime.fromtimestamp(stamp / 1000, timezone.utc).isoformat(), **fields,
    }))


def _checkpoint(flags):
    class Exchange:
        def on_rest_response(self, status):
            pass

    exchange = Exchange()
    writer = CandleFetchHealth(flags / FILENAME, "BTC/USD", clock_ms=lambda: NOW, writer_id=WRITER)
    for _ in range(10):
        with writer.attempt(exchange):
            exchange.on_rest_response(429)
    return writer.attempt_seq


def test_reads_both_statuses_and_matching_checkpoint_without_touching_other_files(tmp_path):
    root, flags = _flags(tmp_path)
    seq = _checkpoint(flags)
    _status(flags / "strategy_runner.status.json", note="kill_cooldown",
            group_a_fetch_writer=WRITER, group_a_fetch_attempt=seq)
    _status(flags / "paper_engine.status.json", NOW - 601_000)
    (flags / "user.yaml").write_text("synthetic configuration; never read")
    before = {path: path.read_bytes() for path in flags.iterdir()}
    result = observe_group_a_status("frozen42", root, now_ms=NOW)
    assert result.alerts == tuple(WatchFinding(SCOPE, code) for code in (
        "paper_status_stale", "kill_cooldown", "candle_fetch_failures", "http_429_burst",
    ))
    assert WatchFinding(SCOPE, "quote_stale") in result.missing
    assert WatchFinding(SCOPE, "order_refused") in result.missing
    assert {path: path.read_bytes() for path in flags.iterdir()} == before


@pytest.mark.parametrize(("writer", "attempt", "state", "age_ms"), [
    ("c" * 32, 10, "running", 0),
    (WRITER, 11, "running", 0),
    (WRITER, True, "running", 0),
    (WRITER, 10, "stopped", 0),
    (WRITER, 10, "running", 601_000),
])
def test_old_or_unbound_checkpoint_never_becomes_current(tmp_path, writer, attempt, state, age_ms):
    root, flags = _flags(tmp_path)
    assert _checkpoint(flags) == 10
    _status(flags / "strategy_runner.status.json", NOW - age_ms,
            status=state, group_a_fetch_writer=writer, group_a_fetch_attempt=attempt)
    report = observe_group_a_status("frozen42", root, now_ms=NOW)
    assert WatchFinding(SCOPE, "candle_fetch_failures") in report.missing
    assert WatchFinding(SCOPE, "http_429_burst") in report.missing
    assert WatchFinding(SCOPE, "candle_fetch_failures") not in report.alerts


@pytest.mark.parametrize("bad", ["symlink", "hardlink", "duplicate", "oversize", "future", "fifo"])
def test_status_path_and_parser_fail_closed(tmp_path, bad):
    root, flags = _flags(tmp_path)
    path = flags / "strategy_runner.status.json"
    if bad in ("symlink", "hardlink"):
        other = tmp_path / "other.json"
        _status(other, NOW - 601_000)
        if bad == "symlink":
            path.symlink_to(other)
        else:
            os.link(other, path)
    elif bad == "duplicate":
        path.write_text('{"ok":true,"ok":true,"ts":"2025-01-01T00:00:00+00:00"}')
    elif bad == "oversize":
        path.write_text(" " * 140_000)
    elif bad == "future":
        _status(path, NOW + 1000)
    else:
        os.mkfifo(path)
    report = observe_group_a_status("frozen42", root, now_ms=NOW)
    assert report.alerts == ()
    assert WatchFinding(SCOPE, "strategy_status_stale") in report.missing


def test_release_does_not_follow_an_account_directory_link(tmp_path):
    root, flags = _flags(tmp_path)
    actual = tmp_path / "other-account"
    account = flags.parent.parent
    account.rename(actual)
    _status(actual / "runtime" / "flags" / "strategy_runner.status.json", NOW - 601_000)
    account.symlink_to(actual, target_is_directory=True)
    report = observe_group_a_status("frozen42", root, now_ms=NOW)
    assert report.alerts == ()
    assert WatchFinding(SCOPE, "strategy_status_stale") in report.missing


def test_duplicate_checkpoint_identity_is_unknown(tmp_path):
    root, flags = _flags(tmp_path)
    seq = _checkpoint(flags)
    _status(flags / "strategy_runner.status.json", group_a_fetch_writer=WRITER, group_a_fetch_attempt=seq)
    checkpoint = flags / FILENAME
    checkpoint.write_text('{"writer_id":"' + "f" * 32 + '","attempt_seq":99,' + checkpoint.read_text()[1:])
    report = observe_group_a_status("frozen42", root, now_ms=NOW)
    assert WatchFinding(SCOPE, "candle_fetch_failures") in report.missing
    assert WatchFinding(SCOPE, "http_429_burst") not in report.alerts


def test_fresh_import_and_absent_release_are_read_only(tmp_path):
    absent = tmp_path.resolve() / "frozen42"
    child = subprocess.run(
        [sys.executable, "-B", "-c", "from pathlib import Path; import sys; "
         "from services.alerts.group_a_observations import observe_group_a_status; "
         "assert len(observe_group_a_status('frozen42', Path(sys.argv[1]), now_ms=1790000000010).missing)==93",
         str(absent)], cwd=Path(__file__).resolve().parents[1],
        env={"PATH": "/usr/bin:/bin", "CBP_STATE_DIR": str(absent)}, timeout=10, check=True,
    )
    assert child.returncode == 0 and not absent.exists()
