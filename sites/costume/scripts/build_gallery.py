# -*- coding: utf-8 -*-
"""构建服装集（COSTUME-DB-01）

产出：
  index.html                单文件画廊（数据内嵌，file:// 可直接打开）
  data/costume-zh.json      中文记录（供复用/校对）
  data/meta.json            分类 / 标签元数据
  data/translations.csv     日⇄中 + 英⇄中 对照表
  robots.txt / sitemap.xml / 404.html

页面外观、顶部栏、偏好与 18+ 来自 shared/ui.py。

用法：
  SITE_URL=https://your-domain.com python build_gallery.py
"""
import json, os, sys, csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "shared"))
from translations import CAT_ZH, TAG_ZH, TAG_JA, TAG_GROUPS, UI
import adult, landing, ui  # noqa: E402

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(root, "manifest.json"), encoding="utf-8"))

# 站点地址：部署前用环境变量覆盖，否则 canonical / sitemap 会指向占位域名
SITE_URL = os.environ.get("SITE_URL", "https://example.com").rstrip("/")

# 成人向的两类排在最后：18+ 打开后也不会出现在列表最前面
CAT_ORDER = ["春", "夏", "秋", "冬", "水着", "パーティ", "ランジェリー", "セクシー"]

# 成人向服装（sites.json 的 adult 规则）：不进落地页；画廊里 18+ 关闭时隐藏
ADULT_RULE = adult.rules("costume")
adult_ids = {r["id"] for r in rows if adult.is_adult(r, ADULT_RULE)}
UI = adult.ui(UI)

items = [{"i": r["id"], "c": r["分类"], "t": r["标签"], "th": r["thumb_path"], "im": r["img_path"], "pg": r["png_path"],
          **({"x": 1} if r["id"] in adult_ids else {})} for r in rows]
# 三档路径都是 <档>/<分类>/<id>.<扩展名>：页面里按规则拼，内联数据只留 id、分类、标签（省掉约 140 KB）
RULE = all(x["th"] == f'thumbs/{x["c"]}/{x["i"]}.webp' and x["im"] == f'img/{x["c"]}/{x["i"]}.webp'
           and x["pg"] == f'png/{x["c"]}/{x["i"]}.png' for x in items)
inline = [{k: v for k, v in x.items() if not RULE or k not in ("th", "im", "pg")} for x in items]

cats = [c for c in CAT_ORDER if any(x["c"] == c for x in items)]
groups = [{"k": k, "ja": ja, "zh": zh, "tags": ts} for k, ja, zh, ts in TAG_GROUPS]

