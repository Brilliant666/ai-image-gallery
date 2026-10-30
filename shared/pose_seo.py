# -*- coding: utf-8 -*-
"""姿势 / 深度姿势共用：静态落地页（系列、分类、系列×分类）与主页静态介绍

两站数据结构相同，文案差异取自各站 config.py 的 SEO_PAGES。
由 shared/pose_gallery.build() 调用 build(root, site_url, cfg, data, series_list, cats)。
"""
from collections import Counter

import landing
from pose_i18n import SERIES_ZH, CAT_ZH, ANG_ZH


def _zh_s(s): return SERIES_ZH.get(s, s)
def _zh_c(c): return CAT_ZH.get(c, c)


def build(root, site_url, cfg, data, series_list, cats):
    sp = cfg["seoPages"]                       # 各站文案
    kind = sp["kind"]                          # 例如「姿势参考图」「姿势深度图」
    n_poses = len(data)
    n_imgs = sum(len(p["v"]) for p in data)
    FAQ = sp["faq"]
    site = landing.Site(
        id=sp["id"], root=root, site_url=site_url, name=sp["name"],
        tagline=f"{sp['tagline']}，{n_poses} 个姿势、{n_imgs} 张图，每个姿势 5 个视角。",
        license_note=sp["licenseNote"], author="ギア", author_url="https://x.com/giaaibusi", source=cfg["source"],
        faq=FAQ, accent=sp.get("accent", "#4f7ee8"),
        index_title=f"{sp['name']}：全部系列与分类",
        index_intro=(f"{sp['name']}收录 {n_poses} 个姿势、{n_imgs} 张{kind}，分 {len(series_list)} 个系列、"
                     f"{len(cats)} 个动作分类。每个姿势都有正面、侧面、斜角、俯视、仰视 5 个视角。"
                     "下面按系列和分类列出全部落地页。"),
    )

    def items_of(ps):
        out = []
        for p in ps:
            v = next((x for x in p["v"] if x["a"] == "正面"), p["v"][0])
            out.append(landing.Item(
                thumb=v["t"], w=300, h=400, caption=f"{p['p']} {p['z']}",
                alt=f"{kind} {p['p']}：{p['z']}（{_zh_s(p['s'])} · {_zh_c(p['c'])} · {ANG_ZH.get(v['a'], v['a'])}）"))
        return out

    def page(slug, group, name, ps, gallery_hash, related, extra_intro=""):
        angs = Counter(v["a"] for p in ps for v in p["v"])
        n_i = sum(angs.values())
        sample = "、".join(p["z"] for p in ps[:6])
        return landing.Facet(
            slug=slug, group=group, label=name.split(" · ")[-1],
            title=f"{name}{kind} {len(ps)} 个姿势 · AI 绘画{sp['short']} · {sp['name']}",
            h1=f"{name}{kind}（{len(ps)} 个姿势）",
            description=(f"{len(ps)} 个「{name}」{kind}，共 {n_i} 张，每个姿势含正面、侧面、斜角、俯视、仰视视角。"
                         f"例如：{sample}。{sp['descTail']}"),
            intro=[f"{sp['name']}中「{name}」共有 {len(ps)} 个姿势、{n_i} 张{kind}。{extra_intro}",
                   f"部分姿势：{sample}。点击下方按钮进入画廊，可切换视角、放大和下载 PNG。"],
            facts=[("姿势", f"{len(ps)} 个"), ("图片", f"{n_i} 张"), ("视角", "正面 / 侧面 / 斜角 / 俯视 / 仰视")],
            items=items_of(ps), gallery_hash=gallery_hash, related=related)

    facets = []
    # 成人向系列（双人交缠、性感系、上半身里露骨的分类）只给系列页，不按分类单独生成落地页：
    # 分类名含性行为术语，作为页面标题被收录会让整个域名被判为成人站，连带 CC0 的人像集。
    # 哪些系列按分类展开，由各站 config.py 的 SEO_PAGES["expandSeries"] 决定。
    expand = set(sp.get("expandSeries", []))
    skip = set(sp.get("skipSeries", []))         # 不生成任何落地页的系列（只在画廊里浏览）
    listed = [s for s in series_list if s not in skip]
    for s in listed:
        ps = [p for p in data if p["s"] == s]
        cs = Counter(p["c"] for p in ps).most_common()
        sub = s in expand
        facets.append(page(
            f"series/{s}", "系列", _zh_s(s), ps, f"series={s}",
            ([(f"series/{s}/{c}", _zh_c(c), n) for c, n in cs] if sub else [])
            + [(f"series/{o}", _zh_s(o), sum(1 for p in data if p["s"] == o)) for o in listed if o != s],
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
         ("分类", f"{len(cats)} 个"), ("语言", "中文 / 日本語"), ("素材", "AI 生成，作者ギア")],
        [(f"series/{s}/", _zh_s(s)) for s in listed],
        FAQ)
    return urls, intro, FAQ
