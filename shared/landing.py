# -*- coding: utf-8 -*-
"""各图库共用：为筛选分面（标签、分类、发型等）生成静态落地页

主画廊是单页 JS 渲染，搜索引擎和 AI 读到的几乎是空壳。这里为每个分面输出一页
不依赖 JS 的 HTML：标题、介绍、数据事实、缩略图网格（带 alt）、相关分面、FAQ，
以及「在画廊中打开」链接（带 #筛选参数，画廊读取后直接定位）。

用法（各站 build_gallery.py 里）:

    from landing import Site, Facet, write_site

    site = Site(id="costume", root=..., site_url=..., name="服装集", ...)
    facets = [Facet(slug="tag/knit", title=..., h1=..., intro=..., items=[...], ...), ...]
    urls = write_site(site, facets)       # 写出 <root>/<slug>/index.html，返回绝对 URL 列表

页面只用站点已有的缩略图档（thumbs/），不额外暴露中图或原图。
外观、顶部栏、深浅色与语言偏好来自 shared/ui.py（与画廊同一套）；正文只有中文。
"""
import html, json, os, shutil, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ui  # noqa: E402
from dataclasses import dataclass, field
from typing import List, Optional

MIN_ITEMS = 6       # 少于这么多张图的分面不单独成页：内容太薄
GRID_MAX = 60       # 每页最多展示的缩略图


@dataclass
class Item:
    thumb: str              # 相对站点根的缩略图路径，或原站绝对 HTTPS URL
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
    license_url: str = ""   # 图片授权地址（CC0 站点填 CC0 链接，结构化数据写 license / acquireLicensePage）
    share_image: str = ""   # 可选的绝对 HTTPS 分享图；默认使用站点根的 og-cover.jpg
    gallery_features: str = "可筛选、放大、下载"


def esc(s):
    return html.escape(str(s), quote=True)


def _ld(obj):
    # </script> 不能出现在 JSON-LD 里
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


CSS = """
.lp{max-width:1180px;margin:0 auto;padding:0 var(--gut) 20px}
.crumb{display:flex;flex-wrap:wrap;gap:4px 8px;margin:22px 0 0;font-size:12.5px;color:var(--mu)}
.crumb a{color:var(--tx2);text-decoration:none}.crumb a:hover{color:var(--tx);text-decoration:underline}
.crumb span{color:var(--line2)}
.lp h1{font-size:clamp(24px,3.4vw,34px);line-height:1.3;margin:12px 0 10px;font-weight:800}
.lead p{margin:0 0 10px;color:var(--tx2);max-width:820px;line-height:1.8}
.facts{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 6px;padding:0;list-style:none}
.facts li{padding:4px 12px;border-radius:999px;background:var(--sf);font-size:13px;color:var(--tx2)}
.facts b{color:var(--tx);font-weight:700;margin-right:6px}
.cta{margin:16px 0 24px}
.lgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:16px 12px;margin:0;padding:0;list-style:none}
.lgrid img{display:block;width:100%;height:auto;aspect-ratio:var(--ar,3/4);object-fit:cover;border-radius:14px;background:var(--imgbg)}
.lgrid figcaption{padding:6px 4px 0;font-size:12px;color:var(--mu);line-height:1.5}
.lp h2{font-size:19px;margin:40px 0 12px}
.lchips{display:flex;flex-wrap:wrap;gap:8px;margin:0;padding:0;list-style:none}
.lchips a{display:inline-flex;align-items:center;gap:6px;height:34px;padding:0 14px;border-radius:999px;background:var(--sf);
  color:var(--tx);text-decoration:none;font-size:13px}
.lchips a:hover{background:var(--sf2)}
.lchips small{color:var(--mu)}
.more{color:var(--tx2);font-size:13px;margin-top:12px}
dl.faq dt{font-weight:700;margin-top:16px}dl.faq dd{margin:4px 0 0;color:var(--tx2);line-height:1.8}
.groups h3{font-size:14px;margin:22px 0 8px;color:var(--mu)}
@media(max-width:640px){.lgrid{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""


def _page(site, *, slug, title, h1, description, crumbs, body, ld, depth):
    """depth = slug 的层数，用于回到站点根的相对路径"""
    up = "../" * depth
    canonical = f"{site.site_url}/{slug}/"
    share_image = site.share_image or site.site_url + "/og-cover.jpg"
    share_size = '' if site.share_image else '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">'
    nav = ' <span>/</span> '.join(
        f'<a href="{esc(href)}">{esc(label)}</a>' if href else esc(label) for href, label in crumbs)
    return f"""<!doctype html>
