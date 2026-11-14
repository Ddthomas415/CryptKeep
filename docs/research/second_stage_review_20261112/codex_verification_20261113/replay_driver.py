"""One-pass scratch reproduction of the owner's named saved analyses."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import time

REPO = Path('/Users/baitus/Downloads/crypto-bot-pro')
ROOT = Path(tempfile.mkdtemp(prefix='cryptkeep-second-stage-20261113-'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest = {'scratch': str(ROOT), 'sources': {}, 'runs': {}}

def copy(rel):
    source, dest = REPO / rel, ROOT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    manifest['sources'][rel] = sha(source)
    assert sha(dest) == manifest['sources'][rel]

for rel in (
    'scripts/__init__.py', 'scripts/research/rerun_frozen_stress.py',
    'scripts/research/corrected_research_math.py',
    'docs/research/btc_eth_stress_test_20261009/stress_btc_eth.py',
    'docs/research/btc_eth_corrected_comparison_20261012/compare.py',
    'docs/research/candidate_descriptive_20261107/describe.py',
    'docs/research/candidate_descriptive_20261107/PLAN.md',
    'docs/research/majors_trend_20261009/BTC-USD_d1.json',
    'docs/research/majors_trend_20261009/ETH-USD_d1.json',
    'research/research_corrections_20261009/stress_corrected_v1.json',
    'docs/research/es_exit_policy_matrix_20261007/es_exit_policy_matrix_20261007.py',
):
    copy(rel)

archive = REPO / 'docs/research/raw_archives_20261009/coinbase_btc_eth_daily.tar.xz'
assert sha(archive) == 'fbfb78339db65dfecd7b7ca5d293cca71c7c2241318f7915dfb651b8e6db6fb0'
manifest['archive_sha256'] = sha(archive)
with tarfile.open(archive) as tf:
    for asset in ('BTC', 'ETH'):
        name = f'maj/{asset}-USD_d1.json'
        member = next(m for m in tf.getmembers() if m.name.lstrip('./') == name)
        assert member.isfile()
        dest = ROOT / 'data' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(tf.extractfile(member).read())
        assert sha(dest) == sha(REPO / 'docs/research/majors_trend_20261009' / dest.name)
        manifest['sources'][f'ARCHIVE/{name}'] = sha(dest)

env = {'PATH': '/usr/bin:/bin', 'HOME': str(ROOT), 'TMPDIR': str(ROOT),
       'PYTHONDONTWRITEBYTECODE': '1', 'CBP_STATE_DIR': str(ROOT / 'state'),
       'GIT_DIR': str(REPO / '.git'), 'GIT_WORK_TREE': str(ROOT)}
python = str(REPO / '.venv/bin/python')

def run(name, args):
    start = time.monotonic()
    with (ROOT / f'{name}.stdout').open('wb') as out, (ROOT / f'{name}.stderr').open('wb') as err:
        try:
            result = subprocess.run([python, '-B', *args], cwd=ROOT, env=env,
                                    stdout=out, stderr=err, timeout=120)
            manifest['runs'][name] = {'returncode': result.returncode}
        except subprocess.TimeoutExpired:
            manifest['runs'][name] = {'timeout_seconds': 120}
    manifest['runs'][name]['seconds'] = round(time.monotonic() - start, 3)
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(name, manifest['runs'][name], flush=True)

print('SCRATCH', ROOT, flush=True)
run('comparison', [str(ROOT / 'docs/research/btc_eth_corrected_comparison_20261012/compare.py'), str(ROOT / 'data')])
run('descriptive', [str(ROOT / 'docs/research/candidate_descriptive_20261107/describe.py'), str(ROOT / 'data')])
run('stress', [str(ROOT / 'scripts/research/rerun_frozen_stress.py'), '--data', str(ROOT / 'data'), '--out', str(ROOT / 'stress'), '--part', 'core'])

try:
    source = REPO / '.cbp_state/data/market_raw.sqlite'
    with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as con:
        rows = con.execute('SELECT ts_ms,o,h,l,cl,v FROM market_ohlcv WHERE exchange=? AND symbol=? AND timeframe=? AND ts_ms>=? AND ts_ms<=? ORDER BY ts_ms',
                           ('coinbase', 'BTC/USD', '1d', 1514764800000, 1780531200000)).fetchall()
    digest = hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()
    manifest['es_input'] = {'rows': len(rows), 'sha256': digest}
    assert digest == 'c0d64661f4c09b4ca7be047694dceff46b22846ba576177f55e4464a623e28eb', 'frozen ES rows unavailable'
    db = ROOT / '.cbp_state/data/market_raw.sqlite'
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as con:
        con.execute('CREATE TABLE market_ohlcv(exchange TEXT,symbol TEXT,timeframe TEXT,ts_ms INTEGER,o REAL,h REAL,l REAL,cl REAL,v REAL)')
        con.executemany('INSERT INTO market_ohlcv VALUES(?,?,?,?,?,?,?,?,?)', [('coinbase', 'BTC/USD', '1d', *r) for r in rows])
    for source in (REPO / 'services').rglob('*.py'):
        if '__pycache__' not in source.parts:
            copy(str(source.relative_to(REPO)))
    run('es', [str(ROOT / 'docs/research/es_exit_policy_matrix_20261007/es_exit_policy_matrix_20261007.py'), str(ROOT)])
except (AssertionError, sqlite3.Error) as exc:
    manifest['es_prerequisite_failure'] = str(exc)
    print('ES prerequisite:', manifest['es_prerequisite_failure'], flush=True)

manifest['originals_unchanged'] = all(sha(REPO / r) == h for r, h in manifest['sources'].items() if not r.startswith('ARCHIVE/'))
(ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print('FINAL', ROOT / 'manifest.json', 'originals_unchanged', manifest['originals_unchanged'], flush=True)
