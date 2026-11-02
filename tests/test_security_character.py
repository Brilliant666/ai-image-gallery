# -*- coding: utf-8 -*-
"""Character catalog trust boundaries; builds stay inside temporary directories."""
import contextlib
from html.parser import HTMLParser
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'sites/character'
SCRIPTS = SITE / 'scripts'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def item(**changes):
    return dict({'id': 'H001', 'set': 'hair', 'cat': '髪型', 'jp': '長髪',
                 'tags': 'long hair', 'tier': 'public'}, **changes)


def source(rows):
    return ('window.DB = ' + json.dumps({'tier': 'public', 'built': '2026-11-01',
                                        'items': rows}, ensure_ascii=False) + ';').encode('utf-8')


class Markup(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.text = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, attrs))

    def handle_data(self, data):
        self.text.append(data)


class CharacterSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.importer = module('security_character_import', SCRIPTS / 'import_catalog.py')
        cls.builder = module('security_character_build', SCRIPTS / 'build_gallery.py')

    def test_import_rejects_category_path_syntax(self):
        for category in ('../outside', '/absolute', 'nested/category', r'nested\category',
                         'foo..bar', '..', ''):
            with self.subTest(category=category), self.assertRaisesRegex(ValueError, '分类'):
                self.importer.parse(source([item(cat=category)]))

    def test_import_preserves_valid_categories_and_id_grammar(self):
        rows = [item(), item(id='H001-black', parent='H001'),
                item(id='O001', set='outfit', cat='カジュアル(春夏)'),
                item(id='P001-s', set='pose', cat='上半身・手の仕草')]
        parsed = self.importer.parse(source(rows))
        self.assertEqual([row['id'] for row in parsed['items']], [row['id'] for row in rows])
        self.assertEqual([row['cat'] for row in parsed['items']], [row['cat'] for row in rows])
        for key in ('H001\" onmouseover=\"alert(1)', '../H001', 'H001/extra',
                    'H001\\extra', 'H001\n', 'X001', 'H001-red'):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'ID'):
                self.importer.parse(source([item(id=key)]))

    def test_current_catalog_import_and_build_remain_compatible(self):
        catalog = json.loads((SITE / 'data/catalog.json').read_text(encoding='utf-8'))
        parsed = self.importer.parse(source([dict(row, tier='public') for row in catalog['items']]))
        self.assertEqual(parsed['items'], catalog['items'])
        with tempfile.TemporaryDirectory(prefix='character-valid-') as tmp:
            root = Path(tmp) / 'character'
            (root / 'data').mkdir(parents=True)
            shutil.copyfile(SITE / 'data/catalog.json', root / 'data/catalog.json')
            with patch.object(self.builder, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                self.builder.build()
            self.assertEqual((root / 'manifest.json').read_text(encoding='utf-8'),
                             (SITE / 'manifest.json').read_text(encoding='utf-8'))
            page = (root / 'index.html').read_text(encoding='utf-8')
            start = page.index('const DB = ') + len('const DB = ')
            db, end = json.JSONDecoder().raw_decode(page, start)
            committed = (SITE / 'index.html').read_text(encoding='utf-8')
            committed_start = committed.index('const DB = ') + len('const DB = ')
            _, committed_end = json.JSONDecoder().raw_decode(committed, committed_start)
            self.assertEqual(page[start:end], committed[committed_start:committed_end])
            self.assertEqual(len(db['items']), 843)
            self.assertEqual(len(db['variants']), 184)
            self.assertEqual({row[0] for row in db['items']} | {row[0] for row in db['variants']},
                             {row['id'] for row in catalog['items']})

    def check_build_rejected_without_output(self, rows, message):
        with tempfile.TemporaryDirectory(prefix='character-security-') as tmp:
            root = Path(tmp) / 'character'
            (root / 'data').mkdir(parents=True)
            (root / 'data/catalog.json').write_text(json.dumps({
                'tier': 'public', 'built': '2026-11-01', 'items': rows}), encoding='utf-8')
            for name in ('manifest.json', 'index.html', 'robots.txt', 'sitemap.xml'):
                (root / name).write_text('existing output', encoding='utf-8')
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            # Keep translations from rejecting a malicious field accidentally. Validation must
            # precede both translation and every output, even if a future translation accepts it.
            categories = dict(self.builder.CATEGORIES)
            categories.update((row['cat'], '测试分类') for row in rows)
            with patch.object(self.builder, 'ROOT', root), \
                    patch.object(self.builder, 'CATEGORIES', categories), \
                    patch.object(self.builder, 'chinese', return_value='测试条目'), \
                    patch.object(self.builder.landing, 'write_site',
                                 side_effect=AssertionError('reached landing writer')), \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, message):
                    self.builder.build()
            after = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            self.assertEqual(after, before, 'Invalid input changed generated output')

    def test_build_revalidates_all_ids_before_output(self):
        for bad in ('H001\" onerror=\"alert(1)', '../H001', 'H001/extra',
                    'H001\\extra', 'H001\n', 'X001', 'H001-red'):
            for row in (item(id=bad), item(id=bad, parent='H001'),
                        item(id=bad, set='outfit', cat='水着')):
                with self.subTest(key=bad, parent=row.get('parent'), cat=row['cat']):
                    self.check_build_rejected_without_output([item(id='H002'), row], 'ID')

    def test_build_validates_raw_categories_before_filtering(self):
        for bad in ('../outside', '/absolute', 'nested/category', r'nested\category',
                    'foo..bar', '..', ''):
            for row in (item(cat=bad), item(id='H001-black', parent='H001', cat=bad),
                        item(id='O013', set='outfit', cat=bad)):
                with self.subTest(category=bad, key=row['id']):
                    self.check_build_rejected_without_output([item(id='H002'), row], '分类')

    def test_card_dom_keeps_ids_keys_and_urls_as_data(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('没有 node')
        # Execute the actual gallery closure with a DOM fixture, as in shisei_adult.js.
        # Python's HTML parser checks the resulting markup instead of trusting a stub's innerHTML.
        code = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
function boot(DB) {
  const elements = new Map();
  function element(key) {
    if (!elements.has(key)) elements.set(key, {
      innerHTML:'', textContent:'', value:'', checked:false, hidden:false, dataset:{},
      addEventListener(){}, setAttribute(){}, removeAttribute(){},
      closest(){return null;}, contains(){return false;}, querySelectorAll(){return [];}
    });
    return elements.get(key);
  }
  const context = vm.createContext({DB, PL:{lang:'zh',adult:false}, URLSearchParams,
    document:{querySelector:element, activeElement:element('active')},
    localStorage:{getItem(){return null;}}, location:{hash:''}, addEventListener(){}});
  vm.runInContext(source.replace(/\}\)\(\);\s*$/,
    'globalThis.probe = {card, items, draw, currentItems};})();'), context);
  return {...context.probe, element};
}
const malicious = 'H001" onerror="alert(1)" injected="yes"><svg onload="alert(2)">&\'&quot;';
const key = 'key" autofocus onfocus="alert(3)"><img src=x onerror="alert(4)">';
const db = {cats:[['髪型','发型']],items:[[malicious,'長髪','长发','long hair',0,0]],
  variants:[], source:'https://charadb-2fi.pages.dev/',built:'test'};
