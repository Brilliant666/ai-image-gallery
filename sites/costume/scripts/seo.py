# -*- coding: utf-8 -*-
"""服装集的静态落地页与主页静态介绍：8 个分类 + 86 个标签

由 build_gallery.py 调用 build(root, site_url, items, cats)，返回
(落地页 URL 列表, 主页静态介绍 HTML, FAQ 列表)。
"""
from collections import Counter

import landing
from translations import CAT_ZH, TAG_ZH, TAG_JA, TAG_GROUPS

GROUP_OF = {t: zh for _k, _ja, zh, ts in TAG_GROUPS for t in ts}


def faq(n_items):
    return [
        ("这些服装图是真人照片吗？",
         "不是。原站声明全部服装图由文字生成图像（t2i）制作，不含真实商品照片，也不是真实人物。"),
        ("可以用在自己的作品或商用项目里吗？",
         "原作者ギア允许免费用于作品制作，包括商用、编辑和作为参考；但禁止把图片文件本身再分发、转载或转售。"
         "本站是中文索引镜像，图片著作权归原作者，以原站条款为准。"),
        ("怎么用来写 AI 绘画提示词？",
         "每个标签都保留原站的英文关键词（如 knit、pleated、ribbon），可以直接作为 Stable Diffusion、"
         "Midjourney 等工具的提示词；在画廊里多选标签可以找到组合，例如 black + knit + mini。"),
        ("图片能下载吗？",
         f"画廊里 {n_items} 套服装都可以打开大图、下载 PNG 原图。每套三档：缩略图 360×540、中图和原图约 1366×2048。"),
        ("和原站有什么不同？",
         "原站分类为日文、关键词为英文，没有组合筛选。本站把 8 个分类和 86 个标签译成中文，"
         "按颜色、单品、鞋袜、配饰、材质图案、长度 6 组做了分面筛选，并支持中日双语切换。"),
    ]


def build(root, site_url, items, cats):
    n_files = len(items) * 3
    FAQ = faq(len(items))
    site = landing.Site(
        id="costume", root=root, site_url=site_url, name="服装集",
        tagline=f"AI 绘画服装参考图库，{len(items)} 套服装、{n_files} 张图、86 个标签。",
        license_note="图片为 AI 生成，著作权归原作者，禁止再分发图片文件本身。",
        author="ギア", author_url="https://x.com/giaaibusi", source="https://ai-costume-gallery.pages.dev/",
        faq=FAQ, accent="#4f7ee8",
        index_title="AI 绘画服装参考：全部 8 个分类与 86 个标签",
        index_intro=(f"服装集收录 {len(items)} 套 AI 生成的服装参考图，按季节和用途分 8 个分类，"
                     "每套服装平均带 8.5 个英文关键词标签。下面按颜色、单品、鞋袜、配饰、材质图案、长度列出全部标签，"
                     "点进去可以看到该标签下的服装缩略图。"),
    )

    def to_item(x):
        zh_tags = "、".join(TAG_ZH.get(t, t) for t in x["t"][:6])
        return landing.Item(thumb=x["th"], alt=f"AI 生成服装参考图 {x['i']}：{CAT_ZH.get(x['c'], x['c'])}，{zh_tags}",
                            caption=x["i"], w=360, h=540)

    facets = []
    for c in cats:
        xs = [x for x in items if x["c"] == c]
        top = Counter(t for x in xs for t in x["t"]).most_common(12)
        czh = CAT_ZH.get(c, c)
        facets.append(landing.Facet(
            slug=f"category/{c}", group="分类", label=czh,
            title=f"{czh}服装参考图 {len(xs)} 套 · AI 绘画服装参考 · 服装集",
            h1=f"{czh}服装参考图（{len(xs)} 套）",
            description=(f"{len(xs)} 套「{czh}」主题的 AI 生成服装参考图，常见标签："
                         + "、".join(TAG_ZH.get(t, t) for t, _ in top[:6]) + "。可按标签组合筛选，带英文提示词关键词。"),
            intro=[f"服装集「{czh}」分类共 {len(xs)} 套服装，原站编号前缀为 {xs[0]['i'].split('-')[0]}。",
                   "这一类最常见的标签是：" + "、".join(f"{TAG_ZH.get(t, t)}（{t}，{n} 套）" for t, n in top[:8]) + "。"],
            facts=[("服装数", f"{len(xs)} 套"), ("每套图片", "缩略图 / 中图 / 原图三档"),
                   ("标签", f"{len(set(t for x in xs for t in x['t']))} 个")],
            items=[to_item(x) for x in xs], gallery_hash=f"cat={c}",
            related=[(f"tag/{t}", f"{TAG_ZH.get(t, t)} {t}", n) for t, n in top]))

    for t, n in Counter(t for x in items for t in x["t"]).most_common():
        xs = [x for x in items if t in x["t"]]
        co = Counter(u for x in xs for u in x["t"] if u != t).most_common(12)
        by_cat = Counter(x["c"] for x in xs).most_common()
        tzh, tja, grp = TAG_ZH.get(t, t), TAG_JA.get(t, t), GROUP_OF.get(t, "其他")
        facets.append(landing.Facet(
            slug=f"tag/{t}", group=grp, label=f"{tzh} {t}",
            title=f"{tzh}（{t}）服装参考图 {n} 套 · AI 绘画提示词 · 服装集",
            h1=f"{tzh}（{t}）服装参考图",
            description=(f"{n} 套带「{tzh} / {t}」标签的 AI 生成服装参考图，分布在"
                         + "、".join(CAT_ZH.get(k, k) for k, _ in by_cat[:4])
                         + f"等分类。英文关键词 {t} 可直接用作 Stable Diffusion 提示词。"),
            intro=[f"「{tzh}」对应原站英文关键词 {t}，日文为「{tja}」，属于{grp}标签，共 {n} 套服装带有这个标签。",
                   "按分类分布：" + "、".join(f"{CAT_ZH.get(k, k)} {v} 套" for k, v in by_cat) + "。",
                   "经常一起出现的标签：" + "、".join(f"{TAG_ZH.get(u, u)}（{u}）" for u, _ in co[:8]) + "，可以在画廊里多选组合。"],
            facts=[("服装数", f"{n} 套"), ("英文关键词", t), ("日文", tja), ("标签组", grp)],
            items=[to_item(x) for x in xs], gallery_hash=f"tag={t}",
            related=[(f"tag/{u}", f"{TAG_ZH.get(u, u)} {u}", m) for u, m in co]
                    + [(f"category/{k}", CAT_ZH.get(k, k), v) for k, v in by_cat[:4]]))

    urls = landing.write_site(site, facets)
    intro = landing.static_intro(
        [f"服装集是一个 AI 绘画服装参考图库：收录 {len(items)} 套 AI 生成的服装图（每套三档，共 {n_files} 张），"
         "不含真人，适合作为 Stable Diffusion、Midjourney 等工具出图时的服装、穿搭与材质参考。",
         "8 个分类（春、夏、秋、冬、内衣、性感、泳装、派对）与 86 个标签全部译为中文，"
         "标签保留原站英文关键词，可直接复制做提示词。"],
        [("服装", f"{len(items)} 套"), ("图片", f"{n_files} 张"), ("分类", "8 个"), ("标签", "86 个，分 6 组"),
         ("语言", "中文 / 日本語"), ("素材", "AI 生成，作者ギア")],
        [(f"category/{c}/", CAT_ZH.get(c, c)) for c in cats],
        FAQ)
    return urls, intro, FAQ
