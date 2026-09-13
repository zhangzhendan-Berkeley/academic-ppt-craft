"""Validate local links and an explicit asset allowlist, then build a portable ZIP."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote
from zipfile import ZipFile, ZIP_DEFLATED


def package(root, output):
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Output ZIP must be outside the skill folder.')
    registry = json.loads((root / 'assets/attachment-manifest.json').read_text(encoding='utf-8'))
    allowed = {x['path'] for x in registry['attachments']}
    allowed |= {'assets/course-brief.md', 'assets/template-profile.json', 'assets/attachment-manifest.json'}
    files = []
    for path in sorted(root.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        if rel == 'PACKAGE_MANIFEST.json':
            continue
        if path.is_symlink() or root not in path.resolve().parents:
            raise ValueError('External/symlink file: ' + rel)
        if rel.startswith('assets/'):
            if rel not in allowed:
                raise ValueError('Unregistered asset: ' + rel)
        elif rel != 'SKILL.md' and not (rel.startswith(('references/', 'agents/', 'scripts/')) and path.suffix in ('.md', '.yaml', '.py')):
            raise ValueError('Unexpected package file: ' + rel)
        files.append(path)
    for rel in allowed:
        if not (root / rel).is_file():
            raise ValueError('Missing asset: ' + rel)
    for item in registry['attachments']:
        actual = hashlib.sha256((root / item['path']).read_bytes()).hexdigest()
        if actual != item['sha256']:
            raise ValueError('Attachment hash mismatch: ' + item['path'])
    for path in files:
        if path.suffix != '.md':
            continue
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            target = unquote(target.strip('<>').split('#', 1)[0])
            if not target or re.match(r'^[a-zA-Z][\w+.-]*:', target):
                continue
            destination = (path.parent / target).resolve()
            if root not in destination.parents or not destination.exists():
                raise ValueError(f'Nonportable/broken link: {path.name}: {target}')
    records = [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size,
                'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    manifest = root / 'PACKAGE_MANIFEST.json'
    manifest.write_text(json.dumps({'skill': root.name, 'files': records,
                                   'note': 'Manifest excludes itself; content integrity is not a teaching-quality audit.'},
                                  ensure_ascii=False, indent=2), encoding='utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED, compresslevel=6) as z:
        for path in files + [manifest]:
            z.write(path, root.name + '/' + path.relative_to(root).as_posix())
    print(json.dumps({'zip': str(output), 'files': len(files)+1, 'bytes': output.stat().st_size}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('skill', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    package(args.skill, args.output)
