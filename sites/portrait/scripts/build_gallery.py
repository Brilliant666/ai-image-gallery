# -*- coding: utf-8 -*-
"""构建人像集（AI 模特脸库，中文版）

产出：
  index.html                单文件画廊（数据内嵌，file:// 可直接打开）
  data/portrait-zh.json     中文记录
  data/meta.json            分区 / 发型 / 风格元数据
  data/translations.csv     日⇄中对照表
  robots.txt / sitemap.xml / 404.html

页面外观、顶部栏与偏好来自 shared/ui.py。

用法：
  SITE_URL=https://your-domain.com python build_gallery.py
"""
import json, os, sys, csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "shared"))
from translations import (HAIR_ZH, HAIR_ORDER, SECTION_ZH, SECTION_NOTE_ZH, SECTION_NOTE_JA,
                          STYLE_ZH, UI, hair_zh, style_zh)
import landing, ui  # noqa: E402

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(root, "manifest.json"), encoding="utf-8"))

SITE_URL = os.environ.get("SITE_URL", "https://example.com").rstrip("/")

# ── 组装数据 ──────────────────────────────────────────
# items：完整记录，给落地页与数据导出用
items = [{"i": r["id"], "s": r["分区"], "hj": r["发型"], "hz": hair_zh(r["发型"]), "sj": r["风格"], "sz": style_zh(r["风格"]),
          "t": r["thumb_path"], "f": r["full_path"], "w": r["宽"], "h": r["高"], "b": r["原图字节"]} for r in rows]
# 页面内联数据：路径按 thumbs/<id>.webp、img/<id>.png 在页面里拼；发型、风格改成查表下标（省掉约 200 KB）
RULE = all(x["t"] == f'thumbs/{x["i"]}.webp' and x["f"] == f'img/{x["i"]}.png' for x in items)
HAIRS = [h for h in HAIR_ORDER if any(x["hj"] == h for x in items)]
STYLES = sorted({x["sj"] for x in items if x["sj"]})
inline = []
for x in items:
    o = {"i": x["i"], "s": 0 if x["s"] == "face" else 1, "h": HAIRS.index(x["hj"]), "w": x["w"], "ht": x["h"], "b": x["b"]}
    if x["sj"]:
        o["y"] = STYLES.index(x["sj"])
    if not RULE:
        o.update(t=x["t"], f=x["f"])
    inline.append(o)

