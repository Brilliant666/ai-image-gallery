# -*- coding: utf-8 -*-
"""从已下载的原站 public data.js 导入目录（只解析 JSON，绝不执行 JS）。

python -I sites/character/scripts/import_catalog.py /path/to/data.js
只接收 public tier，忽略作者的外部下载/社区入口，不下载图片。
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://charadb-2fi.pages.dev/'


def parse(raw):
    text = raw.decode('utf-8-sig').strip()
    match = re.fullmatch(r'window\.DB\s*=\s*(\{.*\})\s*;?', text, re.S)
    if not match:
        raise ValueError('不是原站 window.DB JSON 目录')
    data = json.loads(match.group(1))
    if data.get('tier') != 'public':
        raise ValueError('只导入 public 目录')
    rows, seen = [], set()
    for source in data['items']:
        item = {k: source[k] for k in ('id', 'set', 'cat', 'jp', 'tags')}
        if source.get('tier') != 'public' or item['set'] not in ('hair', 'outfit', 'pose'):
            raise ValueError('非公开条目或未知分区')
        if not re.fullmatch(r'[HOP]\d{3}(?:-(?:s|black|blonde|pink|silver))?', item['id']):
            raise ValueError('未知条目 ID')
        if item['id'] in seen or any(not isinstance(v, str) for v in item.values()):
            raise ValueError('重复 ID 或非文本字段')
        seen.add(item['id'])
        if source.get('sub'):
            item['sub'] = source['sub']
        if source.get('parent'):
            item['parent'] = source['parent']
        if source.get('line'):
            item['line'] = True
        rows.append(item)
    if any(r.get('parent') and r['parent'] not in seen for r in rows):
        raise ValueError('换色版本缺少基础条目')
    return {'source': SOURCE + 'data.js', 'sha256': hashlib.sha256(raw).hexdigest(),
            'built': data['built'], 'tier': 'public', 'items': rows}


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('source', type=Path)
    source = args.parse_args().source
    result = parse(source.read_bytes())
    target = ROOT / 'data' / 'catalog.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('public catalog: %d rows -> %s' % (len(result['items']), target))


if __name__ == '__main__':
    main()
