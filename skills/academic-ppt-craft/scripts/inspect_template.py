"""Inspect direct OOXML declarations; inherited formatting still needs native review."""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def inspect(path):
    result = {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'scope': 'Direct XML declarations only; no theme/layout/master inheritance resolution.',
              'slides': []}
    with ZipFile(path) as z:
        pres = ET.fromstring(z.read('ppt/presentation.xml'))
        size = pres.find('p:sldSz', NS)
        result['size_emu'] = dict(size.attrib)
        rels = ET.fromstring(z.read('ppt/_rels/presentation.xml.rels'))
        targets = {r.get('Id'): r.get('Target') for r in rels}
        for index, sid in enumerate(pres.find('p:sldIdLst', NS), 1):
            target = targets[sid.get('{'+NS['r']+'}id')]
            member = target.lstrip('/') if target.startswith('/') else 'ppt/' + target
            root = ET.fromstring(z.read(member))
            row = {'page': index, 'part': member, 'objects': []}
            for node in root.find('p:cSld/p:spTree', NS):
                if node.tag.rsplit('}', 1)[-1] not in ('sp', 'grpSp', 'pic', 'graphicFrame', 'cxnSp'):
                    continue
                nv = node.find('.//p:cNvPr', NS)
                item = {'kind': node.tag.rsplit('}', 1)[-1], 'id': nv.get('id') if nv is not None else None,
                        'name': nv.get('name') if nv is not None else None,
                        'child_ids': [n.get('id') for n in node.findall('.//p:cNvPr', NS)],
                        'text': ''.join(n.text or '' for n in node.findall('.//a:t', NS)),
                        'custom_geometry_count': len(node.findall('.//a:custGeom', NS)),
                        'paragraphs': []}
                for para in node.findall('.//a:p', NS):
                    ppr = para.find('a:pPr', NS)
                    item['paragraphs'].append({
                        'text': ''.join(n.text or '' for n in para.findall('.//a:t', NS)),
                        'properties_xml': ET.tostring(ppr, encoding='unicode') if ppr is not None else None,
                        'run_properties_xml': [ET.tostring(n, encoding='unicode') for n in para.findall('.//a:rPr', NS)]})
                item['transforms_xml'] = [ET.tostring(n, encoding='unicode') for n in node.findall('.//a:xfrm', NS)]
                row['objects'].append(item)
            result['slides'].append(row)
    result['slide_count'] = len(result['slides'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inspect(args.pptx), ensure_ascii=False, indent=2), encoding='utf-8')
    print(args.output)