const gallery = boot(db);
const rendered = gallery.element('#grid').innerHTML;
assert.equal(gallery.currentItems()[0].item.id, malicious);
const card = gallery.card({item:gallery.items.get(malicious),key});
const variantId = malicious + '-black';
const variant = boot({...db, items:[['H001','長髪','长发','long hair',0,0]],variants:[[variantId,'H001']]});
const variantCard = variant.card({item:variant.items.get(variantId),key:'H001'});
const valid = boot({...db, items:[['H001','長髪','长发','long hair',0,0]],variants:[]});
console.log(JSON.stringify({malicious,key,rendered,card,variantId,variantCard,
  valid:valid.element('#grid').innerHTML}));
'''
        result = subprocess.run([node, '-e', code, str(SCRIPTS / 'gallery.js')],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = json.loads(result.stdout)
        for field, expected_id, expected_key in (
                ('rendered', output['malicious'], output['malicious']),
                ('card', output['malicious'], output['key']),
                ('variantCard', output['variantId'], 'H001'),
                ('valid', 'H001', 'H001')):
            with self.subTest(markup=field):
                markup = Markup(output[field])
                self.assertFalse([tag for tag, _ in markup.elements if tag in ('svg', 'script')])
                self.assertEqual(sum(tag == 'img' for tag, _ in markup.elements), 1)
                for _, attrs in markup.elements:
                    self.assertFalse([name for name, _ in attrs if name.startswith('on') or name in ('autofocus', 'injected')])
                    self.assertEqual(len(attrs), len(dict(attrs)), 'injected duplicate attribute')
                    values = dict(attrs)
                    for name in ('data-id', 'data-open', 'data-copy', 'data-fav'):
                        if name in values:
                            self.assertEqual(values[name], expected_id)
                    if 'data-key' in values:
                        self.assertEqual(values['data-key'], expected_key)
                    if 'src' in values:
                        self.assertEqual(values['src'], 'https://charadb-2fi.pages.dev/thumb/' + expected_id + '.webp')
                self.assertIn(expected_id, markup.text, 'ID must remain literal text')


if __name__ == '__main__':
    unittest.main(verbosity=2)
