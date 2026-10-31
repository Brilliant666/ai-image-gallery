# -*- coding: utf-8 -*-
"""生成资源站入口页

用法:
  python build_hub.py                # 读取 sites.json → index.html
  python build_hub.py --check        # 仅检查封面图是否存在

新增站点：在 sites.json 的 sites 数组里追加一条，重跑本脚本即可。
"""
import json, os, sys
from html import escape

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shared"))
import landing, recipe, ui  # noqa: E402

HUB  = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HUB)
CFG  = os.path.join(ROOT, "sites.json")
OUT  = os.path.join(HUB, "index.html")

LICENSE = {
    "cc0": {"zh": "CC0 可商用", "ja": "CC0 商用可", "cls": "ok"},
    "conditional": {"zh": "有条件", "ja": "条件付き", "cls": "warn"},
    "restricted": {"zh": "禁止再分发", "ja": "再配布禁止", "cls": "no"},
}


def load():
    with open(CFG, encoding="utf-8") as f:
        return json.load(f)


def check(cfg):
    """封面图存在性检查。缺失时给出警告但不中断。"""
    bad = 0
    for s in cfg["sites"]:
        p = os.path.join(ROOT, "sites", s["id"], s["cover"])
        if not os.path.exists(p):
            print(f"  ✗ {s['code']:16s} 封面缺失: {s['cover']}")
            bad += 1
        else:
            kb = os.path.getsize(p) / 1024
            print(f"  ✓ {s['code']:16s} {kb:6.1f} KB  {s['cover']}")
    return bad


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN" data-theme="light" data-lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>__TITLE__</title>
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="description" content="__DESC__">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="__BASE__/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="photoai.life">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:url" content="__BASE__/">
<meta property="og:image" content="__BASE__/og-cover.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="zh_CN">
<meta property="og:locale:alternate" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="__TITLE__">
<meta name="twitter:description" content="__DESC__">
<meta name="twitter:image" content="__BASE__/og-cover.jpg">
<script type="application/ld+json">__LD__</script>
__UI_HEAD__
__UI_CSS__
<style>
.hero{padding:24px 0 26px}
.hero h1{margin:0;font-size:clamp(30px,4.6vw,52px);line-height:1.12;font-weight:800;letter-spacing:.005em}
.hero h1 em{font-style:normal;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero .lead{margin:14px 0 0;max-width:640px;color:var(--tx2);font-size:15px;line-height:1.8}
.big{display:flex;flex-wrap:wrap;gap:10px 40px;margin:26px 0 0;padding:0;list-style:none}
.big li{display:flex;flex-direction:column}
.big b{font-size:clamp(26px,3.4vw,38px);font-weight:800;line-height:1.1;font-variant-numeric:tabular-nums}
.big li>span{margin-top:2px;font-size:13px;color:var(--mu)}
/* 姿势、服装的数字：18+ 关闭时显示可见数量 */
html:not([data-adult="1"]) .n-all,html[data-adult="1"] .n-pub{display:none}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:22px;margin:8px 0 0;padding:0;list-style:none}
.hc{display:flex;flex-direction:column;text-decoration:none;color:var(--tx);min-width:0}
.hc .cv{position:relative;aspect-ratio:4/5;overflow:hidden;border-radius:20px;background:var(--imgbg);
  transition:transform .3s var(--ease),box-shadow .3s}
