# -*- coding: utf-8 -*-
"""姿势 / 深度姿势共用：静态落地页（系列、分类、系列×分类）与主页静态介绍

两站数据结构相同，文案差异取自各站 config.py 的 SEO_PAGES。
由 shared/pose_gallery.build() 调用 build(root, site_url, cfg, data, series_list, cats, adult)。
Shisei 也用这一套：中文名表取 cfg 的 seriesZh / catZh / angZh。
哪些姿势算成人向、不进落地页，由 sites.json 的 adult 规则决定（shared/adult.py）。
"""
from collections import Counter

import landing
from pose_i18n import SERIES_ZH, CAT_ZH, ANG_ZH


def build(root, site_url, cfg, data, series_list, cats, adult=frozenset(), thumb_of=None):
    """adult = 成人向姿势的 (系列, 分類, 编号) 集合；thumb_of(p, v) = 缩略图路径（页面数据不逐张写路径时由生成器提供）"""
    thumb_of = thumb_of or (lambda p, v: v["t"])
    sp = cfg["seoPages"]                       # 各站文案
    kind = sp["kind"]                          # 例如「姿势参考图」「姿势深度图」
    S_ZH, C_ZH, A_ZH = cfg.get("seriesZh", SERIES_ZH), cfg.get("catZh", CAT_ZH), cfg.get("angZh", ANG_ZH)
    _zh_s = lambda x: S_ZH.get(x, x)
    _zh_c = lambda x: C_ZH.get(x, x)
    author, author_url = sp.get("author", "ギア"), sp.get("authorUrl", "https://x.com/giaaibusi")
    # 成人向姿势（sites.json 的 adult 规则，见 shared/adult.py）不进任何落地页，连缩略图也不放
    indexable = [p for p in data if (p["s"], p["c"], p["p"]) not in adult]
    n_poses = len(data)
    n_imgs = sum(len(p["v"]) for p in data)
    FAQ = sp["faq"]
    site = landing.Site(
        id=sp["id"], root=root, site_url=site_url, name=sp["name"],
        tagline=f"{sp['tagline']}，{n_poses} 个姿势、{n_imgs} 张图，每个姿势{sp.get('angNote', '')} 5 个视角。",
        license_note=sp["licenseNote"], author=author, author_url=author_url, source=cfg["source"],
        faq=FAQ, accent=sp.get("accent", "#4f7ee8"), license_url=sp.get("licenseUrl", ""),
        index_title=f"{sp['name']}：全部系列与分类",
        index_intro=(f"{sp['name']}收录 {n_poses} 个姿势、{n_imgs} 张{kind}，分 {len(series_list)} 个系列、"
                     f"{len(cats)} 个动作分类。每个姿势{sp.get('angNote', '都有')}正面、侧面、斜角、俯视、仰视 5 个视角。"
                     "下面按系列和分类列出落地页；成人向的系列与分类不在这里列出，只在画廊中浏览。"),
    )

    def items_of(ps):
        out = []
        for p in ps:
            v = next((x for x in p["v"] if x["a"] == "正面"), p["v"][0])
            out.append(landing.Item(
                thumb=thumb_of(p, v), w=300, h=400, caption=f"{p['p']} {p['z']}",
                alt=f"{kind} {p['p']}：{p['z']}（{_zh_s(p['s'])} · {_zh_c(p['c'])} · {A_ZH.get(v['a'], v['a'])}）"))
        return out

    def page(slug, group, name, ps, gallery_hash, related, extra_intro=""):
        angs = Counter(v["a"] for p in ps for v in p["v"])
        n_i = sum(angs.values())
        sample = "、".join(p["z"] for p in ps[:6])
        short = "、".join(p["z"] for p in ps[:3])          # 描述里只举 3 个，控制在 160 字以内
        return landing.Facet(
            slug=slug, group=group, label=name.split(" · ")[-1],
            title=f"{name}{kind} {len(ps)} 个姿势 · {sp['name']}",
            h1=f"{name}{kind}（{len(ps)} 个姿势）",
            description=(f"{len(ps)} 个「{name}」{kind}，共 {n_i} 张，每个姿势{sp.get('angNote', '')}含正面、侧面、斜角、俯视、仰视视角。"
                         f"例如：{short}。{sp['descTail']}"),
            intro=[f"{sp['name']}中「{name}」共有 {len(ps)} 个姿势、{n_i} 张{kind}。{extra_intro}",
                   f"部分姿势：{sample}。点击下方按钮进入画廊，可切换视角、放大和下载 {sp.get('dlFormat', 'PNG')}。"],
            facts=[("姿势", f"{len(ps)} 个"), ("图片", f"{n_i} 张"), ("视角", "正面 / 侧面 / 斜角 / 俯视 / 仰视")],
            items=items_of(ps), gallery_hash=gallery_hash, related=related)

    facets = []
    # 成人向内容不进可收录页面：混有成人内容的整个域名可能被判为成人站，SafeSearch 下连带 CC0 的人像集。
    # adult 里的系列与分类已在上面从 indexable 去掉（只剩其余姿势的系列页不会出现成人向缩略图）；
    # 剩下的系列里只有 SEO_PAGES["expandSeries"] 按分类展开，skipSeries 整个系列不生成落地页。
    expand = set(sp.get("expandSeries", []))
    skip = set(sp.get("skipSeries", []))         # 不生成任何落地页的系列（只在画廊里浏览）
    listed = [s for s in series_list if s not in skip and any(p["s"] == s for p in indexable)]
    for s in listed:
        ps = [p for p in indexable if p["s"] == s]
        cs = Counter(p["c"] for p in ps).most_common()
        sub = s in expand
        facets.append(page(
            f"series/{s}", "系列", _zh_s(s), ps, f"series={s}",
            ([(f"series/{s}/{c}", _zh_c(c), n) for c, n in cs] if sub else [])
            + [(f"series/{o}", _zh_s(o), sum(1 for p in indexable if p["s"] == o)) for o in listed if o != s],
            ("包含分类：" + "、".join(f"{_zh_c(c)} {n} 个" for c, n in cs) + "。") if sub else ""))
        if not sub:
            continue
        for c, n in cs:
            psc = [p for p in ps if p["c"] == c]
            facets.append(page(
                f"series/{s}/{c}", _zh_s(s), f"{_zh_s(s)} · {_zh_c(c)}", psc, f"series={s}&cat={c}",
                [(f"series/{s}/{c2}", _zh_c(c2), n2) for c2, n2 in cs if c2 != c] + [(f"series/{s}", _zh_s(s), len(ps))]))

    urls = landing.write_site(site, facets)
    intro = landing.static_intro(
        sp["introParas"](n_poses, n_imgs),
        [("姿势", f"{n_poses} 个"), ("图片", f"{n_imgs} 张"), ("视角", "5 个"), ("系列", f"{len(series_list)} 个"),
         ("分类", f"{len(cats)} 个"), ("语言", "中文 / 日本語"), ("素材", sp.get("factSource", "AI 生成，作者ギア"))],
        [(f"series/{s}/", _zh_s(s)) for s in listed],
        FAQ)
    return urls, intro, FAQ
