# -*- coding: utf-8 -*-
"""姿势生成器：姿势（线稿 + 深度图，一个模块）与 Shisei 共用

由 sites/<id>/scripts/build_gallery.py 调用 build(<站点根>, CONFIG)。

姿势与深度姿势是同一批 288 个姿势的两种图（1439 张图 id 与相对路径完全相同、逐像素对齐），
合成一个模块：/pose/ 默认显示线稿，/pose-depth/ 默认显示深度图，页面里用开关切换，大图里另可左右对比。
两页内联同一份数据，只有默认版本、标题、说明与落地页不同（cfg 的 variant / variants）。

cfg 需要的键：code, title, desc, ogSite, ogTitle, ogDesc, twTitle, twDesc, schemaName, schemaAlt, schemaAbout, source, ui
可选键（缺省为姿势集原来的值）：
  seriesOrder / angOrder   系列与视角的顺序（manifest 里的原文）
  seriesZh / catZh / angZh 中文名表；nameZh 为 None 时直接用 manifest 的「姿势名_zh」
  author / authorUrl       原作者
  imgExt                   原图扩展名
  adultMode                成人向姿势（sites.json 的 adult 规则）在画廊里的处理：hide 隐藏（默认）/ blur 模糊
  variant / variants       姿势模块：本页默认版本（line / depth）与两个版本的站点 id、文案
"""
import csv, json, os, re

import adult, landing, ui
from pose_i18n import SERIES_ZH, CAT_ZH, ANG_ZH, NAME_ZH


def _thumb_dir(rows):
    """缩略图 / 原图路径能否按规则由 系列/分類/编号/视角 拼出来；能就只内联规则，不逐张写路径"""
    def rule(r, kind):
        ext = {"t": r["thumb_path"].rsplit(".", 1)[1], "f": r["full_path"].rsplit(".", 1)[1]}[kind]
        top = "thumbs" if kind == "t" else "img"
        return f'{top}/{r["系列"]}/{r["分類"]}/{r["编号"]}/{r["视角"]}.{ext}'
    exts = {(r["thumb_path"].rsplit(".", 1)[1], r["full_path"].rsplit(".", 1)[1]) for r in rows}
    if len(exts) != 1:
        return None
    ok = all(rule(r, "t") == r["thumb_path"] and rule(r, "f") == r["full_path"] for r in rows)
    return {"tx": next(iter(exts))[0], "fx": next(iter(exts))[1]} if ok else None


