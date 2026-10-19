#!/usr/bin/env python3
"""Bounded foreground ingestion; never evaluates strategy outcomes."""
from __future__ import annotations

import argparse
import fcntl
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.research.run_coinbase_confirmation import check_registration, digest, load_contract
from scripts.research.run_multisymbol_baseline import HOUR, read_rows, utc_ms
from scripts.research.run_ohlcv_archive_backfill import fetch_public_ohlcv
from services.backtest.ohlcv_archive import backfill_archive
from services.backtest.research_prefix_freeze import rows_hash


def stamp(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def inspect(plan_path, archive, previous, registration, *, now_ms, max_hours=24):
    if type(max_hours) is not int or not 1 <= max_hours <= 24:
        raise ValueError('max_hours_must_be_1_to_24')
    plan, _, identity = load_contract(plan_path)
    check_registration(registration, plan, identity, now_ms)
    prior = json.loads(Path(previous).read_bytes())
    if (prior.get('kind') != 'COLLECTION_CHECKPOINT_NOT_PHASE_COMPLETION'
            or prior.get('identity') != identity or prior.get('scoring_authorized') is not False
            or set(prior['markets']) != set(plan['symbols'])):
        raise ValueError('invalid_parent_checkpoint')
    start = utc_ms(plan['archive_start_utc'])
    evaluation = utc_ms(plan['evaluation_start_utc'])
    old_end = utc_ms(prior['cutoff_exclusive_utc'])
    if old_end % HOUR or not evaluation <= old_end <= now_ms // HOUR * HOUR:
        raise ValueError('invalid_parent_boundary')
    end = min(now_ms // HOUR * HOUR, old_end + max_hours * HOUR,
              utc_ms(plan['evaluation_end_exclusive_utc']))
    if end < old_end:
        raise ValueError('parent_beyond_contract')
    missing = {}
    with sqlite3.connect(f'file:{Path(archive).resolve()}?mode=ro', uri=True) as db:
        for symbol in plan['symbols']:
            rows = read_rows(archive, venue=plan['venue'], symbol=symbol, start_ms=start, end_ms=old_end)
            ev = read_rows(archive, venue=plan['venue'], symbol=symbol, start_ms=evaluation, end_ms=old_end) if old_end > evaluation else []
            expected = {'total_bars': len(rows), 'total_rows_sha256': rows_hash(rows),
                        'evaluation_bars': len(ev), 'evaluation_rows_sha256': rows_hash(ev)}
            if prior['markets'][symbol] != expected:
                raise ValueError(f'parent_prefix_changed:{symbol}')
            tail = db.execute("SELECT ts_ms FROM market_ohlcv WHERE exchange=? AND symbol=? "
                              "AND timeframe='1h' AND ts_ms>=? AND ts_ms<? ORDER BY ts_ms",
                              (plan['venue'], symbol, old_end, end)).fetchall()
            present = {row[0] for row in tail}
            if any(t % HOUR for t in present):
                raise ValueError(f'non_hourly_tail:{symbol}')
            missing[symbol] = [t for t in range(old_end, end, HOUR) if t not in present]
    return plan, identity, start, evaluation, end, missing


def _collect(plan_path, archive, previous, registration, output, *, now_ms,
            max_hours=24, dry_run=True, fetcher=fetch_public_ohlcv):
    plan, identity, start, evaluation, end, missing = inspect(
        plan_path, archive, previous, registration, now_ms=now_ms, max_hours=max_hours)
    report = {'kind': 'BOUNDED_COLLECTION_STATUS', 'cutoff_exclusive_utc': stamp(end),
              'missing_bars': {s: len(ts) for s, ts in missing.items()},
              'scoring_authorized': False, 'dry_run': dry_run}
    if dry_run:
        return report
    # Exclusive reservation prevents two copies of this command writing one batch.
    # A failed/interrupted batch is retained for inspection, never overwritten.
    output = Path(output)
    with output.open('x', encoding='utf-8') as reservation:
        reservation.write(json.dumps({**report, 'status': 'INCOMPLETE'}) + '\n')
    errors = {}
    for symbol, timestamps in missing.items():
        if not timestamps:
            continue
        wanted = set(timestamps)

        def bounded_fetch(venue, market, **kwargs):
            return [row for row in fetcher(venue, market, **kwargs)
                    if row and row[0] in wanted]

        try:
            backfill_archive(bounded_fetch, venue=plan['venue'], symbol=symbol, timeframe='1h',
                             since_ms=min(timestamps), until_ms=end - 1, page_limit=24,
                             max_pages=1, max_bars=24, db_path=archive)
        except Exception as exc:
            errors[symbol] = str(exc)
    markets = {}
    for symbol in plan['symbols']:
        try:
            rows = read_rows(archive, venue=plan['venue'], symbol=symbol, start_ms=start, end_ms=end)
            ev = read_rows(archive, venue=plan['venue'], symbol=symbol, start_ms=evaluation, end_ms=end) if end > evaluation else []
            markets[symbol] = {'total_bars': len(rows), 'total_rows_sha256': rows_hash(rows),
                               'evaluation_bars': len(ev), 'evaluation_rows_sha256': rows_hash(ev)}
        except Exception as exc:
            errors[symbol] = str(exc)
    # Recheck the immutable prefix after ingestion, including frozen source identities.
    inspect(plan_path, archive, previous, registration, now_ms=now_ms, max_hours=max_hours)
    result = {**report, 'status': 'INCOMPLETE', 'errors': errors}
    if not errors:
        result = {'kind': 'COLLECTION_CHECKPOINT_NOT_PHASE_COMPLETION',
                  'cutoff_exclusive_utc': stamp(end), 'identity': identity,
                  'parent_checkpoint_sha256': digest(previous), 'markets': markets,
                  'scoring_authorized': False,
                  'limits': ['content_freeze_not_authenticity', 'not_checkpoint_or_final_phase',
                             'no_strategy_evaluation']}
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return result


def collect(plan_path, archive, previous, registration, output, **kwargs):
    archive = Path(archive).resolve()
    if kwargs.get('dry_run', True):
        return _collect(plan_path, archive, previous, registration, output, **kwargs)
    with Path(str(archive) + '.collection.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _collect(plan_path, archive, previous, registration, output, **kwargs)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'archive', 'previous', 'registration', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--max-hours', type=int, default=24)
    p.add_argument('--collect', action='store_true', help='Otherwise read-only status; no network.')
    args = p.parse_args()
    try:
        result = collect(args.plan, args.archive, args.previous, args.registration, args.output,
                         now_ms=int(time.time() * 1000), max_hours=args.max_hours,
                         dry_run=not args.collect)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result.get('status') == 'INCOMPLETE' else 0
    except Exception as exc:
        print(json.dumps({'status': 'INCOMPLETE', 'reason': str(exc), 'scoring_authorized': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
