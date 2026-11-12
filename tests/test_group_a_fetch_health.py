import json
from pathlib import Path
import subprocess
import sys

import pytest

from services.alerts import group_a_fetch_health as health
from services.alerts.group_a_watch import (
    AccountObservation, HostObservation, WatchFinding, assess_group_a_watch,
)


class Exchange:
    def on_rest_response(self, code, body):
        return body


def _record(log, statuses=(), *, success=False):
    exchange = Exchange()
    with log.attempt(exchange) as result:
        for status in statuses:
            assert exchange.on_rest_response(status, "unchanged payload") == "unchanged payload"
        result.success = success
    assert "on_rest_response" not in vars(exchange)


def test_real_429s_and_failure_streak_drive_the_accepted_watcher(tmp_path):
    path = tmp_path / health.FILENAME
    now = [1_790_000_000_010]
    clock = lambda: now[0]
    log = health.CandleFetchHealth(path, "BTC/USD", clock_ms=clock)
    for i in range(10):
        _record(log, (429, 503) if i < 5 else (503, "429"))
        now[0] += 1000
    failures, burst = health.watcher_fetch_counts(path, "BTC/USD", now_ms=clock())
    assert (failures, burst) == (10, 5)
    account = "cbp-group-a-frozen42-breakout-default-btc"
    assert assess_group_a_watch("frozen42", accounts={
        account: AccountObservation(consecutive_candle_failures=failures, http_429_last_10_min=burst),
    }, host=HostObservation()).alerts == (
        WatchFinding(account, "candle_fetch_failures"), WatchFinding(account, "http_429_burst"),
    )
    _record(log, (429,), success=True)
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=clock()) == (0, 6)
    assert "unchanged payload" not in path.read_text()
    _record(health.CandleFetchHealth(path, "BTC/USD", clock_ms=clock))
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=clock()) == (None, 6)


def test_window_boundary_and_unknown_prefix_do_not_create_false_counts(tmp_path):
    now = [1_790_000_000_010]
    path = tmp_path / health.FILENAME
    log = health.CandleFetchHealth(path, "BTC/USD", clock_ms=lambda: now[0])
    _record(log, [429] * 5, success=True)
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now[0] + 599_980) == (0, 5)
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now[0] + 600_000) == (0, None)
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now[0] + 600_001) == (None, None)
    now[0] += 600_000
    _record(log, success=True)
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now[0] + 1000) == (0, 0)


def test_abrupt_exit_leaves_pending_marker_and_recovers_known_previous_responses(tmp_path):
    path = tmp_path / health.FILENAME
    now = 1_790_000_000_010
    _record(health.CandleFetchHealth(path, "BTC/USD", clock_ms=lambda: now), [429] * 4, success=True)
    subprocess.run(
        [sys.executable, "-B", "-c", "import os,sys; from pathlib import Path; "
         "from services.alerts.group_a_fetch_health import CandleFetchHealth; "
         "attempt=CandleFetchHealth(Path(sys.argv[1]), 'BTC/USD', clock_ms=lambda: int(sys.argv[2])).attempt(object()); "
         "attempt.__enter__(); os._exit(0)", str(path), str(now + 1000)],
        env={"PATH": "/usr/bin:/bin", "CBP_STATE_DIR": str(tmp_path / "unused")},
        cwd=Path(__file__).resolve().parents[1], check=True, timeout=10,
    )
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now + 1000) == (None, None)
    log = health.CandleFetchHealth(path, "BTC/USD", clock_ms=lambda: now + 2000)
    _record(log, (429,))
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now + 2000) == (None, 5)


def test_unsupported_hook_and_failed_checkpoint_do_not_change_operation(tmp_path, monkeypatch):
    now = 1_790_000_000_010
    path = tmp_path / health.FILENAME
    log = health.CandleFetchHealth(path, "BTC/USD", clock_ms=lambda: now)

    class BrokenHook:
        @property
        def on_rest_response(self):
            raise OSError("synthetic getter error")

    with log.attempt(BrokenHook()) as attempt:
        attempt.success = True
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now) == (0, None)

    real_save = health._save

    def break_finish(path, checkpoint):
        if not checkpoint["pending"]:
            raise OSError("synthetic write failure")
        real_save(path, checkpoint)

    monkeypatch.setattr(health, "_save", break_finish)
    with pytest.raises(RuntimeError, match="fetch failure"):
        with log.attempt(Exchange()):
            raise RuntimeError("fetch failure")
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now) == (None, None)


def test_reader_rejects_corrupt_wrong_market_future_and_linked_state(tmp_path):
    now = 1_790_000_000_010
    path = tmp_path / health.FILENAME
    _record(health.CandleFetchHealth(path, "BTC/USD", clock_ms=lambda: now), success=True)
    assert health.watcher_fetch_counts(path, "ETH/USD", now_ms=now) == (None, None)
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now - 1) == (None, None)
    obj = json.loads(path.read_bytes())
    obj["buckets"] = [[now // 1000, True]]
    path.write_text(json.dumps(obj))
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now) == (None, None)
    link = tmp_path / "link"
    link.symlink_to(path)
    assert health.watcher_fetch_counts(link, "BTC/USD", now_ms=now) == (None, None)


def test_restart_does_not_extend_streak_across_unwritten_success(tmp_path, monkeypatch):
    path = tmp_path / health.FILENAME
    now = [1_790_000_000_010]
    log = health.CandleFetchHealth(path, "BTC/USD", clock_ms=lambda: now[0])
    _record(log, success=True)
    for _ in range(9):
        now[0] += 1000
        _record(log)
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now[0])[0] == 9

    def unavailable(*_args):
        raise OSError("synthetic missing checkpoint")

    with monkeypatch.context() as context:
        context.setattr(health, "_save", unavailable)
        now[0] += 1000
        _record(log, success=True)

    now[0] += 1000
    restarted = health.CandleFetchHealth(path, "BTC/USD", clock_ms=lambda: now[0])
    _record(restarted)
    assert health.watcher_fetch_counts(path, "BTC/USD", now_ms=now[0])[0] is None
