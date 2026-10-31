# -*- coding: utf-8 -*-
"""配方：跨图库挑选人像、服装、姿势各一项，拼成中英文提示词，或下载一张参考拼图

五个子站同源，配方存在 localStorage 的 pl.recipe 里，各页共用、其他标签页实时同步。
每项只存渲染与拼提示词需要的字段，路径是相对站点根的（例如 "pose/thumbs/…"），任何一页都能显示，
不依赖其他站的内联数据：
  {k:'portrait'|'costume'|'pose', id, site, th, im, n:{zh,ja,en}, kw?, v?, ang?:{zh,ja,en}, at}
成人向条目不能加入（页面在加入前就拦下；这里读取时也再过滤一次）。

页面这样用（PL.recipe 由本文件的 JS 提供）：
  PL.recipe.items()                    当前配方
  PL.recipe.has(k, id)                 是否已加入
  PL.recipe.toggle(item, opener)       加入 / 移除；同一类已有另一项时替换
  addEventListener('pl:recipe', …)     配方变化（本页或其他标签页）
页面在大图里放一个 data-recipe 按钮，自己决定 item 怎么生成。
"""
from html import escape

import ui

# 画风预设：拼在提示词末尾（中、英两套；none 表示不加）
STYLES = [
    ("none", "无画风（跟随参考）", "スタイル指定なし", "", ""),
    ("photo", "写实人像摄影", "リアルなポートレート写真",
     "写实人像摄影，85mm 镜头，柔和自然光，真实的皮肤与布料质感。",
     "photorealistic portrait photography, 85mm lens, soft natural light, realistic skin and fabric texture"),
    ("fashion", "时尚杂志", "ファッション誌",
     "时尚杂志大片，干净的摄影棚背景，柔光，突出服装剪裁。",
     "fashion editorial photo, clean studio backdrop, soft key light, emphasis on garment cut and fit"),
    ("anime", "日系动漫插画", "アニメ調イラスト",
     "日系动漫插画，干净的线条与赛璐璐上色，色彩通透。",
     "Japanese anime illustration, clean line art, cel shading, vivid clear colors"),
    ("semireal", "2.5D 游戏立绘", "2.5D ゲーム立ち絵",
     "2.5D 半写实游戏角色立绘，细腻厚涂光影。",
     "2.5D semi-realistic game character art, painterly rendering, detailed lighting"),
    ("3d", "3D 角色渲染", "3D キャラクターレンダー",
     "3D 角色渲染，次表面散射皮肤，电影级布光。",
     "3D character render, subsurface scattering skin, cinematic lighting"),
    ("sheet", "角色设定图（白底）", "キャラクター設定画（白背景）",
     "角色设定图，纯白背景，全身站姿，均匀光照，清楚展示服装结构。",
     "character design sheet, plain white background, full body, even lighting, clear view of outfit construction"),
    ("film", "胶片质感", "フィルム写真",
     "35mm 胶片摄影质感，轻微颗粒，柔和暖色调。",
     "35mm film photography, subtle grain, soft warm tones"),
]

