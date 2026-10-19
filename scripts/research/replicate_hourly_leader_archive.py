"""Adapt checksum-verified prior public archive for one unchanged hourly arm."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tarfile

from scripts.research.hourly_leader_recovery import analyze, digest, save, HOUR


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    folder = root/'docs/research/raw_archives_20261009'
    archive = folder/'coinbase_hourly_last60d.tar.xz'
    expected = next(line.split()[0] for line in (folder/'SHA256SUMS_archives.txt').read_text().splitlines()
                    if 'coinbase_hourly_last60d.tar.xz' in line)
    if digest(archive) != expected:
        raise ValueError('archive_checksum_mismatch')
    input_hashes = {line.split()[1].lstrip('./'): line.split()[0]
                    for line in (folder/'SHA256SUMS_inputs.txt').read_text().splitlines()}
    prior = json.loads((root/'research/hourly_leader_plan_20261012.json').read_text())
    end = prior['start']+24*HOUR
    markets = {}
    with tarfile.open(archive, 'r:xz') as tar:
        members = [m for m in tar.getmembers() if m.isfile() and m.name.startswith('cb/h1/')
                   and m.name.endswith('-USD.json')]
        for member in members:
            raw = tar.extractfile(member).read()
            actual = hashlib.sha256(raw).hexdigest()
            if input_hashes.get(member.name) != actual:
                raise ValueError('input_checksum_mismatch:'+member.name)
            rows = json.loads(raw)
            candles = [{'start':str(int(row[0])), 'open':str(row[1]),
                        'close':str(row[4]), 'volume':str(row[5])}
                       for row in rows if int(row[0]) < end]
            symbol = Path(member.name).stem
            markets[symbol] = {'raw':{'candles':candles}, 'original_input_sha256':actual}
    timestamps = [int(b['start']) for m in markets.values() for b in m['raw']['candles']]
    plan = deepcopy(prior)
    plan.update(start=min(timestamps), end=end, symbols=sorted(markets),
                pullbacks=[.2], targets=[.05], holds_hours=[48],
                universe_sha256=digest(archive), adapter_source_sha256=digest(__file__),
                archive_members_verified=len(markets),
                limits=['current_20261009_archive_universe_not_historical_listings',
                        'rankable_subset_not_exact_live_leaderboard', 'assumed_spread',
                        'earlier_nonoverlap_but_already_explored_archive_not_holdout',
                        'single_candidate_selected_after_eight_recent_arms'])
    # Freeze adaptation and unchanged selected rule before evaluating returns.
    plan_path = root/'research/hourly_leader_earlier_plan_20261012.json'
    raw_path = root/'research/hourly_leader_earlier_raw_20261012.json'
    save(plan_path, plan)
    save(raw_path, {'plan_sha256':digest(plan_path),'archive_sha256':expected,'markets':markets})
    analyze(plan_path, raw_path, root/'research/hourly_leader_earlier_results_20261012.json')
