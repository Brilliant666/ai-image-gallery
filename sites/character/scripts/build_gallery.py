# -*- coding: utf-8 -*-
"""构建原生二次元角色库；公开目录内嵌，图片始终从原站读取。Python 3.8+。"""
import json
import os
import sys
from pathlib import Path
from html import escape

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT.parents[1] / 'shared'))
import landing
import ui
from translations import CATEGORIES, chinese

SOURCE = 'https://charadb-2fi.pages.dev/'
LICENSE = '可免费用于作品制作、商用、加工与参考；禁止再分发、转载或转售图片本身（包括加工后的图片）。不得用于表现真实人物或未成年人。'
# 按本库内容单独审核：泳装与这些偏性感条目默认隐藏；普通双人动作不整类隐藏。
ADULT_IDS = {'O013', 'O111', 'O170', 'O171', 'O193', 'O195', 'O304', 'O321', 'O435', 'O436',
             'P059', 'P065', 'P074', 'P082', 'P082-s', 'P156', 'P161'}
FAQ = [
    ('这个角色库收录了什么？', '原作者公开版的发型、刘海、发色、发饰、眼睛、服装和姿势目录。843 个基础条目之外，另有 184 个发型换色版本；281 个姿势另提供原站线稿。侧面姿势是独立条目，不等于基础姿势去重数量。'),
    ('怎样查找参考图？', '可按头发与眼睛、服装、姿势分区浏览，直接点击带数量的分类按钮切换。搜索支持中文、日文、英文标签和条目 ID；点击图片可放大，姿势详情中可切换原站线稿。'),
    ('怎样预览不同发色？', '每张发型卡片下的五个色点只改变当前卡片，放大详情也能换色。顶部「统一发色预览」会重设各卡片的预览色；点击「重置」恢复棕色。换色不修改已保存的收藏，星标保存当前展示版本。'),
    ('怎样复制标签和保存收藏？', '点击卡片或图片详情中的「复制标签」，即可复制当前条目的原始英文标签。星标用于收藏，收藏保存在当前浏览器，可通过「只看收藏」筛选；清除浏览器网站数据会移除收藏。'),
    ('图片和标签可以商用吗？', LICENSE + ' 原作者为 たき AI，无需署名；此处保留出处方便查阅。本站代码的 MIT 许可不覆盖原作者图片，也不代表目录数据获得独立再许可。'),
    ('为什么有些图片不显示？', '泳装和部分偏性感条目默认隐藏，可用顶部 18+ 开关确认年龄后查看。普通双人日常动作正常展示。所有图片通过网络从原站读取；原站不可用时仍能查看本地目录和复制标签，也可使用原站链接检查。'),
    ('英文标签描述什么？', '英文标签来自当前条目的原始目录。服装与姿势图使用相同的示例角色，复制标签时不额外添加示例角色的棕发、齐刘海和棕眼，也不合并其他条目的标签。'),
]
DESCRIPTION = '二次元角色参考图库：公开版 843 个基础条目、184 个发型换色版本，涵盖发型、发色、眼睛、440 套服装和 281 个姿势。中日双语检索、收藏与标签复制；图片由原作者站点提供，禁止再分发。'


