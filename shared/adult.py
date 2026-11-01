# -*- coding: utf-8 -*-
"""成人向内容：判定规则与画廊里用到的文案

规则写在 sites.json 各站的 "adult" 字段：{manifest 字段名: [取值, ...]}，
manifest 里任一字段的取值命中，这张图就算成人向。例如姿势集：

    "adult": {"系列": ["2人絡み", "全身1人・セクシー系"], "分類": ["胸寄せ・谷間強調系", "セクシー・露骨寄り系"]}

姿势与服装的分类口径与 posewear（atuizz/posewear，MIT）的 18+ 开关一致；Shisei 隐藏全身・セクシー、ふたり整个系列，以及其他系列中上游 rating 为 suggestive 的姿势。
静态落地页不放成人向缩略图（shared/pose_seo.py、sites/costume/scripts/seo.py），tests/run.py 据此检查。

开关本身在全站顶部栏（shared/ui.py）：状态存 localStorage 的 hub.adult，写到 <html data-adult>，
变化时页面收到 pl:adult 事件。18+ 关闭时画廊隐藏成人向条目，不提供单图模糊或点击解锁。
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


# 筛选结果只剩被隐藏的成人向条目时，网格里显示的提示（例如分享链接带 #series=成人向系列）
UI = {
    "zh": {"adultEmptyTitle": "这是成人向内容", "adultEmptyDesc": "打开顶部栏的「18+」后可以查看。",
           "adultEmptyGo": "打开 18+"},
    "ja": {"adultEmptyTitle": "成人向けの内容です", "adultEmptyDesc": "上部バーの「18+」をオンにすると表示されます。",
           "adultEmptyGo": "18+ をオン"},
}


def ui(site_ui):
    """把这些文案合并进站点 UI（站点自己的同名键优先）"""
    return {lang: {**UI.get(lang, {}), **strings} for lang, strings in site_ui.items()}
