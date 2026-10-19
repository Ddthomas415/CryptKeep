"""Check the remaining-pass evidence tables against immutable extracted bytes."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
items = {
    item['sha256']: item
    for item in json.loads(Path('/private/tmp/cryptkeep-shared-unique-20261005/coverage.json').read_text())
}
reports = sorted(ROOT.glob('remaining_batch_*_review.md'))
seen = {}
for report in reports:
    hashes = re.findall(r'^\|[^\n]*?`([0-9a-f]{64})`', report.read_text(), re.MULTILINE)
    for digest in hashes:
        if digest not in items:
            raise ValueError(f'{report.name}: unknown digest {digest}')
        if digest in seen:
            raise ValueError(f'{report.name}: duplicate review allocation with {seen[digest]}')
        data = Path(items[digest]['extracted']).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f'{report.name}: extracted bytes changed for {digest}')
        seen[digest] = report.name
    print(f'{report.name}: {len(hashes)} verified content identities')
print(f'Unique remaining-pass content identities: {len(seen)} / 89')
if len(seen) != 89:
    print('INCOMPLETE: not all 89 items have full-read evidence tables')
else:
    print('Identity coverage complete; this does not validate semantic judgments or runtime safety')
with (ROOT / 'all_review_family_coverage.csv').open() as stream:
    rows = list(csv.DictReader(stream))
counts = {}
for row in rows:
    counts[row['coverage']] = counts.get(row['coverage'], 0) + 1
print(json.dumps(counts, sort_keys=True))
