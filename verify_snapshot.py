"""Read-only verification of the transferred snapshot; requires only Python stdlib."""
from pathlib import Path, PurePosixPath
from hashlib import sha256
from zipfile import ZipFile
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent

def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def local(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError('Included file unavailable: ' + str(value))
    return path

def workbook_cells(path):
    ns = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    rel_ns = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    with ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            shared = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        book = ET.fromstring(z.read('xl/workbook.xml'))
        sheet = next(s for s in book.findall('s:sheets/s:sheet', ns) if s.attrib['name']=='ترجمه‌ها')
        relationships = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target = next(r.attrib['Target'] for r in relationships if r.attrib['Id']==sheet.attrib[rel_ns])
        sheet_path = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        cells = {}
        for c in ET.fromstring(z.read(sheet_path)).findall('.//s:c', ns):
            value = c.find('s:v', ns)
            if c.get('t')=='s' and value is not None:
                text = shared[int(value.text)]
            elif c.get('t')=='inlineStr':
                text = ''.join(t.text or '' for t in c.findall('.//s:t',ns))
            else:
                text = value.text if value is not None else ''
            cells[c.attrib['r']] = text
        return cells

def main():
    checked = 0
    for line in (ROOT/'FILES.sha256').read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ',1)
        if not re.fullmatch(r'[0-9a-f]{64}', expected):
            raise ValueError('Invalid checksum entry')
        if digest(local(relative)) != expected:
            raise ValueError('Snapshot differs: ' + relative)
        checked += 1
    book_path = local('Excellent-Advice-460-FA.xlsx')
    book = read(ROOT/'review-data/sentences.json')
    assert digest(book_path)==book['sourceSha256'], 'Workbook/source checksum mismatch'
    cells = workbook_cells(book_path)
    for sentence in book['sentences']:
        row = sentence['sourceRow']
        assert cells.get(f'A{row}')==str(sentence['id']), 'Workbook ID mismatch'
        assert cells.get(f'B{row}')==sentence['english'], 'English sentence mismatch'
        assert cells.get(f'C{row}')==sentence['persian'], 'Persian sentence mismatch'
    wave = read(ROOT/'book-review/dist/wave.json')
    candidates = 0
    for sentence in wave['sentences']:
        for candidate in sentence['ideas']:
            original = local('book-review/dist/' + candidate['image'])
            assert original.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'), 'Original PNG missing'
            assert digest(original)==candidate['imageHash'], 'Candidate image hash mismatch'
            prompt = candidate['fullGenerationPromptEnglish']
            assert 800<len(prompt)<=32767, 'Complete prompt missing'
            assert sha256(prompt.encode('utf-8')).hexdigest()==candidate['fullGenerationPromptEnglishHash']
            assert local(candidate['fullGenerationPromptEnglishPath']).read_text(encoding='utf-8-sig')==prompt
            candidates += 1
    ledger = read(ROOT/'review-data/finalization-state.json')
    latest = {}
    for entry in ledger.get('entries',[]):
        if entry.get('status')=='finalized':
            latest[entry['sentenceId']] = entry
    for sid, entry in latest.items():
        assert digest(local(f'Images/{sid}.png'))==entry['imageHash'], 'Approved original mismatch'
        excel = entry['excel']
        assert excel['column']=='D'
        value = cells.get(f"D{excel['row']}", '')
        assert sha256(value.encode('utf-8')).hexdigest()==excel['promptSha256'], 'Approved Excel prompt mismatch'
    print(json.dumps({'verified':True,'snapshotFiles':checked,'sentences':len(book['sentences']),
                      'galleryCandidates':candidates,'finalImagesAndExcelPrompts':len(latest)},ensure_ascii=False))

if __name__=='__main__':
    try:
        main()
    except (OSError,ValueError,AssertionError,KeyError,StopIteration,ET.ParseError) as error:
        print('Snapshot verification failed: ' + str(error),file=sys.stderr)
        sys.exit(1)
