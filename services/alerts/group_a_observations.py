"""Read only the fixed Group A status and fetch-health files, offline."""

from contextlib import contextmanager, nullcontext
from dataclasses import replace
from datetime import datetime
import json
import os
from pathlib import Path
import stat

from services.alerts.group_a_fetch_health import FILENAME, valid_writer_id, watcher_fetch_counts
from services.alerts.group_a_watch import AccountObservation, HostObservation, assess_group_a_watch
from services.alerts.group_a_support_observations import QueueSample, ResourceSample, observe_queue, observe_resources
from services.control.group_a_systemd_policy import render_group_a_policy
from services.market_data.paper_snapshot_quote import MAX_SNAPSHOT_BYTES, assess_paper_snapshot


_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
_STATUS_CAP = 131_072
_MAX_EPOCH_MS = 253_402_300_799_999


@contextmanager
def _directory(parts, *, parent=None):
    fd = None
    try:
        for part in parts:
            next_fd = os.open(part, _DIR_FLAGS, dir_fd=parent if fd is None else fd)
            if fd is not None:
                os.close(fd)
            fd = next_fd
        yield fd
    finally:
        if fd is not None:
            os.close(fd)


def _unique_object(pairs):
    obj = dict(pairs)
    if len(obj) != len(pairs):
        raise ValueError("duplicate_status_key")
    return obj


def _read_json(fd, name, cap):
    try:
        status_fd = os.open(name, _FILE_FLAGS, dir_fd=fd)
        with os.fdopen(status_fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                return None
            raw = stream.read(cap + 1)
            after = os.fstat(stream.fileno())
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns,
            ):
                return None
        return json.loads(raw, object_pairs_hook=_unique_object) if len(raw) <= cap else None
    except (OSError, ValueError, OverflowError, RecursionError):
        return None


def _status(fd, name, now_ms):
    try:
        data = _read_json(fd, name, _STATUS_CAP)
        if type(data) is not dict or type(data.get("ok")) is not bool or type(data.get("ts")) is not str:
            return {}, None
        raw_ts = data["ts"]
        stamp = datetime.fromisoformat(raw_ts[:-1] + "+00:00" if raw_ts.endswith("Z") else raw_ts)
        if stamp.tzinfo is None:
            return {}, None
        age = (now_ms / 1000) - stamp.timestamp()
        return (data, age) if age >= 0 else ({}, None)
    except (OSError, ValueError, OverflowError, RecursionError):
        return {}, None


def _account(fd, account, market, now_ms):
    try:
        with _directory((account, "runtime", "flags"), parent=fd) as flags:
            strategy, age = _status(flags, "strategy_runner.status.json", now_ms)
            _, paper_age = _status(flags, "paper_engine.status.json", now_ms)
            kill, streak, responses = None, None, None
            if age is not None and age <= 600 and strategy.get("status") == "running" and strategy["ok"]:
                if strategy.get("note") == "kill_cooldown":
                    kill = True
                writer = strategy.get("group_a_fetch_writer")
                seq = strategy.get("group_a_fetch_attempt")
                if valid_writer_id(writer) and type(seq) is int and seq > 0:
                    streak, responses = watcher_fetch_counts(
                        Path(FILENAME), market, now_ms=now_ms,
                        expected_writer=writer, expected_sequence=seq, dir_fd=flags,
                    )
            return AccountObservation(
                strategy_status_age_sec=age, paper_status_age_sec=paper_age, kill_cooldown=kill,
                consecutive_candle_failures=streak, http_429_last_10_min=responses,
            )
    except OSError:
        return AccountObservation()


def observe_group_a_status(release: str, release_root: Path, *, now_ms: int):
    """Return R3 findings for fixed file names; never open queues or a config.

    The caller must supply an owned release root. A matching writer/attempt is
    evidence of file attribution, not a current process or mount attestation.
    """
    return _observe(release, release_root, now_ms=now_ms, queues=None, resources=None, support=False)


