# -*- coding: utf-8 -*-
"""四站共用：为筛选分面（标签、分类、发型等）生成静态落地页

主画廊是单页 JS 渲染，搜索引擎和 AI 读到的几乎是空壳。这里为每个分面输出一页
不依赖 JS 的 HTML：标题、介绍、数据事实、缩略图网格（带 alt）、相关分面、FAQ，
以及「在画廊中打开」链接（带 #筛选参数，画廊读取后直接定位）。

用法（各站 build_gallery.py 里）:

    from landing import Site, Facet, write_site

    site = Site(id="costume", root=..., site_url=..., name="服装集", ...)
    facets = [Facet(slug="tag/knit", title=..., h1=..., intro=..., items=[...], ...), ...]
    urls = write_site(site, facets)       # 写出 <root>/<slug>/index.html，返回绝对 URL 列表

页面只用站点已有的缩略图档（thumbs/），不额外暴露中图或原图。
"""
import html, json, os, shutil
from dataclasses import dataclass, field
from typing import List, Optional

MIN_ITEMS = 6       # 少于这么多张图的分面不单独成页：内容太薄
GRID_MAX = 60       # 每页最多展示的缩略图


@dataclass
class Item:
    thumb: str              # 相对站点根的缩略图路径
    alt: str                # 图片说明（中文）
    caption: str = ""       # 卡片下方小字
    w: int = 0
    h: int = 0


@dataclass
class Facet:
    slug: str               # 例如 "tag/knit"；页面写到 <站点>/<slug>/index.html
    title: str              # <title>
    h1: str
    description: str        # meta description，约 80～120 字
    intro: List[str]        # 正文段落
    items: List[Item]
    gallery_hash: str       # 打开主画廊时附带的筛选参数，例如 "tag=knit"
    facts: List[tuple] = field(default_factory=list)   # [(名称, 值)]
    related: List[tuple] = field(default_factory=list) # [(slug, 显示名, 数量)]
    group: str = ""         # 分面所属的组，用于面包屑与索引页分组
    label: str = ""         # 索引页与相关链接里的短名，默认用 h1


@dataclass
class Site:
    id: str
    root: str               # 站点目录（sites/<id>）
    site_url: str           # 例如 https://photoai.life/costume（不带末尾 /）
    name: str               # 站点中文名，例如「服装集」
    tagline: str            # 一句话说明，用于页脚与索引页
    license_note: str       # 授权一句话，会出现在每页
    author: str             # 原作者
    author_url: str
    source: str             # 原站
    faq: List[tuple]        # [(问, 答)]，每页底部 + FAQPage JSON-LD
    accent: str = "#2563eb"
    index_title: str = ""   # 分面索引页 /<站点>/browse/ 的标题
    index_intro: str = ""


def esc(s):
    return html.escape(str(s), quote=True)


def _ld(obj):
    # </script> 不能出现在 JSON-LD 里
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


CSS = """
:root{--bg:#fafaf9;--bg2:#fff;--tx:#1c1917;--tx2:#57534e;--tx3:#a8a29e;--line:#e7e5e4;--ac:%(accent)s}
@media (prefers-color-scheme:dark){:root{--bg:#0c0a09;--bg2:#1c1917;--tx:#f5f5f4;--tx2:#a8a29e;--tx3:#78716c;--line:#292524}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.75 system-ui,-apple-system,"PingFang SC","Hiragino Sans","Microsoft YaHei",sans-serif}
a{color:var(--ac)}
.wrap{max-width:1180px;margin:0 auto;padding:0 clamp(16px,4vw,40px)}
header{border-bottom:1px solid var(--line);background:var(--bg2)}
header .wrap{display:flex;gap:14px;align-items:center;min-height:56px;font-size:13px;flex-wrap:wrap}
header a{color:var(--tx2);text-decoration:none}header a:hover{color:var(--ac)}
.crumb span{color:var(--tx3);margin:0 6px}
h1{font-size:clamp(24px,3.4vw,34px);line-height:1.3;margin:34px 0 10px}
.lead p{margin:0 0 10px;color:var(--tx2);max-width:820px}
.facts{display:flex;flex-wrap:wrap;gap:10px 22px;margin:18px 0 6px;padding:0;list-style:none;font-size:13px;color:var(--tx2)}
.facts b{color:var(--tx);font-weight:600;margin-right:6px}
.cta{display:inline-block;margin:16px 0 26px;padding:10px 18px;border-radius:999px;background:var(--ac);color:#fff;text-decoration:none;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin:0;padding:0;list-style:none}
.grid li{background:var(--bg2);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.grid img{display:block;width:100%%;height:auto;aspect-ratio:var(--ar,3/4);object-fit:cover;background:var(--line)}
.grid figcaption{padding:6px 9px 8px;font-size:12px;color:var(--tx2);line-height:1.5}
h2{font-size:19px;margin:40px 0 12px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0;padding:0;list-style:none}
.chips a{display:inline-block;padding:5px 12px;border:1px solid var(--line);border-radius:999px;background:var(--bg2);color:var(--tx);text-decoration:none;font-size:13px}
.chips a:hover{border-color:var(--ac);color:var(--ac)}
.chips small{color:var(--tx3);margin-left:4px}
.more{color:var(--tx2);font-size:13px;margin-top:12px}
dl.faq dt{font-weight:600;margin-top:16px}dl.faq dd{margin:4px 0 0;color:var(--tx2)}
.groups h3{font-size:15px;margin:22px 0 8px;color:var(--tx2)}
footer{margin-top:56px;border-top:1px solid var(--line);padding:22px 0 40px;font-size:12px;color:var(--tx3);line-height:1.9}
footer a{color:var(--tx3)}
"""


