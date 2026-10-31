# -*- coding: utf-8 -*-
"""成人向内容：判定规则与画廊里的 18+ 开关

规则写在 sites.json 各站的 "adult" 字段：{manifest 字段名: [取值, ...]}，
manifest 里任一字段的取值命中，这张图就算成人向。例如姿势集：

    "adult": {"系列": ["2人絡み", "全身1人・セクシー系"], "分類": ["胸寄せ・谷間強調系", "セクシー・露骨寄り系"]}

姿势与服装的分类口径与 posewear（atuizz/posewear，MIT）的 18+ 开关一致；Shisei 用上游的 rating。
静态落地页不放成人向缩略图（shared/pose_seo.py、sites/costume/scripts/seo.py），tests/run.py 据此检查。

画廊页：成人向内容默认隐藏（Shisei 默认模糊），工具栏的「18+」开关打开后显示。
第一次打开要确认年龄。五个子站同源，状态存 localStorage 的 hub.adult，确认存 hub.ageOk，各图库通用。
两套页面模板（服装、姿势生成器）都用这里的 css() / switch_html() / box_html() / js()。
"""
import json, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rules(site_id):
    """站点的 adult 规则；没有配置时返回空 dict（该站没有成人向内容）"""
    with open(os.path.join(REPO, "sites.json"), encoding="utf-8") as f:
        sites = json.load(f)["sites"]
    return next((s.get("adult", {}) for s in sites if s["id"] == site_id), {})


def is_adult(row, rule):
    return any(row.get(k) in vs for k, vs in rule.items())


# ── 画廊页的 18+ 开关 ─────────────────────────────────────────
# 文案；各站另给 ageWhat（这个图库里哪些内容算成人向），合并进站点 UI
UI = {
    "zh": {
        "adultTipOff": "成人向内容已隐藏，点击显示",
        "adultTipOffBlur": "偏性感的姿势已模糊，点击取消模糊",
        "adultTipOn": "成人向内容已显示，点击隐藏",
        "ageTitle": "显示成人向内容？",
        "ageNote": "仅适合已满 18 岁的用户。确认一次后，各图库都可以用「18+」开关随时打开或关闭。",
        "ageYes": "我已满 18 岁，显示", "ageNo": "暂不",
        "adultEmptyTitle": "这是成人向内容",
        "adultEmptyDesc": "打开右上角的「18+」开关后可以查看。",
        "adultEmptyGo": "打开 18+",
    },
    "ja": {
        "adultTipOff": "成人向けの内容は非表示です。クリックで表示",
        "adultTipOffBlur": "セクシーなポーズはぼかし表示です。クリックで解除",
        "adultTipOn": "成人向けの内容を表示中。クリックで非表示",
        "ageTitle": "成人向けの内容を表示しますか？",
        "ageNote": "18 歳以上の方のみご覧ください。一度確認すると、各ギャラリーの「18+」スイッチでいつでも切り替えられます。",
        "ageYes": "18 歳以上です。表示する", "ageNo": "やめておく",
        "adultEmptyTitle": "成人向けの内容です",
        "adultEmptyDesc": "右上の「18+」スイッチをオンにすると表示されます。",
        "adultEmptyGo": "18+ をオン",
    },
}


def ui(site_ui, what):
    """把开关文案与本站的 ageWhat 合并进站点 UI（站点自己的同名键优先）"""
    return {lang: {**UI.get(lang, {}), "ageWhat": what.get(lang, ""), **strings}
            for lang, strings in site_ui.items()}


# 两套模板的主题变量同名（--panel / --line / --tx / --ac …），这段样式两边通用
CSS = (
    ".switch.adultsw button{min-width:44px;font-weight:700;letter-spacing:.02em}"
    ".agebox{position:fixed;inset:0;z-index:80;background:var(--scrim);backdrop-filter:blur(6px);"
    "display:flex;align-items:center;justify-content:center;padding:16px}"
    ".agebox[hidden]{display:none}"
    ".agecard{width:min(420px,100%);background:var(--panel);color:var(--tx);border:1px solid var(--line);"
    "border-radius:16px;padding:22px 22px 18px;box-shadow:var(--sh)}"
    ".agecard h3{margin:0 0 8px;font-size:17px}"
    ".agecard p{margin:0 0 18px;font-size:13.5px;line-height:1.75;color:var(--tx2)}"
    ".agecard .row{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}"
    ".agecard button{height:36px;padding:0 16px;border-radius:10px;border:1px solid var(--line2);"
    "background:var(--bg2);color:var(--tx);font-size:13px;cursor:pointer}"
    ".agecard button.primary{background:var(--ac);border-color:var(--ac);color:var(--on-ac);font-weight:700}"
    ".empty .adult-go{margin-top:14px;height:36px;padding:0 16px;border-radius:10px;border:1px solid var(--ac);"
    "background:var(--ac);color:var(--on-ac);font-size:13px;font-weight:700;cursor:pointer}")

