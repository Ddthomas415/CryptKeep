"""Check supplied data structure; never infer semantic verification from parsing."""
import json
from pathlib import Path
import sqlite3

root = Path('/private/tmp/cryptkeep-shared-unique-20261005')
for path in sorted(root.iterdir()):
    if path.name == 'coverage.json':
        continue
    if path.suffix == '.json':
        try:
            data = json.loads(path.read_text())
            print(path.name, 'PARSED', type(data).__name__,
                  list(data)[:25] if isinstance(data, dict) else len(data))
        except Exception as error:
            print(path.name, 'ERROR', repr(error))
    elif path.suffix == '.jsonl':
        count = 0
        errors = []
        keys = set()
        with path.open() as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    count += 1
                    if isinstance(row, dict):
                        keys.update(row)
                except Exception as error:
                    errors.append([number, str(error)])
        print(path.name, 'STRUCTURAL_SCAN_ONLY', count, 'rows', 'errors', errors,
              'keys', sorted(keys))
    elif path.suffix == '.sqlite':
        connection = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
        print(path.name, 'SQLITE_INTEGRITY', connection.execute('PRAGMA integrity_check').fetchall())
        for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            safe = table.replace('"', '""')
            print('TABLE', table, 'ROWS', connection.execute(f'SELECT count(*) FROM "{safe}"').fetchone()[0])
        connection.close()