def _page(site, *, slug, title, h1, description, crumbs, body, ld, depth):
    """depth = slug 的层数，用于回到站点根的相对路径"""
    up = "../" * depth
    canonical = f"{site.site_url}/{slug}/"
    nav = ' <span>/</span> '.join(
        f'<a href="{esc(href)}">{esc(label)}</a>' if href else esc(label) for href, label in crumbs)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="photoai.life · {esc(site.name)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(site.site_url)}/og-cover.jpg">
<meta name="twitter:card" content="summary_large_image">
<style>{CSS % {"accent": site.accent}}</style>
<script type="application/ld+json">{_ld(ld)}</script>
</head>
<body>
<header><div class="wrap"><nav class="crumb" aria-label="位置">{nav}</nav></div></header>
<main class="wrap">
<h1>{esc(h1)}</h1>
{body}
</main>
<footer><div class="wrap">
<p>{esc(site.name)} · {esc(site.tagline)}</p>
<p>{esc(site.license_note)} 素材作者：<a href="{esc(site.author_url)}" rel="noopener">{esc(site.author)}</a> · 原站：<a href="{esc(site.source)}" rel="noopener">{esc(site.source)}</a></p>
<p><a href="{up}">返回{esc(site.name)}画廊</a> · <a href="{up}browse/">全部分类与标签</a> · <a href="{up}../">photoai.life 四个参考图库</a></p>
</div></footer>
</body>
</html>
"""


def _faq_html(faq):
    return '<h2>常见问题</h2>\n<dl class="faq">' + "".join(
        f"<dt>{esc(q)}</dt><dd>{esc(a)}</dd>" for q, a in faq) + "</dl>"


def _faq_ld(faq):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}


def facet_page(site, f, all_facets):
    depth = f.slug.count("/") + 1
    up = "../" * depth
    shown = f.items[:GRID_MAX]
    grid = "\n".join(
        f'<li><figure style="margin:0"><img src="{up}{esc(it.thumb)}" alt="{esc(it.alt)}" loading="lazy" decoding="async"'
        + (f' width="{it.w}" height="{it.h}" style="--ar:{it.w}/{it.h}"' if it.w and it.h else "")
        + f'>' + (f'<figcaption>{esc(it.caption)}</figcaption>' if it.caption else "") + '</figure></li>'
        for it in shown)
    gallery_url = f"{up}#{f.gallery_hash}"
    rel = [r for r in f.related if r[0] in {x.slug for x in all_facets}]
    body = ('<div class="lead">' + "".join(f"<p>{esc(p)}</p>" for p in f.intro) + "</div>"
            + ('<ul class="facts">' + "".join(f"<li><b>{esc(k)}</b>{esc(v)}</li>" for k, v in f.facts) + "</ul>" if f.facts else "")
            + f'<a class="cta" href="{esc(gallery_url)}">在画廊中查看全部 {len(f.items)} 张 →</a>'
            + f'<ul class="grid">{grid}</ul>'
            + (f'<p class="more">本页展示前 {len(shown)} 张，其余 {len(f.items) - len(shown)} 张请在<a href="{esc(gallery_url)}">画廊</a>中查看（可筛选、放大、下载）。</p>'
               if len(f.items) > len(shown) else "")
            + ('<h2>相关分类与标签</h2><ul class="chips">' + "".join(
                f'<li><a href="{up}{esc(s)}/">{esc(label)}<small>{n}</small></a></li>' for s, label, n in rel) + "</ul>" if rel else "")
            + _faq_html(site.faq))
    crumbs = [(f"{up}../", "photoai.life"), (up, site.name), (f"{up}browse/", "分类与标签")] + ([(None, f.group)] if f.group else []) + [(None, f.h1)]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "name": f.title, "description": f.description, "url": f"{site.site_url}/{f.slug}/",
         "inLanguage": "zh-CN", "isPartOf": {"@type": "WebSite", "name": f"photoai.life · {site.name}", "url": f"{site.site_url}/"},
         "mainEntity": {"@type": "ImageGallery", "name": f.h1, "numberOfItems": len(f.items),
                        "image": [{"@type": "ImageObject", "contentUrl": f"{site.site_url}/{it.thumb}", "caption": it.alt,
                                   "creator": {"@type": "Person", "name": site.author}} for it in shown[:12]]}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "photoai.life", "item": site.site_url.rsplit("/", 1)[0] + "/"},
            {"@type": "ListItem", "position": 2, "name": site.name, "item": f"{site.site_url}/"},
            {"@type": "ListItem", "position": 3, "name": f.h1, "item": f"{site.site_url}/{f.slug}/"}]},
        _faq_ld(site.faq)]}
    return _page(site, slug=f.slug, title=f.title, h1=f.h1, description=f.description,
                 crumbs=crumbs, body=body, ld=ld, depth=depth)


def index_page(site, facets):
    groups = {}
    for f in facets:
        groups.setdefault(f.group or "其他", []).append(f)
    body = ('<div class="lead"><p>' + esc(site.index_intro) + "</p></div>"
            + f'<a class="cta" href="../">打开{esc(site.name)}画廊 →</a>'
            + '<div class="groups">' + "".join(
                f"<h3>{esc(g)}</h3><ul class=\"chips\">" + "".join(
                    f'<li><a href="../{esc(f.slug)}/">{esc(f.label or f.h1)}<small>{len(f.items)}</small></a></li>' for f in fs) + "</ul>"
                for g, fs in groups.items()) + "</div>"
            + _faq_html(site.faq))
    title = site.index_title or f"{site.name} · 全部分类与标签"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "name": title, "url": f"{site.site_url}/browse/", "inLanguage": "zh-CN",
         "hasPart": [{"@type": "CollectionPage", "name": f.h1, "url": f"{site.site_url}/{f.slug}/"} for f in facets]},
        _faq_ld(site.faq)]}
    return _page(site, slug="browse", title=title, h1=title, description=site.index_intro[:150],
                 crumbs=[("../../", "photoai.life"), ("../", site.name), (None, "分类与标签")], body=body, ld=ld, depth=1)


def write_site(site, facets):
    """写出全部分面页与索引页，返回绝对 URL 列表（不含站点首页）。
    先清掉上次生成的分面目录，避免改名后留下孤儿页。"""
    keep = [f for f in facets if len(f.items) >= MIN_ITEMS]
    slugs = [f.slug for f in keep]
    assert len(slugs) == len(set(slugs)), "分面 slug 重复"
    tops = {s.split("/")[0] for s in slugs} | {"browse"}
    for top in tops:
        shutil.rmtree(os.path.join(site.root, top), ignore_errors=True)
    for f in keep:
        out = os.path.join(site.root, *f.slug.split("/"), "index.html")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(facet_page(site, f, keep))
    out = os.path.join(site.root, "browse", "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(index_page(site, keep))
    # 记录生成了哪些目录，release.py 据此复制
    with open(os.path.join(site.root, "data", "landing.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"dirs": sorted(tops), "pages": ["browse"] + slugs}, fh, ensure_ascii=False, indent=1)
    print(f"landing: {len(keep)} 个分面页 + 1 个索引页（跳过 {len(facets) - len(keep)} 个不足 {MIN_ITEMS} 张的分面）")
    return [f"{site.site_url}/browse/"] + [f"{site.site_url}/{s}/" for s in slugs]


def sitemap(site_url, urls, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{esc(site_url)}/</loc><changefreq>monthly</changefreq><priority>1.0</priority></url>\n')
        for u in urls:
            f.write(f'  <url><loc>{esc(u)}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n')
        f.write("</urlset>\n")


def static_intro(paras, facts, links, faq):
    """主画廊页里的静态介绍块：不依赖 JS，搜索引擎和 AI 直接可读。"""
    return ('<section class="seo-intro" aria-label="关于本图库">'
            + "".join(f"<p>{esc(p)}</p>" for p in paras)
            + ('<ul class="seo-facts">' + "".join(f"<li><b>{esc(k)}</b> {esc(v)}</li>" for k, v in facts) + "</ul>" if facts else "")
            + ('<p class="seo-links">按分类浏览：' + " · ".join(
                f'<a href="{esc(h)}">{esc(t)}</a>' for h, t in links) + ' · <a href="browse/">全部分类与标签</a></p>' if links else "")
            + '<details class="seo-faq"><summary>常见问题</summary><dl>'
            + "".join(f"<dt>{esc(q)}</dt><dd>{esc(a)}</dd>" for q, a in faq) + "</dl></details></section>")


SEO_INTRO_CSS = (".seo-intro{max-width:1600px;margin:8px auto 0;padding:0 clamp(16px,4vw,48px) 28px;"
                 "color:var(--tx3,#888);font-size:12.5px;line-height:1.8}"
                 ".seo-intro p{margin:0 0 6px}.seo-intro a{color:inherit}"
                 ".seo-facts{display:flex;flex-wrap:wrap;gap:4px 18px;margin:6px 0;padding:0;list-style:none}"
                 ".seo-faq summary{cursor:pointer;margin-top:6px}.seo-faq dt{font-weight:600;margin-top:8px}.seo-faq dd{margin:2px 0 0}")


def faq_ld_script(faq):
    return '<script type="application/ld+json">' + _ld({"@context": "https://schema.org", **_faq_ld(faq)}) + "</script>"
