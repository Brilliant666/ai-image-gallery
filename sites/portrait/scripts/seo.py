# -*- coding: utf-8 -*-
"""人像集的静态落地页与主页静态介绍

分面：分区（面部 / 造型）、分区 × 发型（8 页）、面部风格（每种风格一页，图太少的跳过）。
由 build_gallery.py 调用 build(root, site_url, items)，items 是页面内嵌数据的那份列表。
"""
from collections import Counter

import landing
from translations import HAIR_ZH, HAIR_ORDER, SECTION_ZH, style_zh

FAQ = [
    ("这些人像是真人吗？",
     "不是。原作者声明全部为 AI 生成的虚构人物，不对应任何真实的人，图片元数据已清除。"),
    ("可以商用吗？",
     "可以。人像集的图片以 CC0 1.0 公有领域方式提供，可以免费商用、修改、二次创作和再分发，不需要署名。"
     "作者另有两点请求：尽量不要原样再分发图片数据本身，不要冒充真实人物或用于违反公序良俗的用途。"),
    ("怎么用来保持 AI 绘画里角色的脸一致？",
     "从「面部」分区选一张正面、纯色背景的脸，作为图像生成工具里「参考脸 / 角色参考」功能的输入图；"
     "同一张脸配合不同提示词，就能生成同一角色的不同场景。"),
    ("「面部」和「造型」有什么区别？",
     "面部是 893 张正面、纯色背景的脸部特写，用来锁定五官；造型是 606 张完整原图，能看清发型、服装和整体氛围。"),
    ("图片多大，能下载吗？",
     "原图为 1122×1402 至 1597×2000 的 PNG，每张卡片都有下载按钮；浏览和灯箱使用压缩后的缩略图与中图。"),
]


