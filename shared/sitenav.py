# -*- coding: utf-8 -*-
"""子站共用的顶部栏与快捷键面板

五个子站（三套页面模板：人像、服装、姿势生成器）页首放同一条栏：
左边 photoai.life 首页，中间各子站（当前站高亮），右边「?」打开快捷键说明。
中日文案都写进 HTML，按 <html data-lang> 用 CSS 只显示一种（三套模板切换语言时都会改 data-lang），
不依赖各页面自己的翻译函数。入口页（hub）不放这条栏。

用法（各站构建脚本）:

    import sitenav
    head, body = sitenav.parts("pose", max_width=1600, keys=sitenav.POSE_KEYS, search="#q")
    html = html.replace("__SITENAV_HEAD__", head).replace("__SITENAV__", body)
"""
import json, os
from html import escape

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 栏上的短名；sites.json 里新加的站没写时用它的 name
LABELS = {
    "portrait": {"zh": "人像", "ja": "ポートレート"},
    "costume": {"zh": "服装", "ja": "衣装"},
    "pose": {"zh": "姿势", "ja": "ポーズ"},
    "pose-depth": {"zh": "深度图", "ja": "デプス"},
    "shisei": {"zh": "CC0 线稿", "ja": "CC0 線画"},
}

# 快捷键说明：([按键], 中文, 日文)
_SEARCH = (["/"], "跳到搜索框", "検索欄へ移動")
_ESC = (["Esc"], "关闭大图或对话框", "拡大表示・ダイアログを閉じる")
_HELP = (["?"], "打开 / 关闭这个面板", "このパネルを開く / 閉じる")
POSE_KEYS = [_SEARCH, (["←", "→"], "大图：切换视角", "拡大表示：アングル切り替え"),
             (["↑", "↓"], "大图：上一个 / 下一个姿势", "拡大表示：前 / 次のポーズ"), _ESC, _HELP]
COSTUME_KEYS = [_SEARCH, (["←", "→"], "大图：上一张 / 下一张", "拡大表示：前 / 次へ"), _ESC, _HELP]
PORTRAIT_KEYS = [(["←", "→"], "大图：上一张 / 下一张", "拡大表示：前 / 次へ"), _ESC, _HELP]

# 与入口页 favicon.svg 同一图形（渐变 id 换成页面里不会重名的 snG）
LOGO = ('<svg viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="snG" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#2563eb"/><stop offset="1" stop-color="#7c3aed"/></linearGradient></defs>'
        '<rect width="64" height="64" rx="14" fill="url(#snG)"/>'
        '<rect x="14" y="14" width="16" height="16" rx="4" fill="#fff"/>'
        '<rect x="34" y="14" width="16" height="16" rx="4" fill="#fff" fill-opacity=".72"/>'
        '<rect x="14" y="34" width="16" height="16" rx="4" fill="#fff" fill-opacity=".72"/>'
        '<rect x="34" y="34" width="16" height="16" rx="4" fill="#fff" fill-opacity=".45"/></svg>')

# 三套模板的主题变量名不同（姿势 / 服装用 --tx* / --panel / --ac，人像用 --fg / --muted / --paper / --accent），
# 用 var(a, var(b, 兜底)) 两边兼容，深浅主题跟随页面
CSS = """
.sn,.sn-box{--sn-tx:var(--tx,var(--fg,#16191f));--sn-tx2:var(--tx2,var(--muted,#525b6a));--sn-tx3:var(--tx3,var(--muted,#8a93a3));
  --sn-line:var(--line,#e3e7ed);--sn-line2:var(--line2,var(--line,#ccd4e0));--sn-bg:var(--bg2,var(--paper,#fff));
  --sn-panel:var(--panel,var(--paper,#fff));--sn-ac:var(--ac,var(--accent,#2563eb));--sn-on-ac:var(--on-ac,var(--accent-fg,#fff))}
html:not([data-lang="ja"]) .snl-ja,html[data-lang="ja"] .snl-zh{display:none!important}
.sn{background:var(--sn-bg);border-bottom:1px solid var(--sn-line);font-family:inherit}
.sn-in{max-width:var(--sn-max,1600px);margin:0 auto;padding:0 clamp(16px,4vw,48px);display:flex;align-items:center;gap:18px;height:46px}
.sn-home{flex:none;display:inline-flex;align-items:center;gap:8px;color:var(--sn-tx);text-decoration:none;
  font-size:13.5px;font-weight:700;letter-spacing:.01em}
.sn-home svg{width:22px;height:22px;display:block}
.sn-links{flex:1 1 auto;min-width:0;display:flex;overflow-x:auto;scrollbar-width:none}
.sn-links::-webkit-scrollbar{display:none}
.sn-links a{flex:none;display:flex;align-items:center;height:46px;padding:0 12px;color:var(--sn-tx2);
  text-decoration:none;font-size:13px;white-space:nowrap;transition:color .15s,box-shadow .15s}
.sn-links a:hover{color:var(--sn-tx)}
.sn-links a[aria-current="page"]{color:var(--sn-tx);font-weight:700;box-shadow:inset 0 -2px 0 var(--sn-ac)}
.sn-help{flex:none;width:28px;height:28px;border-radius:50%;border:1px solid var(--sn-line2);background:transparent;
  color:var(--sn-tx2);font:inherit;font-size:13px;font-weight:700;line-height:1;cursor:pointer;transition:.15s}
.sn-help:hover{color:var(--sn-tx);border-color:var(--sn-tx3)}
.sn-vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.sn-box{position:fixed;inset:0;z-index:90;background:var(--scrim,rgba(15,23,42,.55));backdrop-filter:blur(6px);
  display:flex;align-items:center;justify-content:center;padding:16px}
.sn-box[hidden]{display:none}
.sn-card{width:min(400px,100%);background:var(--sn-panel);color:var(--sn-tx);border:1px solid var(--sn-line);
  border-radius:16px;padding:20px 22px 16px;box-shadow:var(--sh,0 10px 30px rgba(0,0,0,.25))}
.sn-card h3{margin:0 0 14px;font-size:16px}
.sn-card dl{display:grid;grid-template-columns:auto 1fr;gap:10px 16px;margin:0 0 18px;font-size:13px;align-items:center}
.sn-card dt{white-space:nowrap}
.sn-card dd{margin:0;color:var(--sn-tx2)}
.sn-card kbd{display:inline-block;min-width:24px;padding:1px 6px;margin-right:4px;border:1px solid var(--sn-line2);
  border-bottom-width:2px;border-radius:5px;background:var(--sn-bg);color:var(--sn-tx);text-align:center;
  font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.sn-row{display:flex;justify-content:flex-end}
.sn-row button{height:34px;padding:0 16px;border-radius:10px;border:1px solid var(--sn-ac);background:var(--sn-ac);
  color:var(--sn-on-ac);font:inherit;font-size:13px;font-weight:700;cursor:pointer}
@media(max-width:560px){.sn-name{display:none}.sn-in{gap:8px}.sn-links a{padding:0 9px;font-size:12.5px}}
"""

