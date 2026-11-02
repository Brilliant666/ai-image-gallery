# -*- coding: utf-8 -*-
"""Independent remote anime-costume catalog, trust boundaries and native UI."""
import contextlib
from copy import deepcopy
from html.parser import HTMLParser
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'sites/costume-anime'
SCRIPTS = SITE / 'scripts'


def module(name, path):
    # Restore module names/search paths: old sites also have catalog/seo modules.
    saved = list(sys.path)
    conflicts = {k: sys.modules.pop(k) for k in ('catalog', 'seo') if k in sys.modules}
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        result = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(result)
        return result
    finally:
        for k in ('catalog', 'seo'):
            sys.modules.pop(k, None)
        sys.modules.update(conflicts)
        sys.path[:] = saved


def db_from(page):
    return json.JSONDecoder().raw_decode(page, page.index('const DB = ') + len('const DB = '))[0]


def archive(catalog):
    return ('<script>const META=' + json.dumps(catalog['meta'], ensure_ascii=False)
            + ';\nconst D = ' + json.dumps(catalog['rows'], ensure_ascii=False)
            + ';\nthrow new Error("must never execute source JS");</script>').encode('utf-8')


class Markup(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.elements, self.text = [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, attrs))

    def handle_data(self, value):
        self.text.append(value)