def observe_group_a_support(
    release: str, release_root: Path, *, now_ms: int,
    queues: dict[str, QueueSample], resources: ResourceSample | None = None,
):
    """Add the release publisher and caller-supplied, trusted observations."""
    return _observe(release, release_root, now_ms=now_ms, queues=queues, resources=resources, support=True)


def _observe(release, release_root, *, now_ms, queues, resources, support, root_fd=None,
             account_still_matches=None, queue_events=None, queue_health=None):
    if type(release) is not str:
        raise ValueError("invalid_group_a_release")
    policy = render_group_a_policy(release)
    if (not isinstance(release_root, Path) or not release_root.is_absolute()
            or release_root.anchor != "/" or release_root.name != release or ".." in release_root.parts):
        raise ValueError("invalid_group_a_release_root")
    if type(now_ms) is not int or not 1 <= now_ms <= _MAX_EPOCH_MS:
        raise ValueError("invalid_group_a_clock")
    prefix = policy.target.removesuffix(".target") + "-"
    scopes = tuple(unit.removesuffix("-strategy.service") for unit in policy.services
                   if unit.endswith("-strategy.service"))
    if support and (type(queues) is not dict or any(
            type(scope) is not str or scope not in scopes or type(sample) is not QueueSample
            or type(sample.scope) is not str or sample.scope != scope
            for scope, sample in queues.items())):
        raise ValueError("invalid_group_a_queue_scope")
    if support and len({id(sample.connection) for sample in queues.values()}) != len(queues):
        raise ValueError("aliased_group_a_queue_copy")
    accounts = {}
    try:
        with (nullcontext(root_fd) if root_fd is not None else _directory(release_root.parts)) as root:
            snapshot = None
            if support:
                try:
                    with _directory(("support", "publisher", "runtime", "snapshots"), parent=root) as quotes:
                        snapshot = _read_json(quotes, "system_status.latest.json", MAX_SNAPSHOT_BYTES)
                except OSError:
                    pass
                if (type(snapshot) is not dict or type(snapshot.get("ts_ms")) is not int
                        or not 0 <= snapshot["ts_ms"] <= now_ms
                        or not isinstance(snapshot.get("ticks"), list)
                        or any(type(row) is not dict or type(row.get("venue")) is not str
                               or not row["venue"] or type(row.get("symbol")) is not str
                               or not row["symbol"] for row in snapshot["ticks"])
                        or (snapshot["ts_ms"] == 0 and snapshot.get("ticks") != [])):
                    snapshot = None
            for scope in scopes:
                account = scope.removeprefix(prefix)
                market = account.rsplit("-", 1)[1].upper() + "/USD"
                observation = _account(root, account, market, now_ms)
                if support:
                    quote, reason = assess_paper_snapshot(
                        snapshot, venue="coinbase", symbol=market, clock=lambda: now_ms / 1000,
                        require_canonical_mapping=True,
                    )
                    queue = observe_queue(queues.get(scope), market=market, now_ms=now_ms,
                                          track_events=queue_events is not None)
                    if queue_health is not None:
                        queue_health[scope] = queue.coverage
                    if queue_events is not None and queue.event_keys is not None:
                        queue_events[scope] = queue.event_keys
                    observation = replace(
                        observation,
                        quote_fresh=True if quote is not None else (
                            False if reason in ("stale_quote", "missing_quote") else None
                        ),
                        order_refused=queue.order_refused, order_expired=queue.order_expired,
                        oldest_pending_exit_sec=queue.oldest_pending_exit_sec,
                        oldest_submitting_sec=queue.oldest_submitting_sec,
                    )
                accounts[scope] = observation
    except OSError:
        pass
    if account_still_matches is not None:
        # Recheck after all reads; an earlier account may change while a later one is composed.
        accounts = {scope: observation for scope, observation in accounts.items() if account_still_matches(scope)}
        if queue_events is not None:
            for scope in queue_events.keys() - accounts.keys():
                del queue_events[scope]
        if queue_health is not None:
            for scope in queue_health.keys() - accounts.keys():
                del queue_health[scope]
    host = observe_resources(resources, now_ms=now_ms) if support else HostObservation()
    return assess_group_a_watch(release, accounts=accounts, host=host)
