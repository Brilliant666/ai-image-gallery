# -*- coding: utf-8 -*-
"""原生角色库：公开目录、远程素材与可复现构建约束。"""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'sites/character'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class Character(unittest.TestCase):
    def test_public_snapshot_and_provenance(self):
        catalog = json.loads((SITE / 'data/catalog.json').read_text(encoding='utf-8'))
        self.assertEqual(catalog['tier'], 'public')
        self.assertRegex(catalog['sha256'], r'^[0-9a-f]{64}$')
        self.assertNotIn('zip_url', catalog)
        self.assertNotIn('line_url', catalog)
        self.assertEqual(len(catalog['items']), 1027)
        self.assertEqual(sum(not i.get('parent') for i in catalog['items']), 843)
        rows = {i['id']: i for i in catalog['items']}
        self.assertEqual(len(rows), 1027)
        for r in rows.values():
            if r.get('parent'):
                self.assertIn(r['parent'], rows)
                self.assertEqual(rows[r['parent']]['tags'], r['tags'])

    def test_import_does_not_execute_or_accept_private_data(self):
        importer = module('character_import', SITE / 'scripts/import_catalog.py')
        fixture = {'tier':'public', 'built':'2026-11-01', 'items':[{'id':'H001','set':'hair','cat':'髪型','jp':'長髪','tags':'long hair','tier':'public'}]}
        parsed = importer.parse(('window.DB = ' + json.dumps(fixture) + ';').encode())
        self.assertEqual(parsed['items'][0]['id'], 'H001')
        for content in [b'window.DB = {}; alert(1);', b'window.DB = {"tier":"private","items":[]};']:
            with self.assertRaises(ValueError):
                importer.parse(content)
        fixture['items'].append(dict(fixture['items'][0]))
        with self.assertRaises(ValueError):
            importer.parse(('window.DB = ' + json.dumps(fixture)).encode())

    def test_own_translations_complete(self):
        translations = module('character_translation', SITE / 'scripts/translations.py')
        catalog = json.loads((SITE / 'data/catalog.json').read_text(encoding='utf-8'))
        for row in catalog['items']:
            self.assertTrue(translations.chinese(row), row['id'])
            self.assertIn(row['cat'], translations.CATEGORIES)

    def test_landing_share_images_and_features(self):
        import re
        pages = [SITE / 'browse/index.html'] + sorted((SITE / 'cat').glob('*/index.html'))
        self.assertGreater(len(pages), 1)
        for page in pages:
            text = page.read_text(encoding='utf-8')
            for field in ('og:image', 'twitter:image'):
                self.assertIn('"%s" content="https://charadb-2fi.pages.dev/thumb/H001.webp"' % field, text, str(page))
            self.assertNotIn('character/og-cover.jpg', text)
            more = re.search(r'<p class="more">(.*?)</p>', text)
            if more:
                self.assertIn('收藏和复制标签', more.group(1))
                self.assertNotIn('下载', more.group(1))

    def test_manifest_remote_and_adult_rules(self):
        rows = json.loads((SITE / 'manifest.json').read_text(encoding='utf-8'))
        by_id = {r['id']:r for r in rows}
        config = next(s for s in json.loads((ROOT/'sites.json').read_text(encoding='utf-8'))['sites'] if s['id']=='character')
        self.assertEqual(config['imageMode'], 'remote')
        self.assertEqual(config['tiers'], [])
        self.assertEqual(config['imageDirs'], [])
        self.assertEqual(sum(r['rating']=='suggestive' and not r.get('parent') for r in rows),52)
        self.assertEqual(by_id['P255']['rating'],'general')
        self.assertEqual(by_id['O231']['rating'],'suggestive')
        self.assertEqual(by_id['P082-s']['rating'],'suggestive')
        for row in rows:
            for tier in ['thumb','full'] + (['line'] if row.get('line') else []):
                self.assertEqual(row[tier+'_url'], config['source'] + row[tier+'_path'])
        self.assertEqual(len([r for r in rows if r.get('line')]),281)
        self.assertEqual(int(config['stats'][0]['public']),791)


if __name__ == '__main__':
    unittest.main(verbosity=2)