def build(root, site_url, items):
    n = len(items)
    n_face = sum(1 for x in items if x["s"] == "face")
    site = landing.Site(
        id="portrait", root=root, site_url=site_url, name="人像集",
        tagline=f"AI 绘画角色脸部一致性参考图库，{n} 张 AI 生成人像，CC0 免费商用。",
        license_note="图片为 AI 生成的虚构人物，CC0 1.0 公有领域，可免费商用。",
        author="あぎ", author_url="https://x.com/agi_aibusi", source="https://ai-portrait-gallery.pages.dev/",
        faq=FAQ, accent="#b45f3c", license_url="https://creativecommons.org/publicdomain/zero/1.0/",
        index_title="AI 人脸参考图：按分区、发型与发型风格浏览",
        index_intro=(f"人像集收录 {n} 张 AI 生成的人像，分为面部（{n_face} 张正面脸部特写）和造型（{n - n_face} 张完整原图）两个分区，"
                     "按短发、中发、中长发、长发 4 种发型分类，面部分区还细分到具体的发型风格。全部 CC0，可免费商用。"),
    )

    def to_item(x):
        hz = HAIR_ZH.get(x["hj"], x["hj"])
        st = f"・{x['sz']}" if x.get("sz") else ""
        w, h = (400, 500) if x["w"] < x["h"] else (400, 224)
        return landing.Item(thumb=x["t"], w=w, h=h, caption=f"{hz}{st}",
                            alt=f"AI 生成人像 {x['i']}：{SECTION_ZH[x['s']]}，{hz}{st}")

    hairs = [h for h in HAIR_ORDER if any(x["hj"] == h for x in items)]
    facets = []
    for sec in ("face", "styling"):
        xs = [x for x in items if x["s"] == sec]
        szh = SECTION_ZH[sec]
        what = "正面、纯色背景的脸部特写，用来锁定角色五官" if sec == "face" else "能看清发型、服装和整体氛围的完整原图"
        by_h = Counter(x["hj"] for x in xs)
        facets.append(landing.Facet(
            slug=f"section/{sec}", group="分区", label=szh,
            title=f"AI 人像{szh}参考图 {len(xs)} 张 · CC0 · 人像集",
            h1=f"{szh}参考图（{len(xs)} 张）",
            description=f"{len(xs)} 张 AI 生成的{what}，按短发、中发、中长发、长发分类，CC0 公有领域，可免费商用。",
            intro=[f"人像集「{szh}」分区共 {len(xs)} 张，是{what}。",
                   "按发型分布：" + "、".join(f"{HAIR_ZH[h]} {by_h[h]} 张" for h in hairs if by_h[h]) + "。"],
            facts=[("图片", f"{len(xs)} 张"), ("授权", "CC0 1.0"), ("原图", "PNG，1122×1402 起")],
            items=[to_item(x) for x in xs], gallery_hash=f"sec={sec}",
            related=[(f"section/{sec}/{h}", f"{szh} · {HAIR_ZH[h]}", by_h[h]) for h in hairs if by_h[h]]
                    + [(f"section/{o}", SECTION_ZH[o], 0) for o in ("face", "styling") if o != sec]))
        for h in hairs:
            xh = [x for x in xs if x["hj"] == h]
            if not xh:
                continue
            hz = HAIR_ZH[h]
            styles = Counter(x["sj"] for x in xh if x.get("sj")).most_common(10)
            facets.append(landing.Facet(
                slug=f"section/{sec}/{h}", group=szh, label=hz,
                title=f"{hz} AI 人像{szh}参考图 {len(xh)} 张 · 人像集",
                h1=f"{hz} · {szh}参考图（{len(xh)} 张）",
                description=f"{len(xh)} 张{hz}的 AI 生成人像（{szh}），可作为 AI 绘画角色脸部与发型参考，CC0 免费商用。",
                intro=[f"人像集里{hz}的{szh}图共 {len(xh)} 张。"]
                      + (["常见发型风格：" + "、".join(style_zh(st) for st, _ in styles[:8]) + "。"] if styles else []),
                facts=[("图片", f"{len(xh)} 张"), ("发型", hz), ("分区", szh), ("授权", "CC0 1.0")],
                items=[to_item(x) for x in xh], gallery_hash=f"sec={sec}&hair={h}",
                related=[(f"section/{sec}/{o}", f"{szh} · {HAIR_ZH[o]}", by_h[o]) for o in hairs if o != h and by_h[o]]
                        + [(f"style/{st}", style_zh(st), c) for st, c in styles]))

    for st, c in Counter(x["sj"] for x in items if x.get("sj")).most_common():
        xs = [x for x in items if x.get("sj") == st]
        zh = style_zh(st)
        h = xs[0]["hj"]
        facets.append(landing.Facet(
            slug=f"style/{st}", group=f"发型风格 · {HAIR_ZH.get(h, h)}", label=zh,
            title=f"{zh} AI 人像参考图 {c} 张 · 人像集",
            h1=f"{zh}（{c} 张）",
            description=f"{c} 张「{zh}」发型的 AI 生成正面人像，可作为 AI 绘画发型与角色脸部参考，CC0 免费商用。",
            intro=[f"「{zh}」是人像集面部分区里的一种发型风格，日文原名「{st}」，共 {c} 张，属于{HAIR_ZH.get(h, h)}。",
                   "同一风格下是不同的脸，适合比较同一发型在不同角色上的效果。"],
            facts=[("图片", f"{c} 张"), ("发型", HAIR_ZH.get(h, h)), ("日文", st), ("授权", "CC0 1.0")],
            items=[to_item(x) for x in xs], gallery_hash=f"sec=face&hair={h}",
            related=[(f"section/face/{h}", f"面部 · {HAIR_ZH.get(h, h)}", sum(1 for x in items if x['s'] == 'face' and x['hj'] == h))]
                    + [(f"style/{o}", style_zh(o), m) for o, m in Counter(x["sj"] for x in items
                       if x.get("sj") and x["hj"] == h and x["sj"] != st).most_common(10)]))

    urls = landing.write_site(site, facets)
    intro = landing.static_intro(
        [f"人像集是一个 AI 绘画角色脸部一致性参考图库：收录 {n} 张 AI 生成的虚构人物肖像，"
         f"其中面部分区 {n_face} 张为正面、纯色背景的脸部特写，造型分区 {n - n_face} 张为完整原图。",
         "可作为图像生成工具「参考脸 / 角色参考」功能的输入图，让同一角色在不同画面里保持同一张脸。"
         "全部图片以 CC0 1.0 公有领域提供，可免费商用。"],
        [("图片", f"{n} 张"), ("面部", f"{n_face} 张"), ("造型", f"{n - n_face} 张"), ("发型", "4 类"),
         ("授权", "CC0 1.0，可商用"), ("素材", "AI 生成，作者あぎ")],
        [(f"section/face/{h}/", f"面部 · {HAIR_ZH[h]}") for h in hairs] + [("section/styling/", "造型")],
        FAQ)
    return urls, intro, FAQ