# 「?」开关面板，「/」跳到搜索框。在输入框里打字、或大图 / 对话框开着时不响应
JS = r"""(function(){
  const box = document.getElementById('snHelp'), btn = document.getElementById('snHelpBtn');
  const SEARCH = __SEARCH__;
  const open = () => { box.hidden = false; box.querySelector('[data-close]').focus(); };
  const close = () => { box.hidden = true; btn.focus(); };
  btn.addEventListener('click', () => { if (box.hidden) open(); else close(); });
  box.addEventListener('click', e => { if (e.target === box || e.target.closest('[data-close]')) close(); });
  const busy = () => document.querySelector('.modal.open, .lightbox:not([hidden]), .agebox:not([hidden])');
  document.addEventListener('keydown', e => {
    if (!box.hidden) {
      if (e.key === 'Escape' || e.key === '?') { e.preventDefault(); e.stopImmediatePropagation(); close(); }
      return;
    }
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const el = document.activeElement;
    if (el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable)) return;
    if (busy()) return;
    if (e.key === '?') { e.preventDefault(); open(); }
    else if (e.key === '/' && SEARCH) {
      const q = document.querySelector(SEARCH);
      if (q) { e.preventDefault(); q.focus(); q.select(); }
    }
  }, true);
})();"""


def _bi(zh, ja):
    return f'<span class="snl-zh">{escape(zh)}</span><span class="snl-ja">{escape(ja)}</span>'


def parts(site_id, max_width, keys, search=None):
    """返回 (放进 <head> 的样式, 放在 <body> 开头的栏 + 快捷键面板 + 脚本)"""
    with open(os.path.join(REPO, "sites.json"), encoding="utf-8") as f:
        sites = json.load(f)["sites"]
    links = []
    for s in sites:
        lab = LABELS.get(s["id"], s["name"])
        cur = ' aria-current="page"' if s["id"] == site_id else ""
        links.append(f'<a href="../{escape(s["id"])}/"{cur}>{_bi(lab["zh"], lab["ja"])}</a>')
    rows = "".join(
        "<dt>" + "".join(f"<kbd>{escape(k)}</kbd>" for k in ks) + f"</dt><dd>{_bi(zh, ja)}</dd>"
        for ks, zh, ja in keys if search or ks != ["/"])
    body = (f'<nav class="sn" aria-label="photoai.life"><div class="sn-in">'
            f'<a class="sn-home" href="../">{LOGO}<span class="sn-name">photoai.life</span></a>'
            f'<div class="sn-links">{"".join(links)}</div>'
            f'<button type="button" class="sn-help" id="snHelpBtn" aria-haspopup="dialog">'
            f'<span aria-hidden="true">?</span><span class="sn-vh">{_bi("快捷键", "ショートカット")}</span></button>'
            f'</div></nav>\n'
            f'<div class="sn-box" id="snHelp" role="dialog" aria-modal="true" aria-labelledby="snHelpT" hidden>'
            f'<div class="sn-card"><h3 id="snHelpT">{_bi("快捷键", "ショートカット")}</h3><dl>{rows}</dl>'
            f'<div class="sn-row"><button type="button" data-close>{_bi("知道了", "閉じる")}</button></div></div></div>\n'
            f'<script>{JS.replace("__SEARCH__", json.dumps(search))}</script>\n')
    head = f"<style>{CSS}.sn{{--sn-max:{int(max_width)}px}}</style>"
    return head, body
