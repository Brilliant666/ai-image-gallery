# -*- coding: utf-8 -*-
"""Shisei（CC0 姿势线稿）站点配置

数据来自上游 wquguru/shisei 的 v0.3.0 标签（data/catalog.json，见 scripts/manifest.py），页面由
shared/pose_gallery.py 生成。与姿势集 / 深度姿势集的区别：
  - 图片 CC0，可商用、可再分发；姿势名与中文译名直接取自上游 catalog
  - 四个系列全部收录；上游标为 suggestive 的姿势在 18+ 关闭时模糊显示，点开或打开顶部栏的 18+ 才清晰，
    且不生成静态落地页（同上游站点的做法）
"""
import json, os, sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared"))
from pose_i18n import gallery_ui  # noqa: E402

SITE = os.path.dirname(os.path.abspath(__file__))
CODE = "SHISEI-v0.3.0"
SOURCE = "https://shisei.indaloop.app/"
REPO = "https://github.com/wquguru/shisei"

_cat = json.load(open(os.path.join(SITE, "data", "catalog.json"), encoding="utf-8"))
_m = json.load(open(os.path.join(SITE, "manifest.json"), encoding="utf-8"))
N_POSES, N_IMAGES = len({r["编号"] for r in _m}), len(_m)

SERIES_JA = ["全身・標準", "上半身", "全身・セクシー", "ふたり"]
SERIES_ZH = {"全身・標準": "全身・标准", "上半身": "上半身", "全身・セクシー": "全身・性感", "ふたり": "双人"}
ANG_JA = ["正面", "斜め", "横", "上から", "下から"]
ANG_ZH = {"正面": "正面", "斜め": "斜角", "横": "侧面", "上から": "俯视", "下から": "仰视"}
# 分类中文名取上游 class_cn；同一个日文分类在不同系列里偶有两种译法（立ち：站立 / 站姿），取最常见的
_votes = {}
for p in _cat:
    _votes.setdefault(p["class_jp"], Counter())[p["class_cn"]] += 1
CAT_ZH = {k: v.most_common(1)[0][0] for k, v in _votes.items()}

FOOTER_ZH = ("图片来自 <a href=\"" + REPO + "\" target=\"_blank\" rel=\"noopener noreferrer\">Shisei</a> v0.3.0，CC0 1.0 公有领域，可商用、可再分发。"
             "姿势的选题、编号、名称与分类沿用 ギア 的 ai-pose-gallery 公开目录，这部分仅注明出处、不在 CC0 授权范围内；Shisei 与其作者无关联。")
FOOTER_JA = ("画像は <a href=\"" + REPO + "\" target=\"_blank\" rel=\"noopener noreferrer\">Shisei</a> v0.3.0（CC0 1.0）。商用・再配布可。"
             "ポーズの選定・番号・名称・分類は ギア 氏の ai-pose-gallery 公開目録に基づき、出典表記のみで CC0 の対象外です。Shisei は同氏と無関係です。")

SEO = {
    "title": f"CC0 姿势线稿参考图库：{N_POSES} 个姿势、{N_IMAGES} 张线稿，可商用 · Shisei",
    "desc": (f"无脸人偶的 AI 绘画姿势参考：{N_POSES} 个姿势、{N_IMAGES} 张线稿，全身・标准、上半身、全身・性感、双人四个系列，"
             "每个姿势最多正面・斜角・侧面・俯视・仰视五个视角。图片 CC0，可商用、可再分发。"),
    "ogSite": "Shisei · CC0 姿势线稿",
    "ogTitle": f"CC0 姿势线稿 · {N_POSES} 个姿势 / {N_IMAGES} 张，可商用",
    "ogDesc": "无脸人偶姿势参考线稿，每个姿势最多五个视角，CC0 可商用、可再分发。",
    "twTitle": f"CC0 姿势线稿 · {N_POSES} 个姿势 / {N_IMAGES} 张",
    "twDesc": "无脸人偶姿势参考线稿，每个姿势最多五个视角，CC0 可商用。",
    "schemaName": "Shisei · CC0 姿势线稿",
    "schemaAlt": "Shisei mannequin pose reference (CC0)",
    "schemaAbout": "AI 绘画・插画・ControlNet 的人体姿势参考线稿",
}

UI = gallery_ui({
    "ja": {
        "title": f"CC0 ポーズ線画集：{N_POSES} ポーズ・{N_IMAGES} 枚、最大 5 アングル · Shisei",
        "eyebrow": "SHISEI v0.3.0 · CC0 ポーズ線画 · ミラー",
        "brand1": "Shisei", "brand2": "CC0 ポーズ線画",
        "sub1": "顔なしマネキンの線画（3:4）。4 シリーズ・各最大 5 アングル。CC0 で商用・再配布できます。"
                "suggestive なポーズは 18+ がオフの間ぼかし表示で、タップすると見られます。",
        "dlPng": "WEBP をダウンロード", "openFull": "900px 画像を開く", "footer": FOOTER_JA,
    },
    "zh": {
        "title": SEO["title"],
        "eyebrow": "SHISEI v0.3.0 · CC0 姿势线稿 · 镜像",
        "brand1": "Shisei", "brand2": "CC0 姿势线稿",
        "sub1": "无脸人偶线稿（3:4），四个系列、每个姿势最多 5 个视角。CC0 可商用、可再分发。"
                "偏性感的姿势在 18+ 关闭时模糊显示，点开即可查看。",
        "dlPng": "下载 WEBP", "openFull": "打开 900px 原图", "footer": FOOTER_ZH,
    },
})

