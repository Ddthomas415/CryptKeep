import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

root = Path('/Users/baitus/Downloads')
previous = {}
for revision in range(58, 88):
    path = root / f'cryptkeep_review_bundle_2026-10-02_rev{revision}.zip'
    with zipfile.ZipFile(path) as archive:
        patches = {}
        for name in archive.namelist():
            match = re.match(r'(\d{4})-.*\.patch$', Path(name).name)
            if match:
                patches[match[1]] = hashlib.sha256(archive.read(name)).hexdigest()
        print(json.dumps({'revision': revision, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'patches': len(patches), 'added': sorted(set(patches) - set(previous)),
                          'changed': sorted(key for key in patches if key in previous and patches[key] != previous[key])}))
        previous = patches

path = root / 'cryptkeep_backlog_status_2026-10-05.xlsx'
ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(path) as archive:
    shared = []
    if 'xl/sharedStrings.xml' in archive.namelist():
        for item in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('m:si', ns):
            shared.append(''.join(item.itertext()))
    workbook = ET.fromstring(archive.read('xl/workbook.xml'))
    print('WORKBOOK SHEETS', [sheet.attrib.get('name') for sheet in workbook.findall('m:sheets/m:sheet', ns)])
    for name in sorted(archive.namelist()):
        if re.match(r'xl/worksheets/sheet\d+\.xml$', name):
            print(name)
            for row in ET.fromstring(archive.read(name)).findall('m:sheetData/m:row', ns):
                values = []
                for cell in row.findall('m:c', ns):
                    value = cell.find('m:v', ns)
                    text = value.text if value is not None else ''.join(cell.find('m:is', ns).itertext()) if cell.find('m:is', ns) is not None else ''
                    if cell.attrib.get('t') == 's' and text:
                        text = shared[int(text)]
                    formula = cell.find('m:f', ns)
                    values.append(f"{cell.attrib.get('r')}={text}" + (f" [formula:{formula.text}]" if formula is not None else ''))
                print(' | '.join(values))