CSS = r"""
/* 配方：右下角胶囊 + 底部面板 */
.rc-fab{position:fixed;right:18px;bottom:18px;z-index:26;display:none;align-items:center;gap:8px;height:48px;padding:0 18px 0 8px;border:0;
  border-radius:999px;background:var(--sel);color:var(--on-sel);font-size:14px;font-weight:700;cursor:pointer;box-shadow:var(--sh2)}
.rc-fab.on{display:inline-flex}
.rc-fab .st{display:flex}
.rc-fab .st img,.rc-fab .st i{width:32px;height:32px;margin-left:-10px;border-radius:50%;object-fit:cover;background:var(--imgbg);
  border:2px solid var(--sel);display:block}
.rc-fab .st :first-child{margin-left:0}
.rc-fab .st i{display:grid;place-items:center;font-style:normal;font-size:12px;color:var(--mu)}
.rc-fab b{font-variant-numeric:tabular-nums;opacity:.7;font-weight:600}
.rc-fab.bump{animation:rc-bump .45s var(--ease)}
@keyframes rc-bump{40%{transform:scale(1.08)}}
.totop.lift{bottom:78px}
.rc-wrap{position:fixed;inset:0;z-index:70;display:flex;align-items:flex-end;justify-content:center;background:var(--scrim);
  backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px)}
.rc-wrap[hidden]{display:none}
.rc-pan{width:min(980px,100%);max-height:min(88vh,860px);overflow:auto;background:var(--bg2);border-radius:24px 24px 0 0;box-shadow:var(--sh3);
  padding:18px 20px calc(18px + env(safe-area-inset-bottom));animation:rc-up .28s var(--ease)}
@keyframes rc-up{from{transform:translateY(24px);opacity:.4}}
.rc-hd{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.rc-hd h3{margin:0;font-size:18px}
.rc-hd .sp{flex:1}
.rc-x{width:40px;height:40px;border:0;border-radius:50%;background:var(--sf);color:var(--tx);font-size:20px;cursor:pointer}
.rc-slots{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.rc-slot{position:relative;display:flex;flex-direction:column;min-width:0;border-radius:18px;background:var(--sf);overflow:hidden}
.rc-slot .im{position:relative;aspect-ratio:4/5;background:var(--imgbg)}
.rc-slot .im img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
.rc-slot .tx{padding:10px 12px 12px;min-width:0}
.rc-slot .k{font-size:12px;font-weight:700;letter-spacing:.06em;color:var(--mu)}
.rc-slot .nm{margin-top:2px;font-size:14px;font-weight:600;line-height:1.4;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;
  -webkit-line-clamp:2;-webkit-box-orient:vertical}
.rc-slot .rm{position:absolute;top:8px;right:8px;width:36px;height:36px;border:0;border-radius:50%;background:rgba(255,255,255,.9);color:#111;
  font-size:18px;cursor:pointer;box-shadow:var(--sh1)}
.rc-slot .rm::before{content:"";position:absolute;inset:-2px}
.rc-slot.vac .im{display:grid;place-items:center;color:var(--mu);font-size:13px;text-align:center;padding:12px}
.rc-slot.vac a{color:var(--ac);font-weight:600}
.rc-opts{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center;margin:16px 0 10px}
.rc-opts label{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--mu)}
.rc-pv{width:100%;min-height:120px;max-height:260px;margin:0;padding:12px 14px;border:0;border-radius:14px;background:var(--sf);color:var(--tx);
  font:13px/1.75 var(--mono);white-space:pre-wrap;overflow:auto;resize:vertical}
.rc-acts{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.rc-acts .btn{height:42px}
.rc-note{margin:10px 0 0;font-size:12.5px;color:var(--mu);line-height:1.8}
/* 大图与卡片上的「加入配方」 */
.btn[data-recipe][aria-pressed="true"]{background:var(--ac);color:var(--on-ac)}
.btn[data-recipe]:disabled{opacity:.45;cursor:not-allowed}
.macts:has([data-recipe]) .btn.pri,.macts .btn[data-recipe]{flex:1 1 calc(50% - 4px)}
/* 卡片上的「+」：桌面悬停出现，已加入的常亮 */
.rc-add{position:absolute;right:6px;top:48px;width:40px;height:40px;padding:2px;border:0;border-radius:50%;display:grid;place-items:center;
  background:rgba(255,255,255,.9);background-clip:content-box;color:#111;cursor:pointer;opacity:0;transform:scale(.9);transition:.2s var(--ease);
  filter:drop-shadow(0 1px 2px rgba(0,0,0,.12))}
.rc-add svg{width:17px;height:17px}
.card:hover .rc-add,.rc-add:focus-visible{opacity:1;transform:none}
.rc-add[aria-pressed="true"]{opacity:1;transform:none;background-color:var(--ac);color:#fff}
@media (hover:none){.rc-add:not([aria-pressed="true"]){display:none}}
@media(max-width:640px){
  .rc-fab{right:12px;bottom:12px;height:46px;padding:0 14px 0 6px}
  .rc-pan{padding:14px 14px calc(14px + env(safe-area-inset-bottom));border-radius:20px 20px 0 0}
  .rc-slots{gap:8px}
  .rc-slot .tx{padding:8px 8px 10px}.rc-slot .nm{font-size:12.5px}
  .rc-opts{gap:8px}
}
"""

