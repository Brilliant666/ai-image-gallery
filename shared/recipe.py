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
/* 配方栏：常驻右下角；点开向上展开（不遮罩、不锁滚动，背后页面照常浏览） */
.rc{position:fixed;right:16px;bottom:16px;z-index:35;width:min(720px,calc(100vw - 32px));display:flex;flex-direction:column;
  border-radius:22px;background:var(--bg2);color:var(--tx);box-shadow:var(--sh3);border:1px solid var(--line);overflow:hidden;
  transition:width .25s var(--ease)}
.rc:not(.open){width:auto;max-width:calc(100vw - 32px)}
.rc-bar{display:flex;align-items:center;gap:10px;height:56px;padding:0 8px 0 10px;flex:none}
.rc-tg{display:flex;align-items:center;gap:10px;height:44px;padding:0 10px 0 4px;border:0;border-radius:14px;background:transparent;color:inherit;
  cursor:pointer;min-width:0}
.rc-tg:hover{background:var(--sf)}
.rc-st{display:flex;flex:none}
.rc-st img,.rc-st i{width:34px;height:34px;margin-left:-8px;border-radius:10px;object-fit:cover;background:var(--imgbg);border:2px solid var(--bg2);display:block}
.rc-st :first-child{margin-left:0}
.rc-st i{display:grid;place-items:center;font-style:normal;font-size:12px;color:var(--mu)}
.rc-lb{display:flex;flex-direction:column;align-items:flex-start;line-height:1.25;min-width:0}
.rc-lb b{font-size:14px}.rc-lb small{font-size:12px;color:var(--mu);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:220px}
.rc-ch{width:16px;height:16px;flex:none;color:var(--mu);transition:transform .25s var(--ease)}
.rc.open .rc-ch{transform:rotate(180deg)}
.rc-go{margin-left:auto;height:42px;padding:0 18px}
.rc-go[data-busy]{background:var(--sf);color:var(--tx)}
.rc-go .sp{width:14px;height:14px;border-radius:50%;border:2px solid currentColor;border-right-color:transparent;animation:rc-spin .8s linear infinite;display:none}
.rc-go[data-busy] .sp{display:block}.rc-go[data-busy] svg{display:none}
@keyframes rc-spin{to{transform:rotate(360deg)}}
.rc-dot{width:9px;height:9px;border-radius:50%;background:var(--ac);flex:none}
.rc-dot[hidden]{display:none}
.rc.bump{animation:rc-bump .45s var(--ease)}
@keyframes rc-bump{40%{transform:scale(1.03)}}
.totop{bottom:86px}
.rc-body{max-height:min(72vh,720px);overflow:auto;padding:4px 16px 16px;border-top:1px solid var(--line)}
.rc-body[hidden]{display:none}
/* 节点：三个参考 → 提示词 → 生成 */
.rc-flow{position:relative;padding-top:12px}
.rc-wires{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible}
.rc-wires path{fill:none;stroke:var(--line2);stroke-width:2}
.rc-wires path.on{stroke:var(--ac);stroke-dasharray:6 6;animation:rc-flow 1s linear infinite}
@keyframes rc-flow{to{stroke-dashoffset:-12}}
.rc-refs{position:relative;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.rc-node{position:relative;border-radius:16px;background:var(--bg2);border:1px solid var(--line2);box-shadow:var(--sh1);min-width:0}
.rc-nh{display:flex;align-items:center;gap:8px;padding:8px 10px;font-size:12.5px;font-weight:700}
.rc-nh i{width:22px;height:22px;border-radius:7px;display:grid;place-items:center;font-style:normal;font-size:12px;background:var(--sf);color:var(--mu)}
.rc-nh small{margin-left:auto;font-size:11.5px;color:var(--mu);font-weight:600;letter-spacing:.04em}
.rc-nh button{margin-left:auto;width:28px;height:28px;border:0;border-radius:8px;background:transparent;color:var(--mu);font-size:16px;cursor:pointer}
.rc-nh button:hover{background:var(--sf);color:var(--tx)}
.rc-im{position:relative;display:block;aspect-ratio:1/1;margin:0 10px;border-radius:10px;overflow:hidden;background:var(--imgbg)}
.rc-im img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
.rc-nm{padding:6px 10px 10px;font-size:12.5px;line-height:1.45;color:var(--tx2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rc-node.vac .rc-im{display:grid;place-items:center;text-align:center;font-size:12.5px;color:var(--mu);padding:10px}
.rc-node.vac .rc-im a{color:var(--ac);font-weight:600}
.rc-vsw{display:flex;gap:4px;padding:0 10px 10px}
.rc-vsw button{flex:1;height:30px;border:0;border-radius:8px;background:var(--sf);color:var(--tx2);font-size:12px;cursor:pointer}
.rc-vsw button[aria-pressed="true"]{background:var(--sel);color:var(--on-sel)}
.rc-low{position:relative;display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:12px;margin-top:26px}
.rc-pn textarea{display:block;width:calc(100% - 20px);height:132px;margin:0 10px 8px;padding:9px 10px;border:0;border-radius:10px;background:var(--sf);
  color:var(--tx);font:12.5px/1.65 var(--mono);resize:vertical}
.rc-pn .row{display:flex;flex-wrap:wrap;gap:6px;padding:0 10px 10px;align-items:center}
.rc-pn select.sel,.rc-gn select.sel{height:32px;font-size:12.5px;padding:0 28px 0 12px;background-position:right 9px center}
.rc-pn .seg button{height:32px;padding:0 11px;font-size:12px}
.rc-pn .lk{margin-left:auto;border:0;background:transparent;color:var(--ac);font-size:12.5px;cursor:pointer;padding:4px}
.rc-gn{background:linear-gradient(160deg,#172a20,#1f3a2a);color:#f2f7f3;border-color:transparent}
.rc-gn .rc-nh i{background:rgba(255,255,255,.12);color:#cfe8d5}.rc-gn .rc-nh small{color:#9fc2a8}
.rc-gn .rc-nh button{color:#cfe8d5}.rc-gn .rc-nh button:hover{background:rgba(255,255,255,.1);color:#fff}
.rc-gn .kv{display:grid;grid-template-columns:auto 1fr;gap:6px 10px;align-items:center;padding:0 12px 10px;font-size:12.5px}
.rc-gn .kv span{color:#9fc2a8}
.rc-gn select.sel{width:100%;background-color:rgba(255,255,255,.1);color:#fff}
.rc-gn select.sel option{color:#111}
.rc-run{display:flex;align-items:center;justify-content:center;gap:8px;width:calc(100% - 24px);height:42px;margin:4px 12px 8px;border:0;border-radius:12px;
  background:#d7efa0;color:#16301f;font-size:14px;font-weight:800;cursor:pointer}
.rc-run:hover{filter:brightness(1.05)}.rc-run:disabled{opacity:.5;cursor:not-allowed}
.rc-run svg{width:15px;height:15px}
.rc-gn .sub{display:flex;gap:6px;padding:0 12px 12px}
.rc-gn .sub button{flex:1;height:34px;border:0;border-radius:10px;background:rgba(255,255,255,.1);color:#e6f2e9;font-size:12.5px;cursor:pointer}
.rc-gn .sub button:hover{background:rgba(255,255,255,.16)}
.rc-msg{margin:0 12px 10px;padding:8px 10px;border-radius:10px;background:rgba(255,255,255,.1);font-size:12.5px;line-height:1.6}
.rc-msg[hidden]{display:none}.rc-msg.err{background:rgba(239,68,68,.22)}
.rc-msg a,.rc-msg button.lk{color:#d7efa0;background:none;border:0;padding:0;cursor:pointer;font:inherit;text-decoration:underline}
/* Key 设置 */
.rc-set{margin-top:14px;padding:12px 14px;border-radius:16px;background:var(--sf)}
.rc-set[hidden]{display:none}
.rc-set h4{margin:0 0 8px;font-size:14px}
.rc-set .g{display:grid;grid-template-columns:auto minmax(0,1fr);gap:8px 12px;align-items:center;font-size:13px}
.rc-set .g>span{color:var(--mu)}
.rc-set input[type=password],.rc-set input[type=url],.rc-set input[type=text]{width:100%;height:36px;padding:0 12px;border:0;border-radius:10px;background:var(--bg2);color:var(--tx);font:13px var(--mono)}
.rc-set label.ck{display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--tx2)}
.rc-set .row{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;align-items:center}
.rc-set p{margin:8px 0 0;font-size:12px;color:var(--mu);line-height:1.7}
.rc-set a{color:var(--ac)}
/* 结果与记录 */
.rc-res{margin-top:16px}
.rc-res[hidden]{display:none}
.rc-res h4{display:flex;align-items:center;gap:8px;margin:0 0 8px;font-size:13px;color:var(--mu)}
.rc-res h4 button{margin-left:auto;border:0;background:transparent;color:var(--mu);font-size:12.5px;cursor:pointer}
.rc-gal{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px}
.rc-it{position:relative;border-radius:12px;overflow:hidden;background:var(--imgbg);aspect-ratio:3/4}
.rc-it img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;cursor:zoom-in}
.rc-it .ov{position:absolute;inset:auto 0 0 0;display:flex;gap:4px;padding:6px;justify-content:flex-end;
  background:linear-gradient(transparent,rgba(0,0,0,.55));opacity:0;transition:opacity .15s}
.rc-it:hover .ov,.rc-it:focus-within .ov{opacity:1}
@media (hover:none){.rc-it .ov{opacity:1}}
.rc-it .ov a,.rc-it .ov button{width:30px;height:30px;border:0;border-radius:8px;display:grid;place-items:center;background:rgba(255,255,255,.9);color:#111;cursor:pointer;text-decoration:none;font-size:14px}
.rc-it .ov svg{width:15px;height:15px}
.rc-it.run,.rc-it.bad{display:grid;place-items:center;text-align:center;padding:10px;font-size:12px;color:var(--mu);cursor:default}
.rc-it.run b{display:block;font-size:18px;color:var(--tx);font-variant-numeric:tabular-nums}
.rc-it.bad{color:#b42318}
.rc-it.run button,.rc-it.bad button{margin-top:6px;border:0;background:var(--bg2);border-radius:8px;padding:4px 10px;font-size:12px;cursor:pointer;color:var(--tx)}
.rc-view{position:fixed;inset:0;z-index:90;background:rgba(0,0,0,.85);display:grid;place-items:center;padding:20px;cursor:zoom-out}
.rc-view[hidden]{display:none}
.rc-view img{max-width:100%;max-height:100%;border-radius:12px}
/* 大图与卡片上的「加入配方」 */
.btn[data-recipe][aria-pressed="true"]{background:var(--ac);color:var(--on-ac)}
.btn[data-recipe]:disabled{opacity:.45;cursor:not-allowed}
.macts:has([data-recipe]) .btn.pri,.macts .btn[data-recipe]{flex:1 1 calc(50% - 4px)}
.rc-add{position:absolute;right:6px;top:48px;width:40px;height:40px;padding:2px;border:0;border-radius:50%;display:grid;place-items:center;
  background:rgba(255,255,255,.9);background-clip:content-box;color:#111;cursor:pointer;opacity:0;transform:scale(.9);transition:.2s var(--ease);
  filter:drop-shadow(0 1px 2px rgba(0,0,0,.12))}
.rc-add svg{width:17px;height:17px}
.card:hover .rc-add,.rc-add:focus-visible{opacity:1;transform:none}
.rc-add[aria-pressed="true"]{opacity:1;transform:none;background-color:var(--ac);color:#fff}
@media (hover:none){.rc-add:not([aria-pressed="true"]){display:none}}
main{padding-bottom:110px}
@media(max-width:720px){
  .rc{right:8px;left:8px;bottom:8px;width:auto!important;max-width:none;border-radius:20px}
  .rc-lb small{max-width:120px}
  .rc-body{max-height:74vh;padding:2px 10px 12px}
  .rc-refs{gap:6px}
  .rc-nh{padding:6px 8px;font-size:12px}.rc-nh small{display:none}
  .rc-im{margin:0 6px;aspect-ratio:4/5}.rc-nm{padding:5px 8px 8px;font-size:12px}
  .rc-vsw{padding:0 6px 8px}
  .rc-low{grid-template-columns:1fr;margin-top:18px}
  .rc-wires{display:none}
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


PLAY = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4.5v15l13-7.5z"/></svg>'
CHEV = ('<svg class="rc-ch" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><path d="m6 15 6-6 6 6"/></svg>')
GEAR = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1'
        'a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1'
        'a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1'
        'a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1'
        'a1.7 1.7 0 0 0-1.5 1z"/></svg>')


def html(up):
    """配方栏（常驻右下角，点开向上展开）；up = 回到站点根的相对路径（子站 ../，入口页 ./）"""
    sel = "".join(f'<option value="{k}">{escape(zh)}</option>' for k, zh, ja, _, _ in STYLES)
    return f"""<section class="rc" id="rc" data-up="{escape(up)}" aria-labelledby="rcT">
  <div class="rc-body" id="rcBody" hidden>
    <div class="rc-flow" id="rcFlow">
      <svg class="rc-wires" id="rcWires" aria-hidden="true"></svg>
      <div class="rc-refs" id="rcSlots"></div>
      <div class="rc-low">
        <div class="rc-node rc-pn" id="rcPn">
          <div class="rc-nh"><i>T</i><span id="rcPnT"></span><small>PROMPT</small></div>
          <textarea id="rcPv" spellcheck="false"></textarea>
          <div class="row">
            <select class="sel" id="rcStyle">{sel}</select>
            <div class="seg" id="rcLang" role="group"><button type="button" data-pl="en">EN</button><button type="button" data-pl="zh">中</button></div>
            <button type="button" class="lk" id="rcCopy"></button>
          </div>
        </div>
        <div class="rc-node rc-gn" id="rcGn">
          <div class="rc-nh"><i>▲</i><span id="rcGnT"></span><button type="button" id="rcSetB">{GEAR}</button></div>
          <div class="kv">
            <span id="rcServiceL"></span><select class="sel" id="rcService"></select>
            <span id="rcModelL"></span><select class="sel" id="rcModel"></select>
            <span id="rcRatioL"></span><select class="sel" id="rcRatio"></select>
            <span id="rcNL"></span><select class="sel" id="rcN"><option>1</option><option>2</option><option>3</option><option>4</option></select>
          </div>
          <button type="button" class="rc-run" id="rcRun">{PLAY}<span></span></button>
          <p class="rc-msg" id="rcMsg" hidden></p>
          <div class="sub"><button type="button" id="rcBoard"></button><button type="button" id="rcClear"></button></div>
        </div>
      </div>
    </div>
    <div class="rc-set" id="rcSet" hidden>
      <h4 id="rcSetT"></h4>
      <div class="g">
        <span id="rcProvL"></span><select class="sel" id="rcProv"></select>
        <span id="rcKeyL"></span><input type="password" id="rcKey" autocomplete="off" spellcheck="false">
        <span id="rcBaseL"></span><input type="url" id="rcBase" placeholder="https://…/v1">
        <span id="rcMidL"></span><input type="text" id="rcMid" list="rcModels" spellcheck="false"><datalist id="rcModels"></datalist>
        <span id="rcProtoL" hidden></span><select class="sel" id="rcProto" hidden><option value="edits">images/edits · multipart</option><option value="json">images/generations · JSON</option></select>
        <span id="rcFieldL" hidden></span><select class="sel" id="rcField" hidden><option>image[]</option><option>image</option></select>
      </div>
      <div class="row"><label class="ck"><input type="checkbox" id="rcRem"><span id="rcRemL"></span></label>
        <button type="button" class="btn pri" id="rcSave"></button><button type="button" class="btn ghost" id="rcTest"></button><button type="button" class="btn ghost" id="rcForget"></button></div>
      <p id="rcSetHelp"></p><p id="rcTestMsg" role="status"></p><p id="rcSetNote"></p>
    </div>
    <div class="rc-res" id="rcRes" hidden><h4><span id="rcResT"></span><button type="button" id="rcResClr"></button></h4><div class="rc-gal" id="rcGal"></div></div>
  </div>
  <div class="rc-bar">
    <button type="button" class="rc-tg" id="rcTg" aria-expanded="false" aria-controls="rcBody">
      <span class="rc-st" id="rcStack"></span><span class="rc-lb"><b id="rcT"></b><small id="rcSub"></small></span>{CHEV}<span class="rc-dot" id="rcDot" hidden></span>
    </button>
    <button type="button" class="btn pri rc-go" id="rcGo"><span class="sp"></span>{PLAY}<span class="tx"></span></button>
  </div>
</section>
<div class="rc-view" id="rcView" hidden><img alt=""></div>"""


JS = r"""<script>
(function(){
const $ = s => document.querySelector(s), esc = s => String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KEY = 'pl.recipe', KINDS = ['portrait', 'costume', 'pose'];
const STYLES = __STYLES__;
const UP = $('#rc').dataset.up;
const T = {
 zh:{fab:'配方', title:'配方', clear:'清空配方', portrait:'人像', costume:'服装', pose:'姿势', pick:'去挑选', remove:'移除',
     ref:'多图参考', text:'纯文字', style:'画风', copy:'复制提示词', board:'下载参考拼图', added:'已加入配方', removed:'已从配方移除',
     replaced:'已替换配方里的{k}', boardFail:'拼图需要在线打开（本地 file:// 下浏览器不允许导出图片）', boardOk:'参考拼图已下载',
     empty:'先在各图库的大图里点「加入配方」，人像、服装、姿势各选一项。',
     add:'加入配方', inRec:'已在配方中', adult:'不可加入配方', adultWhy:'成人向内容不能加入配方', prompt:'复制提示词',
     sub0:'在大图里点「加入配方」', subN:'{n}/3 · 点开编辑', gen:'生成', running:'生成中 {s}s', pn:'画面与融合描述', gn:'图像生成',
     model:'模型', ratio:'比例', count:'张数', setT:'生图服务', prov:'服务商', key:'API Key', base:'Base URL', mid:'模型 ID', proto:'接口协议', field:'图片字段名', test:'测试连接', testing:'连接中…', connected:'模型列表读取成功，共 {n} 项；生图仍需实际测试。', noModels:'此接口未提供模型列表，无法用此方式验证；可保存后直接尝试生图。', testTimeout:'连接测试超过 15 秒，请检查地址或稍后重试。', relayHelp:'填写中转商的 Base URL、Key 和模型 ID；接口与图片字段按中转文档选择。支持多张参考图的模型才能合成配方。', directHelp:'可修改 Base URL；留空使用官方地址。',
     remember:'在这台设备上记住 Key', save:'保存', forget:'清除 Key', getKey:'获取 Key',
     setNote:'Key 只保存在你的浏览器里，生成时由浏览器直接发给服务商，不经过本站服务器。默认只在当前标签页有效，勾选「记住」后才长期保存。生成会按服务商的价格计费。',
     res:'生成结果', resClr:'清空记录', dl:'下载', delOne:'删除', cancel:'取消', retry:'重试', line:'线稿', depth:'深度图',
     needOne:'先在配方里放至少一张参考图', needKey:'先填写 API Key', badBase:'Base URL 需要以 https:// 开头', offline:'生图需要在线打开本站（file:// 下不可用）',
     inPage:'这个浏览器不支持后台生成，生成完成前请留在本页', done:'已生成 {n} 张', saved:'已保存',
     e_auth:'Key 无效或没有权限，请检查 Key、模型和账号', e_rate:'请求太频繁或额度不足，请稍后再试或检查余额', e_safety:'被服务商的安全审核拦截了，可以换一张参考图或修改描述',
     e_model:'模型不存在或接口地址不对，请检查模型 ID 与 Base URL', e_server:'服务商暂时出错，请稍后重试', e_timeout:'超过 3 分钟没有返回，已停止',
     e_network:'连不上服务商：可能是网络或地区限制（OpenAI、Gemini 不对中国大陆开放），也可能是该接口不允许浏览器直接调用', e_cancel:'已取消',
     e_empty:'服务商没有返回图片', e_bad:'请求被拒绝',
     note:'「多图参考」按图 1、图 2、图 3 的顺序引用，适合 Nano Banana、GPT Image、Seedream、Qwen-Image-Edit 等支持多张参考图的模型，按同样顺序上传图片即可；「纯文字」只用文字描述，适合 Midjourney、Stable Diffusion。'},
 ja:{fab:'レシピ', title:'レシピ', clear:'クリア', portrait:'ポートレート', costume:'衣装', pose:'ポーズ', pick:'選びに行く', remove:'外す',
     ref:'複数画像参照', text:'テキストのみ', style:'スタイル', copy:'プロンプトをコピー', board:'参考ボードを保存', added:'レシピに追加しました', removed:'レシピから外しました',
     replaced:'レシピの{k}を置き換えました', boardFail:'参考ボードはオンラインで開いたときのみ保存できます（file:// では画像を書き出せません）', boardOk:'参考ボードを保存しました',
     empty:'各ギャラリーの拡大表示で「レシピに追加」を押し、ポートレート・衣装・ポーズを 1 つずつ選びます。',
     add:'レシピに追加', inRec:'レシピに追加済み', adult:'レシピに追加できません', adultWhy:'成人向けの内容はレシピに追加できません', prompt:'プロンプトをコピー',
     sub0:'拡大表示で「レシピに追加」', subN:'{n}/3 · 開いて編集', gen:'生成', running:'生成中 {s}秒', pn:'画面と合成の説明', gn:'画像生成',
     model:'モデル', ratio:'比率', count:'枚数', setT:'画像生成サービス', prov:'サービス', key:'API Key', base:'Base URL', mid:'モデル ID', proto:'API 形式', field:'画像フィールド', test:'接続テスト', testing:'接続中…', connected:'モデル一覧を取得しました（{n} 件）。画像生成は別途テストしてください。', noModels:'モデル一覧 API がないため確認できません。保存後に画像生成をお試しください。', testTimeout:'接続テストが 15 秒を超えました。URL を確認するか、後でもう一度お試しください。', relayHelp:'中継の Base URL・Key・モデル ID を入力し、API 形式と画像フィールドを選びます。複数の参考画像に対応するモデルを選んでください。', directHelp:'Base URL は変更できます。空欄なら公式 URL を使います。',
     remember:'この端末に Key を記憶する', save:'保存', forget:'Key を消去', getKey:'Key を取得',
     setNote:'Key はブラウザ内にのみ保存され、生成時にブラウザから直接サービスへ送られます。本サイトのサーバーは経由しません。初期状態ではこのタブの間だけ有効で、「記憶する」をオンにすると保存されます。料金は各サービスの規定に従います。',
     res:'生成結果', resClr:'履歴を消去', dl:'保存', delOne:'削除', cancel:'キャンセル', retry:'再試行', line:'線画', depth:'デプス',
     needOne:'レシピに参考画像を 1 枚以上入れてください', needKey:'API Key を入力してください', badBase:'Base URL は https:// で始めてください', offline:'画像生成はオンラインで開いたときのみ使えます（file:// 不可）',
     inPage:'このブラウザはバックグラウンド生成に対応していません。完了までこのページに留まってください', done:'{n} 枚生成しました', saved:'保存しました',
     e_auth:'Key が無効か権限がありません。Key・モデル・アカウントを確認してください', e_rate:'リクエストが多すぎるか残高不足です', e_safety:'サービスの安全審査でブロックされました。参考画像か説明を変えてください',
     e_model:'モデルが存在しないか URL が違います', e_server:'サービス側のエラーです。しばらくしてから再試行してください', e_timeout:'3 分以上応答がないため停止しました',
     e_network:'サービスに接続できません。ネットワークや地域制限、またはブラウザからの直接呼び出しが許可されていない可能性があります', e_cancel:'キャンセルしました',
     e_empty:'画像が返されませんでした', e_bad:'リクエストが拒否されました',
     note:'「複数画像参照」は画像 1・2・3 の順に参照します。Nano Banana、GPT Image、Seedream、Qwen-Image-Edit など複数の参考画像を受け付けるモデル向けで、同じ順に画像をアップロードしてください。「テキストのみ」は Midjourney や Stable Diffusion 向けです。'}};
const t = k => T[PL.lang][k];
const GO = {portrait:'portrait/', costume:'costume/', pose:'pose/'};

/* ── 存储 ── */
function load(){ try{ const o = JSON.parse(localStorage.getItem(KEY) || '{}'); return o && typeof o === 'object' ? o : {}; }catch(_){ return {}; } }
let R = load();
const valid = x => x && KINDS.includes(x.k) && typeof x.id === 'string' && typeof x.th === 'string' && !/^[a-z]+:|^\/\//i.test(x.th + (x.im || ''));
const items = () => KINDS.map(k => R[k]).filter(valid);
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(R)); }catch(_){} dispatchEvent(new Event('pl:recipe')); }
const opt = () => Object.assign({lang:'en', mode:'ref', style:'none'}, R.opt || {}, {mode:'ref'});

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

/* ── 配方栏 ── */
const rc = $('#rc'), body = $('#rcBody'), pv = $('#rcPv'), go = $('#rcGo');
const abs = p => UP + p;
const DL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v11m0 0-4.5-4.5M12 15l4.5-4.5M5 19.5h14"/></svg>';
let edited = false;          // 用户改过提示词：配方变化时不覆盖
const ICON = {portrait:'人', costume:'服', pose:'姿'};
function poseSend(x){ return x.vs && x.vs[x.var || 'line'] ? x.vs[x.var || 'line'] : (x.im || x.th); }
function drawBar(){
  const xs = items(), busy = running();
  $('#rcStack').innerHTML = KINDS.map(k => R[k] && valid(R[k]) ? '<img src="'+esc(abs(R[k].th))+'" alt="">' : '<i>'+esc(PL.lang === 'ja' ? t(k)[0] : ICON[k])+'</i>').join('');
  $('#rcT').textContent = t('title');
  $('#rcSub').textContent = busy ? t('running').replace('{s}', Math.round((Date.now() - busy.at) / 1000)) : xs.length ? t('subN').replace('{n}', xs.length) : t('sub0');
  go.querySelector('.tx').textContent = busy ? t('cancel') : t('gen');
  busy ? go.setAttribute('data-busy', '') : go.removeAttribute('data-busy');
  go.disabled = !busy && !xs.length;
  $('#rcTg').setAttribute('aria-expanded', body.hidden ? 'false' : 'true');
}
function drawSlots(){
  $('#rcSlots').innerHTML = KINDS.map(k => { const x = R[k];
    const head = '<div class="rc-nh"><i>'+esc(ICON[k])+'</i>'+esc(t(k))+'<small>0'+(KINDS.indexOf(k) + 1)+' INPUT</small>'+(valid(x) ? '<button type="button" data-rm="'+k+'" aria-label="'+esc(t('remove'))+'">×</button>' : '')+'</div>';
    if (!valid(x)) return '<div class="rc-node vac" data-k="'+k+'">'+head+'<div class="rc-im"><a href="'+esc(UP + GO[k])+'">'+esc(t('pick'))+' →</a></div><div class="rc-nm">&nbsp;</div></div>';
    const n = PL.lang === 'ja' ? (x.n.ja || x.n.zh) : x.n.zh;
    const site = /^[a-z-]+$/.test(x.site || '') ? x.site : GO[k].slice(0, -1);
    const vsw = k === 'pose' && x.vs && x.vs.depth ? '<div class="rc-vsw" role="group">' + ['line', 'depth'].map(v =>
      '<button type="button" data-var="'+v+'" aria-pressed="'+((x.var || 'line') === v)+'">'+esc(t(v))+'</button>').join('') + '</div>' : '';
    return '<div class="rc-node" data-k="'+k+'">'+head+'<a class="rc-im" href="'+esc(UP + site + '/')+'"><img src="'+esc(abs(x.th))+'" alt="'+esc(n)+'"></a>'+
      '<div class="rc-nm" title="'+esc(n)+'">'+esc(n + (x.ang ? ' · ' + (PL.lang === 'ja' ? x.ang.ja : x.ang.zh) : ''))+'</div>'+vsw+'</div>';
  }).join('');
}
function drawPrompt(force){
  const o = opt();
  [...$('#rcLang').children].forEach(b => b.setAttribute('aria-pressed', b.dataset.pl === o.lang ? 'true' : 'false'));
  $('#rcStyle').value = o.style;
  [...$('#rcStyle').options].forEach((op, i) => { op.textContent = PL.lang === 'ja' ? STYLES[i][2] : STYLES[i][1]; });
  if (force || !edited) { pv.value = items().length ? prompt(o.lang, 'ref', o.style) : ''; edited = false; }
  pv.placeholder = t('empty');
}
function drawGen(){
  const G = PL.gen, c = G.cfg(), P = G.PROV[c.p] || G.PROV.openai;
  $('#rcPnT').textContent = t('pn'); $('#rcGnT').textContent = t('gn'); $('#rcCopy').textContent = t('copy');
  $('#rcServiceL').textContent = t('prov');
  $('#rcService').innerHTML = Object.entries(G.PROV).map(([k, v]) => '<option value="'+k+'">'+esc(v.name)+'</option>').join(''); $('#rcService').value = c.p;
  $('#rcModelL').textContent = t('model'); $('#rcRatioL').textContent = t('ratio'); $('#rcNL').textContent = t('count');
  const ms = [...new Set([G.modelOf(c, c.p), ...P.models])];
  $('#rcModel').innerHTML = ms.map(m => '<option>'+esc(m)+'</option>').join(''); $('#rcModel').value = G.modelOf(c, c.p);
  $('#rcRatio').innerHTML = G.RATIOS.map(r => '<option>'+r+'</option>').join(''); $('#rcRatio').value = c.ratio;
  $('#rcN').value = String(c.n || 1);
  $('#rcRun span').textContent = running() ? t('cancel') : t('gen');
  $('#rcBoard').textContent = t('board'); $('#rcClear').textContent = t('clear');
  $('#rcSetB').title = $('#rcSetB').ariaLabel = t('setT');
}
function drawSet(){
  const G = PL.gen, c = G.cfg();
  $('#rcSetT').textContent = t('setT');
  ['prov', 'key', 'base', 'mid', 'proto', 'field'].forEach(k => { $('#rc' + k[0].toUpperCase() + k.slice(1) + 'L').textContent = t(k); });
  $('#rcProv').innerHTML = Object.entries(G.PROV).map(([k, v]) => '<option value="'+k+'">'+esc(v.name)+'</option>').join('');
  $('#rcProv').value = c.p;
  $('#rcKey').value = G.key(c.p); $('#rcKey').placeholder = c.p === 'gemini' ? 'AIza…' : 'sk-…';
  const relay = c.p === 'relay'; $('#rcBase').value = (c.base && c.base[c.p]) || '';
  $('#rcBase').placeholder = G.PROV[c.p].base || 'https://…/v1';
  $('#rcProto').value = c.proto || 'edits'; $('#rcField').value = c.field || 'image[]';
  $('#rcProto').hidden = $('#rcProtoL').hidden = !relay; drawField();
  $('#rcSetHelp').textContent = t(relay ? 'relayHelp' : 'directHelp');
  $('#rcTest').textContent = t('test'); $('#rcTestMsg').textContent = '';
  $('#rcMid').value = G.modelOf(c, c.p);
  $('#rcModels').innerHTML = G.PROV[c.p].models.map(m => '<option value="'+esc(m)+'">').join('');
  $('#rcRem').checked = !!c.remember; $('#rcRemL').textContent = t('remember');
  $('#rcSave').textContent = t('save'); $('#rcForget').textContent = t('forget');
  const get = G.PROV[c.p].get;
  $('#rcSetNote').innerHTML = esc(t('setNote')) + (get ? ' <a href="'+esc(get)+'" target="_blank" rel="noopener noreferrer">'+esc(t('getKey'))+' ↗</a>' : '');
}
function drawField(){
  $('#rcField').hidden = $('#rcFieldL').hidden = PL.gen.cfg().p !== 'relay' || $('#rcProto').value !== 'edits';
}
$('#rcProto').addEventListener('change', drawField);
/* 连线：三个参考节点底部 → 提示词节点顶部，提示词右侧 → 生成节点左侧 */
function wires(){
  const box = $('#rcFlow'), svg = $('#rcWires'); if (body.hidden || !box.offsetWidth) return;
  const R0 = box.getBoundingClientRect(), pn = $('#rcPn').getBoundingClientRect(), gn = $('#rcGn').getBoundingClientRect();
  const at = (r, x, y) => [r.left - R0.left + r.width * x, r.top - R0.top + r.height * y];
  const busy = !!running(), seg = (a, b, cls) => '<path class="'+cls+'" d="M'+a[0]+','+a[1]+' C'+a[0]+','+(a[1] + b[1]) / 2+' '+b[0]+','+(a[1] + b[1]) / 2+' '+b[0]+','+b[1]+'"/>';
  const tgt = at(pn, .35, 0);
  let d = [...$('#rcSlots').children].map(n => seg(at(n.getBoundingClientRect(), .5, 1), tgt, n.classList.contains('vac') ? '' : (busy ? 'on' : ''))).join('');
  const a = at(pn, 1, .5), b = at(gn, 0, .45);
  d += '<path class="'+(busy ? 'on' : '')+'" d="M'+a[0]+','+a[1]+' C'+(a[0] + b[0]) / 2+','+a[1]+' '+(a[0] + b[0]) / 2+','+b[1]+' '+b[0]+','+b[1]+'"/>';
  svg.setAttribute('viewBox', '0 0 ' + R0.width + ' ' + R0.height); svg.innerHTML = d;
}
function drawAll(force){ drawBar(); if (!body.hidden){ drawSlots(); drawPrompt(force); drawGen(); drawJobs(); requestAnimationFrame(wires); } }
function openDock(o){ body.hidden = !o; rc.classList.toggle('open', o); try{ sessionStorage.setItem('pl.rcOpen', o ? '1' : ''); }catch(_){} drawAll(); }
$('#rcTg').addEventListener('click', () => openDock(body.hidden));
document.addEventListener('keydown', e => { if (e.key === 'Escape' && !body.hidden && !PL.top() && rc.contains(document.activeElement)){ openDock(false); $('#rcTg').focus(); } });
addEventListener('resize', () => requestAnimationFrame(wires));
$('#rcSlots').addEventListener('click', e => {
  const rm = e.target.closest('[data-rm]'); if (rm){ delete R[rm.dataset.rm]; edited = false; save(); return; }
  const v = e.target.closest('[data-var]'); if (v && R.pose){ R.pose.var = v.dataset.var; save(); }
});
$('#rcClear').addEventListener('click', () => { KINDS.forEach(k => delete R[k]); edited = false; save(); });
const setOpt = (k, v) => { R.opt = Object.assign(opt(), {[k]: v}); edited = false; save(); };
$('#rcLang').addEventListener('click', e => { const b = e.target.closest('[data-pl]'); if (b) setOpt('lang', b.dataset.pl); });
$('#rcStyle').addEventListener('change', e => setOpt('style', e.target.value));
pv.addEventListener('input', () => { edited = true; });
$('#rcCopy').addEventListener('click', () => { if (pv.value) PL.copy(pv.value); });
$('#rcModel').addEventListener('change', e => { const c = PL.gen.cfg(); PL.gen.setCfg({model: Object.assign({}, c.model, {[c.p]: e.target.value})}); });
$('#rcRatio').addEventListener('change', e => PL.gen.setCfg({ratio: e.target.value}));
$('#rcN').addEventListener('change', e => PL.gen.setCfg({n: +e.target.value}));
$('#rcSetB').addEventListener('click', () => { const s = $('#rcSet'); s.hidden = !s.hidden; if (!s.hidden){ drawSet(); $('#rcKey').focus(); } });
['#rcProv', '#rcService'].forEach(s => $(s).addEventListener('change', e => { PL.gen.setCfg({p: e.target.value}); drawSet(); }));
$('#rcSave').addEventListener('click', () => {
  const G = PL.gen, c = G.cfg(), base = $('#rcBase').value.trim();
  if ((base && !G.httpsOk(base)) || (c.p === 'relay' && !base)){ PL.toast(t('badBase')); return; }
  G.setCfg({remember: $('#rcRem').checked, model: Object.assign({}, c.model, {[c.p]: $('#rcMid').value.trim() || G.PROV[c.p].models[0]}),
    base: Object.assign({}, c.base, {[c.p]: base}), proto: $('#rcProto').value, field: $('#rcField').value});
  G.setKey(c.p, $('#rcKey').value.trim(), $('#rcRem').checked);
  $('#rcSet').hidden = true; PL.toast(t('saved'));
});
$('#rcTest').addEventListener('click', async () => {
  const G = PL.gen, c = G.cfg(), p = c.p, b = $('#rcBase').value.trim(), k = $('#rcKey').value.trim(), el = $('#rcTestMsg'), btn = $('#rcTest');
  const base = G.baseOf({base:{[p]:b}}, p);
  if (!G.httpsOk(base)){ el.textContent = t('badBase'); return; }
  if (!k){ el.textContent = t('needKey'); return; }
  btn.disabled = true; el.textContent = t('testing');
  const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), 15000);
  try{
    const headers = p === 'gemini' ? {'x-goog-api-key':k} : {authorization:'Bearer ' + k};
    const res = await fetch(base + '/models', {headers, signal:ctl.signal, credentials:'omit'});
    const text = await res.text(); let j; try{ j = JSON.parse(text); }catch(_){}
    const models = j && (j.data || j.models);
    if (res.status === 404 || res.ok && !Array.isArray(models)) el.textContent = t('noModels');
    else if (!res.ok){
      const err = G.parse([{status:res.status, text}]).err;
      el.textContent = t('e_' + err.k) + ' · HTTP ' + res.status;
    } else el.textContent = t('connected').replace('{n}', models.length);
  }catch(e){ el.textContent = t(ctl.signal.aborted ? 'testTimeout' : 'e_network'); }
  finally{ clearTimeout(timer); btn.disabled = false; }
});
$('#rcForget').addEventListener('click', () => { const c = PL.gen.cfg(); PL.gen.setKey(c.p, '', false); drawSet(); });

/* ── 生成 ── */
let JOBS = [];
const running = () => JOBS.find(j => j.state === 'queued' || j.state === 'running');
function say(msg, err){ const m = $('#rcMsg'); m.hidden = !msg; m.className = 'rc-msg' + (err ? ' err' : ''); m.innerHTML = msg || ''; }
async function generate(){
  const xs = items(); if (!xs.length){ say(esc(t('needOne')), true); return; }
  const G = PL.gen;
  if (!G.key(G.cfg().p)){ if (body.hidden) openDock(true); $('#rcSet').hidden = false; drawSet(); $('#rcKey').focus(); say(esc(t('needKey')), true); return; }
  const send = xs.map(x => Object.assign({}, x, {send: x.k === 'pose' ? poseSend(x) : (x.im || x.th)}));
  const text = pv.value.trim() || prompt(opt().lang, 'ref', opt().style);
  say('');
  try{
    await G.run({items: send, prompt: text, up: UP});
    if (!G.swOk) say(esc(t('inPage')));
  }catch(e){
    const k = e && e.k;
    say(esc(k === 'offline' ? t('offline') : k === 'nokey' ? t('needKey') : k === 'base' ? t('badBase') : t('e_network')), true);
  }
}
go.addEventListener('click', () => { const r = running(); r ? PL.gen.cancel(r.id) : generate(); });
$('#rcRun').addEventListener('click', () => { const r = running(); r ? PL.gen.cancel(r.id) : generate(); });
const urls = new Map();
const src = (j, i) => { const o = j.out[i]; if (o.url) return o.url; const k = j.id + ':' + i; if (!urls.has(k)) urls.set(k, URL.createObjectURL(o.blob)); return urls.get(k); };
function drawJobs(){
  const box = $('#rcRes'); box.hidden = !JOBS.length; if (!JOBS.length) return;
  $('#rcResT').textContent = t('res'); $('#rcResClr').textContent = t('resClr');
  $('#rcGal').innerHTML = JOBS.slice(0, 12).map(j => {
    if (j.state === 'queued' || j.state === 'running')
      return '<div class="rc-it run"><div><b data-at="'+j.at+'">'+Math.round((Date.now() - j.at) / 1000)+'s</b>'+esc(j.model)+'<br><button type="button" data-cancel="'+j.id+'">'+esc(t('cancel'))+'</button></div></div>';
    if (j.state === 'error' || j.state === 'canceled'){
      const k = j.state === 'canceled' ? 'cancel' : (j.err && j.err.k) || 'bad';
      return '<div class="rc-it bad" title="'+esc(j.err && j.err.msg || '')+'"><div>'+esc(t('e_' + k) || t('e_bad'))+'<br><button type="button" data-del="'+j.id+'">'+esc(t('delOne'))+'</button></div></div>';
    }
    return (j.out || []).map((o, i) => '<div class="rc-it"><img src="'+esc(src(j, i))+'" alt="" data-view="'+j.id+':'+i+'"><div class="ov">'+
      '<a href="'+esc(src(j, i))+'" download="photoai-'+j.id+'-'+(i + 1)+'.'+(((o.mime || 'image/png').split('/')[1]) || 'png')+'" title="'+esc(t('dl'))+'" target="_blank" rel="noopener">'+DL+'</a>'+
      '<button type="button" data-del="'+j.id+'" title="'+esc(t('delOne'))+'">×</button></div></div>').join('');
  }).join('');
}
$('#rcGal').addEventListener('click', e => {
  const c = e.target.closest('[data-cancel]'); if (c){ PL.gen.cancel(c.dataset.cancel); return; }
  const d = e.target.closest('[data-del]'); if (d){ PL.gen.del(d.dataset.del); return; }
  const v = e.target.closest('[data-view]'); if (v){ const vw = $('#rcView'); vw.querySelector('img').src = v.src; vw.hidden = false; }
});
$('#rcView').addEventListener('click', e => { e.currentTarget.hidden = true; });
$('#rcResClr').addEventListener('click', () => PL.gen.clear());
let lastDone = null;
async function refreshJobs(){
  const prev = JOBS; JOBS = await PL.gen.jobs();
  const fresh = JOBS.find(j => j.state === 'done' && !prev.some(p => p.id === j.id && p.state === 'done'));
  if (fresh && prev.length && lastDone !== fresh.id){ lastDone = fresh.id; $('#rcDot').hidden = !body.hidden ? true : false;
    PL.toast(t('done').replace('{n}', (fresh.out || []).length)); }
  const bad = JOBS[0] && JOBS[0].state === 'error' && !prev.some(p => p.id === JOBS[0].id && p.state === 'error') ? JOBS[0] : null;
  if (bad && prev.length) say(esc(t('e_' + ((bad.err && bad.err.k) || 'bad'))), true);
  drawAll();
}
setInterval(() => { if (running()){ drawBar(); document.querySelectorAll('#rcGal [data-at]').forEach(b => { b.textContent = Math.round((Date.now() - +b.dataset.at) / 1000) + 's'; }); } }, 1000);
$('#rcTg').addEventListener('click', () => { $('#rcDot').hidden = true; });

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
    edited = false; rc.classList.remove('bump'); void rc.offsetWidth; rc.classList.add('bump');
  },
};
addEventListener('pl:recipe', () => { drawAll(); syncAll(); });
addEventListener('pl:lang', () => { drawAll(); syncAll(); });
addEventListener('pl:gen', refreshJobs);
addEventListener('storage', e => { if (e.key === KEY){ R = load(); dispatchEvent(new Event('pl:recipe')); } else if (e.key === 'pl.gen' || e.key === 'pl.genkey') drawAll(); });
let o0 = false; try{ o0 = sessionStorage.getItem('pl.rcOpen') === '1'; }catch(_){}
if (o0) openDock(true); else drawBar();
refreshJobs();
if (PL.gen.swOk) PL.gen.sw(UP);
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
    """生图核心（shared/gen.py，定义 PL.gen）+ 配方栏"""
    import json
    import gen
    return _strip(gen.JS) + "\n" + _strip(JS.replace("__STYLES__", json.dumps(STYLES, ensure_ascii=False)))
