# -*- coding: utf-8 -*-
"""Strict, shared validation for the independent anime costume source snapshot."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from collections import Counter

REPO = Path(__file__).resolve().parents[3]
SOURCE = 'https://ai-costume-anime-gallery.pages.dev/'
AUTHOR_URL = 'https://x.com/giaaibusi'
COUNTS = {'春': 197, '夏': 237, '秋': 230, '冬': 232, 'ランジェリー': 197,
          'パーティ': 36, '水着': 52, 'セクシー': 139}
PREFIX = dict(zip(COUNTS, ('SPR', 'SUM', 'AUT', 'WIN', 'LNG', 'PTY', 'SWM', 'SXY')))
CAT_ORDER = ['春', '夏', '秋', '冬', '水着', 'パーティ', 'ランジェリー', 'セクシー']
ADULT = frozenset(('ランジェリー', 'セクシー'))
RAW_FIELDS = {'id', 'カテゴリ', 'キーワード', 'サムネ', '画像', '原寸'}

# Reuse trusted translations without importing/executing the original builder.
_spec = importlib.util.spec_from_file_location('costume_anime_dictionaries',
                                               REPO / 'sites/costume/scripts/translations.py')
translations = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(translations)
CAT_ZH, TAG_ZH, TAG_JA, TAG_GROUPS = (translations.CAT_ZH, translations.TAG_ZH,
                                    translations.TAG_JA, translations.TAG_GROUPS)


def validate_rows(rows, meta):
    """Validate ALL raw fields, including adult rows, before translation or writes."""
    if not isinstance(rows, list) or not rows:
        raise ValueError('D must be a nonempty array')
    seen, tags_seen = set(), set()
    grouped = [tag for _, _, _, tags in TAG_GROUPS for tag in tags]
    if len(grouped) != len(set(grouped)) or set(grouped) != set(TAG_ZH) or set(grouped) != set(TAG_JA):
        raise ValueError('tag dictionary/group coverage mismatch')
    for row in rows:
        if not isinstance(row, dict) or set(row) != RAW_FIELDS:
            raise ValueError('raw row fields mismatch')
        key, cat, tags = row['id'], row['カテゴリ'], row['キーワード']
        if not isinstance(key, str) or not re.fullmatch(r'(SPR|SUM|AUT|WIN|LNG|PTY|SWM|SXY)-\d{4}', key, re.ASCII):
            raise ValueError(f'invalid ID: {key!r}')
        if key in seen:
            raise ValueError(f'duplicate ID: {key}')
        seen.add(key)
        if not isinstance(cat, str) or cat not in COUNTS or not key.startswith(PREFIX[cat] + '-'):
            raise ValueError(f'invalid category/ID: {cat!r}')
        if not isinstance(tags, str) or not re.fullmatch(r'[a-z]+(?:-[a-z]+)*(?: [a-z]+(?:-[a-z]+)*)*', tags, re.ASCII):
            raise ValueError(f'invalid tags string: {key}')
        split = tags.split(' ')
        if len(split) != len(set(split)) or any(t not in TAG_ZH or t not in TAG_JA for t in split):
            raise ValueError(f'unknown/duplicate tag: {key}')
        tags_seen.update(split)
        for field, directory, ext in [('サムネ', 'thumbs', 'webp'), ('画像', 'img', 'webp'), ('原寸', 'png', 'png')]:
            if row[field] != f'{directory}/{key}.{ext}':
                raise ValueError(f'invalid image path: {key} {field}')
    counts = dict(Counter(row['カテゴリ'] for row in rows))
    if len(rows) != 1320 or counts != COUNTS or tags_seen != set(grouped):
        raise ValueError('snapshot totals/category counts/tag coverage mismatch')
    if (not isinstance(meta, dict) or set(meta) != {'total', 'cats', 'counts'}
            or type(meta['total']) is not int or meta['total'] != len(rows)
            or meta['cats'] != list(COUNTS) or not isinstance(meta['counts'], dict)
            or any(type(v) is not int for v in meta['counts'].values()) or meta['counts'] != counts):
        raise ValueError('META does not match full raw data')
    return rows


def validate_catalog(catalog):
    if (not isinstance(catalog, dict) or set(catalog) != {'source', 'author', 'sha256', 'meta', 'rows'}
            or catalog['source'] != SOURCE or catalog['author'] != 'ギア'
            or not isinstance(catalog['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', catalog['sha256'])):
        raise ValueError('invalid catalog provenance')
    validate_rows(catalog['rows'], catalog['meta'])
    return catalog


def manifest_rows(rows):
    return [{'id': r['id'], '分类': r['カテゴリ'], '标签': r['キーワード'].split(' '),
             'thumb_path': r['サムネ'], 'thumb_url': SOURCE + r['サムネ'],
             'preview_path': r['画像'], 'preview_url': SOURCE + r['画像'],
             'full_path': r['原寸'], 'full_url': SOURCE + r['原寸']} for r in rows]


def validate_manifest(rows, expected):
    """Do not silently overwrite manually edited unsafe manifest fields on rebuild."""
    if not isinstance(rows, list) or rows != expected:
        raise ValueError('manifest differs from validated source catalog; reimport trusted archive')
    return rows


def parse(content):
    """Read only JSON literals assigned to const D/META. Never evaluate JavaScript."""
    if not isinstance(content, bytes):
        raise ValueError('archive must be bytes')
    text = content.decode('utf-8-sig')
    decoder = json.JSONDecoder(object_pairs_hook=_unique_object)
    values = {}
    for name in ('D', 'META'):
        matches = list(re.finditer(r'\bconst\s+' + name + r'\s*=\s*', text))
        if len(matches) != 1:
            raise ValueError(f'expected exactly one const {name}')
        value, end = decoder.raw_decode(text, matches[0].end())
        if not text[end:].lstrip().startswith(';'):
            raise ValueError(f'const {name} must contain only JSON followed by semicolon')
        values[name] = value
    validate_rows(values['D'], values['META'])
    return {'source': SOURCE, 'author': 'ギア', 'sha256': hashlib.sha256(content).hexdigest(),
            'meta': values['META'], 'rows': values['D']}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON field: {key}')
        result[key] = value
    return result


def read_catalog(path):
    return validate_catalog(json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=_unique_object))
