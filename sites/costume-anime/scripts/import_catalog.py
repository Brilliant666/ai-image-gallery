# -*- coding: utf-8 -*-
"""Read a local HTML archive as data. No network access or image download.

Run from a trusted directory: python -I scripts/import_catalog.py /path/to/archive.html
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import parse, manifest_rows
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from assets import safe_under

ROOT = Path(__file__).resolve().parents[1]


def import_archive(archive, root=ROOT):
    # All input validation and output path checks precede the first write.
    catalog = parse(Path(archive).read_bytes())
    outputs = {'data/catalog.json': catalog, 'manifest.json': manifest_rows(catalog['rows'])}
    paths = {name: Path(safe_under(str(root), name)) for name in outputs}
    for path in paths.values():
        if path.exists() and not path.is_file():
            raise ValueError(f'output is not a file: {path}')
        if path.parent.exists() and not path.parent.is_dir():
            raise ValueError(f'output parent is not a directory: {path.parent}')
    for name, obj in outputs.items():
        path = paths[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'imported {len(catalog["rows"])} outfits; no images fetched; sha256={catalog["sha256"]}')
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path, help='local source HTML archive (read only)')
    args = parser.parse_args()
    import_archive(args.archive)


if __name__ == '__main__':
    main()
