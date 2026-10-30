# -*- coding: utf-8 -*-
"""生成资源站入口页

用法:
  python build_hub.py                # 读取 sites.json → index.html
  python build_hub.py --check        # 仅检查封面图是否存在

新增站点：在 sites.json 的 sites 数组里追加一条，重跑本脚本即可。
"""
import json, os, sys

HUB  = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HUB)
CFG  = os.path.join(ROOT, "sites.json")
OUT  = os.path.join(HUB, "index.html")

LICENSE_LABEL = {
    "cc0":        {"zh": "CC0", "ja": "CC0", "cls": "ok"},
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
<meta name="description" content="__DESC__">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<script>
(function(){try{
  var t=localStorage.getItem('hub.theme'); if(t==='light'||t==='dark') document.documentElement.dataset.theme=t;
  var l=localStorage.getItem('hub.lang');  if(l==='zh'||l==='ja')      document.documentElement.dataset.lang=l;
}catch(e){}})();
</script>
<style>
:root{
  --r:18px;
  --f:system-ui,-apple-system,"Segoe UI","PingFang SC","Hiragino Sans","Noto Sans SC","Microsoft YaHei",sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --bg:#f4f6f9;--panel:#ffffff;--line:#e3e7ed;--line2:#ccd4e0;
  --tx:#16191f;--tx2:#525b6a;--tx3:#8a93a3;--ac:#2563eb;--on-ac:#fff;
  --hover:#eef1f6;--hb:#b9c3d2;
  --sh:0 8px 24px rgba(16,24,40,.10);--g1:#e6eefc;--g2:#f0e9fb;
  --grad:linear-gradient(90deg,#2563eb,#7c3aed);
  --ok-bg:#e7f6ec;--ok-tx:#186b3a;--warn-bg:#fdf2e0;--warn-tx:#8a5a12;--no-bg:#fdeaea;--no-tx:#a02020;
}
html[data-theme="dark"]{
  --bg:#0d0f12;--panel:#1a1e24;--line:#272c34;--line2:#343a44;
  --tx:#e9ecf1;--tx2:#a3abb8;--tx3:#6c7482;--ac:#8fb4ff;--on-ac:#0b1220;
  --hover:#232831;--hb:#3b4350;
  --sh:0 10px 30px rgba(0,0,0,.45);--g1:#1b2433;--g2:#211a2b;
  --grad:linear-gradient(90deg,#c3d5ff,#e3c8ff);
  --ok-bg:#12291c;--ok-tx:#7ee2a8;--warn-bg:#2b2213;--warn-tx:#f0c274;--no-bg:#2b1616;--no-tx:#f19a9a;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--tx);font-family:var(--f);min-height:100vh;
  -webkit-font-smoothing:antialiased;transition:background-color .22s,color .22s;
  background-image:radial-gradient(1200px 500px at 15% -10%,var(--g1) 0,transparent 60%),
                   radial-gradient(900px 400px at 100% 0,var(--g2) 0,transparent 55%)}
a{color:inherit}
button{font:inherit;color:inherit}

.wrap{max-width:1180px;margin:0 auto;padding:52px clamp(18px,5vw,40px) 72px}

/* 顶栏 */
.top{display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap;margin-bottom:10px}
.eyebrow{font-size:11.5px;letter-spacing:.24em;color:var(--tx3);text-transform:uppercase;padding-top:6px}
.switches{display:flex;gap:8px;margin-left:auto}
.switch{display:flex;border:1px solid var(--line2);border-radius:10px;overflow:hidden;background:var(--panel)}
.switch button{height:34px;min-width:34px;padding:0 9px;border:0;background:transparent;color:var(--tx2);
  font-size:12px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.13s;white-space:nowrap}
.switch button+button{border-left:1px solid var(--line2)}
.switch button:hover{background:var(--hover);color:var(--tx)}
.switch button[aria-pressed="true"]{background:var(--ac);color:var(--on-ac);font-weight:700}
.switch svg{width:14px;height:14px;display:block}

h1{margin:10px 0 10px;font-size:clamp(26px,4vw,40px);font-weight:700;letter-spacing:.02em;line-height:1.25}
h1 span{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.lead{color:var(--tx2);font-size:14px;line-height:1.8;margin:0 0 12px;max-width:680px}
.count-line{display:flex;align-items:center;gap:10px;color:var(--tx3);font-size:12.5px;
  letter-spacing:.06em;margin:0 0 34px}
.count-line b{font-family:var(--mono);color:var(--tx2);font-weight:600}

/* 卡片：左图右文。图片框 3:4 贴合素材比例，竖构图基本不裁切 */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:18px}
.card{display:grid;grid-template-columns:156px 1fr;background:var(--panel);
  border:1px solid var(--line);border-radius:var(--r);overflow:hidden;text-decoration:none;
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s}
.card:hover{transform:translateY(-3px);box-shadow:var(--sh);border-color:var(--hb)}
.thumb{position:relative;aspect-ratio:3/4;background:var(--line);overflow:hidden}
.thumb img{width:100%;height:100%;object-fit:cover;display:block;
  transition:transform .5s cubic-bezier(.2,.7,.2,1)}
.card:hover .thumb img{transform:scale(1.05)}
.info{padding:17px 19px 16px;display:flex;flex-direction:column;gap:7px;min-width:0}
.head{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
.head h2{margin:0;font-size:17px;font-weight:700;letter-spacing:.01em}
.code{font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;color:var(--tx3)}
.desc{margin:0;font-size:12.5px;color:var(--tx2);line-height:1.65;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.nums{display:flex;gap:16px;margin-top:auto;padding-top:11px;border-top:1px solid var(--line)}
.nums div{display:flex;flex-direction:column;gap:0}
.nums b{font-size:15px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1.35}
.nums span{font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--tx3)}
.foot{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:10px}
.go{display:inline-flex;align-items:center;gap:7px;font-size:13px;color:var(--ac);font-weight:600}
.go svg{width:15px;height:15px;transition:transform .18s}
.card:hover .go svg{transform:translateX(3px)}
.lic{font-size:10.5px;letter-spacing:.1em;padding:3px 9px;border-radius:999px;font-weight:600;white-space:nowrap}
.lic.ok{background:var(--ok-bg);color:var(--ok-tx)}
.lic.warn{background:var(--warn-bg);color:var(--warn-tx)}
.lic.no{background:var(--no-bg);color:var(--no-tx)}

footer{margin-top:38px;padding-top:16px;border-top:1px solid var(--line);
  color:var(--tx3);font-size:11.5px;line-height:1.8}
.ft{margin:0 0 6px;font-size:10.5px;font-weight:600;letter-spacing:.16em;
  text-transform:uppercase;color:var(--tx3);opacity:.8}
.credits{list-style:none;margin:0 0 6px;padding:0;max-width:940px;
  display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px 34px}
.credits li{display:flex;align-items:baseline;gap:9px;padding:2px 0}
.c-site{min-width:78px;font-size:12px;font-weight:600;color:var(--tx2);
  text-decoration:none;border-bottom:1px solid transparent}
.c-site:hover{color:var(--ac);border-color:var(--ac)}
.c-author{color:var(--tx3);white-space:nowrap}
.c-author a{color:var(--tx3);text-decoration:none;border-bottom:1px solid transparent}
.c-author a:hover{color:var(--ac);border-color:var(--ac)}
.credits .lic{margin-left:auto;font-size:9.5px;padding:1px 7px}
footer .note{margin:0;color:var(--tx3);opacity:.85}

@media(max-width:820px){ .cards{grid-template-columns:1fr} }
@media(max-width:720px){ .credits{grid-template-columns:1fr} }
@media(max-width:520px){
  .card{grid-template-columns:112px 1fr}
  .info{padding:14px 15px 13px;gap:6px}
  .head h2{font-size:15.5px}
  .desc{-webkit-line-clamp:2}
  .nums{gap:12px}
  .nums b{font-size:14px}
}
@media(max-width:600px){ .wrap{padding-top:32px} .switches{width:100%;margin-left:0} }
</style>
</head>
<body>
<div class="wrap">

  <div class="top">
    <div class="eyebrow" id="eyebrow"></div>
    <div class="switches">
      <div class="switch" id="themeSw" role="group" aria-label="Theme">
        <button type="button" data-t="light" title="Light" aria-label="Light"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/></svg></button>
        <button type="button" data-t="dark" title="Dark" aria-label="Dark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg></button>
      </div>
      <div class="switch" id="langSw" role="group" aria-label="Language">
        <button type="button" data-l="zh">中文</button>
        <button type="button" data-l="ja">日本語</button>
      </div>
    </div>
  </div>

  <h1><span id="h1"></span></h1>
  <p class="lead" id="lead"></p>
  <p class="count-line"><b id="cnt"></b><span id="cntLbl"></span></p>

  <div class="cards" id="cards"></div>

  <footer>
    <h2 class="ft" id="ftitle"></h2>
    <ul class="credits" id="credits"></ul>
    <p class="note" id="fnote"></p>
  </footer>
</div>

<script>
const DATA = __DATA__;
const LIC = __LIC__;
const LIC_NAME = {
  zh: { ok: 'CC0', warn: '有条件', no: '禁止再分发' },
  ja: { ok: 'CC0', warn: '条件付き', no: '再配布禁止' }
};

let LANG  = document.documentElement.dataset.lang  || 'zh';
let THEME = document.documentElement.dataset.theme || 'light';

const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const tx = o => (o && typeof o === 'object') ? (o[LANG] || o.zh || '') : (o || '');

function render(){
  const M = DATA.meta;

  $('#eyebrow').textContent = M.eyebrow;
  $('#h1').textContent = tx(M.title);
  $('#lead').textContent = tx(M.lead);
  $('#cnt').textContent = String(DATA.sites.length).padStart(2, '0');
  $('#cntLbl').textContent = LANG === 'zh' ? '个站点' : 'サイト';
  document.title = tx(M.title) + ' · ' + DATA.sites.length + (LANG === 'zh' ? ' 站' : ' サイト');

  $('#cards').innerHTML = DATA.sites.map(s => {
    const lic = LIC[s.license] || LIC.restricted;
    return '<a class="card" href="./' + esc(s.id) + '/">' +
      '<div class="thumb">' +
        '<img src="' + esc('./' + s.id + '/' + s.cover) + '" alt="' + esc(s.code) + '" loading="lazy"' +
          (s.coverPos ? ' style="object-position:' + esc(s.coverPos) + '"' : '') + '>' +
      '</div>' +
      '<div class="info">' +
        '<div class="head"><h2>' + esc(tx(s.name)) + '</h2>' +
          '<span class="code">' + esc(s.code) + '</span></div>' +
        '<p class="desc">' + esc(tx(s.desc)) + '</p>' +
        '<div class="nums">' + s.stats.map(st =>
          '<div><b>' + esc(st.v) + '</b><span>' + esc(tx(st.l)) + '</span></div>').join('') + '</div>' +
        '<div class="foot">' +
          '<span class="go">' + (LANG === 'zh' ? '进入' : '開く') +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h13M13 6l6 6-6 6"/></svg></span>' +
          '<span class="lic ' + esc(lic.cls) + '">' + esc(LIC_NAME[LANG][lic.cls]) + '</span>' +
        '</div>' +
      '</div></a>';
  }).join('');

  $('#ftitle').textContent = tx(M.creditTitle);
  $('#fnote').textContent = tx(M.licenseNote);

  // 素材来源与版权：链接原站、标注原作者、标出各站授权
  $('#credits').innerHTML = DATA.sites.map(s => {
    const lic = LIC[s.license] || LIC.restricted;
    const host = String(s.source || '').replace(/^https?:\/\//, '').replace(/\/$/, '');
    const handle = String(s.author.url || '').split('/').pop();
    return '<li>' +
      '<a class="c-site" href="' + esc(s.source) + '" target="_blank" rel="noopener noreferrer"' +
        ' title="' + esc(host) + '">' + esc(tx(s.name)) + '</a>' +
      '<span class="c-author">' + esc(s.author.name) + ' <a href="' + esc(s.author.url) +
        '" target="_blank" rel="noopener noreferrer">@' + esc(handle) + '</a></span>' +
      '<span class="lic ' + esc(lic.cls) + '">' + esc(LIC_NAME[LANG][lic.cls]) + '</span>' +
    '</li>';
  }).join('');

  document.querySelectorAll('#themeSw button').forEach(b =>
    b.setAttribute('aria-pressed', b.dataset.t === THEME ? 'true' : 'false'));
  document.querySelectorAll('#langSw button').forEach(b =>
    b.setAttribute('aria-pressed', b.dataset.l === LANG ? 'true' : 'false'));
  document.documentElement.lang = LANG === 'zh' ? 'zh-CN' : 'ja';
}

$('#themeSw').addEventListener('click', e => {
  const b = e.target.closest('[data-t]'); if (!b || b.dataset.t === THEME) return;
  THEME = b.dataset.t;
  document.documentElement.dataset.theme = THEME;
  try { localStorage.setItem('hub.theme', THEME); } catch(_){}
  render();
});
$('#langSw').addEventListener('click', e => {
  const b = e.target.closest('[data-l]'); if (!b || b.dataset.l === LANG) return;
  LANG = b.dataset.l;
  document.documentElement.dataset.lang = LANG;
  try { localStorage.setItem('hub.lang', LANG); } catch(_){}
  render();
});

render();
</script>
</body>
</html>
"""


def main():
    cfg = load()
    only_check = "--check" in sys.argv

    print(f"读取 sites.json：{len(cfg['sites'])} 个站点")
    bad = check(cfg)
    if bad:
        print(f"\n⚠️  {bad} 张封面缺失，生成的页面会出现空图。")

    if only_check:
        print("\n仅校验模式，未生成 index.html")
        return 1 if bad else 0

    lic = {k: {"cls": v["cls"]} for k, v in LICENSE_LABEL.items()}
    data = json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))
    lic_js = json.dumps(lic, ensure_ascii=False, separators=(",", ":"))

    title = cfg["meta"]["title"]["zh"] + " · " + str(len(cfg["sites"])) + " 站"
    desc = cfg["meta"]["lead"]["zh"]

    html = (TEMPLATE
            .replace("__TITLE__", title)
            .replace("__DESC__", desc)
            .replace("__LIC__", lic_js)
            .replace("__DATA__", data))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    print(f"\n写出 index.html  {os.path.getsize(OUT)/1024:.1f} KB")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
