"""Restore original unsupported OOXML display metadata after Artifact Tool authoring.

No cell values, formulas, table contents, fonts, or fills are authored here.
The spreadsheet runtime does not expose readingOrder or worksheet view settings.
"""
from pathlib import Path
import argparse, copy, hashlib, json, os, uuid, zipfile
import xml.etree.ElementTree as ET

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
def tag(name): return '{' + NS + '}' + name
def read_zip(path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}
def xml_bytes(element, namespace):
    ET.register_namespace('', namespace)
    ET.register_namespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
    return ET.tostring(element, encoding='utf-8', xml_declaration=True)
def cell_text(cell, files):
    if cell.get('t') == 'inlineStr': return ''.join(cell.itertext())
    if cell.get('t') == 's':
        strings = ET.fromstring(files['xl/sharedStrings.xml'])
        return ''.join(strings[int(cell.find(tag('v')).text)].itertext())
    value = cell.find(tag('v'))
    return value.text if value is not None else ''

def preserve(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    before_bytes = target.read_bytes()
    original, output = read_zip(source), read_zip(target)
    sheet_path, styles_path = 'xl/worksheets/sheet1.xml', 'xl/styles.xml'
    original_sheet, sheet = ET.fromstring(original[sheet_path]), ET.fromstring(output[sheet_path])
    original_styles, styles = ET.fromstring(original[styles_path]), ET.fromstring(output[styles_path])
    original_xfs, xfs = original_styles.find(tag('cellXfs')), styles.find(tag('cellXfs'))
    originals = {cell.get('r'): cell for cell in original_sheet.iter(tag('c'))}
    current_cells = {cell.get('r'): cell for cell in sheet.iter(tag('c'))}
    source_headers = {cell_text(originals[col+'1'], original): col for col in ('A','B','C','D') if col+'1' in originals}
    target_headers = {col: cell_text(current_cells[col+'1'], output) for col in ('A','B','C','D')}
    assert target_headers['C'] == 'ترجمه‌ی فارسی'
    assert target_headers['D'] == 'پرامپت کامل انگلیسی تصویر'
    data_before = copy.deepcopy(sheet.find(tag('sheetData')))
    cache, restored = {}, 0
    for reference, cell in current_cells.items():
        column = reference.rstrip('0123456789')
        row = reference[len(column):]
        previous_column = source_headers.get(target_headers.get(column), column)
        previous_ref = previous_column + row
        original_cell = originals.get(previous_ref)
        # New prompt cells use English reading order; their Persian header uses RTL.
        if column == 'D' and target_headers['D'] not in source_headers:
            reading_order = '2' if row == '1' else '1'
        elif original_cell is not None:
            alignment = original_xfs[int(original_cell.get('s', '0'))].find(tag('alignment'))
            reading_order = alignment.get('readingOrder') if alignment is not None else None
            if reading_order is None and column == 'D': reading_order = '2' if row == '1' else '1'
        else: continue
        if reading_order is None: continue
        style_index = int(cell.get('s', '0'))
        key = style_index, reading_order
        if key not in cache:
            adjusted = copy.deepcopy(xfs[style_index])
            alignment = adjusted.find(tag('alignment'))
            if alignment is None: alignment = ET.SubElement(adjusted, tag('alignment'))
            alignment.set('readingOrder', reading_order)
            adjusted.set('applyAlignment', '1')
            cache[key] = len(xfs)
            xfs.append(adjusted)
        cell.set('s', str(cache[key]))
        restored += 1
    xfs.set('count', str(len(xfs)))
    # View metadata is copied verbatim from the input, including RTL, zoom and selection.
    original_views = original_sheet.find(tag('sheetViews'))
    if original_views is not None:
        current_views = sheet.find(tag('sheetViews'))
        if current_views is not None:
            index = list(sheet).index(current_views); sheet.remove(current_views)
        else:
            dimension = sheet.find(tag('dimension'))
            index = list(sheet).index(dimension) + 1 if dimension is not None else 0
        sheet.insert(index, copy.deepcopy(original_views))
    # Verify that the content of every cell is untouched; only the style references differ.
    data_after = copy.deepcopy(sheet.find(tag('sheetData')))
    for data in (data_before, data_after):
        for cell in data.iter(tag('c')): cell.attrib.pop('s', None)
    assert ET.tostring(data_before) == ET.tostring(data_after), 'Cell content changed during display restoration'
    output[sheet_path] = xml_bytes(sheet, NS)
    output[styles_path] = xml_bytes(styles, NS)
    restored_parts = []
    for name in ('docProps/core.xml', 'docProps/app.xml'):
        if name in original:
            output[name] = original[name]; restored_parts.append(name)
    if restored_parts:
        content_types = ET.fromstring(output['[Content_Types].xml'])
        original_types = ET.fromstring(original['[Content_Types].xml'])
        for item in original_types:
            if item.get('PartName', '').lstrip('/') in restored_parts and not any(x.get('PartName') == item.get('PartName') for x in content_types):
                content_types.append(copy.deepcopy(item))
        output['[Content_Types].xml'] = xml_bytes(content_types, CT)
        relations = ET.fromstring(output['_rels/.rels'])
        original_relations = ET.fromstring(original['_rels/.rels'])
        for item in original_relations:
            if item.get('Target', '').lstrip('/') in restored_parts and not any(x.get('Type') == item.get('Type') for x in relations):
                new_relation = copy.deepcopy(item)
                used = {x.get('Id') for x in relations}
                index = 1
                while 'rId' + str(index) in used: index += 1
                new_relation.set('Id', 'rId' + str(index))
                relations.append(new_relation)
        output['_rels/.rels'] = xml_bytes(relations, REL)
    temporary = target.with_name(target.name + '.' + uuid.uuid4().hex + '.display.tmp')
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in output.items(): archive.writestr(name, data)
        with zipfile.ZipFile(temporary) as archive:
            assert archive.testzip() is None
        assert target.read_bytes() == before_bytes, 'Target workbook changed during display restoration'
        os.replace(temporary, target)
    finally:
        if temporary.exists(): temporary.unlink()
    return {'restored':True, 'cellsWithExplicitReadingOrder':restored, 'worksheetViewPreserved':original_views is not None, 'documentPropertiesPreserved':restored_parts, 'cellContentsUnchanged':True, 'targetSha256':hashlib.sha256(target.read_bytes()).hexdigest()}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    args = parser.parse_args()
    print(json.dumps(preserve(args.source, args.target)))
