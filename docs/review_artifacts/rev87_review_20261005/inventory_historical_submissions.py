"""Inventory the historical review family without claiming semantic review."""
import hashlib
import json
from pathlib import Path
import zipfile

downloads = Path('/Users/baitus/Downloads')
files = sorted(downloads.glob('*cryptkeep_review_bundle_2026-10-02*.zip'))
unique = {}
archives = []
for path in files:
    raw_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        error = archive.testzip()
        archives.append({'path': str(path), 'sha256': raw_hash, 'crc_error': error})
        for info in archive.infolist():
            if info.is_dir():
                continue
            data = archive.read(info)
            digest = hashlib.sha256(data).hexdigest()
            item = unique.setdefault(digest, {'sha256': digest, 'bytes': len(data),
                                             'coverage': 'INVENTORIED_ONLY', 'references': []})
            item['references'].append({'archive': str(path), 'member': info.filename})
result = {'archives': archives, 'unique_contents': list(unique.values())}
destination = Path(__file__).with_name('historical_submission_inventory.json')
destination.write_text(json.dumps(result, indent=2))
print(json.dumps({'archives': len(archives), 'unique_archive_bytes': len({a['sha256'] for a in archives}),
                  'unique_contents': len(unique), 'crc_errors': [a for a in archives if a['crc_error']]}))