SWITCH_HTML = ('\n        <div class="switch adultsw" role="group">'
               '<button type="button" id="adultSw" aria-pressed="false">18+</button></div>')

BOX_HTML = ('<div class="agebox" id="ageBox" role="dialog" aria-modal="true" aria-labelledby="ageT" hidden>'
            '<div class="agecard"><h3 id="ageT"></h3><p id="ageP"></p><div class="row">'
            '<button type="button" id="ageN"></button><button type="button" class="primary" id="ageY"></button>'
            '</div></div></div>')

# 页面需要先定义 $、esc、t（三套模板都有）和 onAdult()（开关变化后重画）
JS = r"""
/* ══ 18+ 开关（shared/adult.py）══ */
const ADULT_MODE = '__MODE__';   // hide：默认隐藏成人向条目；blur：默认模糊
let ADULT = false;               // 五个子站同源，状态存 hub.adult，年龄确认存 hub.ageOk
try{ ADULT = localStorage.getItem('hub.adult') === '1'; }catch(_){}
const adultSw = $('#adultSw'), ageBox = $('#ageBox');
function adultStatic(){
  adultSw.setAttribute('aria-pressed', ADULT ? 'true' : 'false');
  adultSw.title = t(ADULT ? 'adultTipOn' : (ADULT_MODE === 'blur' ? 'adultTipOffBlur' : 'adultTipOff'));
  adultSw.setAttribute('aria-label', adultSw.title);
  $('#ageT').textContent = t('ageTitle');
  $('#ageP').textContent = t('ageWhat') + t('ageNote');
  $('#ageY').textContent = t('ageYes');
  $('#ageN').textContent = t('ageNo');
}
function setAdult(on, fromOtherTab){
  ADULT = !!on;
  if (!fromOtherTab) try{ localStorage.setItem('hub.adult', ADULT ? '1' : '0'); }catch(_){}
  adultStatic(); onAdult();
}
function askAdult(){
  let seen = false; try{ seen = localStorage.getItem('hub.ageOk') === '1'; }catch(_){}
  if (seen) return setAdult(true);
  ageBox.hidden = false; $('#ageY').focus();
}
function closeAge(){ ageBox.hidden = true; adultSw.focus(); }
adultSw.addEventListener('click', ()=>{ if (ADULT) setAdult(false); else askAdult(); });
$('#ageY').addEventListener('click', ()=>{
  try{ localStorage.setItem('hub.ageOk', '1'); }catch(_){}
  ageBox.hidden = true; setAdult(true); adultSw.focus();
});
$('#ageN').addEventListener('click', closeAge);
ageBox.addEventListener('click', e=>{ if (e.target === ageBox) closeAge(); });
// 捕获阶段先处理：对话框开着时 Esc 只关对话框
document.addEventListener('keydown', e=>{
  if (e.key === 'Escape' && !ageBox.hidden){ e.stopImmediatePropagation(); closeAge(); }
}, true);
document.addEventListener('click', e=>{ if (e.target.closest('[data-adult-go]')) askAdult(); });
addEventListener('storage', e=>{ if (e.key === 'hub.adult') setAdult(e.newValue === '1', true); });
// 筛选结果只剩被隐藏的成人向条目时，网格里显示这一块
function adultEmpty(){
  return '<div class="empty"><b>'+esc(t('adultEmptyTitle'))+'</b>'+esc(t('adultEmptyDesc'))+
    '<br><button type="button" class="adult-go" data-adult-go>'+esc(t('adultEmptyGo'))+'</button></div>';
}
"""

# 没有成人向内容的站点：不渲染开关，页面逻辑照常（ADULT 恒为 true，什么都不隐藏）
JS_NONE = "\nconst ADULT_MODE = 'none'; const ADULT = true;\nfunction adultStatic(){}\nfunction adultEmpty(){ return ''; }\n"


def parts(mode):
    """返回 (css, 开关 html, 对话框 html, js)。mode 为 hide / blur / None（本站无成人向内容）"""
    if not mode:
        return "", "", "", JS_NONE
    assert mode in ("hide", "blur"), mode
    return CSS, SWITCH_HTML, BOX_HTML, JS.replace("__MODE__", mode)