def build(root, cfg):
    sid = os.path.basename(os.path.normpath(root))
    rows = json.load(open(os.path.join(root, "manifest.json"), encoding="utf-8"))
    ADULT_RULE = adult.rules(sid)
    SITE_URL = os.environ.get("SITE_URL", "https://example.com").rstrip("/")

    ANG_ORDER = cfg.get("angOrder", ["正面", "横", "斜め", "上から", "下から"])
    # 标准系排第一：画廊默认按系列排序，打开页面首屏就是这一系列（2026-10-31 前是性感系在前）
    SERIES_ORDER = cfg.get("seriesOrder", ["全身1人・標準系", "上半身1人", "全身1人・セクシー系", "2人絡み"])
    S_ZH, C_ZH, A_ZH = cfg.get("seriesZh", SERIES_ZH), cfg.get("catZh", CAT_ZH), cfg.get("angZh", ANG_ZH)
    N_ZH = cfg.get("nameZh", NAME_ZH)
    AUTHOR, AUTHOR_URL = cfg.get("author", "ギア"), cfg.get("authorUrl", "https://x.com/giaaibusi")
    EXT = cfg.get("imgExt", ".png")
    ADULT_MODE = cfg.get("adultMode", "hide") if ADULT_RULE else None
    UI = adult.ui(cfg["ui"])

    # 姿势模块：两个版本的图片目录相对本页的前缀
    VARIANT, VARS = cfg.get("variant"), cfg.get("variants")
    if VARS:
        here = VARS[VARIANT]["site"]
        vpre = {k: ("" if v["site"] == here else f'../{v["site"]}/') for k, v in VARS.items()}
        other = next(v["site"] for k, v in VARS.items() if k != VARIANT)
        mine = {r["id"]: (r["thumb_path"], r["full_path"]) for r in rows}
        theirs = {r["id"]: (r["thumb_path"], r["full_path"])
                  for r in json.load(open(os.path.join(os.path.dirname(root), other, "manifest.json"), encoding="utf-8"))}
        assert mine == theirs, "线稿与深度图的 manifest 不再一一对应，不能合成一个模块"

    rule = _thumb_dir(rows)
    by_view = {(r["系列"], r["分類"], r["编号"], r["视角"]): r for r in rows}
    poses, adult_keys = {}, set()
    for r in rows:
        key = (r["系列"], r["分類"], r["编号"])
        if adult.is_adult(r, ADULT_RULE):
            adult_keys.add(key)
        if key not in poses:
            zh = r.get("姿势名_zh") if N_ZH is None else N_ZH.get(r["姿势名"], r["姿势名"])
            poses[key] = {"s": r["系列"], "c": r["分類"], "p": r["编号"], "n": r["姿势名"], "z": zh or r["姿势名"], "v": []}
        v = {"a": r["视角"]}
        if not rule:
            v.update(t=r["thumb_path"].replace("\\", "/"), f=r["full_path"].replace("\\", "/"))
        poses[key]["v"].append(v)
    for key in adult_keys:
        poses[key]["x"] = 1
    for p in poses.values():
        p["v"].sort(key=lambda v: ANG_ORDER.index(v["a"]) if v["a"] in ANG_ORDER else 99)
    data = sorted(poses.values(), key=lambda p: (SERIES_ORDER.index(p["s"]) if p["s"] in SERIES_ORDER else 99, p["p"]))
    series_list = [s for s in SERIES_ORDER if any(p["s"] == s for p in data)]
    cats = sorted({p["c"] for p in data})
    n_images = sum(len(p["v"]) for p in data)

    payload = {"poses": data, "series": series_list, "cats": cats, "angs": ANG_ORDER,
               "seriesZh": S_ZH, "catZh": C_ZH, "angZh": A_ZH, "ui": UI}
    if rule:
        payload["path"] = rule
    if VARS:
        payload["vars"] = {k: {"pre": vpre[k], "ext": EXT if k == VARIANT else VARS[k].get("ext", EXT)} for k in VARS}
        payload["variant"] = VARIANT
    payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    # 静态落地页、主页里不依赖 JS 的介绍与 FAQ
    landing_urls, seo_intro, FAQ = [], "", []
    if cfg.get("seoPages"):
        import pose_seo
        thumb_of = lambda p, v: by_view[(p["s"], p["c"], p["p"], v["a"])]["thumb_path"]
        landing_urls, seo_intro, FAQ = pose_seo.build(root, SITE_URL, cfg, data, series_list, cats, adult_keys, thumb_of)

    U = UI["zh"]
    keys = ui.POSE_KEYS if VARS else ui.LINE_KEYS
    toggle = ""
    if VARS:
        lz, lj = VARS["line"]["label"]["zh"], VARS["line"]["label"]["ja"]
        dz, dj = VARS["depth"]["label"]["zh"], VARS["depth"]["label"]["ja"]
        toggle = (f'<button type="button" class="toggle" id="vsw" role="switch" aria-checked="{"true" if VARIANT == "depth" else "false"}">'
                  f'<span class="t-a">{ui.bi(lz, lj)}</span><span class="t-b">{ui.bi(dz, dj)}</span></button>')
    stats = "".join(f'<li><b>{v}</b>{ui.bi(zh, ja)}</li>' for v, zh, ja in cfg.get("stats", []))

    html = TEMPLATE
    for k, v in {
        "__UI_HEAD__": ui.head_script(), "__UI_CSS__": ui.head_css(),
        "__BLUR_CSS__": adult.BLUR_CSS if ADULT_MODE == "blur" else "",
        "__UI_BAR__": ui.bar(sid), "__UI_DIALOGS__": ui.dialogs(keys), "__UI_JS__": ui.body_script(),
        "__SEO_CSS__": landing.SEO_INTRO_CSS, "__SEO_INTRO__": seo_intro,
        "__FAQ_LD__": landing.faq_ld_script(FAQ) if FAQ else "",
        "__EYEBROW__": ui.bi(U["eyebrow"], UI["ja"]["eyebrow"]),
        "__H1__": ui.bi(U["brand1"] + " " + U["brand2"], UI["ja"]["brand1"] + " " + UI["ja"]["brand2"]),
        "__LEAD__": ui.bi(U["sub1"], UI["ja"]["sub1"]),
        "__STATS__": stats, "__TOGGLE__": toggle,
        "__FOOTER__": f'<span class="zh">{U["footer"]}</span><span class="ja">{UI["ja"]["footer"]}</span>',
        "__SEARCH_ICON__": ui.SEARCH_ICON, "__DL_ICON__": json.dumps(ui.DL_ICON),
        "__ADULT_MODE__": ADULT_MODE or "none", "__EXT__": EXT,
        "__N_IMAGES__": str(cfg.get("schemaImages", n_images)),
        "__LICENSE_LD__": cfg.get("licenseLd", ""),
        "__AUTHOR_URL__": AUTHOR_URL, "__AUTHOR__": AUTHOR,
        "__TITLE__": cfg["title"], "__DESC__": cfg["desc"], "__OG_SITE__": cfg["ogSite"],
        "__OG_TITLE__": cfg["ogTitle"], "__OG_DESC__": cfg["ogDesc"], "__TW_TITLE__": cfg["twTitle"], "__TW_DESC__": cfg["twDesc"],
        "__SCHEMA_NAME__": cfg["schemaName"], "__SCHEMA_ALT__": cfg["schemaAlt"], "__SCHEMA_ABOUT__": cfg["schemaAbout"],
    }.items():
        html = html.replace(k, v)
    html = html.replace("__PAYLOAD__", payload).replace("__SITE__", SITE_URL)
    out = os.path.join(root, "index.html")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("wrote index.html", "%.1f KB" % (os.path.getsize(out) / 1024))
    print("poses:", len(data), "| images:", n_images, "| series:", len(series_list), "| cats:", len(cats),
          "| paths:", "rule" if rule else "inline")

    # ── 导出可复用的数据文件 ─────────────────────────────
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    zh = [{"id": p["p"] + "_" + v["a"], "系列": p["s"], "系列_zh": S_ZH.get(p["s"], p["s"]),
           "分类": p["c"], "分类_zh": C_ZH.get(p["c"], p["c"]), "姿势编号": p["p"],
           "姿势名": p["n"], "姿势名_zh": p["z"], "视角": v["a"], "视角_zh": A_ZH.get(v["a"], v["a"]),
           "缩略图": by_view[(p["s"], p["c"], p["p"], v["a"])]["thumb_path"],
           "原图": by_view[(p["s"], p["c"], p["p"], v["a"])]["full_path"]}
          for p in data for v in p["v"]]
    with open(os.path.join(data_dir, "pose-zh.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(zh, f, ensure_ascii=False, indent=1)
    meta = {"site": cfg["code"], "source": cfg["source"], "author": cfg.get("authorMeta", "ギア (@giaaibusi)"),
            "poses": len(data), "images": n_images,
            "系列": [{"ja": s, "zh": S_ZH.get(s, s), "poses": sum(1 for p in data if p["s"] == s)} for s in series_list],
            "分类": [{"ja": c, "zh": C_ZH.get(c, c), "poses": sum(1 for p in data if p["c"] == c)} for c in cats],
            "视角": [{"ja": a, "zh": A_ZH.get(a, a)} for a in ANG_ORDER]}
    with open(os.path.join(data_dir, "meta.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    with open(os.path.join(data_dir, "translations.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["字段", "日文原文", "中文译文"])
        for k, v in S_ZH.items():
            w.writerow(["系統", k, v])
        for k, v in C_ZH.items():
            w.writerow(["分類", k, v])
        for k, v in A_ZH.items():
            w.writerow(["アングル", k, v])
        for k, v in (N_ZH if N_ZH is not None else {p["n"]: p["z"] for p in data}).items():
            w.writerow(["ポーズ名", k, v])
    print("wrote data/pose-zh.json, data/meta.json, data/translations.csv")

    with open(os.path.join(root, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL)
    landing.sitemap(SITE_URL, landing_urls, os.path.join(root, "sitemap.xml"))
    with open(os.path.join(root, "404.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(ui.page_404("/"))
    print("wrote robots.txt, sitemap.xml, 404.html")
    print("SITE_URL =", SITE_URL)


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN" data-theme="light" data-lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="__SITE__/">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="__OG_SITE__">
<meta property="og:title" content="__OG_TITLE__">
<meta property="og:description" content="__OG_DESC__">
<meta property="og:url" content="__SITE__/">
<meta property="og:image" content="__SITE__/og-cover.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="zh_CN">
<meta property="og:locale:alternate" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="__TW_TITLE__">
<meta name="twitter:description" content="__TW_DESC__">
<meta name="twitter:image" content="__SITE__/og-cover.jpg">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ImageGallery","name":"__SCHEMA_NAME__","alternateName":"__SCHEMA_ALT__","url":"__SITE__/","inLanguage":["zh-CN","ja"],"numberOfItems":__N_IMAGES__,"about":"__SCHEMA_ABOUT__","isAccessibleForFree":true,__LICENSE_LD__"creator":{"@type":"Person","name":"__AUTHOR__","url":"__AUTHOR_URL__"}}
</script>
__UI_HEAD__
__UI_CSS__
<style>
.ph>img{object-fit:contain}
/* 线稿是白底：浅色主题下与卡片底色正片叠底，成为柔和的灰色卡片（深度图本身是深色底，几乎不受影响） */
html:not([data-theme="dark"]) .ph>img,html:not([data-theme="dark"]) .strip img,html:not([data-theme="dark"]) .mang img,html:not([data-theme="dark"]) .mstage img{mix-blend-mode:multiply}
@media(max-width:640px){.trow .toggle span{padding:0 10px}.fbtn{padding:0 12px}}
.strip{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin-top:6px}
.strip button{position:relative;padding:0;border:0;border-radius:8px;overflow:hidden;background:var(--imgbg);aspect-ratio:3/4;cursor:pointer;
  outline:2px solid transparent;outline-offset:-2px;transition:outline-color .15s}
.strip button img{width:100%;height:100%;object-fit:contain;display:block}
.strip button:hover,.strip button.on{outline-color:var(--sel)}
.filters{display:none;flex-wrap:wrap;gap:8px;align-items:center}
.filters.open{display:flex}
.fbtn[aria-expanded="true"]{background:var(--sel);color:var(--on-sel)}
.fbtn b{min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:var(--ac);color:#fff;font-size:11px;display:none;place-items:center}
.fbtn b.on{display:inline-grid}
.fbtn[aria-expanded="true"] b{background:var(--on-sel);color:var(--sel)}
/* 大图：线稿 / 深度图 / 对比 */
.mstage .cmp{position:absolute;inset:0;opacity:0;pointer-events:none;transition:opacity .2s}
.mstage.cmpon .cmp{opacity:1;pointer-events:auto}
.mstage.cmpon .hi,.mstage.cmpon .lo{opacity:0!important}
.cmp img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
.cmp .cb{clip-path:inset(0 0 0 var(--x,50%))}
.cmp .ln{position:absolute;top:0;bottom:0;left:var(--x,50%);width:2px;margin-left:-1px;background:var(--ac);pointer-events:none}
.cmp .ln::after{content:"";position:absolute;top:50%;left:50%;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;
  background:var(--bg2) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m9 6-6 6 6 6M15 6l6 6-6 6'/%3E%3C/svg%3E") center/18px no-repeat;
  box-shadow:var(--sh2)}
.cmp .tg{position:absolute;top:10px;padding:2px 10px;border-radius:999px;background:rgba(17,17,17,.62);color:#fff;font-size:11.5px;font-weight:600;pointer-events:none}
.cmp .tg.a{left:10px}.cmp .tg.b{right:10px}
.cmp input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:ew-resize}
.mang{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}
.mang button{position:relative;padding:0;border:0;border-radius:10px;overflow:hidden;background:var(--imgbg);aspect-ratio:3/4;cursor:pointer;
  outline:2px solid transparent;outline-offset:-2px}
.mang button img{width:100%;height:100%;object-fit:contain;display:block}
.mang button span{position:absolute;left:0;right:0;bottom:0;font-size:10px;line-height:1.7;text-align:center;background:rgba(17,17,17,.6);color:#fff}
.mang button.on{outline-color:var(--sel)}
.mview{display:flex}
.mview button{flex:1}
__BLUR_CSS__
.seo-intro{--si-max:var(--w)}
__SEO_CSS__
</style>
__FAQ_LD__
</head>
<body>
__UI_BAR__
<section class="wrap phead">
  <p class="eyebrow">__EYEBROW__</p>
  <h1>__H1__</h1>
  <p class="lead">__LEAD__</p>
  <ul class="stats">__STATS__</ul>
</section>

<div class="tools" id="tools">
  <div class="tools-in">
    <div class="chips" id="tabs" role="tablist"></div>
    <div class="trow">
      <label class="search">__SEARCH_ICON__<input id="q" type="search" autocomplete="off" data-pl-search></label>
      __TOGGLE__
      <button type="button" class="btn fbtn" id="ftog" aria-expanded="false" aria-controls="filters"><span id="ftogT"></span><b id="fn"></b></button>
      <span class="count" id="count" aria-live="polite"></span>
    </div>
    <div class="filters" id="filters">
      <select class="sel" id="cat"></select>
      <select class="sel" id="sort">
        <option value="series"></option><option value="pid"></option><option value="cat"></option><option value="name"></option>
      </select>
      <div class="seg" id="ang" role="group"></div>
      <div class="seg" id="view" role="group"><button type="button" data-v="pose" aria-pressed="true"></button><button type="button" data-v="card" aria-pressed="false"></button></div>
    </div>
  </div>
</div>

<main><div class="grid" id="grid"></div><button type="button" class="btn loadmore" id="load-more" hidden></button></main>
<footer class="foot">__FOOTER__</footer>
__SEO_INTRO__

<div class="modal" id="modal" role="dialog" aria-modal="true" aria-labelledby="mtitle">
  <div class="mbox">
    <button type="button" class="mclose" id="mclose">×</button>
    <div class="mimg">
      <div class="mstage" id="mstage">
        <img id="mimgLo" class="lo" alt="" aria-hidden="true">
        <img id="mimg" class="hi" alt="">
        <div class="cmp" id="cmp" aria-hidden="true">
          <img id="cmpA" alt=""><img id="cmpB" class="cb" alt=""><div class="ln"></div>
          <span class="tg a" id="cmpTa"></span><span class="tg b" id="cmpTb"></span>
          <input type="range" id="cmpR" min="0" max="100" value="50">
        </div>
      </div>
      <button type="button" class="mnav l" id="mprev">‹</button>
      <button type="button" class="mnav r" id="mnext">›</button>
    </div>
    <div class="mside">
      <div><h2 id="mtitle"></h2><div class="mid" id="mid"></div></div>
      <div class="seg mview" id="mview" role="group" hidden></div>
      <dl class="mkv" id="mkv"></dl>
      <div class="mang" id="mang"></div>
      <div class="macts">
        <a id="mdl" class="btn pri" href="#" download></a>
        <a id="mfull" class="btn" href="#" target="_blank" rel="noopener"></a>
        <button type="button" id="mcopy" class="btn ghost"></button>
      </div>
      <div class="hint" id="mhint"></div>
    </div>
  </div>
</div>
__UI_DIALOGS__
__UI_JS__
<script>
(function(){
const DB = __PAYLOAD__;
const POSES = DB.poses, SERIES = DB.series, CATS = DB.cats, ANGS = DB.angs;
const SZ = DB.seriesZh, CZ = DB.catZh, AZ = DB.angZh, UI = DB.ui;
const ADULT_MODE = '__ADULT_MODE__';     // hide：18+ 关闭时隐藏成人向；blur：模糊；none：本站没有成人向
const DL_ICON = __DL_ICON__;
const $ = s => document.querySelector(s);
const esc = s => String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const t = k => (UI[PL.lang] && UI[PL.lang][k] != null) ? UI[PL.lang][k] : (UI.zh[k] != null ? UI.zh[k] : k);
const isZh = () => PL.lang === 'zh';
const nS = s => isZh() ? (SZ[s]||s) : s, nC = c => isZh() ? (CZ[c]||c) : c, nA = a => isZh() ? (AZ[a]||a) : a;
const nN = p => isZh() ? (p.z||p.n) : p.n;

/* 图片路径：内联规则时按 系列/分類/编号/视角 拼；姿势模块再加版本前缀（线稿 / 深度图目录）。
   PATHS 标记之间的代码只依赖 DB，tests/run.py 单独执行它与 manifest 对照 */
const VARS = DB.vars || null;
let VAR = DB.variant || null;
const VSW = document.getElementById(VARS ? 'vsw' : '');   // 只有姿势模块有线稿 / 深度图开关
/*PATHS*/
const base = (p, v, kind) => DB.path
  ? (kind === 't' ? 'thumbs/' : 'img/') + p.s + '/' + p.c + '/' + p.p + '/' + v.a + '.' + (kind === 't' ? DB.path.tx : DB.path.fx)
  : v[kind];
const pre = k => VARS ? VARS[k || VAR].pre : '';
const thumbOf = (p, v, k) => pre(k) + base(p, v, 't');
const fullOf = (p, v, k) => pre(k) + base(p, v, 'f');
// img/a/b.png → mid/a/b.webp，规则与 tools/mid.py 的 mid_rel() 一致
const midOf = f => f.replace(/(^|\/)img\//, '$1mid/').replace(/\.[^./]+$/, '.webp');
const pathOf = (p, v) => [base(p, v, 't'), base(p, v, 'f')];
/*END PATHS*/

const PAGE_POSE = 60, PAGE_IMG = 120;
const S = {series:null, cat:null, ang:null, sort:'series', view:'pose', q:'', n:PAGE_POSE};
// 落地页「在画廊中查看」带过来的筛选：#series=…&cat=…
(function(){
  const h = new URLSearchParams(location.hash.slice(1));
  const s = h.get('series'); if (s && SERIES.includes(s)) S.series = s;
  const c = h.get('cat');    if (c && CATS.includes(c) && POSES.some(p => p.c === c && (!S.series || p.s === S.series))) S.cat = c;
})();
const visible = () => (PL.adult || ADULT_MODE !== 'hide') ? POSES : POSES.filter(p => !p.x);
const unblurred = new Set();

/* ══ 文案 ══ */
function applyText(){
  document.title = t('title');
  $('#q').placeholder = t('search');
  $('#ftogT').textContent = t('filter');
  ['series','pid','cat','name'].forEach((k,i) => { $('#sort').options[i].textContent = t('sort' + k[0].toUpperCase() + k.slice(1)); });
  $('#cat').ariaLabel = t('kCat'); $('#sort').ariaLabel = t('sortLabel');
  $('#view').children[0].textContent = t('viewPose'); $('#view').children[1].textContent = t('viewCard');
  $('#mhint').innerHTML = t('hint');
  $('#mdl').textContent = t('dlPng'); $('#mfull').textContent = t('openFull'); $('#mcopy').textContent = t('copyLink');
  $('#mclose').ariaLabel = t('close'); $('#mprev').ariaLabel = t('prev'); $('#mnext').ariaLabel = t('next');
  if (VARS){ $('#cmpTa').textContent = t('vLine'); $('#cmpTb').textContent = t('vDepth'); $('#cmpR').ariaLabel = t('compare'); }
}

/* ══ 系列标签 / 分类 / 视角 ══ */
function drawTabs(){
  const vis = visible();
  const mk = (k, label, n) => '<button type="button" class="chip" role="tab" data-s="'+esc(k||'')+'" aria-selected="'+(S.series===k)+'">'+
    esc(label)+'<small>'+n+'</small></button>';
  $('#tabs').innerHTML = mk(null, t('all'), vis.length) +
    SERIES.map(s => { const n = vis.filter(p=>p.s===s).length; return n ? mk(s, nS(s), n) : ''; }).join('');
}
$('#tabs').addEventListener('click', e => { const b = e.target.closest('[data-s]'); if (!b) return;
  S.series = b.dataset.s || null; S.cat = null; drawTabs(); drawCats(); draw(); });
function drawCats(){
  const sel = $('#cat'), pool = visible().filter(p=>!S.series||p.s===S.series), avail = CATS.filter(c=>pool.some(p=>p.c===c));
  sel.innerHTML = '<option value="">'+esc(t('catAll'))+' ('+pool.length+')</option>' +
    avail.map(c=>'<option value="'+esc(c)+'">'+esc(nC(c))+' ('+pool.filter(p=>p.c===c).length+')</option>').join('');
  if (S.cat && !avail.includes(S.cat)) S.cat = null;
  sel.value = S.cat || '';
}
function drawAng(){
  $('#ang').innerHTML = [['',t('angAll')],...ANGS.map(a=>[a,nA(a)])].map(([k,l]) =>
    '<button type="button" data-a="'+esc(k)+'" aria-pressed="'+((S.ang||'')===k)+'">'+esc(l)+'</button>').join('');
}
$('#ang').addEventListener('click', e => { const b = e.target.closest('[data-a]'); if (!b) return; S.ang = b.dataset.a || null; drawAng(); draw(); });
$('#view').addEventListener('click', e => { const b = e.target.closest('[data-v]'); if (!b) return; S.view = b.dataset.v;
  [...$('#view').children].forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false')); draw(); });
$('#sort').addEventListener('change', e => { S.sort = e.target.value; draw(); });
$('#cat').addEventListener('change', e => { S.cat = e.target.value || null; draw(); });
$('#ftog').addEventListener('click', () => { const o = $('#filters').classList.toggle('open'); $('#ftog').setAttribute('aria-expanded', o ? 'true' : 'false'); });
let tid = null;
$('#q').addEventListener('input', e => { clearTimeout(tid); tid = setTimeout(() => { S.q = e.target.value.trim().toLowerCase(); draw(); }, 130); });

/* ══ 过滤与排序 ══ */
const SI = s => { const i = SERIES.indexOf(s); return i < 0 ? 99 : i; };
const SORTERS = {
  series: (a,b) => (SI(a.s)-SI(b.s)) || a.p.localeCompare(b.p),
  pid:    (a,b) => a.p.localeCompare(b.p) || (SI(a.s)-SI(b.s)),
  cat:    (a,b) => nC(a.c).localeCompare(nC(b.c),'ja') || a.p.localeCompare(b.p),
  name:   (a,b) => nN(a).localeCompare(nN(b),'ja'),
};
const hay = p => (p.n+' '+p.z+' '+p.p+' '+p.c+' '+(CZ[p.c]||'')+' '+p.s+' '+(SZ[p.s]||'')).toLowerCase();
function hitPose(p){
  if (S.series && p.s !== S.series) return false;
  if (S.cat && p.c !== S.cat) return false;
  if (S.ang && !p.v.some(v => v.a === S.ang)) return false;
  return !S.q || hay(p).includes(S.q);
}
function badge(){ const n = [S.cat,S.ang].filter(Boolean).length + (S.view==='card'?1:0) + (S.sort!=='series'?1:0);
  const el = $('#fn'); el.textContent = n || ''; el.classList.toggle('on', n > 0); }

/* ══ 渲染 ══ */
const grid = $('#grid'), countEl = $('#count'), moreEl = $('#load-more');
let VIEW = [];
const pageSize = () => S.view === 'pose' ? PAGE_POSE : PAGE_IMG;
function count(){
  if (S.view === 'pose'){
    const ps = new Set(VIEW.map(o=>o.p)), m = [...ps].reduce((a,p)=>a+(S.ang?p.v.filter(v=>v.a===S.ang).length:p.v.length),0);
    countEl.innerHTML = t('countPose').replace('{n}', ps.size).replace('{m}', m);
  } else countEl.innerHTML = t('countImg').replace('{n}', VIEW.length);
}
function draw(keep){
  const ORD = visible().slice().sort(SORTERS[S.sort] || SORTERS.series).filter(hitPose);
  VIEW = S.view === 'pose'
    ? ORD.map(p => ({p, d:(S.ang && p.v.find(v=>v.a===S.ang)) || p.v[0]}))
    : ORD.flatMap(p => p.v.filter(v => !S.ang || v.a === S.ang).map(v => ({p, d:v})));
  count(); badge();
  if (!VIEW.length){
    const hidden = !PL.adult && ADULT_MODE === 'hide' && POSES.some(p => p.x && hitPose(p));
    grid.innerHTML = hidden
      ? '<div class="empty"><b>'+esc(t('adultEmptyTitle'))+'</b>'+esc(t('adultEmptyDesc'))+'<br><button type="button" class="btn pri" data-adult-go>'+esc(t('adultEmptyGo'))+'</button></div>'
      : '<div class="empty"><b>'+esc(t('emptyTitle'))+'</b>'+esc(t('emptyDesc'))+'</div>';
    moreEl.hidden = true; return;
  }
  S.n = keep ? Math.min(Math.max(S.n, pageSize()), VIEW.length) : pageSize();
  grid.innerHTML = VIEW.slice(0, S.n).map(card).join('');
  sweep(); syncMore();
}
function addMore(){
  if (S.n >= VIEW.length) return;
  const from = S.n; S.n = Math.min(S.n + pageSize(), VIEW.length);
  grid.insertAdjacentHTML('beforeend', VIEW.slice(from, S.n).map((o,k) => card(o, from+k)).join(''));
  sweep(); syncMore();
}
const sweep = () => grid.querySelectorAll('img').forEach(im => { if (im.complete && im.naturalWidth) done(im); });
function done(im){ im.classList.add('ld'); const ph = im.closest('.ph'); if (ph) ph.classList.add('done'); }
function syncMore(){ const rest = VIEW.length - S.n; moreEl.hidden = rest <= 0;
  moreEl.textContent = rest > 0 ? t(S.view === 'pose' ? 'morePose' : 'moreImg').replace('{n}', rest) : ''; }
function card({p, d}, i){
  const name = nN(p), file = p.p + '-' + d.a + (VAR === 'depth' ? '-depth' : '') + '__EXT__';
  const strip = S.view === 'pose' ? '<div class="strip">' + p.v.map(v =>
    '<button type="button" data-a="'+esc(v.a)+'" class="'+(v.a===d.a?'on':'')+'" title="'+esc(nA(v.a))+'" aria-label="'+esc(nA(v.a))+'">'+
    '<img loading="lazy" decoding="async" src="'+esc(thumbOf(p, v))+'" alt=""></button>').join('') + '</div>' : '';
  return '<article class="card'+(unblurred.has(p.p)?' unblur':'')+'" tabindex="0" data-i="'+i+'"'+(p.x?' data-x="1"':'')+' aria-label="'+esc(name+' '+p.p)+'">'+
    '<div class="ph"'+(p.x?' data-blur="'+esc(t('blurTap'))+'"':'')+'><img'+(i<12?' fetchpriority="high"':' loading="lazy"')+' decoding="async" src="'+esc(thumbOf(p, d))+'" alt="'+esc(name)+'">'+
      '<span class="badge">'+esc(S.view==='pose' ? p.p : nA(d.a))+'</span>'+
      '<a class="dl" href="'+esc(fullOf(p, d))+'" download="'+esc(file)+'" title="'+esc(t('dlOne'))+'" aria-label="'+esc(t('dlOne'))+'">'+DL_ICON+'</a></div>'+
    '<div class="info"><h3>'+esc(name)+'</h3><div class="sub">'+esc(nS(p.s)+' · '+nC(p.c)+(S.view==='card'?' · '+p.p:''))+'</div></div>'+strip+'</article>';
}
/* 切换线稿 / 深度图：只换已渲染图片的地址，不重画网格 */
function swapVariant(k){
  if (!VARS || k === VAR) return;
  VAR = k;
  VSW.setAttribute('aria-checked', VAR === 'depth' ? 'true' : 'false');
  grid.querySelectorAll('.card').forEach(c => {
    const o = VIEW[+c.dataset.i]; if (!o) return;
    const main = c.querySelector('.ph>img'), cur = c.querySelector('.strip .on');
    const v = cur ? o.p.v.find(x => x.a === cur.dataset.a) || o.d : o.d;
    main.classList.remove('ld'); main.closest('.ph').classList.remove('done'); main.src = thumbOf(o.p, v);
    c.querySelectorAll('.strip button').forEach(b => { const x = o.p.v.find(y => y.a === b.dataset.a); b.querySelector('img').src = thumbOf(o.p, x); });
    const dl = c.querySelector('.dl'); dl.href = fullOf(o.p, v); dl.download = o.p.p + '-' + v.a + (VAR === 'depth' ? '-depth' : '') + '__EXT__';
  });
  if (modal.classList.contains('open')){ if (MV !== 'cmp') MV = VAR; showM(); }
}
if (VSW) VSW.addEventListener('click', () => swapVariant(VAR === 'depth' ? 'line' : 'depth'));
document.addEventListener('keydown', e => {
  if (!VARS || e.ctrlKey || e.metaKey || e.altKey || (PL.top() && PL.top() !== modal)) return;
  const el = document.activeElement; if (el && /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) return;
  if (e.key === 'd' || e.key === 'D') swapVariant(VAR === 'depth' ? 'line' : 'depth');
});

/* ══ 卡片交互 ══ */
grid.addEventListener('mouseover', e => {
  const b = e.target.closest('.strip button'); if (!b) return;
  const c = b.closest('.card'), o = VIEW[+c.dataset.i]; if (!o) return;
  const v = o.p.v.find(x => x.a === b.dataset.a); if (!v) return;
  c.querySelector('.ph>img').src = thumbOf(o.p, v);
  c.querySelectorAll('.strip button').forEach(x => x.classList.toggle('on', x === b));
});
moreEl.onclick = addMore;
if ('IntersectionObserver' in window) new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) addMore(); }, {rootMargin:'800px'}).observe(moreEl);
grid.addEventListener('load', e => { if (e.target.tagName === 'IMG') done(e.target); }, true);
grid.addEventListener('error', e => { if (e.target.tagName === 'IMG') done(e.target); }, true);
grid.addEventListener('click', e => {
  if (e.target.closest('.dl')) return;
  const c = e.target.closest('.card'); if (!c) return;
  const o = VIEW[+c.dataset.i]; if (!o) return;
  const b = e.target.closest('.strip button');
  openM(+c.dataset.i, (b && o.p.v.find(x => x.a === b.dataset.a)) || o.d, c);
});
// 只有焦点在卡片本身时 Enter / 空格打开大图；卡片里的下载链接、视角按钮照常
grid.addEventListener('keydown', e => {
  if ((e.key !== 'Enter' && e.key !== ' ') || !e.target.classList.contains('card')) return;
  e.preventDefault(); const o = VIEW[+e.target.dataset.i]; if (o) openM(+e.target.dataset.i, o.d, e.target);
});
let hoverT = 0;
const cardView = e => { const c = e.target.closest('.card'), o = c && VIEW[+c.dataset.i]; if (!o) return null;
  const b = e.target.closest('.strip button'); return [o.p, (b && o.p.v.find(x => x.a === b.dataset.a)) || o.d]; };
grid.addEventListener('pointerover', e => { const pv = cardView(e); clearTimeout(hoverT); if (pv) hoverT = setTimeout(() => warm(midOf(fullOf(...pv))), 120); });
grid.addEventListener('pointerout', () => clearTimeout(hoverT));
grid.addEventListener('pointerdown', e => { const pv = cardView(e); if (pv) warm(midOf(fullOf(...pv))); });

/* ══ 大图 ══ */
const modal = $('#modal'), mimg = $('#mimg'), mimgLo = $('#mimgLo'), mstage = $('#mstage'), mwrap = document.querySelector('.mimg');
let loT = 0, M = {i:0, d:null}, MV = VAR;   // MV：大图显示 line / depth / cmp
const warmed = new Set(), warmRefs = [];
function warm(u){ if (!u || warmed.has(u)) return; warmed.add(u); const im = new Image(); im.decoding = 'async'; im.src = u;
  warmRefs.push(im); if (warmRefs.length > 8) warmRefs.shift(); }
function fitStage(){
  const nw = mimgLo.naturalWidth || 3, nh = mimgLo.naturalHeight || 4, bw = mwrap.clientWidth, bh = mwrap.clientHeight;
  if (!bw || !bh) return; const s = Math.min(bw/nw, bh/nh);
  mstage.style.width = Math.round(nw*s) + 'px'; mstage.style.height = Math.round(nh*s) + 'px';
}
addEventListener('resize', () => { if (modal.classList.contains('open')) fitStage(); });
function openM(i, v, opener){
  M = {i, d:v}; MV = VAR;
  const o = VIEW[i];
  if (ADULT_MODE === 'blur' && o && o.p.x){ unblurred.add(o.p.p); grid.querySelectorAll('.card[data-i="'+i+'"]').forEach(c => c.classList.add('unblur')); }
  PL.openDialog(modal, opener, () => grid.querySelector('.card[data-i="'+M.i+'"]') || grid);
  showM();
}
modal.addEventListener('pl:close', () => { mimg.onerror = null; mimg.removeAttribute('src'); });
function drawMView(){
  const box = $('#mview'); if (!VARS){ box.hidden = true; return; }
  box.hidden = false;
  box.innerHTML = [['line', t('vLine')], ['depth', t('vDepth')], ['cmp', t('compare')]].map(([k, l]) =>
    '<button type="button" data-mv="'+k+'" aria-pressed="'+(MV===k)+'">'+esc(l)+'</button>').join('');
}
$('#mview').addEventListener('click', e => { const b = e.target.closest('[data-mv]'); if (!b) return;
  MV = b.dataset.mv; if (MV !== 'cmp') swapVariant(MV); showM(); });
function showM(){
  const o = VIEW[M.i]; if (!o) return;
  const p = o.p, v = M.d || o.d, k = MV === 'cmp' ? VAR : MV;
  mimg.onload = mimg.onerror = null;
  mimg.classList.add('nt'); mimg.classList.remove('rd'); void mimg.offsetWidth; mimg.classList.remove('nt');
  mimgLo.src = thumbOf(p, v, k); fitStage(); mimgLo.onload = fitStage;
  mimg.alt = nN(p) + ' ' + nA(v.a);
  const settle = () => { mimg.classList.add('rd'); clearTimeout(loT); loT = setTimeout(() => { mimgLo.style.opacity = '0'; }, 340); };
  mimgLo.style.opacity = '1'; mimg.onload = settle;
  const f = fullOf(p, v, k);
  mimg.onerror = () => { mimg.onerror = null; mimg.src = f; };
  mimg.src = midOf(f);
  if (mimg.complete && mimg.naturalWidth) settle();
  p.v.forEach(x => warm(midOf(fullOf(p, x, k))));
  mstage.classList.toggle('cmpon', MV === 'cmp');
  if (VARS){
    $('#cmpA').src = midOf(fullOf(p, v, 'line')); $('#cmpB').src = midOf(fullOf(p, v, 'depth'));
    $('#cmp').setAttribute('aria-hidden', MV === 'cmp' ? 'false' : 'true');
    if (MV === 'cmp') warm(midOf(fullOf(p, v, 'depth')));
  }
  drawMView();
  $('#mtitle').textContent = nN(p);
  $('#mid').textContent = p.p + ' · ' + nA(v.a) + (VARS ? ' · ' + t(k === 'depth' ? 'vDepth' : 'vLine') : '');
  $('#mfull').href = f; $('#mdl').href = f;
  $('#mdl').setAttribute('download', p.p + '-' + v.a + (k === 'depth' ? '-depth' : '') + '__EXT__');
  $('#mkv').innerHTML = [[t('kSeries'), nS(p.s)], [t('kCat'), nC(p.c)], [t('kPid'), p.p], [t('kAng'), nA(v.a)],
    [t('kAngN'), p.v.length + ' ' + t('angUnit')]].map(([a, b]) => '<dt>'+esc(a)+'</dt><dd>'+esc(b)+'</dd>').join('');
  $('#mang').innerHTML = p.v.map(x => '<button type="button" data-a="'+esc(x.a)+'" class="'+(x.a===v.a?'on':'')+'" aria-label="'+esc(nA(x.a))+'">'+
    '<img src="'+esc(thumbOf(p, x, k))+'" alt=""><span>'+esc(nA(x.a))+'</span></button>').join('');
  $('#mprev').disabled = $('#mnext').disabled = p.v.length < 2;
}
/* 对比：拖动或用键盘调 range，--x 控制上层深度图的裁切位置 */
const cmp = $('#cmp'), cmpR = $('#cmpR');
const setX = x => { cmp.style.setProperty('--x', x + '%'); };
cmpR.addEventListener('input', () => setX(cmpR.value));
if (VARS) setX(50);
$('#mang').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return;
  const o = VIEW[M.i], v = o.p.v.find(x => x.a === b.dataset.a); if (v){ M.d = v; showM(); } });
$('#mprev').onclick = () => stepA(-1); $('#mnext').onclick = () => stepA(1);
$('#mclose').onclick = () => PL.closeDialog(modal);
modal.addEventListener('click', e => { if (e.target === modal) PL.closeDialog(modal); });
function stepA(n){ const o = VIEW[M.i]; if (!o) return; const order = o.p.v; if (order.length < 2) return;
  const cur = order.findIndex(x => x.a === (M.d || o.d).a); M.d = order[(cur + n + order.length) % order.length]; showM(); }
function stepP(n){ const j = M.i + n; if (j < 0 || j >= VIEW.length) return;
  const np = VIEW[j].p, same = np.v.find(x => x.a === (M.d || VIEW[M.i].d).a); M = {i:j, d: same || np.v[0]}; showM(); }
document.addEventListener('keydown', e => {
  if (PL.top() !== modal || e.target === cmpR) return;
  if (e.key === 'ArrowRight'){ e.preventDefault(); stepA(1); }
  else if (e.key === 'ArrowLeft'){ e.preventDefault(); stepA(-1); }
  else if (e.key === 'ArrowDown'){ e.preventDefault(); stepP(1); }
  else if (e.key === 'ArrowUp'){ e.preventDefault(); stepP(-1); }
});
let tx = null;
mwrap.addEventListener('touchstart', e => { if (MV === 'cmp') return; tx = e.touches[0].clientX; }, {passive:true});
mwrap.addEventListener('touchend', e => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx;
  if (Math.abs(dx) > 40) stepA(dx < 0 ? 1 : -1); tx = null; }, {passive:true});
$('#mcopy').addEventListener('click', function(){
  const o = VIEW[M.i]; if (!o) return;
  const url = new URL($('#mfull').getAttribute('href'), location.href).href;
  const fin = ok => { this.textContent = ok ? t('copied') : t('copyFail'); setTimeout(() => { this.textContent = t('copyLink'); }, 1400); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(() => fin(true)).catch(() => fin(false)); else fin(false);
});

/* ══ 偏好变化 ══ */
addEventListener('pl:lang', () => {
  applyText(); drawTabs(); drawCats(); drawAng(); count(); syncMore();
  // 只更新卡片文字，不重画网格：保留已加载的页数与滚动位置
  grid.querySelectorAll('.card').forEach(c => { const o = VIEW[+c.dataset.i]; if (!o) return;
    c.querySelector('h3').textContent = nN(o.p);
    c.querySelector('.sub').textContent = nS(o.p.s) + ' · ' + nC(o.p.c) + (S.view === 'card' ? ' · ' + o.p.p : '');
    c.querySelector('.ph>img').alt = nN(o.p); c.ariaLabel = nN(o.p) + ' ' + o.p.p;
    const dl = c.querySelector('.dl'); dl.title = dl.ariaLabel = t('dlOne');
    if (S.view === 'card') c.querySelector('.badge').textContent = nA(o.d.a);
    if (o.p.x) c.querySelector('.ph').dataset.blur = t('blurTap');
    c.querySelectorAll('.strip button').forEach(b => { b.title = b.ariaLabel = nA(b.dataset.a); }); });
  if (!grid.querySelector('.card')) draw();
  if (modal.classList.contains('open')) showM();
});
addEventListener('pl:adult', () => {
  if (ADULT_MODE !== 'hide') return;
  if (S.series && !visible().some(p => p.s === S.series)) S.series = null;
  drawTabs(); drawCats(); draw();
  if (modal.classList.contains('open') && !VIEW[M.i]) PL.closeDialog(modal);
});

applyText(); drawTabs(); drawCats(); drawAng(); draw();
})();
</script>
</body>
</html>"""