def build():
    catalog = json.loads((ROOT / 'data/catalog.json').read_text(encoding='utf-8'))
    assert catalog['tier'] == 'public'
    cats = list(dict.fromkeys(r['cat'] for r in catalog['items']))
    rows, inline, variants = [], [], []
    for raw in catalog['items']:
        key = raw['id']
        adult = raw['cat'] == '水着' or key in ADULT_IDS
        row = dict(raw, zh=chinese(raw), catZh=CATEGORIES[raw['cat']], rating='suggestive' if adult else 'general',
                   thumb_path='thumb/' + key + '.webp', full_path='img/' + key + '.jpg',
                   thumb_url=SOURCE + 'thumb/' + key + '.webp', full_url=SOURCE + 'img/' + key + '.jpg')
        if raw.get('line'):
            row.update(line_path='line/' + key + '.png', line_url=SOURCE + 'line/' + key + '.png')
        rows.append(row)
        if raw.get('parent'):
            variants.append([key, raw['parent']])
        else:
            inline.append([key, raw['jp'], row['zh'], raw['tags'], cats.index(raw['cat']), int(adult)])
    (ROOT / 'manifest.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    payload = {'items': inline, 'cats': [[c, CATEGORIES[c]] for c in cats], 'variants': variants,
               'source': SOURCE, 'built': catalog['built']}
    site_url = os.environ.get('SITE_URL', 'https://example.com/character').rstrip('/')
    site = landing.Site(id='character', root=str(ROOT), site_url=site_url, name='二次元角色库',
                        tagline='发型、服装与姿势的英文标签参考', license_note=LICENSE,
                        author='たき AI', author_url='https://x.com/taki_auto', source=SOURCE, faq=FAQ,
                        share_image=SOURCE + 'thumb/H001.webp', gallery_features='可筛选、放大、收藏和复制标签',
                        index_title='二次元角色参考 · 全部分类与标签',
                        index_intro='按分类浏览二次元角色的发型、刘海、发色、眼睛、服装和姿势参考，保留原日文名称与英文标签。只展示非成人向公开条目；图片由原站提供，可在画廊中放大、收藏和复制单条标签。')
    facets = []
    for cat in cats:
        members = [r for r in rows if r['cat'] == cat and not r.get('parent') and r['rating'] == 'general']
        if not members:
            continue
        label = CATEGORIES[cat]
        desc = '二次元角色%s参考，共 %d 个公开条目。保留日文名称和可复制的英文标签，可在本站角色库中放大、收藏与复制单条标签；图片从原作者站点加载，使用前请阅读原站授权。' % (label, len(members))
        facets.append(landing.Facet(slug='cat/' + cat, title=label + '参考 · 二次元角色库 · photoai.life',
                                   h1='二次元角色' + label + '参考', description=desc, intro=[desc],
                                   items=[landing.Item(r['thumb_url'], r['zh'] + ' · ' + r['jp'] + '参考图', r['tags']) for r in members],
                                   gallery_hash='cat=' + cat, group='角色部件' if members[0]['set'] == 'hair' else ('服装参考' if members[0]['set'] == 'outfit' else '姿势参考'), label=label))
    urls = landing.write_site(site, facets)
    landing.sitemap(site_url, urls, str(ROOT / 'sitemap.xml'))
    (ROOT / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + site_url + '/sitemap.xml\n', encoding='utf-8')
    (ROOT / '404.html').write_text(ui.page_404('../'), encoding='utf-8')
    intro = landing.static_intro(
        [('浏览发型、服装与姿势参考，查看和复制各条目的英文标签。目录与界面由本站独立整理，保留原站的日文名称和标签。',
          '髪型・衣装・ポーズの参考画像を閲覧し、各項目の英語タグをコピー。原作の日本語名とタグを保持した独自の索引です。'),
         LICENSE, '原站公开目录版本标记：' + catalog['built'] + '。图片为原站网络资源，离线时可检索目录和复制标签。'],
        [(('基础条目', '基本項目'), '843'), (('发型换色', '髪型の色違い'), '184'), (('姿势线稿', 'ポーズ線画'), '281')],
        [('cat/髪型/', ('发型', '髪型')), ('cat/カジュアル(春夏)/', ('服装', '衣装')), ('cat/立ち/', ('姿势', 'ポーズ'))], FAQ,
        title=('关于二次元角色库', 'このキャラDBについて'))
    ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': '二次元角色库',
          'url': site_url + '/', 'description': DESCRIPTION, 'inLanguage': ['zh-CN', 'ja'],
          'isBasedOn': SOURCE, 'creator': {'@type': 'Person', 'name': 'たき AI', 'url': 'https://x.com/taki_auto'}}
    replacements = {'__HEAD__': ui.head_script() + ui.head_css(), '__BAR__': ui.bar('character', '../'),
                    '__DIALOGS__': ui.dialogs(ui.HUB_KEYS + [ui.K_SEARCH]), '__SHARED_JS__': ui.body_script(),
                    '__INTRO__': intro, '__SEO_CSS__': landing.SEO_INTRO_CSS, '__SITE__': escape(site_url),
                    '__DESCRIPTION__': escape(DESCRIPTION), '__FAQ__': landing.faq_ld_script(FAQ),
                    '__LD__': json.dumps(ld, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'),
                    '__CSS__': (HERE / 'gallery.css').read_text(encoding='utf-8'),
                    '__JS__': (HERE / 'gallery.js').read_text(encoding='utf-8'),
                    '__DB__': json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')}
    page = (HERE / 'gallery.html').read_text(encoding='utf-8')
    for key, value in replacements.items():
        page = page.replace(key, value)
    (ROOT / 'index.html').write_text(page, encoding='utf-8')
    print('character: %d base + %d variants; %d adult base; %d KB' % (len(inline), len(variants), sum(x[5] for x in inline), len(page.encode('utf-8')) // 1024))


if __name__ == '__main__':
    build()