payload = json.dumps({
    "items": inline, "rule": RULE, "ui": UI,
    "hairs": [[h, hair_zh(h)] for h in HAIRS], "styles": [[s, style_zh(s)] for s in STYLES],
    "secNote": {"zh": SECTION_NOTE_ZH, "ja": SECTION_NOTE_JA},
}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

html = r"""<!doctype html>
<html lang="zh-CN" data-theme="light" data-lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>人像参考图库：1499 张 CC0 AI 人像 · photoai.life</title>
<meta name="description" content="让 AI 生成的角色保持同一张脸的人像参考图库：1499 张 AI 生成人像，面部 893 张（正面、纯色背景）、造型 606 张，可按发型筛选，CC0 免费商用，中日双语。">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="__SITE__/">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="photoai.life">
<meta property="og:title" content="AI 绘画角色脸部一致性参考 · 1499 张 CC0 人像">
<meta property="og:description" content="让 AI 生成的角色保持同一张脸。面部与造型两个分区，可按发型筛选，CC0 免费商用。">
<meta property="og:url" content="__SITE__/">
<meta property="og:image" content="__SITE__/og-cover.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="zh_CN">
<meta property="og:locale:alternate" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="AI 绘画角色脸部一致性参考 · 1499 张 CC0 人像">
<meta name="twitter:description" content="面部与造型两个分区，可按发型筛选，CC0 免费商用。">
<meta name="twitter:image" content="__SITE__/og-cover.jpg">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ImageGallery","name":"人像集 · AI 模特脸库","alternateName":"AI Portrait Gallery 中文版","url":"__SITE__/","inLanguage":["zh-CN","ja"],"numberOfItems":1499,"about":"AI 绘画角色脸部一致性参考","isAccessibleForFree":true,"license":"https://creativecommons.org/publicdomain/zero/1.0/","acquireLicensePage":"https://ai-portrait-gallery.pages.dev/","copyrightNotice":"CC0 1.0 (あぎ)","creditText":"あぎ / AI Portrait Gallery","creator":{"@type":"Person","name":"あぎ","url":"https://x.com/agi_aibusi"}}
</script>
__UI_HEAD__
__UI_CSS__
<style>
.ph{aspect-ratio:4/5}
.ph>img{object-fit:cover}
.card .size{font-size:11.5px;color:var(--mu);font-variant-numeric:tabular-nums}
.secnote{margin:0;font-size:12.5px;color:var(--mu)}
.mbox .lb-note{font-size:12px;color:var(--mu)}
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
    <div class="chips" id="sections" role="tablist">
      <button type="button" class="chip" role="tab" data-sec="face" id="seg-face" aria-controls="grid"></button>
      <button type="button" class="chip" role="tab" data-sec="styling" id="seg-styling" aria-controls="grid"></button>
    </div>
    <div class="trow">
      <div class="chips" id="filters" role="group"></div>
      <span class="count" id="count" aria-live="polite"></span>
    </div>
    <p id="sec-note" class="secnote"></p>
  </div>
</div>

<main id="gallery">
  <div class="grid" id="grid"></div>
  <p id="empty" class="empty" hidden></p>
  <button type="button" id="more" class="btn loadmore" hidden></button>
  <div id="sentinel" aria-hidden="true"></div>
</main>
<footer class="foot">__FOOTER__</footer>
__SEO_INTRO__

<div class="modal" id="lightbox" role="dialog" aria-modal="true" aria-labelledby="lb-label">
  <div class="mbox">
    <button type="button" class="mclose" id="lb-close">×</button>
    <div class="mimg" id="lb-wrap">
      <div class="mstage" id="lb-stage">
        <img id="lb-img-lo" class="lo" alt="" aria-hidden="true">
        <img id="lb-img" class="hi" alt="">
      </div>
      <button type="button" class="mnav l" id="lb-prev">‹</button>
      <button type="button" class="mnav r" id="lb-next">›</button>
    </div>
    <div class="mside">
      <h2 id="lb-label"></h2>
      <dl class="mkv" id="lb-kv"></dl>
      <div class="macts">
        <a id="lb-dl" class="btn pri" href="#" download></a>
        <a id="lb-full" class="btn" href="#" target="_blank" rel="noopener"></a>
        <button type="button" id="lb-copy" class="btn ghost"></button>
        <span class="lb-note" id="lb-note"></span>
      </div>
      <div class="hint" id="lb-hint"></div>
    </div>
  </div>
</div>
__UI_DIALOGS__
__UI_JS__
<script>
(function(){
const DB = __PAYLOAD__;
const ITEMS = DB.items, UI = DB.ui, HAIRS = DB.hairs, STYLES = DB.styles;
const DL_ICON = __DL_ICON__;
const PAGE = 60;
const $ = s => document.querySelector(s);
const esc = s => String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const t = k => (UI[PL.lang] && UI[PL.lang][k] != null) ? UI[PL.lang][k] : (UI.zh[k] != null ? UI.zh[k] : k);
const L = () => PL.lang === 'ja' ? 0 : 1;
const SEC = ['face', 'styling'];
const hairName = it => HAIRS[it.h][L()];
const styleName = it => it.y == null ? '' : STYLES[it.y][L()];
const labelOf = it => { const s = styleName(it); return s ? hairName(it) + '・' + s : hairName(it); };
const fmt = n => Number(n).toLocaleString('zh-CN');
const mb = b => (b / 1048576).toFixed(1) + ' MB';
/*PATHS*/  // 由 tests/run.py 单独执行，与 manifest 对照
const TH = it => DB.rule ? 'thumbs/' + it.i + '.webp' : it.t;
const FU = it => DB.rule ? 'img/' + it.i + '.png' : it.f;
const pathOf = it => [TH(it), FU(it)];
/*END PATHS*/
const dlName = it => (it.s === 0 ? 'ai-face-' : 'ai-styling-') + it.i + '.png';

const S = { sec: 0, hair: -1, n: PAGE };
// 落地页「在画廊中查看」带过来的筛选：#sec=styling&hair=ロング
(function(){
  const m = /(?:^#|&)sec=([^&]*)/.exec(location.hash); if (m && SEC.includes(m[1])) S.sec = SEC.indexOf(m[1]);
  const h = /(?:^#|&)hair=([^&]*)/.exec(location.hash);
  if (h){ try { const v = decodeURIComponent(h[1]); const i = HAIRS.findIndex(x => x[0] === v); if (i >= 0) S.hair = i; } catch(_){} }
})();
function writeHash(){
  const p = [];
  if (S.sec) p.push('sec=' + SEC[S.sec]);
  if (S.hair >= 0) p.push('hair=' + encodeURIComponent(HAIRS[S.hair][0]));
  history.replaceState(null, '', p.length ? '#' + p.join('&') : location.pathname + location.search);
}

const grid = $('#grid'), countEl = $('#count'), moreEl = $('#more'), emptyEl = $('#empty');
function applyText(){
  document.title = (PL.lang === 'ja' ? 'ポートレート参考画像集' : '人像参考图库') + ' · photoai.life';
  $('#lb-dl').textContent = t('download'); $('#lb-full').textContent = t('openFull'); $('#lb-copy').textContent = t('copyLink');
  $('#lb-close').ariaLabel = t('close'); $('#lb-prev').ariaLabel = t('prev'); $('#lb-next').ariaLabel = t('next');
  $('#lb-hint').innerHTML = t('hint'); $('#sections').ariaLabel = t('secLabel'); $('#filters').ariaLabel = t('hairLabel');
}
const pool = () => ITEMS.filter(it => it.s === S.sec);
const view = () => S.hair < 0 ? pool() : pool().filter(it => it.h === S.hair);
function drawSections(){
  [['face', 'secFace'], ['styling', 'secStyling']].forEach(([k, lab], i) => {
    const b = $('#seg-' + k), on = S.sec === i;
    b.setAttribute('aria-selected', on ? 'true' : 'false'); b.tabIndex = on ? 0 : -1;
    b.innerHTML = esc(t(lab)) + '<small>' + fmt(ITEMS.filter(x => x.s === i).length) + '</small>';
  });
  $('#sec-note').textContent = DB.secNote[PL.lang][SEC[S.sec]] || '';
}
function drawFilters(){
  const c = new Array(HAIRS.length).fill(0); pool().forEach(it => c[it.h]++);
  $('#filters').innerHTML = '<button type="button" class="chip" data-hair="-1" aria-pressed="'+(S.hair<0)+'">'+esc(t('all'))+'<small>'+fmt(pool().length)+'</small></button>' +
    HAIRS.map((h, i) => c[i] ? '<button type="button" class="chip" data-hair="'+i+'" aria-pressed="'+(S.hair===i)+'">'+esc(h[L()])+'<small>'+fmt(c[i])+'</small></button>' : '').join('');
}
function card(it, i){
  return '<article class="card" tabindex="0" data-i="'+i+'" aria-label="'+esc(labelOf(it))+'">'+
    '<div class="ph"><img'+(i<12?' fetchpriority="high"':' loading="lazy"')+' decoding="async" src="'+esc(TH(it))+'" alt="'+esc(labelOf(it))+'">'+
      '<a class="dl" href="'+esc(FU(it))+'" download="'+esc(dlName(it))+'" title="'+esc(t('dlOne')+' · '+mb(it.b))+'" aria-label="'+esc(t('dlOne')+' · '+mb(it.b))+'">'+DL_ICON+'</a></div>'+
    '<div class="info"><h3>'+esc(hairName(it))+'</h3><div class="sub">'+esc(styleName(it) || (it.w + '×' + it.ht))+'</div></div></article>';
}
let VIEW = [];
function draw(){
  VIEW = view();
  countEl.textContent = fmt(VIEW.length) + ' ' + t('countUnit');
  if (!VIEW.length){ grid.innerHTML = ''; emptyEl.hidden = false; emptyEl.textContent = t('empty'); moreEl.hidden = true; return; }
  emptyEl.hidden = true; S.n = PAGE;
  grid.innerHTML = VIEW.slice(0, S.n).map(card).join(''); sweep(); syncMore();
}
function addMore(){ if (S.n >= VIEW.length) return; const from = S.n; S.n = Math.min(S.n + PAGE, VIEW.length);
  grid.insertAdjacentHTML('beforeend', VIEW.slice(from, S.n).map((it, k) => card(it, from + k)).join('')); sweep(); syncMore(); }
function done(im){ im.classList.add('ld'); const ph = im.closest('.ph'); if (ph) ph.classList.add('done'); }
const sweep = () => grid.querySelectorAll('img').forEach(im => { if (im.complete && im.naturalWidth) done(im); });
function syncMore(){ const rest = VIEW.length - S.n; moreEl.hidden = rest <= 0; moreEl.textContent = rest > 0 ? t('more').replace('{n}', fmt(rest)) : ''; }

/* 分区标签：方向键在两个标签间移动（tabindex 只给选中的那个） */
$('#sections').addEventListener('click', e => { const b = e.target.closest('[data-sec]'); if (!b) return;
  S.sec = SEC.indexOf(b.dataset.sec); S.hair = -1; drawSections(); drawFilters(); draw(); writeHash(); });
$('#sections').addEventListener('keydown', e => {
  if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
  e.preventDefault(); S.sec = S.sec ? 0 : 1; S.hair = -1; drawSections(); drawFilters(); draw(); writeHash();
  $('#seg-' + SEC[S.sec]).focus();
});
$('#filters').addEventListener('click', e => { const b = e.target.closest('[data-hair]'); if (!b) return;
  S.hair = +b.dataset.hair; drawFilters(); draw(); writeHash(); });

/* 大图 */
const lb = $('#lightbox'), img = $('#lb-img'), lo = $('#lb-img-lo'), stage = $('#lb-stage'), wrapEl = $('#lb-wrap');
let LB = 0, loT = 0;
const midOf = f => f.replace(/^img\//, 'mid/').replace(/\.[^./]+$/, '.webp');
const warmed = new Set(), warmRefs = [];
function warm(u){ if (!u || warmed.has(u)) return; warmed.add(u); const im = new Image(); im.decoding = 'async'; im.src = u;
  warmRefs.push(im); if (warmRefs.length > 6) warmRefs.shift(); }
function fit(){ const nw = lo.naturalWidth || 400, nh = lo.naturalHeight || 500, bw = wrapEl.clientWidth, bh = wrapEl.clientHeight;
  if (!bw || !bh) return; const s = Math.min(bw/nw, bh/nh); stage.style.width = Math.round(nw*s)+'px'; stage.style.height = Math.round(nh*s)+'px'; }
addEventListener('resize', () => { if (lb.classList.contains('open')) fit(); });
function openLb(i, opener){ LB = i; PL.openDialog(lb, opener, () => grid.querySelector('.card[data-i="'+LB+'"]') || grid); showLb(); }
lb.addEventListener('pl:close', () => { img.onerror = null; img.removeAttribute('src'); });
function showLb(){
  const it = VIEW[LB]; if (!it) return;
  img.onload = img.onerror = null; img.classList.add('nt'); img.classList.remove('rd'); void img.offsetWidth; img.classList.remove('nt');
  lo.src = TH(it); fit(); lo.onload = fit; img.alt = labelOf(it); lo.style.opacity = '1';
  $('#lb-label').textContent = labelOf(it);
  $('#lb-kv').innerHTML = [[t(it.s ? 'secStyling' : 'secFace'), it.w + '×' + it.ht], ['PNG', mb(it.b)], ['ID', it.i]]
    .map(([a,b]) => '<dt>'+esc(a)+'</dt><dd>'+esc(b)+'</dd>').join('');
  $('#lb-dl').href = FU(it); $('#lb-dl').setAttribute('download', dlName(it)); $('#lb-full').href = FU(it); $('#lb-note').textContent = '';
  const settle = () => { img.classList.add('rd'); clearTimeout(loT); loT = setTimeout(() => { lo.style.opacity = '0'; }, 340); };
  img.onload = settle;
  img.onerror = () => { img.onerror = () => { $('#lb-note').textContent = t('noFull'); }; img.src = FU(it); };
  img.src = midOf(FU(it)); if (img.complete && img.naturalWidth) settle();
  [VIEW[LB + 1], VIEW[LB - 1]].forEach(n => n && warm(midOf(FU(n))));
  $('#lb-prev').disabled = LB <= 0; $('#lb-next').disabled = LB >= VIEW.length - 1;
}
function stepLb(d){ const n = LB + d; if (n < 0 || n >= VIEW.length) return; LB = n; if (LB >= S.n) addMore(); showLb(); }
grid.addEventListener('load', e => { if (e.target.tagName === 'IMG') done(e.target); }, true);
grid.addEventListener('error', e => { if (e.target.tagName === 'IMG') done(e.target); }, true);
grid.addEventListener('click', e => { if (e.target.closest('.dl')) return; const c = e.target.closest('.card'); if (c) openLb(+c.dataset.i, c); });
grid.addEventListener('keydown', e => { if ((e.key !== 'Enter' && e.key !== ' ') || !e.target.classList.contains('card')) return;
  e.preventDefault(); openLb(+e.target.dataset.i, e.target); });
let hoverT = 0;
const cardItem = e => { const c = e.target.closest('.card'); return c && VIEW[+c.dataset.i]; };
grid.addEventListener('pointerover', e => { const it = cardItem(e); clearTimeout(hoverT); if (it) hoverT = setTimeout(() => warm(midOf(FU(it))), 120); });
grid.addEventListener('pointerout', () => clearTimeout(hoverT));
grid.addEventListener('pointerdown', e => { const it = cardItem(e); if (it) warm(midOf(FU(it))); });
moreEl.addEventListener('click', addMore);
if ('IntersectionObserver' in window) new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) addMore(); }, {rootMargin:'800px'}).observe($('#sentinel'));
$('#lb-close').addEventListener('click', () => PL.closeDialog(lb));
$('#lb-prev').addEventListener('click', () => stepLb(-1)); $('#lb-next').addEventListener('click', () => stepLb(1));
lb.addEventListener('click', e => { if (e.target === lb) PL.closeDialog(lb); });
document.addEventListener('keydown', e => { if (PL.top() !== lb) return;
  if (e.key === 'ArrowLeft'){ e.preventDefault(); stepLb(-1); } else if (e.key === 'ArrowRight'){ e.preventDefault(); stepLb(1); } });
let tx = null;
wrapEl.addEventListener('touchstart', e => { tx = e.touches[0].clientX; }, {passive:true});
wrapEl.addEventListener('touchend', e => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx; if (Math.abs(dx) > 40) stepLb(dx < 0 ? 1 : -1); tx = null; }, {passive:true});
$('#lb-copy').addEventListener('click', function(){ const it = VIEW[LB]; if (!it) return;
  const url = new URL(FU(it), location.href).href, btn = this;
  const fin = ok => { btn.textContent = ok ? t('copied') : t('copyFail'); setTimeout(() => { btn.textContent = t('copyLink'); }, 1400); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(() => fin(true)).catch(() => fin(false)); else fin(false); });

// 切换语言只更新文字，保留已加载的页数与滚动位置
addEventListener('pl:lang', () => {
  applyText(); drawSections(); drawFilters(); countEl.textContent = fmt(VIEW.length) + ' ' + t('countUnit'); syncMore();
  grid.querySelectorAll('.card').forEach(c => { const it = VIEW[+c.dataset.i]; if (!it) return;
    c.querySelector('h3').textContent = hairName(it); c.querySelector('.sub').textContent = styleName(it) || (it.w + '×' + it.ht);
    c.ariaLabel = labelOf(it); c.querySelector('.ph>img').alt = labelOf(it);
    const dl = c.querySelector('.dl'); dl.title = dl.ariaLabel = t('dlOne') + ' · ' + mb(it.b); });
  if (lb.classList.contains('open')) showLb();
});

applyText(); drawSections(); drawFilters(); draw();
})();
</script>
</body>
</html>"""

# 静态落地页（分区、分区 × 发型、发型风格）与主页里不依赖 JS 的介绍、FAQ
import seo  # noqa: E402
landing_urls, seo_intro, FAQ = seo.build(root, SITE_URL, items)
n_face = sum(1 for x in items if x["s"] == "face")
stats = [(f"{len(items):,}", "张人像", "枚"), (f"{n_face:,}", "张面部", "フェイス"),
         (f"{len(items) - n_face:,}", "张造型", "スタイリング"), ("CC0", "可商用", "商用可")]
for k, v in {
    "__UI_HEAD__": ui.head_script(), "__UI_CSS__": ui.head_css(), "__UI_BAR__": ui.bar("portrait"),
    "__UI_DIALOGS__": ui.dialogs(ui.PORTRAIT_KEYS), "__UI_JS__": ui.body_script(),
    "__SEO_INTRO__": seo_intro, "__SEO_CSS__": landing.SEO_INTRO_CSS, "__FAQ_LD__": landing.faq_ld_script(FAQ),
    "__EYEBROW__": ui.bi(UI["zh"]["eyebrow"], UI["ja"]["eyebrow"]), "__H1__": ui.bi(UI["zh"]["h1"], UI["ja"]["h1"]),
    "__LEAD__": ui.bi(UI["zh"]["lead"], UI["ja"]["lead"]),
    "__STATS__": "".join(f'<li><b>{v}</b>{ui.bi(zh, ja)}</li>' for v, zh, ja in stats),
    "__FOOTER__": f'<span class="zh">{UI["zh"]["footer"]}</span><span class="ja">{UI["ja"]["footer"]}</span>',
    "__DL_ICON__": json.dumps(ui.DL_ICON),
}.items():
    html = html.replace(k, v)
html = html.replace("__PAYLOAD__", payload).replace("__SITE__", SITE_URL)
out = os.path.join(root, "index.html")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(html)
print("wrote index.html %.1f KB" % (os.path.getsize(out) / 1024))
print("items:", len(items), "| face:", n_face, "| styling:", len(items) - n_face, "| paths:", "rule" if RULE else "inline")
print("SITE_URL =", SITE_URL)

# ── 导出数据 ──────────────────────────────────────────
data_dir = os.path.join(root, "data")
zh = [{"id": it["i"], "分区": it["s"], "分区_zh": SECTION_ZH.get(it["s"], it["s"]),
       "发型": it["hj"], "发型_zh": it["hz"], "风格": it["sj"], "风格_zh": it["sz"],
       "宽": it["w"], "高": it["h"], "缩略图": it["t"], "原图": it["f"]} for it in items]
with open(os.path.join(data_dir, "portrait-zh.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(zh, f, ensure_ascii=False, indent=1)

meta = {
    "site": "AI PORTRAIT / FACE REFERENCE",
    "source": "https://ai-portrait-gallery.pages.dev/",
    "author": "あぎ (@agi_aibusi)",
    "license": "CC0 1.0",
    "items": len(items),
    "face": n_face,
    "styling": len(items) - n_face,
    "分区": [{"key": k, "zh": v} for k, v in SECTION_ZH.items()],
    "发型": [{"ja": h, "zh": HAIR_ZH[h], "count": sum(1 for i in items if i["hj"] == h)} for h in HAIRS],
    "风格数": len(STYLES),
}
with open(os.path.join(data_dir, "meta.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)

with open(os.path.join(data_dir, "translations.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["字段", "日文原文", "中文译文"])
    for k, v in SECTION_ZH.items():
        w.writerow(["section", k, v])
    for k, v in HAIR_ZH.items():
        w.writerow(["hair", k, v])
    for k, v in STYLE_ZH.items():
        w.writerow(["style", k, v])
print("wrote data/portrait-zh.json, data/meta.json, data/translations.csv")

# ── SEO 附属 ──────────────────────────────────────────
with open(os.path.join(root, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL)
landing.sitemap(SITE_URL, landing_urls, os.path.join(root, "sitemap.xml"))
with open(os.path.join(root, "404.html"), "w", encoding="utf-8", newline="\n") as f:
    f.write(ui.page_404("/"))
print("wrote robots.txt, sitemap.xml, 404.html")
