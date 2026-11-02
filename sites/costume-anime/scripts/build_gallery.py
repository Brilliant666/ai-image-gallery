# -*- coding: utf-8 -*-
"""Build the remote-only anime costume resource gallery; no network access."""
from copy import deepcopy
import csv
import html
import io
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parents[2]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / 'shared'))
from catalog import (SOURCE, AUTHOR_URL, CAT_ORDER, CAT_ZH, TAG_ZH, TAG_JA, TAG_GROUPS,
                     ADULT, read_catalog, manifest_rows, validate_manifest, translations)
import adult
import landing
import ui
from assets import safe_under
import seo

ROOT = SCRIPTS.parent
TERMS = (
    '图片由原站加载，需要联网。禁止批量下载（含自动获取）、再分发、转载或销售图片。',
    '画像は元サイトから読み込み、接続が必要です。一括ダウンロード（自動取得を含む）・再配布・転載・販売は禁止です。')


def json_script(obj):
    return (json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
            .replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def interface():
    text = deepcopy(translations.UI)
    for lang, updates in {
        'zh': {'title': '二次元服装库：1320 套与标签筛选 · photoai.life',
               'eyebrow': 'COSTUME-ANIME-DB · 动漫服装参考', 'h1': '二次元服装库',
               'sub1': '1320 套不含人物的动漫风服装。86 个中日标签按颜色、单品、鞋袜、配饰、材质、长度组合筛选，保留英文关键词。',
               'copyTags': '复制英文标签', 'openFull': '打开原站 PNG',
               'hint': '← → 前后切换 · Esc 关闭 · 点击标签加入筛选 · 图片从原站加载'},
        'ja': {'title': 'アニメ衣装参考集：1320 着・タグ検索 · photoai.life',
               'eyebrow': 'COSTUME-ANIME-DB · アニメ衣装参考', 'h1': 'アニメ衣装集',
               'sub1': '人物の入っていないアニメ調の衣装 1320 着。色・アイテム・素材など 86 タグで組み合わせ検索。英語キーワードをコピーできます。',
               'copyTags': '英語タグをコピー', 'openFull': '元サイトの PNG を開く',
               'hint': '← → 前後 · Esc 閉じる · タグで絞り込み · 画像は元サイトから読み込み'},
    }.items():
        text[lang].update(updates)
        text[lang]['footer'] = (('素材来源：' if lang == 'zh' else '素材元：')
            + f'<a href="{SOURCE}" target="_blank" rel="noopener noreferrer">ai-costume-anime-gallery.pages.dev</a> · '
            + f'<a href="{AUTHOR_URL}" rel="noopener noreferrer">ギア</a><br>' + TERMS[0 if lang == 'zh' else 1])
    return adult.ui(text)


def write(path, text, encoding='utf-8', newline='\n'):
    # Path.write_text gained newline only in 3.10; CI still supports Python 3.8.
    with path.open('w', encoding=encoding, newline=newline) as stream:
        stream.write(text)


def build():
    root = Path(ROOT)
    # Catalog and derived manifest are both boundaries: validate every raw row before
    # filtering adult content or invoking ANY writer, including landing.write_site.
    catalog = read_catalog(root / 'data/catalog.json')
    manifest = manifest_rows(catalog['rows'])
    manifest_file = root / 'manifest.json'
    if manifest_file.exists():
        validate_manifest(json.loads(manifest_file.read_text(encoding='utf-8')), manifest)
    rule = adult.rules('costume-anime')
    if rule != {'分类': ['ランジェリー', 'セクシー']}:
        raise ValueError('costume-anime adult config must hide lingerie and sexy categories')
    site_url = os.environ.get('SITE_URL', 'https://example.com/costume-anime').rstrip('/')
    parsed = urlsplit(site_url)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.query or parsed.fragment or re.search(r'[\s<>"\x00-\x1f]', site_url):
        raise ValueError('SITE_URL must be an absolute HTTPS base URL')
    items = [{'i': r['id'], 'c': r['分类'], 't': r['标签'],
              **({'x': 1} if r['分类'] in ADULT else {})} for r in manifest]
    strings = interface()
    payload = {'items': items, 'cats': CAT_ORDER, 'groups': [
        {'k': key, 'ja': ja, 'zh': zh, 'tags': tags} for key, ja, zh, tags in TAG_GROUPS],
        'catZh': CAT_ZH, 'tagZh': TAG_ZH, 'tagJa': TAG_JA, 'ui': strings, 'source': SOURCE}
    # Group keys used in metadata but not UI need not be sent to the browser.
    for group in payload['groups']:
        group.pop('k')
    schema = {'@context': 'https://schema.org', '@type': 'ImageGallery', '@id': site_url + '/#gallery', 'name': '二次元服装库 COSTUME-ANIME-DB',
              'url': site_url + '/', 'inLanguage': ['zh-CN', 'ja'], 'numberOfItems': 1320,
              'isAccessibleForFree': True, 'creditText': 'ギア / AI Costume Anime Gallery',
              'copyrightNotice': '图片及原始元数据按原站条件使用',
              'creator': {'@type': 'Person', 'name': 'ギア', 'url': AUTHOR_URL}}
    page = (SCRIPTS / 'gallery.html').read_text(encoding='utf-8')
    # Check fixed output paths before landing generation writes anything.
    names = ['index.html', 'manifest.json', 'data/costume-anime-zh.json', 'data/meta.json',
             'data/translations.csv', 'robots.txt', 'sitemap.xml', '404.html']
    paths = {name: Path(safe_under(str(root), name)) for name in names}
    for path in paths.values():
        if path.exists() and not path.is_file():
            raise ValueError(f'output must be a file: {path}')
        if path.parent.exists() and not path.parent.is_dir():
            raise ValueError(f'output parent must be a directory: {path.parent}')
    urls, intro = seo.build(root, site_url, items, CAT_ORDER)
    for key, value in {
        '__SITE__': html.escape(site_url, quote=True), '__SHARE__': html.escape(site_url + '/og-cover.jpg', quote=True),
        '__SCHEMA__': json_script(schema), '__UI_HEAD__': ui.head_script(), '__UI_CSS__': ui.head_css(),
        '__UI_BAR__': ui.bar('costume-anime'), '__UI_DIALOGS__': ui.dialogs(ui.COSTUME_KEYS), '__UI_JS__': ui.body_script(),
        '__SEO_CSS__': landing.SEO_INTRO_CSS, '__SEO_INTRO__': intro, '__FAQ_LD__': landing.faq_ld_script(seo.FAQ),
        '__EYEBROW__': ui.bi(strings['zh']['eyebrow'], strings['ja']['eyebrow']),
        '__H1__': ui.bi(strings['zh']['h1'], strings['ja']['h1']), '__LEAD__': ui.bi(strings['zh']['sub1'], strings['ja']['sub1']),
        '__STATS__': ''.join(f'<li><b>{n}</b>{ui.bi(zh, ja)}</li>' for n, zh, ja in [('1,320', '套服装', '着の衣装'), ('8', '个分类', 'カテゴリ'), ('86', '个标签', 'タグ')]),
        '__TERMS__': ui.bi(*TERMS), '__TABS_LABEL__': '服装分类 / 衣装カテゴリ', '__SEARCH_ICON__': ui.SEARCH_ICON,
        '__FOOTER__': '<span class="zh">' + strings['zh']['footer'] + '</span><span class="ja">' + strings['ja']['footer'] + '</span>',
    }.items():
        page = page.replace(key, value)
    page = page.replace('__PAYLOAD__', json_script(payload))
    if re.search(r'__[A-Z_]+__', page):
        raise ValueError('unresolved template placeholder')
    if len(page.encode('utf-8')) >= 240 * 1024:
        raise ValueError('gallery exceeds 240 KB')
    write(paths['index.html'], page)
    write(paths['manifest.json'], json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')
    translated = [dict(r, 分类_zh=CAT_ZH[r['分类']], 标签_zh=[TAG_ZH[t] for t in r['标签']],
                       标签_ja=[TAG_JA[t] for t in r['标签']]) for r in manifest]
    for name, obj in [('data/costume-anime-zh.json', translated), ('data/meta.json', {
        'site': 'COSTUME-ANIME-DB', 'source': SOURCE, 'author': 'ギア', 'imageMode': 'remote',
        'items': 1320, 'public': 984, 'adult': 336, 'tags': 86, 'categories': catalog['meta']['counts'],
        'source_sha256': catalog['sha256'], 'metadata_terms': 'Original metadata and images retain source terms; translations/code only are original work.'})]:
        write(paths[name], json.dumps(obj, ensure_ascii=False, indent=1) + '\n')
    table = io.StringIO(newline='')
    writer = csv.writer(table, lineterminator='\n')
    writer.writerow(['字段', '原文', '日文', '中文'])
    writer.writerows(['カテゴリ', c, c, CAT_ZH[c]] for c in CAT_ORDER)
    writer.writerows(['キーワード', t, TAG_JA[t], TAG_ZH[t]] for t in TAG_ZH)
    write(paths['data/translations.csv'], table.getvalue(), encoding='utf-8-sig', newline='')
    write(paths['robots.txt'], 'User-agent: *\nAllow: /\n\nSitemap: ' + site_url + '/sitemap.xml\n')
    landing.sitemap(site_url, urls, str(paths['sitemap.xml']), lastmod=landing.updated('costume-anime'))
    write(paths['404.html'], ui.page_404('/'))
    print(f'costume-anime: 1320 outfits / 984 public / 336 adult; {len(page.encode("utf-8"))/1024:.1f} KB; remote-only')


if __name__ == '__main__':
    build()
