# -*- coding: utf-8 -*-
"""Public-only category/tag pages using the common landing renderer."""
from collections import Counter
from catalog import SOURCE, AUTHOR_URL, CAT_ZH, TAG_ZH, TAG_JA, TAG_GROUPS, ADULT
import landing

FAQ = [
    ('二次元服装库与原服装集有什么区别？',
     '这是ギア的独立动漫风服装来源，共 1320 套；原服装集是另一份 1407 套的图库。编号可能相同，但属于不同来源，不能按编号跨库合并。'),
    ('图片是否保存在本站？离线能打开吗？',
     '本站只提供原生资源索引与中日双语翻译，图片由原站直接加载。页面内嵌筛选数据，file:// 可用，查看图片仍需联网。没有下载或镜像图片文件。'),
    ('可以怎样使用图片？',
     '原站允许免费用于作品制作（含商用、编辑、参考），禁止批量下载（含自动获取）以及图片数据本身（含加工后）的再分发、转载、转售。单张作为生成参考请按原站最新条件使用。'),
    ('如何复制英文提示词标签？',
     '打开任一服装大图，点「复制英文标签」可复制该条目的全部英文关键词；点击标签可加入组合筛选。标签按颜色、单品、鞋袜、配饰、材质图案与长度分组。'),
    ('为什么没有内衣和性感分类的落地页？',
     '336 套内衣和性感分类默认隐藏，确认年满 18 岁后可在画廊查看。可收录的分类页、标签页与缩略图仅使用其余 984 套公开服装。'),
]


def build(root, site_url, items, cats):
    pub = [x for x in items if x['c'] not in ADULT]
    pub_cats = [c for c in cats if any(x['c'] == c for x in pub)]
    group = {t: zh for _, _, zh, tags in TAG_GROUPS for t in tags}
    site = landing.Site(
        id='costume-anime', root=str(root), site_url=site_url, name='二次元服装库',
        tagline='1320 套动漫风服装的独立参考索引，图片由原站加载，需要联网。',
        license_note='禁止批量下载（含自动获取）、再分发、转载或销售图片；原始元数据与图片按原站条款使用。',
        author='ギア', author_url=AUTHOR_URL, source=SOURCE, faq=FAQ,
        gallery_features='组合筛选、放大、复制英文标签',
        index_title='动漫服装参考：全部公开分类与标签',
        index_intro='1320 套动漫风服装按 8 个分类、86 个标签建立中日双语索引。这里仅展示 984 套公开服装，内衣和性感分类不进入落地页。图片由原站远程加载。')

    def image(x):
        return landing.Item(thumb=SOURCE + 'thumbs/' + x['i'] + '.webp',
                            alt=f"动漫服装参考 {x['i']}：{CAT_ZH[x['c']]}，" + '、'.join(TAG_ZH[t] for t in x['t'][:5]),
                            caption=x['i'], w=360, h=540)

    facets = []
    for c in pub_cats:
        xs = [x for x in pub if x['c'] == c]
        top = Counter(t for x in xs for t in x['t']).most_common(12)
        zh = CAT_ZH[c]
        facets.append(landing.Facet(
            slug=f'category/{c}', group='分类', label=zh,
            title=f'{zh}动漫服装参考 {len(xs)} 套 · 二次元服装库', h1=f'{zh}动漫服装参考图（{len(xs)} 套）',
            description=f'{len(xs)} 套{zh}主题的动漫风服装参考图，常见标签：' + '、'.join(TAG_ZH[t] for t, _ in top[:6]) + '。中日双语画廊可多选标签组合筛选并复制英文关键词，图片由原站加载。',
            intro=[f'独立动漫服装来源的「{zh}」分类共 {len(xs)} 套。这些编号仅在本库内标识条目。',
                   '常见英文标签：' + '、'.join(f'{TAG_ZH[t]}（{t}）' for t, _ in top[:8]) + '。'],
            items=[image(x) for x in xs], gallery_hash=f'cat={c}', facts=[('服装', f'{len(xs)} 套'), ('图片', '原站远程加载')],
            related=[(f'tag/{t}', f'{TAG_ZH[t]} {t}', n) for t, n in top]))
    for t, n in Counter(t for x in pub for t in x['t']).most_common():
        xs = [x for x in pub if t in x['t']]
        co = Counter(u for x in xs for u in x['t'] if u != t).most_common(12)
        by_cat = Counter(x['c'] for x in xs).most_common()
        facets.append(landing.Facet(
            slug=f'tag/{t}', group=group[t], label=f'{TAG_ZH[t]} {t}',
            title=f'{TAG_ZH[t]}（{t}）动漫服装参考 · 二次元服装库', h1=f'{TAG_ZH[t]}（{t}）动漫服装参考',
            description=f'{n} 套带{TAG_ZH[t]}（{t}）标签的动漫风服装，分布在' + '、'.join(CAT_ZH[c] for c, _ in by_cat[:4]) + '等分类。可在画廊多选标签组合筛选、放大并复制英文关键词，图片从原站远程加载。',
            intro=[f'英文关键词 {t} 对应中文「{TAG_ZH[t]}」、日文「{TAG_JA[t]}」，属于{group[t]}标签。公开服装中有 {n} 套使用该标签。',
                   '常一起出现的标签：' + '、'.join(f'{TAG_ZH[u]}（{u}）' for u, _ in co[:8]) + '。'],
            items=[image(x) for x in xs], gallery_hash=f'tag={t}',
            facts=[('公开服装', f'{n} 套'), ('英文标签', t), ('日文', TAG_JA[t])],
            related=[(f'tag/{u}', f'{TAG_ZH[u]} {u}', count) for u, count in co]
                    + [(f'category/{c}', CAT_ZH[c], count) for c, count in by_cat]))
    urls = landing.write_site(site, facets)
    intro = landing.static_intro(
        [('二次元服装库索引独立原站的 1320 套动漫风服装，8 个分类、86 个标签。图片远程加载，可按中日标签组合筛选、放大并复制英文关键词。',
          'アニメ衣装集は独立した元サイトの 1320 着を、8 カテゴリ・86 タグで整理した参照インデックスです。画像は元サイトから読み込み、中文・日本語で検索できます。'),
         ('本库与 1407 套的原服装集是独立来源，编号可能重合，不能跨库合并。仅本站原创代码与翻译适用本项目许可，原始元数据与图片保留原站使用条件。',
          '1407 着の既存衣装集とは独立したデータです。同じ番号でも別の衣装を指します。元データと画像の利用条件は元サイトに従います。')],
        [(('服装', '衣装'), ('1320 套 / 984 套公开', '1320 着 / 通常表示 984 着')), (('标签', 'タグ'), '86'), (('图片', '画像'), ('远程 / 需要联网', '元サイト / 接続が必要'))],
        [(f'category/{c}/', (CAT_ZH[c], c)) for c in pub_cats], FAQ,
        title=('关于二次元服装库', 'アニメ衣装集について'))
    return urls, intro