PLUS = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true">'
        '<path d="M12 5v14M5 12h14"/></svg>')
SPARK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true">'
         '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg>')


def viewer_buttons():
    """大图操作区里的两个按钮：加入配方（id=mrec）、复制提示词（id=mprompt）"""
    return (f'<button type="button" class="btn" id="mrec" data-recipe>{PLUS}<span></span></button>'
            f'<button type="button" class="btn ghost" id="mprompt">{SPARK}<span></span></button>')
BOARD = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true">'
         '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16M15 4v16"/></svg>')


def html(up):
    """配方的胶囊与面板；up = 回到站点根的相对路径（子站 ../，入口页 ./）"""
    sel = "".join(f'<option value="{k}">{escape(zh)}</option>' for k, zh, ja, _, _ in STYLES)
    return f"""<button type="button" class="rc-fab" id="rcFab" aria-haspopup="dialog" aria-controls="rcPan"><span class="st" id="rcStack"></span><span id="rcFabT"></span><b id="rcFabN"></b></button>
<div class="rc-wrap" id="rcPan" role="dialog" aria-modal="true" aria-labelledby="rcT" hidden data-up="{escape(up)}"><div class="rc-pan">
  <div class="rc-hd"><h3 id="rcT"></h3><span class="sp"></span><button type="button" class="btn ghost" id="rcClear"></button><button type="button" class="rc-x" id="rcX" data-close>×</button></div>
  <div class="rc-slots" id="rcSlots"></div>
  <div class="rc-opts">
    <div class="seg" id="rcLang" role="group"><button type="button" data-pl="en">English</button><button type="button" data-pl="zh">中文</button></div>
    <div class="seg" id="rcMode" role="group"><button type="button" data-pm="ref"></button><button type="button" data-pm="text"></button></div>
    <label><span id="rcStyleL"></span><select class="sel" id="rcStyle">{sel}</select></label>
  </div>
  <textarea class="rc-pv" id="rcPv" spellcheck="false"></textarea>
  <div class="rc-acts">
    <button type="button" class="btn pri" id="rcCopy">{ui.COPY_ICON}<span></span></button>
    <button type="button" class="btn" id="rcBoard">{BOARD}<span></span></button>
  </div>
  <p class="rc-note" id="rcNote"></p>
</div></div>"""