def _faq(kind, use):
    return [
        ("这些图是真人吗？", f"不是。全部是 AI 生成的无脸人偶{kind}，不含真实人物，也没有面部特征。"),
        ("可以商用吗？",
         "可以。Shisei 的图片以 CC0 1.0 公有领域发布，可以免费商用、修改和再分发，不需要署名。"
         "姿势的选题、编号、名称与分类沿用 ギア 的 ai-pose-gallery 公开目录，这部分只注明出处，不在 CC0 范围内。"),
        ("怎么用在 AI 绘画里？", use),
        ("每个姿势有几张图？", "最多 5 个视角：正面、斜角、侧面、俯视、仰视。没通过上游质检的视角不收录，所以部分姿势少于 5 张。"),
        ("和姿势集有什么不同？",
         "姿势集是原作者ギア的图，禁止再分发；Shisei 是另一个项目按同一份姿势目录重新绘制的线稿，CC0 可商用、可再分发。"
         "上游标为 suggestive 的姿势在这里默认模糊显示。"),
    ]


SEO_PAGES = {
    "id": "shisei", "name": "Shisei 姿势线稿", "short": "姿势参考", "kind": "姿势线稿",
    "tagline": "CC0 人体姿势参考线稿库",
    "licenseNote": "图片 CC0 1.0，可商用、可再分发；姿势目录沿用 ai-pose-gallery，仅注明出处。",
    "descTail": "CC0 可商用，适合作为 AI 绘画与 ControlNet 的姿势参考。",
    "accent": "#1a5cc8",
    "author": "Shisei", "authorUrl": REPO,
    "dlFormat": "WEBP", "factSource": "AI 生成，Shisei 项目",
    "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/", "angNote": "最多",
    # 同上游站点：suggestive 姿势不生成可被收录的页面（sites.json 的 adult 规则按 rating 判定），系列页只列 general 的姿势
    "expandSeries": ["全身・標準"],
    # 双人与全身・性感整个系列不生成落地页（同姿势集的做法），只在画廊里浏览
    "skipSeries": ["ふたり", "全身・セクシー"],
    "introParas": lambda n, m: [
        f"Shisei 是一个 CC0 的人体姿势参考线稿库：收录 {n} 个姿势、{m} 张无脸人偶线稿，"
        "分全身・标准、上半身、全身・性感、双人四个系列，每个姿势最多 5 个视角，可以免费商用和再分发。",
        "本页面是它的中文镜像：系列、分类和姿势名使用上游 catalog 的中文译名；偏性感的姿势默认模糊，点开或打开开关即可查看。"],
    "faq": _faq("线稿", "把线稿作为图像工具的姿势参考或 ControlNet 的 lineart / openpose 输入；"
                "用同一姿势的多个视角，可以让人物在不同镜头里保持同一个动作。"),
}

CONFIG = {
    "code": CODE,
    "source": SOURCE,
    **SEO,
    "ui": UI,
    "seoPages": SEO_PAGES,
    "seriesOrder": SERIES_JA,
    "angOrder": ANG_JA,
    "seriesZh": SERIES_ZH,
    "catZh": CAT_ZH,
    "angZh": ANG_ZH,
    "nameZh": None,                 # 姿势名中文直接取 manifest 的「姿势名_zh」
    "author": "Shisei", "authorUrl": REPO, "authorMeta": "Shisei (wquguru/shisei, CC0 1.0)",
    "imgExt": ".webp",
    "schemaImages": N_IMAGES,
    # 结构化数据里的授权（CC0）
    "licenseLd": '"license":"https://creativecommons.org/publicdomain/zero/1.0/","acquireLicensePage":"' + REPO + '",'
                 '"copyrightNotice":"CC0 1.0 (Shisei)",',
    "stats": [(str(N_POSES), "个姿势", "ポーズ"), (f"{N_IMAGES:,}", "张线稿", "枚の線画"), ("CC0", "可商用", "商用可")],
    # 18+ 开关（shared/adult.py）：上游标为 suggestive 的姿势默认模糊，与上游站点一致
    "adultMode": "blur",
    "ageWhat": {"zh": "上游标为 suggestive 的偏性感姿势，关闭时模糊显示。", "ja": "上流で suggestive とされたポーズで、オフの間はぼかし表示です。"},
}