<html lang="zh-CN" data-theme="light" data-lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="photoai.life · {esc(site.name)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(share_image)}">
{share_size}
<meta property="og:locale" content="zh_CN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{esc(share_image)}">
<script type="application/ld+json">{_ld(ld)}</script>
{ui.head_script()}
{ui.head_css()}
<style>{CSS}</style>
</head>
<body>
{ui.bar(site.id, up + "../")}
<main class="lp">
<nav class="crumb" aria-label="位置">{nav}</nav>
<h1>{esc(h1)}</h1>
{body}
</main>
<footer class="foot">
<p>{esc(site.name)} · {esc(site.tagline)}</p>
<p>{esc(site.license_note)} 素材作者：<a href="{esc(site.author_url)}" rel="noopener">{esc(site.author)}</a> · 原站：<a href="{esc(site.source)}" rel="noopener">{esc(site.source)}</a></p>
<p><a href="{up}">返回{esc(site.name)}画廊</a> · <a href="{up}browse/">全部分类与标签</a> · <a href="{up}../">photoai.life 全部 {len(ui.nav_sites())} 个参考图库</a></p>
</footer>
{ui.dialogs(ui.HUB_KEYS)}
{ui.body_script()}
</body>
</html>
"""


def _faq_html(faq):
    return '<h2>常见问题</h2>\n<dl class="faq">' + "".join(
        f"<dt>{esc(q)}</dt><dd>{esc(a)}</dd>" for q, a in faq) + "</dl>"


def _faq_ld(faq):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}


def thumb_src(thumb, prefix):
    """远程缩略图保持原站 HTTPS URL；本地缩略图沿用当前页面 / 站点前缀。"""
    return thumb if thumb.startswith("https://") else prefix + thumb


def _img_ld(site, it):
    """缩略图的 ImageObject：CC0 站点写 license / acquireLicensePage；禁止再分发的站点写版权与出处"""
    o = {"@type": "ImageObject", "contentUrl": thumb_src(it.thumb, site.site_url + "/"), "caption": it.alt,
         "creator": {"@type": "Person", "name": site.author, "url": site.author_url},
         "creditText": f"{site.author} / {site.source}"}
    if site.license_url:
        o.update(license=site.license_url, acquireLicensePage=site.source)
    else:
        o["copyrightNotice"] = f"© {site.author}"
    return o


def facet_page(site, f, all_facets):
    depth = f.slug.count("/") + 1
    up = "../" * depth
    shown = f.items[:GRID_MAX]
    grid = "\n".join(
        f'<li><figure style="margin:0"><img src="{esc(thumb_src(it.thumb, up))}" alt="{esc(it.alt)}" loading="lazy" decoding="async"'
        + (f' width="{it.w}" height="{it.h}" style="--ar:{it.w}/{it.h}"' if it.w and it.h else "")
        + f'>' + (f'<figcaption>{esc(it.caption)}</figcaption>' if it.caption else "") + '</figure></li>'
        for it in shown)
    gallery_url = f"{up}#{f.gallery_hash}"
    rel = [r for r in f.related if r[0] in {x.slug for x in all_facets}]
    body = ('<div class="lead">' + "".join(f"<p>{esc(p)}</p>" for p in f.intro) + "</div>"
            + ('<ul class="facts">' + "".join(f"<li><b>{esc(k)}</b>{esc(v)}</li>" for k, v in f.facts) + "</ul>" if f.facts else "")
            + f'<a class="btn pri cta" href="{esc(gallery_url)}">在画廊中查看全部 {len(f.items)} 张 →</a>'
            + f'<ul class="lgrid">{grid}</ul>'
            + (f'<p class="more">本页展示前 {len(shown)} 张，其余 {len(f.items) - len(shown)} 张请在<a href="{esc(gallery_url)}">画廊</a>中查看（{esc(site.gallery_features)}）。</p>'
               if len(f.items) > len(shown) else "")
            + ('<h2>相关分类与标签</h2><ul class="lchips">' + "".join(
                f'<li><a href="{up}{esc(s)}/">{esc(label)}<small>{n}</small></a></li>' for s, label, n in rel) + "</ul>" if rel else "")
            + _faq_html(site.faq))
    crumbs = [(f"{up}../", "photoai.life"), (up, site.name), (f"{up}browse/", "分类与标签")] + ([(None, f.group)] if f.group else []) + [(None, f.h1)]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "name": f.title, "description": f.description, "url": f"{site.site_url}/{f.slug}/",
         "inLanguage": "zh-CN", "isPartOf": {"@type": "WebSite", "name": f"photoai.life · {site.name}", "url": f"{site.site_url}/"},
         "mainEntity": {"@type": "ImageGallery", "name": f.h1, "numberOfItems": len(f.items),
                        "image": [_img_ld(site, it) for it in shown[:12]]}},
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
            + f'<a class="btn pri cta" href="../">打开{esc(site.name)}画廊 →</a>'
            + '<div class="groups">' + "".join(
                f"<h3>{esc(g)}</h3><ul class=\"lchips\">" + "".join(
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


def quote_url(u):
    """站点地图里的网址做百分号编码（中日文路径）"""
    parts = urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit(parts._replace(path=urllib.parse.quote(parts.path, safe="/%")))


def sitemap(site_url, urls, path, lastmod=None):
    """lastmod 取 sites.json 里该站的 updated（固定日期，构建结果可复现）"""
    lastmod = lastmod or updated(site_url.rstrip("/").rsplit("/", 1)[-1])
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in [f"{site_url}/"] + list(urls):
            f.write(f'  <url><loc>{esc(quote_url(u))}</loc>' + (f'<lastmod>{lastmod}</lastmod>' if lastmod else '') + '</url>\n')
        f.write("</urlset>\n")


def updated(site_id):
    s = next((x for x in ui.sites() if x["id"] == site_id), None)
    return s.get("updated") if s else None


def static_intro(paras, facts, links, faq, more_href="browse/", more_label="全部分类与标签",
                 title="关于本站", nav_note=None):
    """静态介绍、快速浏览与授权提示；详细介绍和 FAQ 保留在原生折叠中。"""
    def text(value):
        return ui.bi(*value) if isinstance(value, tuple) else esc(value)

    lead, rest = (paras[0], paras[1:]) if paras else ("", [])
    return ('<section class="seo-intro" aria-label="关于本站"><div class="seo-card">'
            + '<div class="seo-overview"><div class="seo-copy">'
            + f'<h2 class="seo-title">{text(title)}</h2>'
            + (f'<p class="seo-lead">{text(lead)}</p>' if lead else "")
            + ('<ul class="seo-facts">' + "".join(
                f"<li><span>{text(k)}</span><b>{text(v)}</b></li>" for k, v in facts) + "</ul>" if facts else "")
            + '</div>'
            + ('<nav class="seo-nav" aria-label="快速浏览"><h3>' + ui.bi("快速浏览", "カテゴリーから探す") + '</h3>'
               + '<div class="seo-links">' + "".join(f'<a href="{esc(h)}">{text(t)}</a>' for h, t in links)
               + (f'<a class="seo-all" href="{esc(more_href)}">{esc(more_label)}</a>' if more_href else "") + '</div>'
               + (f'<p class="seo-nav-note">{text(nav_note)}</p>' if nav_note else "") + '</nav>' if links else "")
            + '</div><p class="seo-license"><strong>' + ui.bi("使用与授权", "利用とライセンス") + '</strong>'
            + ui.bi("各图库授权不同，请在使用前查看对应说明。", "利用条件はギャラリーごとに異なります。利用前に各説明をご確認ください。") + '</p>'
            + '<details class="seo-more"><summary>' + ui.bi("详细介绍与常见问题", "詳しい紹介とよくある質問") + '</summary>'
            + "".join(f"<p>{text(p)}</p>" for p in rest)
            + "<dl>" + "".join(f"<dt>{text(q)}</dt><dd>{text(a)}</dd>" for q, a in faq) + "</dl></details>"
            + "</div></section>")


# 兼容各图库主题变量，静态内容不依赖 JavaScript。
SEO_INTRO_CSS = (
    ".seo-intro{--si-tx:var(--tx,var(--fg,#16191f));--si-tx2:var(--tx2,var(--muted,#525b6a));"
    "--si-line:var(--line,#e3e7ed);--si-bg:var(--bg2,var(--paper,#fff));--si-ac:var(--ac,#2563eb);"
    "max-width:var(--si-max,1180px);margin:0 auto;padding:0 clamp(16px,4vw,48px) 48px}"
    ".seo-card{border:1px solid var(--si-line);border-radius:16px;background:var(--si-bg);"
    "padding:28px clamp(20px,3vw,32px) 20px;font-size:13.5px;line-height:1.75;color:var(--si-tx2)}"
    ".seo-overview{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(240px,1fr);gap:24px 40px;align-items:start}"
    ".seo-title{margin:0 0 10px;font-size:19px;line-height:1.4;font-weight:700;color:var(--si-tx)}"
    ".seo-lead{margin:0;max-width:64ch;font-size:14px}"
    ".seo-facts{display:flex;flex-wrap:wrap;gap:6px 20px;margin:16px 0 0;padding:0;list-style:none;font-size:12.5px}"
    ".seo-facts li{display:flex;gap:6px}.seo-facts b{font-weight:600;color:var(--si-tx)}"
    ".seo-nav h3{margin:0 0 6px;font-size:13px;font-weight:600;color:var(--si-tx)}"
    ".seo-links{display:flex;flex-wrap:wrap;gap:2px 16px}"
    ".seo-links a{display:inline-flex;align-items:center;min-height:40px;color:var(--si-tx);text-decoration:none;"
    "text-underline-offset:5px}.seo-links a:hover{text-decoration:underline;color:var(--si-ac)}"
    ".seo-links .seo-all{color:var(--si-ac)}.seo-nav-note{margin:4px 0 0;font-size:12px}"
    ".seo-license{margin:22px 0 0;padding-top:16px;border-top:1px solid var(--si-line);font-size:12.5px}"
    ".seo-license strong{margin-right:12px;color:var(--si-tx);font-weight:600}"
    ".seo-more{margin-top:12px}.seo-more summary{display:flex;align-items:center;justify-content:space-between;"
    "min-height:40px;cursor:pointer;color:var(--si-tx);font-size:13px;list-style:none}"
    ".seo-more summary::-webkit-details-marker{display:none}"
    ".seo-more summary::after{content:'＋';margin-left:auto;padding-left:16px}.seo-more[open] summary::after{content:'－'}"
    ".seo-more p{margin:12px 0 0;max-width:78ch}.seo-more dl{margin:8px 0 0;max-width:78ch}"
    ".seo-more dt{margin-top:16px;color:var(--si-tx);font-weight:600}.seo-more dd{margin:4px 0 0}"
    "@media(max-width:760px){.seo-overview{grid-template-columns:1fr;gap:20px}.seo-card{padding:22px 18px 16px}"
    ".seo-title{font-size:18px}.seo-license strong{display:block;margin:0 0 4px}.seo-links{gap:2px 20px}}")


def faq_ld_script(faq):
    return '<script type="application/ld+json">' + _ld({"@context": "https://schema.org", **_faq_ld(faq)}) + "</script>"