JS = r"""<script>
(function(){
const $ = s => document.querySelector(s), esc = s => String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KEY = 'pl.recipe', KINDS = ['portrait', 'costume', 'pose'];
const STYLES = __STYLES__;
const UP = $('#rcPan').dataset.up;
const T = {
 zh:{fab:'配方', title:'配方', clear:'清空', portrait:'人像', costume:'服装', pose:'姿势', pick:'去挑选', remove:'移除',
     ref:'多图参考', text:'纯文字', style:'画风', copy:'复制提示词', board:'下载参考拼图', added:'已加入配方', removed:'已从配方移除',
     replaced:'已替换配方里的{k}', boardFail:'拼图需要在线打开（本地 file:// 下浏览器不允许导出图片）', boardOk:'参考拼图已下载',
     empty:'先在各图库的大图里点「加入配方」，人像、服装、姿势各选一项。',
     add:'加入配方', inRec:'已在配方中', adult:'不可加入配方', adultWhy:'成人向内容不能加入配方', prompt:'复制提示词',
     note:'「多图参考」按图 1、图 2、图 3 的顺序引用，适合 Nano Banana、GPT Image、Seedream、Qwen-Image-Edit 等支持多张参考图的模型，按同样顺序上传图片即可；「纯文字」只用文字描述，适合 Midjourney、Stable Diffusion。'},
 ja:{fab:'レシピ', title:'レシピ', clear:'クリア', portrait:'ポートレート', costume:'衣装', pose:'ポーズ', pick:'選びに行く', remove:'外す',
     ref:'複数画像参照', text:'テキストのみ', style:'スタイル', copy:'プロンプトをコピー', board:'参考ボードを保存', added:'レシピに追加しました', removed:'レシピから外しました',
     replaced:'レシピの{k}を置き換えました', boardFail:'参考ボードはオンラインで開いたときのみ保存できます（file:// では画像を書き出せません）', boardOk:'参考ボードを保存しました',
     empty:'各ギャラリーの拡大表示で「レシピに追加」を押し、ポートレート・衣装・ポーズを 1 つずつ選びます。',
     add:'レシピに追加', inRec:'レシピに追加済み', adult:'レシピに追加できません', adultWhy:'成人向けの内容はレシピに追加できません', prompt:'プロンプトをコピー',
     note:'「複数画像参照」は画像 1・2・3 の順に参照します。Nano Banana、GPT Image、Seedream、Qwen-Image-Edit など複数の参考画像を受け付けるモデル向けで、同じ順に画像をアップロードしてください。「テキストのみ」は Midjourney や Stable Diffusion 向けです。'}};
const t = k => T[PL.lang][k];
const GO = {portrait:'portrait/', costume:'costume/', pose:'pose/'};

/* ── 存储 ── */
function load(){ try{ const o = JSON.parse(localStorage.getItem(KEY) || '{}'); return o && typeof o === 'object' ? o : {}; }catch(_){ return {}; } }
let R = load();
const valid = x => x && KINDS.includes(x.k) && typeof x.id === 'string' && typeof x.th === 'string' && !/^[a-z]+:|^\/\//i.test(x.th + (x.im || ''));
const items = () => KINDS.map(k => R[k]).filter(valid);
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(R)); }catch(_){} dispatchEvent(new Event('pl:recipe')); }
const opt = () => Object.assign({lang:'en', mode:'ref', style:'none'}, R.opt || {});

/* ── 提示词：多图参考按 图1/图2/图3 指代；纯文字只描述 ── */
function prompt(lang, mode, style){
  const xs = items(), en = lang === 'en';
  const nm = x => (en ? x.n.en : x.n.zh) || x.n.en || x.n.zh || x.id;
  const ang = x => x.ang ? (en ? x.ang.en : x.ang.zh) : '';
  if (!xs.length) return '';
  const st = STYLES.find(s => s[0] === style) || STYLES[0];
  const L = [];
  if (mode === 'ref'){
    L.push(en ? 'Combine the ' + xs.length + ' reference images into one image of a single character:'
              : '结合提供的 ' + xs.length + ' 张参考图，生成同一个角色的一张图：');
    xs.forEach((x, i) => { const n = i + 1;
      if (x.k === 'portrait') L.push(en ? '- Image ' + n + ' (face reference): keep the face, features and hairstyle of image ' + n + ' (' + nm(x) + ').'
                                        : '- 图' + n + '（人像参考）：保持图' + n + '人物的脸型、五官与发型（' + nm(x) + '）。');
      else if (x.k === 'costume') L.push(en ? '- Image ' + n + ' (outfit reference): wear the complete outfit from image ' + n + ' (' + x.kw + '), keeping fabric, cut and details.'
                                            : '- 图' + n + '（服装参考）：穿上图' + n + '中的整套服装（' + (x.kz || x.kw) + '），还原面料、剪裁与细节。');
      else L.push(en ? '- Image ' + n + ' (pose reference): match the body pose and camera angle of image ' + n + ' (' + nm(x) + (ang(x) ? ', ' + ang(x) + ' view' : '') + '); use it only for the skeleton and ignore the mannequin surface.'
                     : '- 图' + n + '（姿势参考）：身体姿势与镜头角度参照图' + n + '（' + nm(x) + (ang(x) ? '，' + ang(x) : '') + '），只参考骨架动作，忽略人偶材质。');
    });
    L.push(en ? '- Natural proportions, correct hands and face, consistent lighting.' : '- 人体比例自然，手部与五官正确，光影统一。');
    if (st[3]) L.push(en ? '- Style: ' + st[4] + '.' : '- 画风：' + st[3]);
    return L.join('\n');
  }
  // 纯文字：一段逗号分隔的描述（英文更适合 SD / MJ）
  const by = k => xs.find(x => x.k === k);
  const p = by('portrait'), c = by('costume'), q = by('pose'), parts = [];
  if (en){
    parts.push('a young woman, solo');
    if (p) parts.push('hairstyle: ' + p.n.en);
    if (c) parts.push('wearing ' + c.kw);
    if (q) parts.push((q.d || q.n.en).toLowerCase() + (q.ang ? ', ' + q.ang.en + ' view' : ''));
    parts.push('full body', 'detailed');
    if (st[4]) parts.push(st[4]);
    return parts.join(', ');
  }
  parts.push('一位年轻女性');
  if (p) parts.push('发型：' + p.n.zh);
  if (c) parts.push('服装：' + (c.kz || c.n.zh) + '（' + c.kw + '）');
  if (q) parts.push('姿势：' + q.n.zh + (q.ang ? '，' + q.ang.zh : ''));
  parts.push('全身，细节丰富');
  if (st[3]) parts.push(st[3].replace(/。$/, ''));
  return parts.join('，') + '。';
}
PL.recipePrompt = prompt;   // 测试与生图页复用

/* ── 胶囊与面板 ── */
const fab = $('#rcFab'), pan = $('#rcPan'), pv = $('#rcPv');
const abs = p => UP + p;
function drawFab(){
  const xs = items();
  fab.classList.toggle('on', xs.length > 0);
  const top = document.getElementById('plTop'); if (top) top.classList.toggle('lift', xs.length > 0);
  $('#rcStack').innerHTML = KINDS.map(k => R[k] && valid(R[k]) ? '<img src="'+esc(abs(R[k].th))+'" alt="">' : '<i>'+esc(t(k)[0])+'</i>').join('');
  $('#rcFabT').textContent = t('fab'); $('#rcFabN').textContent = xs.length + '/3';
  fab.ariaLabel = t('fab') + ' ' + xs.length + '/3';
}
function drawPan(){
  const o = opt();
  $('#rcT').textContent = t('title'); $('#rcClear').textContent = t('clear');
  $('#rcSlots').innerHTML = KINDS.map(k => { const x = R[k];
    if (!valid(x)) return '<div class="rc-slot vac"><div class="im"><span><b>'+esc(t(k))+'</b><br><a href="'+esc(UP + GO[k])+'">'+esc(t('pick'))+' →</a></span></div></div>';
    const n = PL.lang === 'ja' ? (x.n.ja || x.n.zh) : x.n.zh;
    const site = /^[a-z-]+$/.test(x.site || '') ? x.site : GO[k].slice(0, -1);
    return '<div class="rc-slot"><a class="im" href="'+esc(UP + site + '/')+'" tabindex="-1"><img src="'+esc(abs(x.th))+'" alt="'+esc(n)+'" loading="lazy"></a>'+
      '<button type="button" class="rm" data-rm="'+k+'" aria-label="'+esc(t('remove')+' '+n)+'">×</button>'+
      '<div class="tx"><div class="k">'+esc(t(k))+'</div><div class="nm">'+esc(n + (x.ang ? ' · ' + (PL.lang === 'ja' ? x.ang.ja : x.ang.zh) : ''))+'</div></div></div>';
  }).join('');
  [...$('#rcLang').children].forEach(b => b.setAttribute('aria-pressed', b.dataset.pl === o.lang ? 'true' : 'false'));
  [...$('#rcMode').children].forEach(b => { b.textContent = t(b.dataset.pm); b.setAttribute('aria-pressed', b.dataset.pm === o.mode ? 'true' : 'false'); });
  $('#rcStyleL').textContent = t('style'); $('#rcStyle').value = o.style;
  [...$('#rcStyle').options].forEach((op, i) => { op.textContent = PL.lang === 'ja' ? STYLES[i][2] : STYLES[i][1]; });
  pv.value = items().length ? prompt(o.lang, o.mode, o.style) : t('empty');
  $('#rcCopy span').textContent = t('copy'); $('#rcBoard span').textContent = t('board');
  $('#rcCopy').disabled = $('#rcBoard').disabled = !items().length;
  $('#rcNote').textContent = t('note');
}
function openPan(){ drawPan(); PL.openDialog(pan, fab); }
fab.addEventListener('click', openPan);
$('#rcSlots').addEventListener('click', e => { const b = e.target.closest('[data-rm]'); if (!b) return; delete R[b.dataset.rm]; save(); drawPan(); });
$('#rcClear').addEventListener('click', () => { KINDS.forEach(k => delete R[k]); save(); drawPan(); });
const setOpt = (k, v) => { R.opt = Object.assign(opt(), {[k]: v}); save(); drawPan(); };
$('#rcLang').addEventListener('click', e => { const b = e.target.closest('[data-pl]'); if (b) setOpt('lang', b.dataset.pl); });
$('#rcMode').addEventListener('click', e => { const b = e.target.closest('[data-pm]'); if (b) setOpt('mode', b.dataset.pm); });
$('#rcStyle').addEventListener('change', e => setOpt('style', e.target.value));
$('#rcCopy').addEventListener('click', () => PL.copy(pv.value));

/* ── 参考拼图：三张图并排 1800×1200，标上 图1/图2/图3（同源图片才能导出） ── */
const loadImg = src => new Promise((ok, no) => { const im = new Image(); im.decoding = 'async'; im.onload = () => ok(im); im.onerror = no; im.src = src; });
$('#rcBoard').addEventListener('click', async () => {
  const xs = items(); if (!xs.length) return;
  if (location.protocol === 'file:'){ PL.toast(t('boardFail')); return; }
  const W = 600 * xs.length, H = 1200, c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d'); g.fillStyle = '#ffffff'; g.fillRect(0, 0, W, H);
  try{
    const ims = await Promise.all(xs.map(x => loadImg(abs(x.im || x.th)).catch(() => loadImg(abs(x.th)))));
    ims.forEach((im, i) => {
      const s = Math.min(560 / im.naturalWidth, 1080 / im.naturalHeight), w = im.naturalWidth * s, h = im.naturalHeight * s;
      g.drawImage(im, i * 600 + (600 - w) / 2, 40 + (1080 - h) / 2, w, h);
      const lab = 'Image ' + (i + 1) + ' · ' + {portrait:'Face', costume:'Outfit', pose:'Pose'}[xs[i].k];
      g.font = '600 24px system-ui,sans-serif'; g.textBaseline = 'middle';
      const lw = Math.ceil(g.measureText(lab).width) + 32;
      g.fillStyle = 'rgba(17,17,17,.82)'; g.beginPath(); g.roundRect ? g.roundRect(i * 600 + 20, 20, lw, 48, 24) : g.rect(i * 600 + 20, 20, lw, 48); g.fill();
      g.fillStyle = '#fff'; g.fillText(lab, i * 600 + 36, 44);
      if (i) { g.fillStyle = '#e5e5e5'; g.fillRect(i * 600, 0, 2, H); }
    });
    g.fillStyle = '#888'; g.font = '20px system-ui,sans-serif'; g.textBaseline = 'alphabetic'; g.fillText('photoai.life · recipe', 20, H - 18);
    c.toBlob(b => { if (!b){ PL.toast(t('boardFail')); return; }
      const d = new Date(), z = n => String(n).padStart(2, '0');
      const a = document.createElement('a'); a.href = URL.createObjectURL(b);
      a.download = 'photoai-recipe-' + d.getFullYear() + z(d.getMonth() + 1) + z(d.getDate()) + '-' + z(d.getHours()) + z(d.getMinutes()) + '.png';
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 4000); PL.toast(t('boardOk')); }, 'image/png');
  }catch(_){ PL.toast(t('boardFail')); }
});

/* ── 页面接口 ── */
const has = (k, id) => !!(R[k] && R[k].id === id);
const PLUS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';
const btns = [];     // 大图里的「加入配方」：[按钮, 取当前条目的函数]
function syncBtn(b, get){
  const g = get() || {}, x = g.item, on = !!x && has(x.k, x.id);
  b.disabled = !!g.adult || !x; b.setAttribute('aria-pressed', on ? 'true' : 'false');
  b.querySelector('span').textContent = g.adult ? t('adult') : on ? t('inRec') : t('add');
  b.title = g.adult ? t('adultWhy') : '';
}
const grids = [];    // 卡片「+」：[网格, 由卡片取条目的函数]
function syncGrid(g, of){ g.querySelectorAll('[data-add]').forEach(b => { const x = of(b.closest('.card'));
  const on = !!x && has(x.k, x.id); b.setAttribute('aria-pressed', on ? 'true' : 'false'); b.title = b.ariaLabel = on ? t('inRec') : t('add'); }); }
function syncAll(){ btns.forEach(([b, g]) => syncBtn(b, g)); grids.forEach(([g, of]) => syncGrid(g, of)); }
PL.recipe = {
  items, has, t,
  // 卡片上的「+」按钮 HTML（x 为空时不出现，例如成人向条目）
  addBtn: x => x ? '<button type="button" class="rc-add" data-add aria-pressed="'+has(x.k, x.id)+'" aria-label="'+esc(t(has(x.k, x.id) ? 'inRec' : 'add'))+'" title="'+esc(t(has(x.k, x.id) ? 'inRec' : 'add'))+'">'+PLUS+'</button>' : '',
  // 网格里点「+」：捕获阶段处理，不触发卡片打开大图
  grid(g, of){ grids.push([g, of]);
    g.addEventListener('click', e => { const b = e.target.closest('[data-add]'); if (!b) return; e.preventDefault(); e.stopPropagation();
      const x = of(b.closest('.card')); if (x) PL.recipe.toggle(x); }, true); },
  // 大图里的按钮：get() 返回 {item, adult}；点按钮或按 A 切换
  button(b, get){ btns.push([b, get]); b.addEventListener('click', () => { const g = get() || {}; if (g.item && !g.adult) PL.recipe.toggle(g.item); }); syncBtn(b, get); },
  refresh: syncAll,
  toggle(x, opener){
    if (!valid(x)) return;
    if (R[x.k] && R[x.k].id === x.id){ delete R[x.k]; save(); PL.toast(t('removed')); return; }
    const had = !!R[x.k]; R[x.k] = Object.assign({}, x, {at: Date.now()}); save();
    PL.toast(had ? t('replaced').replace('{k}', t(x.k)) : t('added'));
    fab.classList.remove('bump'); void fab.offsetWidth; fab.classList.add('bump');
  },
};
addEventListener('pl:recipe', () => { drawFab(); if (!pan.hidden) drawPan(); syncAll(); });
addEventListener('pl:lang', () => { drawFab(); if (!pan.hidden) drawPan(); syncAll(); });
addEventListener('storage', e => { if (e.key === KEY){ R = load(); dispatchEvent(new Event('pl:recipe')); } });
drawFab();
})();
</script>"""


def _strip(js):
    """去掉整行注释与行首缩进；行内的代码与字符串原样保留"""
    out = []
    for line in js.split("\n"):
        s = line.strip()
        if not s or (s.startswith("/*") and s.endswith("*/")) or s.startswith("// "):
            continue
        out.append(s)
    return "\n".join(out)


def script():
    import json
    return _strip(JS.replace("__STYLES__", json.dumps(STYLES, ensure_ascii=False)))