.hc:hover .cv{transform:translateY(-4px);box-shadow:var(--sh2)}
.hc:focus-visible{outline:none}.hc:focus-visible .cv{box-shadow:0 0 0 3px var(--ac)}
.hc .cv img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .6s var(--ease)}
.hc:hover .cv img{transform:scale(1.04)}
.hc .cv.contain img{object-fit:contain;padding:6% 8%}
/* 姿势卡：左线稿右深度图 */
.hc .cv.split img+img{clip-path:inset(0 0 0 50%)}
.hc .cv.split::after{content:"";position:absolute;top:6%;bottom:6%;left:50%;width:2px;margin-left:-1px;background:var(--ac);opacity:.8}
.hc .tag{position:absolute;z-index:1;left:12px;bottom:12px;display:flex;gap:6px}
.hc .tag span{padding:3px 10px;border-radius:999px;background:rgba(255,255,255,.9);color:#111;font-size:12px;font-weight:700}
.hc .tag span.ok{background:#16a34a;color:#fff}
.hc .tx{padding:14px 4px 0}
.hc h2{display:flex;align-items:center;gap:8px;margin:0;font-size:19px;font-weight:800}
.hc h2 svg{width:18px;height:18px;margin-left:auto;color:var(--mu);transition:transform .2s,color .2s}
.hc:hover h2 svg{transform:translateX(3px);color:var(--tx)}
.hc p{margin:6px 0 0;color:var(--tx2);font-size:13.5px;line-height:1.7}
.hc .nums{margin-top:10px;display:flex;gap:16px;font-size:12.5px;color:var(--mu)}
.hc .nums b{color:var(--tx);font-size:14px;font-variant-numeric:tabular-nums;margin-right:3px}
.credits{margin:46px 0 0;padding:22px 0 0;border-top:1px solid var(--line)}
.credits h2{margin:0 0 10px;font-size:13px;font-weight:700;letter-spacing:.06em;color:var(--mu)}
.credits ul{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:6px 30px;margin:0;padding:0;list-style:none;font-size:13px}
.credits li{display:flex;align-items:baseline;gap:10px;min-width:0}
.credits li>a:first-child{font-weight:600;color:var(--tx);text-decoration:none}
.credits li>a:first-child:hover{text-decoration:underline}
.credits .au{color:var(--mu)}.credits .au a{color:var(--mu)}
.credits .lic{margin-left:auto;font-size:12px;white-space:nowrap;padding:1px 8px;border-radius:999px;background:var(--sf);color:var(--tx2)}
.credits .lic.ok{background:#dcfce7;color:#166534}
html[data-theme="dark"] .credits .lic.ok{background:#14301d;color:#86efac}
.credits .note{margin:12px 0 0;font-size:12px;color:var(--mu);line-height:1.8}
.hub-seo{margin-top:34px}
@media(max-width:640px){
  .hero{padding:14px 0 16px}
  .hero .lead{font-size:14px}
  .big{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 16px;margin-top:18px}
  .cards{grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 10px}
  .hc .cv{border-radius:16px}
  .hc h2{font-size:15.5px}
  .hc p{font-size:12.5px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
  .hc .nums{display:none}
  .hc .tag{left:8px;bottom:8px;flex-wrap:wrap}.hc .tag span{font-size:12px;padding:2px 8px}
}
</style>
__SEO_CSS__
<style>__RC_CSS__</style>
__FAQ_LD__
</head>
<body>
__UI_BAR__
<main class="wrap">
  <section class="hero">
    <p class="eyebrow">Reference Gallery · <span class="zh">AI 绘画参考图库</span><span class="ja">AI イラスト参考画像集</span></p>
    <h1><span class="zh">画画、出图时用的<br><em>参考图库</em></span><span class="ja">描く・生成するための<br><em>参考画像集</em></span></h1>
    <p class="lead"><span class="zh">人像、人体姿势的线稿与深度图、服装、CC0 姿势线稿。全部为 AI 生成，可按标签筛选、放大和下载，中日双语。</span><span class="ja">ポートレート、ポーズの線画と深度マップ、衣装、CC0 ポーズ線画。すべて AI 生成で、タグ絞り込み・拡大・ダウンロードに対応。</span></p>
    <ul class="big">__BIG__</ul>
  </section>
  <ul class="cards">__CARDS__</ul>
  <section class="credits">
    <h2><span class="zh">素材来源与授权</span><span class="ja">素材の出典とライセンス</span></h2>
    <ul>__CREDITS__</ul>
    <p class="note"><span class="zh">素材著作权归各原作者所有。本站是个人学习用途的中文索引镜像，代码 MIT，素材按各原站条件使用。</span><span class="ja">素材の著作権は各原作者に帰属します。本サイトは個人学習目的の中国語インデックスで、コードは MIT、素材は各原サイトの条件に従います。</span></p>
  </section>
  <div class="hub-seo">__SEO_INTRO__</div>
</main>
__UI_DIALOGS__
__UI_JS__
__RC_HTML__
__RC_JS__
</body>
</html>
"""

ARROW = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
         'stroke-linejoin="round" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6"/></svg>')


def num(s, i=0):
    """入口页的数字；有 public（成人向隐藏后的数量）时两套都写，CSS 按 18+ 状态显示一套"""
    x = s["stats"][i]
    v = f"{int(x['v']):,}"
    if i == 0 and x.get("public"):
        return f'<span class="n-pub">{int(x["public"]):,}</span><span class="n-all">{v}</span>'
    return v


def cover(s, by_id, extra=""):
    """卡片封面：姿势卡左半线稿、右半深度图（同一张图的两个版本，逐像素对齐）。extra 放在封面框里（授权标签等）"""
    src = f"./{s['id']}/{s['cover']}"
    pos = f' style="object-position:{escape(s["coverPos"])}"' if s.get("coverPos") else ""
    if s["id"] == "pose" and "pose-depth" in by_id:
        dep = f"./pose-depth/{by_id['pose-depth']['cover']}"
        return (f'<div class="cv contain split"><img src="{escape(src)}" alt="" loading="lazy" decoding="async">'
                f'<img src="{escape(dep)}" alt="" loading="lazy" decoding="async">{extra}</div>')
    contain = " contain" if s["id"] in ("shisei",) else ""
    return f'<div class="cv{contain}"><img src="{escape(src)}" alt="" loading="lazy" decoding="async"{pos}>{extra}</div>'


def page(cfg, shown, base, title, desc, ld, seo):
    by_id = {s["id"]: s for s in cfg["sites"]}
    # 一行大数字：每个图库一项，标签用图库短名（姿势、服装的数字跟随 18+）
    unit = {"portrait": ("张人像", "枚のポートレート"), "costume": ("套服装", "着の衣装"),
            "pose": ("个姿势 · 线稿与深度图", "ポーズ · 線画とデプス"), "shisei": ("个 CC0 线稿姿势", "の CC0 線画ポーズ")}
    big = "".join(
        f'<li><b>{num(s)}</b><span>{ui.bi(*unit.get(s["id"], (s["name"]["zh"], s["name"]["ja"])))}</span></li>'
        for s in shown)
    cards = []
    for s in shown:
        lic = LICENSE.get(s["license"], LICENSE["restricted"])
        tags = f'<span class="{lic["cls"]}">{ui.bi(lic["zh"], lic["ja"])}</span>'
        if s["id"] == "pose":
            tags = f'<span>{ui.bi("线稿 ⟷ 深度图", "線画 ⟷ デプス")}</span>' + tags
        nums = "".join(f'<span><b>{num(s, i)}</b>{ui.bi(x["l"]["zh"], x["l"]["ja"])}</span>'
                       for i, x in enumerate(s["stats"]))
        tag_box = f'<div class="tag">{tags}</div>'
        cards.append(
            f'<li><a class="hc" href="./{escape(s["id"])}/">{cover(s, by_id, tag_box)}'
            f'<div class="tx"><h2>{ui.bi(s["name"]["zh"], s["name"]["ja"])}{ARROW}</h2>'
            f'<p>{ui.bi(s["desc"]["zh"], s["desc"]["ja"])}</p><div class="nums">{nums}</div></div></a></li>')
    credits = []
    for s in cfg["sites"]:
        lic = LICENSE.get(s["license"], LICENSE["restricted"])
        handle = str(s["author"]["url"]).rstrip("/").split("/")[-1]
        credits.append(
            f'<li><a href="{escape(s["source"])}" target="_blank" rel="noopener noreferrer">{ui.bi(s["name"]["zh"], s["name"]["ja"])}</a>'
            f'<span class="au">{escape(s["author"]["name"])} <a href="{escape(s["author"]["url"])}" target="_blank" '
            f'rel="noopener noreferrer">@{escape(handle)}</a></span>'
            f'<span class="lic {lic["cls"]}">{ui.bi(lic["zh"], lic["ja"])}</span></li>')
    return (TEMPLATE
            .replace("__UI_HEAD__", ui.head_script())
            .replace("__UI_CSS__", ui.head_css())
            .replace("__UI_BAR__", ui.bar(None, "./"))
            .replace("__UI_DIALOGS__", ui.dialogs(ui.HUB_KEYS))
            .replace("__UI_JS__", ui.body_script())
            .replace("__RC_CSS__", recipe.CSS).replace("__RC_HTML__", recipe.html("./")).replace("__RC_JS__", recipe.script())
            .replace("__SEO_CSS__", "<style>" + landing.SEO_INTRO_CSS + ".seo-intro{padding:0}</style>")
            .replace("__FAQ_LD__", landing.faq_ld_script(seo["faq"]))
            .replace("__SEO_INTRO__", seo["intro"])
            .replace("__BIG__", big)
            .replace("__CARDS__", "".join(cards))
            .replace("__CREDITS__", "".join(credits))
            .replace("__TITLE__", escape(title))
            .replace("__DESC__", escape(desc))
            .replace("__LD__", ld)
            .replace("__BASE__", base))


def bh(zh, ja):
    """中日双语，内容是已转义的 HTML（可含链接、kbd）"""
    return f'<span class="zh">{zh}</span><span class="ja">{ja}</span>'


GUIDE_CSS = """
.gd{max-width:880px;margin:0 auto;padding:0 var(--gut) 40px}
.gd .crumb{margin:14px 0 0;font-size:13px;color:var(--mu)}.gd .crumb a{color:var(--tx2)}
.gd h1{margin:10px 0 8px;font-size:clamp(26px,3.6vw,36px);line-height:1.25;font-weight:800}
.gd .lead{margin:0;color:var(--tx2);font-size:15px;line-height:1.8}
.gd nav.toc{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 6px}
.gd nav.toc a{display:inline-flex;align-items:center;height:36px;padding:0 14px;border-radius:999px;background:var(--sf);color:var(--tx);
  font-size:13.5px;text-decoration:none}
.gd nav.toc a:hover{background:var(--sf2)}
.gd section{scroll-margin-top:calc(var(--stick) + 16px)}
.gd h2{margin:40px 0 12px;font-size:21px;line-height:1.35}
.gd h3{margin:20px 0 6px;font-size:15.5px}
.gd p,.gd li{color:var(--tx2);font-size:14.5px;line-height:1.85}
.gd p{margin:0 0 10px}
.gd ul{margin:0 0 10px;padding-left:1.3em}
.gd a{color:var(--ac)}
.gd .libs{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin:6px 0 0;padding:0;list-style:none}
.gd .libs a{display:block;height:100%;padding:14px 16px;border-radius:16px;background:var(--sf);color:var(--tx);text-decoration:none}
.gd .libs a:hover{background:var(--sf2)}
.gd .libs b{display:flex;align-items:center;gap:8px;font-size:15px}
.gd .libs kbd{margin-left:auto}
.gd .libs span.d{display:block;margin-top:4px;color:var(--tx2);font-size:13px;line-height:1.7}
.gd table{width:100%;border-collapse:collapse;margin:8px 0 12px;font-size:14px}
.gd th,.gd td{padding:10px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;line-height:1.7}
.gd th{color:var(--mu);font-weight:600;font-size:13px;white-space:nowrap}
.gd td:first-child{white-space:nowrap}
.gd .lic{display:inline-block;padding:1px 9px;border-radius:999px;background:var(--sf);font-size:12.5px;white-space:nowrap}
.gd .lic.ok{background:#dcfce7;color:#166534}
html[data-theme="dark"] .gd .lic.ok{background:#14301d;color:#86efac}
.gd .lic.no{background:#fee2e2;color:#991b1b}
html[data-theme="dark"] .gd .lic.no{background:#3a1616;color:#fca5a5}
.gd .box{padding:14px 16px;border-radius:16px;background:var(--sf);margin:10px 0}
.gd .box p:last-child{margin:0}
.gd .ghl{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
@media(max-width:640px){.gd th,.gd td{padding:8px 4px}.gd td:first-child{white-space:normal}}
"""


def guide_page(cfg, base):
    """使用说明与注意事项：静态、中日双语；快捷键表由 shared/ui.py 的快捷键定义生成"""
    shown = [s for s in cfg["sites"] if not s.get("mergedInto")]
    e = escape
    libs = "".join(
        f'<li><a href="../{e(s["id"])}/"><b>{ui.bi(s["name"]["zh"], s["name"]["ja"])}<kbd>{n}</kbd></b>'
        f'<span class="d">{ui.bi(s["desc"]["zh"], s["desc"]["ja"])}</span></a></li>' for n, s in enumerate(shown, 1))
    lic_rows = []
    for s in cfg["sites"]:
        lic = LICENSE.get(s["license"], LICENSE["restricted"])
        cls = {"ok": "ok", "no": "no"}.get(lic["cls"], "")
        lic_rows.append(
            f'<tr><td>{ui.bi(s["name"]["zh"], s["name"]["ja"])}</td><td><span class="lic {cls}">{ui.bi(lic["zh"], lic["ja"])}</span></td>'
            f'<td>{e(s["author"]["name"])} · <a href="{e(s["source"])}" target="_blank" rel="noopener noreferrer">{e(s["source"].split("//")[-1].rstrip("/"))}</a></td></tr>')
    keys = [ui.K_NAV, ui.K_HOME, ui.K_SEARCH, ui.K_THEME, ui.K_LANG, ui.K_DEPTH, ui.K_LR, ui.K_POSE_LR, ui.K_POSE_UD, ui.K_ADD, ui.K_ESC, ui.K_HELP]
    key_rows = "".join("<tr><td>" + "".join(f"<kbd>{e(k)}</kbd>" for k in ks) + f"</td><td>{ui.bi(zh, ja)}</td></tr>"
                       for ks, zh, ja in keys)
    repo, issues = ui.REPO_URL, ui.REPO_URL + "/issues"
    blank = 'target="_blank" rel="noopener noreferrer"'
    toc = [("libs", "四个图库", "4 つのギャラリー"), ("browse", "浏览与筛选", "閲覧と絞り込み"), ("viewer", "大图", "拡大表示"),
           ("pose", "线稿与深度图", "線画とデプス"), ("recipe", "配方与生图", "レシピと画像生成"),
           ("adult", "18+ 内容", "18+ コンテンツ"), ("keys", "快捷键", "ショートカット"),
           ("notes", "注意事项与授权", "注意事項とライセンス"), ("feedback", "反馈", "フィードバック")]
    body = f"""
<nav class="crumb" aria-label="位置"><a href="../">photoai.life</a> / {ui.bi("使用说明", "使い方")}</nav>
<h1>{ui.bi("使用说明", "使い方")}</h1>
<p class="lead">{ui.bi("photoai.life 是给画画、AI 出图用的参考图库合集。不用注册，打开即用；偏好设置只保存在你的浏览器里。",
                       "photoai.life は、イラスト制作や AI 画像生成のための参考画像集です。閲覧に登録は不要です。表示設定はブラウザ、画像生成設定は訪問者セッションに保存します。")}</p>
<nav class="toc" aria-label="{e("目录")}">{"".join(f'<a href="#{k}">{ui.bi(zh, ja)}</a>' for k, zh, ja in toc)}</nav>

<section id="libs"><h2>{ui.bi("四个图库", "4 つのギャラリー")}</h2>
<p>{bh("顶部栏可以随时切换，也可以按数字键 <kbd>1</kbd>–<kbd>4</kbd>，<kbd>0</kbd> 回到入口页。",
       "上部バー、または数字キー <kbd>1</kbd>–<kbd>4</kbd> で切り替えられます。<kbd>0</kbd> でトップページへ。")}</p>
<ul class="libs">{libs}</ul></section>

<section id="browse"><h2>{ui.bi("浏览与筛选", "閲覧と絞り込み")}</h2>
<ul>
<li>{ui.bi("每个图库顶部的胶囊是分类（系列、季节、分区等），点一下只看这一类，数字是数量。", "各ギャラリー上部のチップは分類（シリーズ・季節・セクションなど）。数字は件数です。")}</li>
<li>{bh("搜索框支持中文、日文和英文关键词，也能搜编号；按 <kbd>/</kbd> 直接跳到搜索框。", "検索欄は中国語・日本語・英語のキーワードと番号に対応。<kbd>/</kbd> で検索欄へ移動します。")}</li>
<li>{ui.bi("「筛选」里还有更多条件：服装按颜色、单品、材质等标签组合筛选（多选为同时满足）；姿势按分类、视角筛选，可以按姿势分组或一张张看。",
           "「絞り込み」ではさらに条件を指定できます。衣装は色・アイテム・素材などのタグを組み合わせて（複数選択は AND）、ポーズは分類・アングルで絞り込み、ポーズごと／1 枚ずつ表示を切り替えられます。")}</li>
<li>{ui.bi("人像集的「人气 Top 10」来自原站的综合排行。", "ポートレート集の「人気 Top 10」は元サイトの総合ランキングです。")}</li>
<li>{ui.bi("往下滚动会自动加载更多。落地页（分类、标签页）里的「在画廊中查看」会带着筛选条件打开画廊。",
           "スクロールすると自動で続きを読み込みます。分類・タグのページの「ギャラリーで見る」は条件付きでギャラリーを開きます。")}</li>
<li>{ui.bi("右上角可以切换深浅色和中文 / 日本語，所有图库共用这些设置。", "右上でライト／ダーク、中文／日本語を切り替えられ、全ギャラリー共通です。")}</li>
</ul></section>

<section id="viewer"><h2>{ui.bi("大图", "拡大表示")}</h2>
<ul>
<li>{bh("点卡片打开大图。<kbd>←</kbd> <kbd>→</kbd> 或左右滑动切换，<kbd>Esc</kbd> 关闭。",
       "カードをクリックで拡大。<kbd>←</kbd> <kbd>→</kbd> または左右スワイプで切り替え、<kbd>Esc</kbd> で閉じます。")}</li>
<li>{ui.bi("大图里可以下载原图、在新标签页打开原图，或复制图片链接。卡片右上角的按钮可以直接下载。",
           "拡大表示から原寸のダウンロード・新しいタブで開く・画像リンクのコピーができます。カード右上のボタンからも直接ダウンロードできます。")}</li>
<li>{ui.bi("服装大图里点标签，会把这个标签加入筛选。", "衣装の拡大表示でタグをクリックすると、そのタグで絞り込みます。")}</li>
</ul></section>

<section id="pose"><h2>{ui.bi("线稿与深度图", "線画とデプス")}</h2>
<p>{ui.bi("姿势集的每张图都有线稿和深度图两个版本，像素完全对齐。", "ポーズ集の各画像には線画とデプスマップの 2 種類があり、ピクセル単位で一致しています。")}</p>
<ul>
<li>{bh("工具栏的开关或 <kbd>D</kbd> 键：整页在线稿和深度图之间切换。", "ツールバーのスイッチまたは <kbd>D</kbd> キーで、ページ全体を線画／デプスに切り替え。")}</li>
<li>{bh("大图里的「对比」：拖动竖线左右对照两张图。<kbd>↑</kbd> <kbd>↓</kbd> 换姿势，<kbd>←</kbd> <kbd>→</kbd> 换视角。",
       "拡大表示の「比較」で、縦線をドラッグして左右を見比べられます。<kbd>↑</kbd> <kbd>↓</kbd> でポーズ、<kbd>←</kbd> <kbd>→</kbd> でアングル。")}</li>
<li>{ui.bi("深度图可以直接作为 ControlNet depth 的控制图；线稿可以用于 lineart / scribble，或作为构图参考。",
           "デプスはそのまま ControlNet depth の制御画像に、線画は lineart / scribble や構図の参考に使えます。")}</li>
<li>{ui.bi("/pose-depth/ 是默认显示深度图的入口，和 /pose/ 是同一个模块。", "/pose-depth/ はデプス表示から始まる入口で、/pose/ と同じモジュールです。")}</li>
</ul></section>

<section id="recipe"><h2>{ui.bi("配方与生图", "レシピと画像生成")}</h2>
<p>{ui.bi("配方把人像、服装、姿势各一项组合起来，生成可直接使用的提示词。四个图库共用同一份配方，切换图库不会丢失。",
           "レシピは、ポートレート・衣装・ポーズを 1 つずつ組み合わせて、そのまま使えるプロンプトを作る機能です。4 つのギャラリーで共通です。")}</p>
<ul>
<li>{bh("在大图里点「加入配方」或按 <kbd>A</kbd>；桌面上把鼠标移到卡片上，右上角的 <b>+</b> 也可以直接加入。同一类再加一项会替换原来的。",
       "拡大表示の「レシピに追加」か <kbd>A</kbd> キーで追加します。デスクトップではカード右上の <b>+</b> からも追加でき、同じ種類を追加すると置き換わります。")}</li>
<li>{ui.bi("配方栏常驻右下角，点开后向上展开：上面是人像、服装、姿势三个参考，下面是自动生成、可以修改的提示词，以及「图像生成」。展开时背后的页面照常浏览，可以继续往配方里加图。",
           "レシピバーは右下に常駐し、開くと上に広がります。上段にポートレート・衣装・ポーズの 3 つの参考、下段に自動生成され編集できるプロンプトと「画像生成」があります。開いたままでも後ろのページは閲覧でき、レシピへの追加も続けられます。")}</li>
<li>{ui.bi("点「生成」会用你自己的 API Key 调用所选服务商（OpenAI GPT Image、Google Gemini、豆包 Seedream、通义 Qwen-Image，或 OpenAI 兼容的中转），三张参考图和提示词会一起发过去。生成中可以切换到其他图库，完成后结果出现在配方栏里，可以放大、下载、删除。",
           "「生成」を押すと、ご自身の API Key で選んだサービス（OpenAI GPT Image、Google Gemini、Doubao Seedream、Qwen-Image、OpenAI 互換の中継）を呼び出し、3 枚の参考画像とプロンプトを送ります。生成中に別のギャラリーへ移動してもよく、完成した画像はレシピバーに表示され、拡大・保存・削除できます。")}</li>
<li>{ui.bi("中转用户在「生图服务」里选「自定义中转」，填 Base URL、Key 和模型 ID；按中转文档选择 images/edits（multipart，图片字段 image[] 或 image）或 images/generations（JSON 多图）。只填域名时自动补 /v1。保存后可点「刷新模型列表」，这一步不会生成图片；部分服务商不提供模型列表，仍需实际生图验证。",
           "中継を使う場合は「カスタム中継」を選び、Base URL・Key・モデル ID を入力します。API 形式は images/edits（multipart、image[] または image）か images/generations（JSON 複数画像）から選べます。ドメインだけの場合は /v1 を補います。接続テストはモデル一覧の取得だけで画像は生成しません。一覧 API がないサービスは実際の画像生成で確認してください。")}</li>
<li>{ui.bi("每位访客使用自己的 Key。首次提交后，Key 加密保存在本站生图服务，不回传前端，也不写入浏览器存储；参考图和提示词经本站后端发送给所选服务商。多个标签页共享访客会话，配置闲置 7 天或创建 30 天后清除；服务端生成图片保留 24 小时，浏览器缓存最近 30 条结果。可清除 Key、删除配置或清空会话数据。费用由你的服务商账户承担。",
           "各訪問者が自分の Key を使います。Key は送信後サーバーに暗号化保存し、ブラウザへ返しません。参考画像と説明は本サイトのバックエンド経由で送ります。設定は 7 日間未使用または作成後 30 日で消去し、生成画像はサーバーに 24 時間、最近 30 件はブラウザに保存します。複数タブは同じセッションを共有し、Key・設定・セッションは消去できます。")}</li>
<li>{ui.bi("不想在本站生成，也可以「复制提示词」或「下载参考拼图」，拿到其他工具里用。提示词按图 1、图 2、图 3 的顺序引用参考图，上传时按同样顺序。大图里的「复制提示词」只复制这一项的英文描述。",
           "本サイトで生成しない場合は「プロンプトをコピー」か「参考ボードを保存」で他のツールに持っていけます。プロンプトは画像 1・2・3 の順に参照するので、同じ順にアップロードしてください。拡大表示の「プロンプトをコピー」はその 1 件の英語の説明だけをコピーします。")}</li>
<li>{ui.bi("成人向内容不能加入配方。配方只保存在你的浏览器里。参考拼图需要在线打开本站才能下载，只供你自己出图参考，其中的姿势和服装图片同样不能再分发。",
           "成人向けの内容はレシピに追加できません。レシピはブラウザ内にのみ保存されます。参考ボードの保存はオンラインで開いたときのみ使え、ご自身の制作の参考用です。中のポーズ・衣装画像も再配布できません。")}</li>
</ul></section>

<section id="adult"><h2>{ui.bi("18+ 内容", "18+ コンテンツ")}</h2>
<p>{ui.bi(ui.AGE_WHAT["zh"], ui.AGE_WHAT["ja"])}</p>
<p>{ui.bi("这些内容默认隐藏。点顶部栏的「18+」并确认已满 18 岁后显示，各图库通用，随时可以关闭。它们不会出现在分类、标签等落地页和站点地图里。",
           "これらは初期状態で非表示です。上部バーの「18+」で 18 歳以上であることを確認すると表示され、全ギャラリー共通でいつでもオフにできます。分類・タグのページやサイトマップには掲載しません。")}</p></section>

<section id="keys"><h2>{ui.bi("快捷键", "ショートカット")}</h2>
<p>{bh("在任意页面按 <kbd>?</kbd> 可以查看当前页可用的快捷键。在输入框里打字时不会触发。",
       "どのページでも <kbd>?</kbd> でそのページのショートカットを表示します。入力欄での入力中は反応しません。")}</p>
<table><thead><tr><th>{ui.bi("按键", "キー")}</th><th>{ui.bi("作用", "動作")}</th></tr></thead><tbody>{key_rows}</tbody></table></section>

<section id="notes"><h2>{ui.bi("注意事项与授权", "注意事項とライセンス")}</h2>
<div class="box"><p>{ui.bi("所有图片都是 AI 生成的，不是真人、不对应真实商品。著作权归各原作者所有，本站是个人整理的中文索引镜像，与原作者没有合作关系。",
                          "画像はすべて AI 生成で、実在の人物・商品ではありません。著作権は各原作者に帰属し、本サイトは個人による中国語インデックスで、原作者とは提携していません。")}</p></div>
<table><thead><tr><th>{ui.bi("图库", "ギャラリー")}</th><th>{ui.bi("授权", "ライセンス")}</th><th>{ui.bi("作者 · 原站", "作者 · 元サイト")}</th></tr></thead>
<tbody>{"".join(lic_rows)}</tbody></table>
<ul>
<li>{ui.bi("CC0：可以免费商用、修改和再分发，不需要署名。", "CC0：商用・改変・再配布が自由で、クレジット表記も不要です。")}</li>
<li>{ui.bi("禁止再分发：可以免费用于作品制作（包括商用和作为参考），但不能把图片文件本身转载、打包分享或转售，包括裁切、调色后的版本。深度图原站另外禁止批量下载和用工具自动获取。",
           "再配布禁止：作品制作（商用・参考を含む）には無料で使えますが、画像ファイルそのもの（トリミング・色調整したものを含む）の転載・まとめての共有・販売はできません。デプス元サイトは一括ダウンロードとツールによる自動取得も禁止しています。")}</li>
<li>{ui.bi("人像是 AI 生成的虚构人物，请不要用来冒充真人或制作误导性内容。", "ポートレートは AI 生成の架空の人物です。実在人物へのなりすましや誤解を招く用途には使わないでください。")}</li>
<li>{ui.bi("本站没有统计和广告脚本。显示偏好与配方保存在浏览器；生图服务按访客会话保存加密 Key、配置、任务及结果，并将参考图和提示词发送给你选择的服务商，适用该服务商条款。可随时清空会话；Key 不返回浏览器。",
           "解析・広告スクリプトはありません。表示設定とレシピはブラウザに、暗号化した Key・生成設定・タスク・結果は訪問者セッションに保存します。参考画像と説明はバックエンドから選択したサービスへ送信し、その規約が適用されます。Key はブラウザへ返さず、セッションは消去できます。")}</li>
</ul></section>

<section id="feedback"><h2>{ui.bi("反馈", "フィードバック")}</h2>
<p>{ui.bi(f"发现错误、翻译问题，或有功能建议，欢迎在 GitHub 提交 Issue。网站代码以 MIT 协议开源，由 {ui.AUTHOR} 维护。",
           f"誤り・翻訳の問題・機能の提案は GitHub の Issue へどうぞ。サイトのコードは MIT ライセンスで公開しており、{ui.AUTHOR} が運営しています。")}</p>
<div class="ghl"><a class="btn pri" href="{e(issues)}" {blank}>{ui.GH_ICON}{ui.bi("提交 Issue", "Issue を作成")}</a>
<a class="btn" href="{e(repo)}" {blank}>{ui.bi("GitHub 仓库", "GitHub リポジトリ")}</a>
<a class="btn ghost" href="{e(ui.AUTHOR_URL)}" {blank}>@{e(ui.AUTHOR)}</a></div></section>
"""
    title = "使用说明与注意事项 · photoai.life AI 绘画参考图库"
    desc = ("photoai.life 使用说明：四个参考图库的浏览与筛选、线稿与深度图、配方与生图、18+ 内容、快捷键，"
            "以及各图库的授权（CC0 / 禁止再分发）与注意事项。")
    ld = json.dumps({"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc,
                     "url": base + "/guide/", "inLanguage": ["zh-CN", "ja"],
                     "isPartOf": {"@type": "WebSite", "name": "photoai.life", "url": base + "/"},
                     "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
                         {"@type": "ListItem", "position": 1, "name": "photoai.life", "item": base + "/"},
                         {"@type": "ListItem", "position": 2, "name": "使用说明", "item": base + "/guide/"}]}},
                    ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="zh-CN" data-theme="light" data-lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="description" content="{e(desc)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{base}/guide/">
<meta property="og:type" content="article">
<meta property="og:site_name" content="photoai.life">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{base}/guide/">
<meta property="og:image" content="{base}/og-cover.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{base}/og-cover.jpg">
<script type="application/ld+json">{ld}</script>
{ui.head_script()}
{ui.head_css()}
<style>{GUIDE_CSS}</style>
</head>
<body>
{ui.bar(None, "../")}
<main class="gd">{body}</main>
<footer class="foot"><p>{bh(f'photoai.life · <a href="../">{ui.bi("返回入口页", "トップページへ")}</a> · <a href="{e(repo)}" {blank}>GitHub</a>',
                             f'photoai.life · <a href="../">トップページへ</a> · <a href="{e(repo)}" {blank}>GitHub</a>')}</p></footer>
{ui.dialogs(ui.PAGE_KEYS)}
{ui.body_script()}
</body>
</html>
"""


def total_images(cfg):
    """对外公布的「参考图」总数，沿用最初 12,975 的口径：原站提供的图片文件数，
    即 manifest 条数 × 档位数，不含 mid 档（中图是本仓库生成或补的）。
    这是文件数，不是不同画面数：人像、姿势、深度姿势、Shisei 每张图按缩略图 + 原图算两个文件，服装按三档算三个。"""
    n = 0
    for s in cfg["sites"]:
        p = os.path.join(ROOT, "sites", s["id"], "manifest.json")
        with open(p, encoding="utf-8") as f:
            rows = len(json.load(f))
        n += rows * len([t for t in s.get("tiers", []) if t != "mid"])
    return n


def hub_seo(cfg, base):
    """入口页静态介绍、FAQ 与 llms.txt。事实只取自 sites.json 与固定的授权说明。"""
    sites = {s["id"]: s for s in cfg["sites"]}
    stat = lambda sid, i: f'{int(sites[sid]["stats"][i]["v"]):,}'
    shown = [s for s in cfg["sites"] if not s.get("mergedInto")]
    N, K = f"{total_images(cfg):,}", len(shown)
    faq = [
        ("photoai.life 是什么？",
         f"一组面向 AI 绘画的参考图库：人像集（角色脸部一致性参考）、姿势集（人体姿势的线稿与 ControlNet 深度图，一键切换）、"
         f"服装集（服装与穿搭参考）和 CC0 姿势线稿，共 {N} 个图片文件，全部为 AI 生成，中日双语。"),
        ("图片可以商用吗？",
         "要看图库。人像集与 CC0 姿势线稿为 CC0 1.0 公有领域，可以免费商用和再分发。姿势集（线稿、深度图）与服装集的原作者"
         "允许免费用于作品制作（包括商用与参考），但禁止再分发、转载或转售图片文件本身；深度图原站另禁止批量下载。"),
        ("这些图是真人吗？",
         "不是。人像是 AI 生成的虚构人物，姿势是无脸人偶，服装图由文字生成图像制作，都不对应真实人物或商品。"),
        ("为什么有些内容看不到？",
         "姿势集与 CC0 线稿的双人、性感系列，服装集的内衣与性感两类属于成人向参考，默认隐藏。"
         "用顶部栏的「18+」确认一次年龄即可显示，各图库通用；这些内容不出现在静态落地页里。"),
        ("和原站是什么关系？",
         "这里是各原站的中文索引镜像：把日文分类、标签和姿势名译成中文，加了组合筛选、搜索和中日切换。"
         "图片著作权归原作者，每个图库页脚都有原站和作者链接。"),
    ]
    links = [(f"{s['id']}/browse/", f"{s['name']['zh']} · 分类") for s in cfg["sites"]]
    intro = landing.static_intro(
        [f"photoai.life 收录 {K} 个 AI 绘画参考图库，共 {N} 个 AI 生成的图片文件，可在线浏览、按标签筛选和下载。",
         f"人像集 {stat('portrait', 0)} 张，用来让 AI 生成的角色保持同一张脸，CC0 可商用；"
         f"姿势集 {stat('pose', 0)} 个姿势，线稿与深度图各 {stat('pose', 1)} 张，每个姿势 5 个视角，一键切换、左右对比，深度图可直接用于 ControlNet；"
         f"服装集 {stat('costume', 0)} 套服装、{stat('costume', 2)} 个标签，标签保留英文关键词，可直接作提示词；"
         f"CC0 姿势线稿 {stat('shisei', 0)} 个姿势、{stat('shisei', 1)} 张，可商用、可再分发。"],
        [("图库", f"{K} 个"), ("图片文件", N), ("语言", "中文 / 日本語"), ("素材", "全部 AI 生成")],
        links, faq, more_href=None)

    lic = {"portrait": "CC0 1.0 公有领域，可商用、可再分发。",
           "pose": "允许免费用于作品制作（含商用与参考）；禁止再分发、转载、转售图片文件本身。",
           "pose-depth": "同姿势集；原站另禁止批量下载或用工具自动获取。",
           "costume": "允许免费用于作品制作（含商用与参考）；禁止再分发、转载、转售图片文件本身。",
           "shisei": "图片 CC0 1.0，可商用、可再分发；姿势目录沿用 ai-pose-gallery，仅注明出处。"}
    what = {"portrait": f"{stat('portrait', 0)} 张 AI 生成人像：面部 {stat('portrait', 1)} 张（正面、纯色背景），造型 {stat('portrait', 2)} 张。用于 AI 绘画中保持角色脸部一致，按发型分类。",
            "pose": f"{stat('pose', 0)} 个人体姿势、{stat('pose', 1)} 张无脸灰色人偶线稿，每个姿势正面、侧面、斜角、俯视、仰视 5 个视角；页面里可切换到同一姿势的深度图。双人与性感系列默认隐藏。",
            "pose-depth": f"姿势集的深度图入口：同一批 {stat('pose-depth', 0)} 个姿势的 {stat('pose-depth', 1)} 张灰度深度图，可直接作为 ControlNet depth 控制图，可切换回线稿。",
            "costume": f"{stat('costume', 0)} 套 AI 生成服装、{stat('costume', 1)} 个文件，8 个分类、{stat('costume', 2)} 个标签；标签为英文关键词，可直接用作提示词。内衣与性感两类默认隐藏。",
            "shisei": f"{stat('shisei', 0)} 个姿势、{stat('shisei', 1)} 张无脸人偶线稿（全身・标准、上半身、全身・性感、双人），每个姿势最多 5 个视角；全身・性感、双人系列与偏性感的姿势默认隐藏。"}
    lines = ["# photoai.life", "",
             f"> AI 绘画参考图库合集：人像、人体姿势（线稿与 ControlNet 深度图）、服装、CC0 姿势线稿，共 {N} 个图片文件，全部为 AI 生成。"
             "中文索引镜像，界面支持中文与日本語。", "",
             "每个图库都是一个可筛选的画廊页，另有按分类 / 标签 / 发型生成的静态落地页（见各图库的 browse/ 目录与 sitemap）。"
             "成人向内容默认隐藏，不进落地页与 sitemap。图片著作权归各原作者，授权各不相同，引用时请注明对应图库的授权。", "",
             "## 图库", ""]
    for s in cfg["sites"]:
        lines.append(f"- [{s['name']['zh']}]({base}/{s['id']}/)：{what.get(s['id'], s['desc']['zh'])}"
                     f" 授权：{lic.get(s['id'], '')} 原站：{s['source']}")
    lines += ["", "## 分类与标签索引", ""]
    lines += [f"- [{s['name']['zh']} · 全部分类]({base}/{s['id']}/browse/)" for s in cfg["sites"]]
    lines += ["", "## 常见问题", ""] + [f"- **{q}** {a}" for q, a in faq]
    lines += ["", "## 其他", "",
              f"- [使用说明与注意事项]({base}/guide/)：浏览与筛选、线稿与深度图、18+、快捷键、各图库授权",
              f"- [站点地图]({base}/sitemap.xml)",
              "- [源代码（MIT）](https://github.com/Brilliant666/ai-image-gallery)", ""]
    return {"intro": intro, "faq": faq, "llms": "\n".join(lines)}


def main():
    cfg = load()
    only_check = "--check" in sys.argv

    base = "https://example.com"
    for i, a in enumerate(sys.argv):
        if a == "--base" and i + 1 < len(sys.argv):
            base = sys.argv[i + 1]
        elif a.startswith("--base="):
            base = a.split("=", 1)[1]
    base = base.rstrip("/")

    print(f"读取 sites.json：{len(cfg['sites'])} 个站点")
    bad = check(cfg)
    if bad:
        print(f"\n⚠️  {bad} 张封面缺失，生成的页面会出现空图。")

    if only_check:
        print("\n仅校验模式，未生成 index.html")
        return 1 if bad else 0

    shown = [s for s in cfg["sites"] if not s.get("mergedInto")]
    by_id = {s["id"]: s for s in cfg["sites"]}
    st = lambda sid, i=0: int(by_id[sid]["stats"][i]["v"])
    title = (f"photoai.life · AI 绘画参考图库：人像、姿势线稿与深度图、服装、CC0 线稿")
    desc = (f"{len(shown)} 个 AI 绘画参考图库：{st('portrait'):,} 张 CC0 人像（角色脸部一致性）、"
            f"{st('pose')} 个人体姿势的线稿与 ControlNet 深度图（各 {st('pose', 1):,} 张，五视角）、"
            f"{st('costume'):,} 套服装（{st('costume', 2)} 个标签）、{st('shisei')} 个 CC0 姿势线稿。中日双语，在线浏览。")
    seo = hub_seo(cfg, base)

    # 结构化数据：告诉搜索引擎/AI 引擎这是一组并列的子站点
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": desc,
        "url": base + "/",
        "inLanguage": ["zh-CN", "ja"],
        "hasPart": [
            {"@type": "WebSite", "name": s["name"]["zh"], "url": f"{base}/{s['id']}/"}
            for s in shown
        ],
    }, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    html = page(cfg, shown, base, title, desc, ld, seo)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    with open(os.path.join(HUB, "404.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(ui.page_404("/"))
    os.makedirs(os.path.join(HUB, "guide"), exist_ok=True)
    with open(os.path.join(HUB, "guide", "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(guide_page(cfg, base))

    print(f"\n写出 index.html  {os.path.getsize(OUT)/1024:.1f} KB，404.html，guide/index.html")

    # 根 sitemap：入口页 + 各子站首页 + 各子站落地页（读各站 data/landing.json）
    # lastmod 取 sites.json 各站的 updated（入口页取其中最新的），网址做百分号编码
    hub_day = max((s.get("updated") or "") for s in cfg["sites"]) or None
    urls = [(base + "/", hub_day), (base + "/guide/", hub_day)]
    for s in cfg["sites"]:
        urls.append((f"{base}/{s['id']}/", s.get("updated")))
        p = os.path.join(ROOT, "sites", s["id"], "data", "landing.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                urls += [(f"{base}/{s['id']}/{pg}/", s.get("updated")) for pg in json.load(f)["pages"]]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, day in urls:
        sm.append(f"  <url><loc>{landing.esc(landing.quote_url(u))}</loc>" + (f"<lastmod>{day}</lastmod>" if day else "") + "</url>")
    sm.append("</urlset>")
    with open(os.path.join(HUB, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sm) + "\n")

    # 根 robots：显式允许抓取并指向 sitemap
    with open(os.path.join(HUB, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("User-agent: *\nAllow: /\n\n"
                f"Sitemap: {base}/sitemap.xml\n")

    print(f"写出 sitemap.xml（{len(urls)} 条）与 robots.txt  base = {base}")

    # llms.txt：给 AI 爬虫与助手的站点说明（https://llmstxt.org/）
    with open(os.path.join(HUB, "llms.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(seo["llms"])
    print("写出 llms.txt")

    if bad:
        # 封面缺失不阻断生成：新克隆的仓库还没下图片，先出页面，
        # 下载素材后重跑即可。只有 --check 模式才以非零退出提示。
        print("提示：封面缺失的卡片会显示空图，运行 tools/fetch.py 后重新生成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
