# -*- coding: utf-8 -*-
"""成人向内容的判定规则

规则写在 sites.json 各站的 "adult" 字段：{manifest 字段名: [取值, ...]}，
manifest 里任一字段的取值命中，这张图就算成人向。例如姿势集：

    "adult": {"系列": ["2人絡み", "全身1人・セクシー系"], "分類": ["胸寄せ・谷間強調系", "セクシー・露骨寄り系"]}

姿势与服装的分类口径与 posewear（atuizz/posewear，MIT）的 18+ 开关一致；Shisei 用上游的 rating。
静态落地页不放成人向缩略图（shared/pose_seo.py、sites/costume/scripts/seo.py），tests/run.py 据此检查。
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