payload = json.dumps({
    "items": inline, "cats": cats, "groups": groups, "rule": RULE,
    "catZh": CAT_ZH, "tagZh": TAG_ZH, "tagJa": TAG_JA, "ui": UI,
}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

html = r"""<!doctype html>
<html lang="zh-CN" data-theme="light" data-lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>AI 绘画服装参考图库：1407 套服装、86 个标签组合筛选 · 服装集</title>
<meta name="description" content="AI 绘画服装参考图库中文版：1407 套不含真人的服装图、8 个分类、86 个标签，按颜色・单品・鞋袜・配饰・材质・长度组合筛选，标签可直接作提示词，中日双语。">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="__SITE__/">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="服装集 COSTUME-DB-01">
<meta property="og:title" content="AI 绘画服装参考图库 · 1407 套服装 / 86 个标签">
<meta property="og:description" content="AI 绘画服装参考图库中文版。按颜色・单品・鞋袜・配饰・材质・长度六组标签组合筛选。">
<meta property="og:url" content="__SITE__/">
<meta property="og:image" content="__SITE__/og-cover.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="zh_CN">
<meta property="og:locale:alternate" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="AI 绘画服装参考图库 · 1407 套服装">
<meta name="twitter:description" content="AI 绘画服装参考图库中文版，按材质・颜色・单品标签组合筛选。">
<meta name="twitter:image" content="__SITE__/og-cover.jpg">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ImageGallery","name":"服装集 COSTUME-DB-01","alternateName":"AI Costume Gallery 中文版","url":"__SITE__/","inLanguage":["zh-CN","ja"],"numberOfItems":1407,"about":"AI 绘画・服装设计・穿搭参考","isAccessibleForFree":true,"copyrightNotice":"© ギア (@giaaibusi)","creditText":"ギア / AI Costume Gallery","creator":{"@type":"Person","name":"ギア","url":"https://x.com/giaaibusi"}}
</script>
__UI_HEAD__
__UI_CSS__
<style>
.ph{aspect-ratio:2/3}
.tagbar{position:absolute;left:0;right:0;bottom:0;padding:26px 10px 9px;display:flex;flex-wrap:wrap;gap:4px;
  background:linear-gradient(transparent,rgba(8,10,14,.78));opacity:0;transition:opacity .18s;pointer-events:none}
.card:hover .tagbar,.card:focus-visible .tagbar{opacity:1}
.tagbar i{font-style:normal;font-size:10.5px;padding:2px 7px;border-radius:999px;background:rgba(255,255,255,.18);color:#fff;white-space:nowrap}
.fpanel{display:none;margin-top:2px;padding:14px 16px;border-radius:18px;background:var(--sf);max-height:min(56vh,560px);overflow:auto}
.fpanel.open{display:block}
.fp-top{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.fp-top .btn{margin-left:auto}
.tgrp{margin-bottom:12px}.tgrp:last-child{margin-bottom:0}
.tgrp h4{margin:0 0 8px;font-size:12px;font-weight:700;letter-spacing:.06em;color:var(--mu)}
.tgrp .chips{flex-wrap:wrap;overflow:visible}
.fpanel .chip{background:var(--bg2);height:32px;font-size:13px;padding:0 12px}
.fpanel .chip[aria-pressed="true"]{background:var(--sel);color:var(--on-sel)}
.fbtn[aria-expanded="true"]{background:var(--sel);color:var(--on-sel)}
.fbtn b{min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:var(--ac);color:#fff;font-size:11px;display:none;place-items:center}
.fbtn b.on{display:inline-grid}
.mtags{display:flex;flex-wrap:wrap;gap:6px}
.mtags button{height:32px;padding:0 12px;border:0;border-radius:999px;background:var(--sf);color:var(--tx);font-size:12.5px;cursor:pointer}
.mtags button:hover{background:var(--sf2)}
@media(max-width:640px){.fpanel{max-height:60vh;padding:12px}.fpanel .chip{height:36px}}
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
      <button type="button" class="btn fbtn" id="ftog" aria-expanded="false" aria-controls="fpanel"><span id="ftogT"></span><b id="fn"></b></button>
      <span class="count" id="count" aria-live="polite"></span>
    </div>
    <div class="fpanel" id="fpanel">
      <div class="fp-top">
        <select class="sel" id="sort"><option value="cat"></option><option value="id"></option><option value="tag"></option></select>
        <button type="button" class="btn ghost" id="clearTags"></button>
      </div>
      <div id="tgrps"></div>
    </div>
  </div>
</div>

<main><div class="grid" id="grid"></div><button type="button" class="btn loadmore" id="more" hidden></button></main>
<footer class="foot">__FOOTER__</footer>
__SEO_INTRO__

<div class="modal" id="modal" role="dialog" aria-modal="true" aria-labelledby="mid">
  <div class="mbox">
    <button type="button" class="mclose" id="mclose">×</button>
    <div class="mimg">
      <div class="mstage" id="mstage">
        <img id="mimgLo" class="lo" alt="" aria-hidden="true">
        <img id="mimg" class="hi" alt="">
      </div>
      <button type="button" class="mnav l" id="mprev">‹</button>
      <button type="button" class="mnav r" id="mnext">›</button>
    </div>
    <div class="mside">
      <h2 id="mid"></h2>
      <dl class="mkv" id="mkv"></dl>
      <div class="mtags" id="mtags"></div>
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
const ITEMS = DB.items, CATS = DB.cats, GROUPS = DB.groups;
const CZ = DB.catZh, TZ = DB.tagZh, TJ = DB.tagJa, UI = DB.ui;
const DL_ICON = __DL_ICON__;
const $ = s => document.querySelector(s);
const esc = s => String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const t = k => (UI[PL.lang] && UI[PL.lang][k] != null) ? UI[PL.lang][k] : (UI.zh[k] != null ? UI.zh[k] : k);
const isZh = () => PL.lang === 'zh';
const nC = c => isZh() ? (CZ[c]||c) : c;
const nT = x => isZh() ? (TZ[x]||x) : (TJ[x]||x);
const gName = g => isZh() ? g.zh : g.ja;
// 三档路径：<档>/<分类>/<id>.<扩展名>（规则不成立时内联数据里带 th / im / pg）；PATHS 段由 tests/run.py 单独执行核对
/*PATHS*/
const TH = x => DB.rule ? 'thumbs/' + x.c + '/' + x.i + '.webp' : x.th;
const IM = x => DB.rule ? 'img/' + x.c + '/' + x.i + '.webp' : x.im;
const PG = x => DB.rule ? 'png/' + x.c + '/' + x.i + '.png' : x.pg;
const pathOf = x => [TH(x), IM(x), PG(x)];
/*END PATHS*/

const PAGE = 120;
const S = {cat:null, sort:'cat', q:'', tags:new Set(), n:PAGE};
// 落地页「在画廊中查看」带过来的筛选：#cat=春 / #tag=knit（可多个，逗号分隔）
(function(){
  const h = new URLSearchParams(location.hash.slice(1));
  const c = h.get('cat'); if (c && CATS.includes(c)) S.cat = c;
  const all = new Set(GROUPS.flatMap(g => g.tags));
  (h.get('tag') || '').split(',').filter(x => all.has(x)).forEach(x => S.tags.add(x));
})();
const visible = () => PL.adult ? ITEMS : ITEMS.filter(x => !x.x);
const visCats = () => CATS.filter(c => visible().some(x => x.c === c));

function applyText(){
  document.title = t('title');
  $('#q').placeholder = t('search'); $('#ftogT').textContent = t('filter');
  ['sortCat','sortId','sortTag'].forEach((k,i) => { $('#sort').options[i].textContent = t(k); });
  $('#sort').ariaLabel = t('sortLabel'); $('#clearTags').textContent = t('clearTags');
  $('#mhint').innerHTML = t('hint');
  $('#mdl').textContent = t('dlPng'); $('#mfull').textContent = t('openFull'); $('#mcopy').textContent = t('copyLink');
  $('#mclose').ariaLabel = t('close'); $('#mprev').ariaLabel = t('prev'); $('#mnext').ariaLabel = t('next');
}

function drawTabs(){
  const vis = visible();
  const mk = (k, label, n) => '<button type="button" class="chip" role="tab" data-c="'+esc(k||'')+'" aria-selected="'+(S.cat===k)+'">'+esc(label)+'<small>'+n+'</small></button>';
  $('#tabs').innerHTML = mk(null, t('all'), vis.length) + visCats().map(c => mk(c, nC(c), vis.filter(x=>x.c===c).length)).join('');
}
$('#tabs').addEventListener('click', e => { const b = e.target.closest('[data-c]'); if (!b) return; S.cat = b.dataset.c || null; drawTabs(); draw(); });

function drawTagGroups(){
  const vis = visible();
  $('#tgrps').innerHTML = GROUPS.map(g => {
    // 18+ 关闭时只出现在成人向服装上的标签（例如 bra）不显示；已选中的保留，方便取消
    const avail = g.tags.filter(tg => vis.some(x => x.t.includes(tg)) || S.tags.has(tg));
    if (!avail.length) return '';
    return '<div class="tgrp"><h4>'+esc(gName(g))+'</h4><div class="chips">' + avail.map(tg =>
      '<button type="button" class="chip" data-t="'+esc(tg)+'" title="'+esc(tg)+'" aria-pressed="'+S.tags.has(tg)+'">'+esc(nT(tg))+
      '<small>'+vis.filter(x=>x.t.includes(tg)).length+'</small></button>').join('') + '</div></div>';
  }).join('');
}
$('#tgrps').addEventListener('click', e => { const b = e.target.closest('[data-t]'); if (!b) return;
  const tg = b.dataset.t; S.tags.has(tg) ? S.tags.delete(tg) : S.tags.add(tg);
  b.setAttribute('aria-pressed', S.tags.has(tg) ? 'true' : 'false'); draw(); });
const ftog = $('#ftog'), fpanel = $('#fpanel');
ftog.addEventListener('click', () => { const o = fpanel.classList.toggle('open'); ftog.setAttribute('aria-expanded', o ? 'true' : 'false'); });
$('#clearTags').addEventListener('click', () => { S.tags.clear(); drawTagGroups(); draw(); });
$('#sort').addEventListener('change', e => { S.sort = e.target.value; draw(); });
let tid = null;
$('#q').addEventListener('input', e => { clearTimeout(tid); tid = setTimeout(() => { S.q = e.target.value.trim().toLowerCase(); draw(); }, 130); });

function hit(x){
  if (S.cat && x.c !== S.cat) return false;
  for (const tg of S.tags) if (!x.t.includes(tg)) return false;
  if (S.q){ const h = (x.i+' '+x.c+' '+(CZ[x.c]||'')+' '+x.t.join(' ')+' '+x.t.map(z=>(TZ[z]||'')+' '+(TJ[z]||'')).join(' ')).toLowerCase();
    if (!h.includes(S.q)) return false; }
  return true;
}
function badge(){ const n = S.tags.size; const el = $('#fn'); el.textContent = n || ''; el.classList.toggle('on', n > 0); }
const CI = c => { const i = CATS.indexOf(c); return i < 0 ? 99 : i; };
const SORTERS = { cat:(a,b)=>(CI(a.c)-CI(b.c))||a.i.localeCompare(b.i), id:(a,b)=>a.i.localeCompare(b.i), tag:(a,b)=>b.t.length-a.t.length||a.i.localeCompare(b.i) };

const grid = $('#grid'), countEl = $('#count'), moreEl = $('#more');
let VIEW = [];
const count = () => { countEl.innerHTML = S.tags.size ? t('count').replace('{n}', VIEW.length).replace('{t}', S.tags.size) : t('countNoTag').replace('{n}', VIEW.length); };
function draw(){
  VIEW = visible().filter(hit).sort(SORTERS[S.sort] || SORTERS.cat);
  count(); badge();
  if (!VIEW.length){
    const hidden = !PL.adult && ITEMS.some(x => x.x && hit(x));
    grid.innerHTML = hidden
      ? '<div class="empty"><b>'+esc(t('adultEmptyTitle'))+'</b>'+esc(t('adultEmptyDesc'))+'<br><button type="button" class="btn pri" data-adult-go>'+esc(t('adultEmptyGo'))+'</button></div>'
      : '<div class="empty"><b>'+esc(t('emptyTitle'))+'</b>'+esc(t('emptyDesc'))+'</div>';
    moreEl.hidden = true; return;
  }
  S.n = PAGE;
  grid.innerHTML = VIEW.slice(0, S.n).map(card).join('');
  sweep(); syncMore();
}
function addMore(){ if (S.n >= VIEW.length) return; const from = S.n; S.n = Math.min(S.n + PAGE, VIEW.length);
  grid.insertAdjacentHTML('beforeend', VIEW.slice(from, S.n).map((x,k) => card(x, from+k)).join('')); sweep(); syncMore(); }
function done(im){ im.classList.add('ld'); const ph = im.closest('.ph'); if (ph) ph.classList.add('done'); }
const sweep = () => grid.querySelectorAll('img').forEach(im => { if (im.complete && im.naturalWidth) done(im); });
function syncMore(){ const rest = VIEW.length - S.n; moreEl.hidden = rest <= 0; moreEl.textContent = rest > 0 ? t('more').replace('{n}', rest) : ''; }
const tagHtml = x => x.t.slice(0, 6).map(tg => '<i>'+esc(nT(tg))+'</i>').join('') + (x.t.length > 6 ? '<i>+'+(x.t.length-6)+'</i>' : '');
function card(x, i){
  return '<article class="card" tabindex="0" data-i="'+i+'" aria-label="'+esc(x.i+' '+nC(x.c))+'">'+
    '<div class="ph"><img'+(i<12?' fetchpriority="high"':' loading="lazy"')+' decoding="async" src="'+esc(TH(x))+'" alt="'+esc(x.i)+'">'+
      '<a class="dl" href="'+esc(PG(x))+'" download="'+esc(x.i+'.png')+'" title="'+esc(t('dlOne'))+'" aria-label="'+esc(t('dlOne'))+'">'+DL_ICON+'</a>'+
      '<div class="tagbar">'+tagHtml(x)+'</div></div>'+
    '<div class="info"><h3>'+esc(x.i)+'</h3><div class="sub">'+esc(nC(x.c)+' · '+x.t.length+' '+t('tagUnit'))+'</div></div></article>';
}
moreEl.onclick = addMore;
if ('IntersectionObserver' in window) new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) addMore(); }, {rootMargin:'800px'}).observe(moreEl);
grid.addEventListener('load', e => { if (e.target.tagName === 'IMG') done(e.target); }, true);
grid.addEventListener('error', e => { if (e.target.tagName === 'IMG') done(e.target); }, true);
grid.addEventListener('click', e => { if (e.target.closest('.dl')) return; const c = e.target.closest('.card'); if (c) openM(+c.dataset.i, c); });
// 只有焦点在卡片本身时 Enter / 空格打开大图；卡片里的下载链接照常
grid.addEventListener('keydown', e => { if ((e.key !== 'Enter' && e.key !== ' ') || !e.target.classList.contains('card')) return;
  e.preventDefault(); openM(+e.target.dataset.i, e.target); });

/* 大图 */
const modal = $('#modal'), mimg = $('#mimg'), mimgLo = $('#mimgLo'), mstage = $('#mstage'), mwrap = document.querySelector('.mimg');
let loT = 0, MI = 0;
const warmed = new Set(), warmRefs = [];
function warm(u){ if (!u || warmed.has(u)) return; warmed.add(u); const im = new Image(); im.decoding = 'async'; im.src = u;
  warmRefs.push(im); if (warmRefs.length > 6) warmRefs.shift(); }
let hoverT = 0;
const cardItem = e => { const c = e.target.closest('.card'); return c && VIEW[+c.dataset.i]; };
grid.addEventListener('pointerover', e => { const x = cardItem(e); clearTimeout(hoverT); if (x) hoverT = setTimeout(() => warm(IM(x)), 120); });
grid.addEventListener('pointerout', () => clearTimeout(hoverT));
grid.addEventListener('pointerdown', e => { const x = cardItem(e); if (x) warm(IM(x)); });
function fitStage(){ const nw = mimgLo.naturalWidth || 360, nh = mimgLo.naturalHeight || 540, bw = mwrap.clientWidth, bh = mwrap.clientHeight;
  if (!bw || !bh) return; const s = Math.min(bw/nw, bh/nh); mstage.style.width = Math.round(nw*s)+'px'; mstage.style.height = Math.round(nh*s)+'px'; }
addEventListener('resize', () => { if (modal.classList.contains('open')) fitStage(); });
function openM(i, opener){ MI = i; PL.openDialog(modal, opener, () => grid.querySelector('.card[data-i="'+MI+'"]') || grid); showM(); }
modal.addEventListener('pl:close', () => { mimg.removeAttribute('src'); });
function showM(){
  const x = VIEW[MI]; if (!x) return;
  mimg.onload = null; mimg.classList.add('nt'); mimg.classList.remove('rd'); void mimg.offsetWidth; mimg.classList.remove('nt');
  mimgLo.src = TH(x); fitStage(); mimgLo.onload = fitStage; mimg.alt = x.i; mimgLo.style.opacity = '1';
  const settle = () => { mimg.classList.add('rd'); clearTimeout(loT); loT = setTimeout(() => { mimgLo.style.opacity = '0'; }, 340); };
  mimg.onload = settle; mimg.src = IM(x); if (mimg.complete && mimg.naturalWidth) settle();
  [VIEW[MI+1], VIEW[MI-1]].forEach(n => n && warm(IM(n)));
  $('#mid').textContent = x.i + ' · ' + nC(x.c);
  $('#mfull').href = PG(x); $('#mdl').href = PG(x); $('#mdl').setAttribute('download', x.i + '.png');
  $('#mkv').innerHTML = [[t('kCat'), nC(x.c)], [t('kId'), x.i], [t('kTagN'), x.t.length + ' ' + t('tagUnit')]]
    .map(([a,b]) => '<dt>'+esc(a)+'</dt><dd>'+esc(b)+'</dd>').join('');
  $('#mtags').innerHTML = x.t.map(tg => '<button type="button" data-t="'+esc(tg)+'" title="'+esc(tg)+'">'+esc(nT(tg))+'</button>').join('');
  $('#mprev').disabled = MI <= 0; $('#mnext').disabled = MI >= VIEW.length - 1;
}
$('#mtags').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return;
  PL.closeDialog(modal); S.tags.add(b.dataset.t); drawTagGroups(); draw(); });
$('#mprev').onclick = () => step(-1); $('#mnext').onclick = () => step(1);
$('#mclose').onclick = () => PL.closeDialog(modal);
modal.addEventListener('click', e => { if (e.target === modal) PL.closeDialog(modal); });
// 翻到还没渲染的那一页时先追加卡片，关闭大图后焦点能回到对应的卡片
function step(n){ const j = MI + n; if (j < 0 || j >= VIEW.length) return; MI = j; if (MI >= S.n) addMore(); showM(); }
document.addEventListener('keydown', e => { if (PL.top() !== modal) return;
  if (e.key === 'ArrowRight'){ e.preventDefault(); step(1); } else if (e.key === 'ArrowLeft'){ e.preventDefault(); step(-1); } });
let tx = null;
mwrap.addEventListener('touchstart', e => { tx = e.touches[0].clientX; }, {passive:true});
mwrap.addEventListener('touchend', e => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx; if (Math.abs(dx) > 40) step(dx < 0 ? 1 : -1); tx = null; }, {passive:true});
$('#mcopy').addEventListener('click', function(){ const x = VIEW[MI]; if (!x) return;
  const url = new URL(PG(x), location.href).href;
  const fin = ok => { this.textContent = ok ? t('copied') : t('copyFail'); setTimeout(() => { this.textContent = t('copyLink'); }, 1400); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(() => fin(true)).catch(() => fin(false)); else fin(false); });

// 切换语言只更新文字，保留已加载的页数与滚动位置
addEventListener('pl:lang', () => {
  applyText(); drawTabs(); drawTagGroups(); count(); syncMore();
  grid.querySelectorAll('.card').forEach(c => { const x = VIEW[+c.dataset.i]; if (!x) return;
    c.querySelector('.sub').textContent = nC(x.c) + ' · ' + x.t.length + ' ' + t('tagUnit');
    c.ariaLabel = x.i + ' ' + nC(x.c);
    const dl = c.querySelector('.dl'); dl.title = dl.ariaLabel = t('dlOne');
    c.querySelector('.tagbar').innerHTML = tagHtml(x); });
  if (!grid.querySelector('.card')) draw();
  if (modal.classList.contains('open')) showM();
});
addEventListener('pl:adult', () => {
  if (S.cat && !visCats().includes(S.cat)) S.cat = null;
  drawTabs(); drawTagGroups(); draw();
  if (modal.classList.contains('open') && !VIEW[MI]) PL.closeDialog(modal);
});

applyText(); drawTabs(); drawTagGroups(); draw();
})();
</script>
</body>
</html>"""

# 静态落地页（分类 + 标签，成人向服装不进落地页）与主页里不依赖 JS 的介绍、FAQ
import seo  # noqa: E402
landing_urls, seo_intro, FAQ = seo.build(root, SITE_URL, items, cats, adult_ids)
n_tags = len({tg for x in items for tg in x["t"]})
stats = [(f"{len(items):,}", "套服装", "着の衣装"), (f"{len(items) * 3:,}", "个文件", "ファイル"), (str(n_tags), "个标签", "タグ")]
for k, v in {
    "__UI_HEAD__": ui.head_script(), "__UI_CSS__": ui.head_css(), "__UI_BAR__": ui.bar("costume"),
    "__UI_DIALOGS__": ui.dialogs(ui.COSTUME_KEYS), "__UI_JS__": ui.body_script(),
    "__SEO_INTRO__": seo_intro, "__SEO_CSS__": landing.SEO_INTRO_CSS, "__FAQ_LD__": landing.faq_ld_script(FAQ),
    "__EYEBROW__": ui.bi(UI["zh"]["eyebrow"], UI["ja"]["eyebrow"]), "__H1__": ui.bi(UI["zh"]["h1"], UI["ja"]["h1"]),
    "__LEAD__": ui.bi(UI["zh"]["sub1"], UI["ja"]["sub1"]),
    "__STATS__": "".join(f'<li><b>{v}</b>{ui.bi(zh, ja)}</li>' for v, zh, ja in stats),
    "__FOOTER__": f'<span class="zh">{UI["zh"]["footer"]}</span><span class="ja">{UI["ja"]["footer"]}</span>',
    "__SEARCH_ICON__": ui.SEARCH_ICON, "__DL_ICON__": json.dumps(ui.DL_ICON),
}.items():
    html = html.replace(k, v)
html = html.replace("__PAYLOAD__", payload).replace("__SITE__", SITE_URL)
out = os.path.join(root, "index.html")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(html)
print("wrote index.html", "%.1f KB" % (os.path.getsize(out) / 1024))
print("items:", len(items), "| cats:", len(cats), "| groups:", len(groups), "| paths:", "rule" if RULE else "inline")

# ── 导出可复用的数据文件 ─────────────────────────────
data_dir = os.path.join(root, "data")
os.makedirs(data_dir, exist_ok=True)

zh = [{"id": x["i"], "分类": x["c"], "分类_zh": CAT_ZH.get(x["c"], x["c"]), "标签": x["t"],
       "标签_zh": [TAG_ZH.get(t, t) for t in x["t"]], "标签_ja": [TAG_JA.get(t, t) for t in x["t"]],
       "缩略图": x["th"], "中图": x["im"], "原图": x["pg"]} for x in items]
with open(os.path.join(data_dir, "costume-zh.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(zh, f, ensure_ascii=False, indent=1)

meta = {
    "site": "COSTUME-DB-01",
    "source": "https://ai-costume-gallery.pages.dev/",
    "author": "ギア (@giaaibusi)",
    "items": len(items),
    "images": len(items) * 3,
    "分类": [{"ja": c, "zh": CAT_ZH.get(c, c), "items": sum(1 for x in items if x["c"] == c)} for c in cats],
    "标签分组": [{"key": g["k"], "ja": g["ja"], "zh": g["zh"],
                  "tags": [{"en": t, "ja": TAG_JA.get(t, t), "zh": TAG_ZH.get(t, t)} for t in g["tags"]]} for g in groups],
}
with open(os.path.join(data_dir, "meta.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)

with open(os.path.join(data_dir, "translations.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["字段", "原文", "日文", "中文"])
    for k, v in CAT_ZH.items():
        w.writerow(["カテゴリ", k, k, v])
    for k, v in TAG_ZH.items():
        w.writerow(["キーワード", k, TAG_JA.get(k, k), v])
print("wrote data/costume-zh.json, data/meta.json, data/translations.csv")

# ── SEO 附属文件 ─────────────────────────────────────
with open(os.path.join(root, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL)
landing.sitemap(SITE_URL, landing_urls, os.path.join(root, "sitemap.xml"))
with open(os.path.join(root, "404.html"), "w", encoding="utf-8", newline="\n") as f:
    f.write(ui.page_404("/"))
print("wrote robots.txt, sitemap.xml, 404.html")
print("SITE_URL =", SITE_URL)
