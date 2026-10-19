"""Extract embedded document text for review without changing source artifacts."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

root = Path('/private/tmp/cryptkeep-shared-unique-20261005')
paths = [Path(value) for value in sys.argv[1:]] if len(sys.argv) > 1 else sorted(root.glob('*'))
for path in paths:
    if path.suffix not in {'.docx', '.xlsx'}:
        continue
    print('\nDOCUMENT:', path.name)
    with zipfile.ZipFile(path) as archive:
        if path.suffix == '.docx':
            tree = ET.fromstring(archive.read('word/document.xml'))
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            for paragraph in tree.findall('.//w:p', ns):
                print(''.join(n.text or '' for n in paragraph.findall('.//w:t', ns)))
            continue
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            for item in ET.fromstring(archive.read('xl/sharedStrings.xml')):
                strings.append(''.join(n.text or '' for n in item.findall('.//s:t', ns)))
        for name in archive.namelist():
            if not name.startswith('xl/worksheets/sheet') or not name.endswith('.xml'):
                continue
            print('SHEET:', name)
            for row in ET.fromstring(archive.read(name)).findall('.//s:row', ns):
                values = []
                for cell in row.findall('s:c', ns):
                    value = cell.findtext('s:v', '', ns)
                    if cell.get('t') == 's':
                        value = strings[int(value)]
                    elif cell.get('t') == 'inlineStr':
                        value = ''.join(n.text or '' for n in cell.findall('.//s:t', ns))
                    formula = cell.findtext('s:f', '', ns)
                    values.append(f"{cell.get('r')}: {value}" + (f' FORMULA={formula}' if formula else ''))
                print(' | '.join(values))
