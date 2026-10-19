"""Compare supplied outputs, not reproduce the runs that generated them."""
import json
from pathlib import Path

root = Path('/private/tmp/cryptkeep-shared-unique-20261005')
paths = sorted(root.glob('*-trace_*.json'))
base = next(path for path in paths if path.name.endswith('-trace_0001-0003.json'))
baseline = json.loads(base.read_text())
result = {'baseline': base.name, 'scope': 'SUPPLIED_OUTPUT_COMPARISON_ONLY', 'comparisons': []}
for path in paths:
    rows = json.loads(path.read_text())
    common = sorted(set(baseline) & set(rows))
    changes = {field: [] for field in ['orders', 'error', 'final_position', 'loops_run', 'notes', 'state']}
    for name in common:
        for field in changes:
            if baseline[name].get(field) != rows[name].get(field):
                changes[field].append(name)
    result['comparisons'].append({
        'file': path.name, 'scenarios': len(rows), 'common': len(common),
        'missing': sorted(set(baseline) - set(rows)),
        'additional': sorted(set(rows) - set(baseline)), 'changed': changes,
    })
destination = Path(__file__).with_name('supplied_trace_comparison.json')
destination.write_text(json.dumps(result, indent=2))
for row in result['comparisons']:
    print(row['file'], row['scenarios'], {key: len(value) for key, value in row['changed'].items()})
    print('ORDER DIFFERENCES:', row['changed']['orders'])
