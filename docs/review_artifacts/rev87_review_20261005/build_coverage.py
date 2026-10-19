import hashlib
import json
from pathlib import Path
import zipfile

downloads = Path('/Users/baitus/Downloads')
output = Path('/private/tmp/cryptkeep-shared-unique-20261005')
output.mkdir(exist_ok=True)
entries = {}
for revision in range(58, 88):
    path = downloads / f'cryptkeep_review_bundle_2026-10-02_rev{revision}.zip'
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            data = archive.read(info)
            digest = hashlib.sha256(data).hexdigest()
            item = entries.setdefault(digest, {'sha256': digest, 'size': len(data), 'references': []})
            item['references'].append({'revision': revision, 'member': info.filename})
            if 'extracted' not in item:
                destination = output / (digest[:16] + '-' + Path(info.filename).name)
                destination.write_bytes(data)
                item['extracted'] = str(destination)
                item['coverage'] = 'INVENTORIED_NOT_SEMANTICALLY_REVIEWED'
result = list(entries.values())
(output / 'coverage.json').write_text(json.dumps(result, indent=2))
print(json.dumps({'unique_files': len(result), 'unique_bytes': sum(i['size'] for i in result),
                  'archive_member_occurrences': sum(len(i['references']) for i in result)}, indent=2))
for item in result:
    if not item['extracted'].endswith(('.patch', '.diff')):
        print(item['size'], item['extracted'])