class CostumeAnime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.importer = module('costume_anime_import', SCRIPTS / 'import_catalog.py')
        cls.builder = module('costume_anime_build', SCRIPTS / 'build_gallery.py')
        cls.catalog = json.loads((SITE / 'data/catalog.json').read_text(encoding='utf-8'))
        cls.manifest = json.loads((SITE / 'manifest.json').read_text(encoding='utf-8'))
        cls.page = (SITE / 'index.html').read_text(encoding='utf-8')
        cls.db = db_from(cls.page)

    def test_snapshot_alignment_and_dictionary_coverage(self):
        catalog = self.importer.parse(archive(self.catalog))
        self.assertEqual(catalog['rows'], self.catalog['rows'])
        self.assertEqual(catalog['source'], 'https://ai-costume-anime-gallery.pages.dev/')
        self.assertRegex(self.catalog['sha256'], '^[0-9a-f]{64}$')
        self.assertEqual(len(self.manifest), 1320)
        expected = self.importer.manifest_rows(catalog['rows'])
        self.assertEqual(self.manifest, expected)
        by_id = {r['id']: r for r in self.manifest}
        self.assertEqual(len(by_id), 1320)
        self.assertEqual({x['i'] for x in self.db['items']}, set(by_id))
        self.assertEqual(len(self.db['cats']), 8)
        tags = {t for x in self.db['items'] for t in x['t']}
        self.assertEqual(len(tags), 86)
        self.assertEqual(tags, set(self.db['tagZh']))
        self.assertEqual(tags, set(self.db['tagJa']))
        self.assertEqual(tags, {t for g in self.db['groups'] for t in g['tags']})
        for row in self.db['items']:
            self.assertEqual((row['c'], row['t']), (by_id[row['i']]['分类'], by_id[row['i']]['标签']))
        translated = json.loads((SITE / 'data/costume-anime-zh.json').read_text(encoding='utf-8'))
        self.assertEqual(len(translated), 1320)
        for row in translated:
            self.assertEqual(row['标签_zh'], [self.db['tagZh'][t] for t in row['标签']])
            self.assertEqual(row['标签_ja'], [self.db['tagJa'][t] for t in row['标签']])
        original = json.loads((ROOT / 'sites/costume/manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(len(original), 1407)
        self.assertIn('SPR-0001', {r['id'] for r in original} & set(by_id))

    def test_remote_paths_and_config(self):
        config = next(s for s in json.loads((ROOT / 'sites.json').read_text(encoding='utf-8'))['sites'] if s['id']=='costume-anime')
        self.assertEqual(config['imageMode'], 'remote')
        self.assertEqual(config['tiers'], [])
        self.assertEqual(config['imageDirs'], [])
        self.assertEqual(config['imageBase'], self.db['source'])
        self.assertEqual(config['adult'], {'分类':['ランジェリー','セクシー']})
        self.assertEqual(int(config['stats'][0]['public']),984)
        for row in self.manifest:
            for tier, directory, extension in [('thumb','thumbs','webp'),('preview','img','webp'),('full','png','png')]:
                self.assertEqual(row[tier+'_path'], f'{directory}/{row["id"]}.{extension}')
                self.assertEqual(row[tier+'_url'], config['source'] + row[tier+'_path'])
        self.assertEqual([p.relative_to(SITE).as_posix() for p in SITE.rglob('*')
                          if p.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.gif','.avif')], ['og-cover.jpg'])
        self.assertIn('content="https://example.com/costume-anime/og-cover.jpg"', self.page)
        self.assertNotIn('new Image(', self.page)
        self.assertNotIn('IntersectionObserver', self.page)

    def test_adult_flags_and_public_seo(self):
        adult = {r['id'] for r in self.manifest if r['分类'] in ('ランジェリー','セクシー')}
        self.assertEqual(len(adult),336)
        self.assertEqual({x['i'] for x in self.db['items'] if x.get('x')},adult)
        self.assertEqual(len([x for x in self.db['items'] if not x.get('x')]),984)
        meta = json.loads((SITE / 'data/landing.json').read_text(encoding='utf-8'))
        self.assertEqual(meta['dirs'],['browse','category','tag'])
        self.assertEqual(len([p for p in meta['pages'] if p.startswith('category/')]),6)
        self.assertGreater(len([p for p in meta['pages'] if p.startswith('tag/')]),70)
        public_thumbs={r['thumb_url'] for r in self.manifest if r['id'] not in adult}
        for slug in meta['pages']:
            self.assertFalse(any(c in slug for c in ('ランジェリー','セクシー')))
            page=(SITE / slug / 'index.html').read_text(encoding='utf-8')
            thumbs=re.findall(r'<img src="([^"]+)"',page)
            self.assertTrue(set(thumbs)<=public_thumbs,slug)
            self.assertNotRegex(page,r'<figcaption>(?:LNG|SXY)-')
            self.assertIn('content="https://example.com/costume-anime/og-cover.jpg"',page)
            self.assertNotIn('content="'+self.db['source']+'thumbs/SPR-0001.webp"',page)
            for text in re.findall(r'<script type="application/ld\+json">(.*?)</script>',page,re.S):
                json.loads(text)
        self.assertNotIn('%E3%83%A9%E3%83%B3%E3%82%B8%E3%82%A7', (SITE/'sitemap.xml').read_text())

    def test_import_only_reads_json_never_executes(self):
        content=archive(self.catalog)
        self.assertEqual(len(self.importer.parse(content)['rows']),1320)
        for bad in [content.replace(b'const D = ', b'const D = JSON.parse('),
                    content.replace(b'const D = ', b'const D = (function(){return '),
                    content.replace(b';\nthrow', b'+[];\nthrow'),
                    content + b'const D=[];', content.replace(b'"total": 1320',b'"total": 1320, "total": 1320')]:
            with self.subTest(content=bad[-120:]), self.assertRaises(ValueError):
                self.importer.parse(bad)

    def malicious_catalogs(self):
        # Change the final (adult) row to prove validation occurs before filtering.
        changes = [('id','SPR-0001'),('id','SXY-9999\n'),('id','../SXY-0139'),
                   ('id','SXY-0139" onload="alert(1)'),('カテゴリ','../outside'),
                   ('カテゴリ','春'),('カテゴリ',[]),('キーワード',['lace']),
                   ('キーワード','lace unknown'),('キーワード','lace lace'),
                   ('キーワード','lace\nblack'),('キーワード',''),
                   ('サムネ','//evil.test/x.webp'),('画像','img/../SXY-0139.webp'),
                   ('原寸','png/SXY-0139.png?x=1')]
        for field,value in changes:
            data=deepcopy(self.catalog)
            data['rows'][-1][field]=value
            yield field, data
        data=deepcopy(self.catalog);data['meta']['counts']['春']+=1
        yield 'META counts',data
        data=deepcopy(self.catalog);data['rows'].pop()
        yield 'missing row',data

    def test_malicious_import_fails_before_output(self):
        with tempfile.TemporaryDirectory(prefix='costume-anime-import-') as tmp:
            base=Path(tmp);archive_file=base/'archive.html';output=base/'site'
            (output/'data').mkdir(parents=True)
            (output/'manifest.json').write_text('sentinel',encoding='utf-8')
            (output/'data/catalog.json').write_text('sentinel',encoding='utf-8')
            for field,data in self.malicious_catalogs():
                archive_file.write_bytes(archive(data))
                before={p.relative_to(output):p.read_bytes() for p in output.rglob('*') if p.is_file()}
                with self.subTest(field=field), self.assertRaises(ValueError):
                    self.importer.import_archive(archive_file,output)
                self.assertEqual(before,{p.relative_to(output):p.read_bytes() for p in output.rglob('*') if p.is_file()})

    def test_build_revalidates_all_raw_fields_before_writes(self):
        with tempfile.TemporaryDirectory(prefix='costume-anime-security-') as tmp:
            root=Path(tmp);(root/'data').mkdir()
            for name in ('index.html','manifest.json','robots.txt','sitemap.xml'):
                (root/name).write_text('sentinel',encoding='utf-8')
            for field,data in self.malicious_catalogs():
                (root/'data/catalog.json').write_text(json.dumps(data),encoding='utf-8')
                before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
                with self.subTest(field=field), patch.object(self.builder,'ROOT',root), \
                        patch.object(self.builder.landing,'write_site',side_effect=AssertionError('writer reached')):
                    with self.assertRaises(ValueError):self.builder.build()
                self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_build_rejects_edited_manifest_before_output(self):
        with tempfile.TemporaryDirectory(prefix='costume-anime-manifest-') as tmp:
            root=Path(tmp);(root/'data').mkdir()
            shutil.copyfile(SITE/'data/catalog.json',root/'data/catalog.json')
            (root/'index.html').write_text('sentinel',encoding='utf-8')
            for field,value in [('id','../escape'),('分类','../escape'),('标签',['unknown']),
                                ('thumb_path','../escape.webp'),('thumb_url','https://evil.test/image'),
                                ('full_url','javascript:alert(1)'),('preview_path','img/../../escape')]:
                rows=deepcopy(self.manifest);rows[-1][field]=value
                (root/'manifest.json').write_text(json.dumps(rows),encoding='utf-8')
                before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
                with self.subTest(field=field),patch.object(self.builder,'ROOT',root), \
                        patch.object(self.builder.landing,'write_site',side_effect=AssertionError('writer reached')):
                    with self.assertRaisesRegex(ValueError,'manifest'):self.builder.build()
                self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_reproducible_build_and_inline_contract(self):
        with tempfile.TemporaryDirectory(prefix='costume-anime-rebuild-') as tmp:
            root=Path(tmp);(root/'data').mkdir()
            shutil.copyfile(SITE/'data/catalog.json',root/'data/catalog.json')
            shutil.copyfile(SITE/'manifest.json',root/'manifest.json')
            with patch.object(self.builder,'ROOT',root),patch.dict('os.environ',{'SITE_URL':'https://example.com/costume-anime'}),contextlib.redirect_stdout(io.StringIO()):
                self.builder.build()
            # Match .gitattributes: Git stores CSV as LF on every platform.
            # Local CRLF output used to pass on Windows but fail Linux CI.
            csv_bytes = (root/'data/translations.csv').read_bytes()
            self.assertTrue(csv_bytes.startswith(b'\xef\xbb\xbf'))
            self.assertNotIn(b'\r', csv_bytes)
            for path in root.rglob('*'):
                if path.is_file():
                    self.assertEqual(path.read_bytes(),(SITE/path.relative_to(root)).read_bytes(),str(path.relative_to(root)))
        self.assertLess(len(self.page.encode('utf-8')),240*1024)
        for key in self.db:self.assertRegex(self.page,r'DB\.'+re.escape(key)+r'\b')
        self.assertIn('rel="canonical" href="https://example.com/costume-anime/"',self.page)
        self.assertNotIn('fetch(',self.page)
        self.assertNotRegex(self.builder.json_script({'x':'</script><img onerror="1">& '}),r'[<>& ]')

    def test_native_ui_adult_events_paths_and_escaping(self):
        node=shutil.which('node')
        if not node:self.skipTest('node unavailable')
        code=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const page=fs.readFileSync(process.argv[1],'utf8');
let script=[...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x=>x[1]).find(x=>x.includes('const DB = '));
script=script.replace(/\}\)\(\);\s*$/, 'globalThis.probe={S,visible,hit,card,pathOf,openM,step,draw,getView:()=>VIEW};})();');
const els=new Map(),events={};
function element(key){if(!els.has(key)){const classes=new Set();els.set(key,{innerHTML:'',textContent:'',value:'',hidden:false,dataset:{},options:[{},{},{}],style:{},src:'',complete:false,naturalWidth:0,clientWidth:600,clientHeight:800,
 classList:{add:c=>classes.add(c),remove:c=>classes.delete(c),contains:c=>classes.has(c),toggle:c=>{if(classes.has(c)){classes.delete(c);return false;}classes.add(c);return true;}},
 addEventListener(name,fn){this['on_'+name]=fn;},setAttribute(){},removeAttribute(){},querySelectorAll(){return [];},querySelector(){return null;},closest(){return null;}});}return els.get(key);}
const PL={lang:'zh',adult:false,openDialog(m){m.classList.add('open');},closeDialog(m){m.classList.remove('open');if(m.on_plclose)m.on_plclose();},top(){return element('#modal');}};
const context=vm.createContext({PL,URLSearchParams,console,setTimeout,clearTimeout,location:{hash:''},navigator:{},document:{querySelector:element,addEventListener(name,fn){events['doc:'+name]=fn;}},addEventListener(name,fn){events[name]=fn;}});
vm.runInContext(script,context);const p=context.probe;
assert.equal(p.getView().length,984);assert(p.visible().every(x=>!x.x));assert(!element('#tabs').innerHTML.includes('ランジェリー'));assert(!element('#tabs').innerHTML.includes('セクシー'));
const paths=p.getView().map(x=>[x.i,...p.pathOf(x)]);
p.S.tags.add('knit');p.draw();assert(p.getView().every(x=>x.t.includes('knit')));p.S.q='SPR-0001'.toLowerCase();p.draw();assert(p.getView().every(x=>x.i==='SPR-0001'));p.S.q='';p.S.tags.clear();p.draw();
PL.adult=true;events['pl:adult']();assert.equal(p.getView().length,1320);assert(element('#tabs').innerHTML.includes('ランジェリー'));
const idx=p.getView().findIndex(x=>x.x);p.openM(idx,element('opener'));assert(element('#modal').classList.contains('open'));assert.match(element('#mimg').src,/\/img\/(LNG|SXY)-\d{4}\.webp$/);
PL.adult=false;events['pl:adult']();assert(!element('#modal').classList.contains('open'));assert.equal(p.getView().length,984);assert(p.getView().every(x=>!x.x));
p.S.tags.add('knit');p.S.q='knit';PL.lang='ja';events['pl:lang']();assert.equal(p.S.q,'knit');assert(p.S.tags.has('knit'));assert(element('#ftogT').textContent.includes('タグ'));assert(element('#mcopy').textContent.includes('英語'));
p.S.tags.clear();p.S.q='';p.draw();const target={classList:{contains:c=>c==='card'},dataset:{i:'0'}};let prevented=false;element('#grid').on_keydown({key:'Enter',target,preventDefault(){prevented=true;}});assert(prevented);assert(element('#modal').classList.contains('open'));p.step(1);assert.equal(element('#mid').textContent.split(' ')[0],p.getView()[1].i);
const evil='SXY-0139" onerror="alert(1)" injected="yes"><svg onload="alert(2)">&\'&quot;';
const markup=p.card({i:evil,c:evil,t:[evil]},0);console.log(JSON.stringify({markup,evil,paths}));
'''
        result=subprocess.run([node,'-e',code,str(SITE/'index.html')],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        output=json.loads(result.stdout)
        markup=Markup(output['markup'])
        self.assertEqual(sum(tag=='img' for tag,_ in markup.elements),1)
        self.assertFalse([tag for tag,_ in markup.elements if tag in ('svg','script')])
        for tag,attrs in markup.elements:
            self.assertEqual(len(attrs),len(dict(attrs)))
            self.assertFalse([key for key,_ in attrs if key.startswith('on') or key=='injected'])
        self.assertIn(output['evil'],markup.text)
        by_id={r['id']:r for r in self.manifest}
        for key,thumb,preview,full in output['paths']:
            self.assertEqual([thumb,preview,full],[by_id[key][k] for k in ('thumb_url','preview_url','full_url')])


if __name__=='__main__':
    unittest.main(verbosity=2)
