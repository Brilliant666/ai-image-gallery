# -*- coding: utf-8 -*-
"""姿势模块（线稿 + 深度图）两个入口共用的配置

/pose/ 与 /pose-depth/ 是同一个模块：同一批 288 个姿势，页面里用开关在线稿和深度图之间切换，大图里可以左右对比。
两个入口只有默认版本、标题与说明、静态落地页不同。由 sites/pose/config.py 和 sites/pose-depth/config.py 引用。
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shared"))
from pose_i18n import gallery_ui  # noqa: E402

LINE_SRC, DEPTH_SRC = "https://ai-pose-gallery.pages.dev/", "https://ai-pose-depth-gallery.pages.dev/"
_LINK = '<a href="{0}" target="_blank" rel="noopener noreferrer">{1}</a>'

VARIANTS = {
    "line": {"site": "pose", "label": {"zh": "线稿", "ja": "線画"}},
    "depth": {"site": "pose-depth", "label": {"zh": "深度图", "ja": "デプス"}},
}

FOOTER = {
    "zh": ("素材来源：线稿 " + _LINK.format(LINE_SRC, "ai-pose-gallery") + "（POSE-DB-01）、深度图 "
           + _LINK.format(DEPTH_SRC, "ai-pose-depth-gallery") + "（POSE-DB-02），作者 "
           + _LINK.format("https://x.com/giaaibusi", "ギア") + "。本站是个人参考用的中文镜像，请勿再分发或转售原始图片；"
           "深度图原站另禁止批量下载与用工具自动获取。"),
    "ja": ("素材元：線画 " + _LINK.format(LINE_SRC, "ai-pose-gallery") + "（POSE-DB-01）、深度マップ "
           + _LINK.format(DEPTH_SRC, "ai-pose-depth-gallery") + "（POSE-DB-02）、作者 "
           + _LINK.format("https://x.com/giaaibusi", "ギア") + "。個人の参照用ミラーです。元画像の再配布・転売はご遠慮ください。"
           "深度マップは一括ダウンロード・ツールによる自動取得も禁止されています。"),
}

# 两个入口共用的界面文案；标题、页头按入口分别写
UI_COMMON = {
    "zh": {"dlPng": "下载 PNG", "openFull": "打开原图 PNG", "footer": FOOTER["zh"],
           "eyebrow": "POSE-DB-01 / 02 · 姿势参考 · 线稿与深度图",
           "sub1": "无脸灰色人偶，每个姿势正面・侧面・斜角・俯视・仰视 5 个视角。用开关在线稿和深度图之间切换，大图里可以左右对比；"
                   "深度图越亮越近，可直接用于 ControlNet depth。"},
    "ja": {"dlPng": "PNG をダウンロード", "openFull": "原寸 PNG を開く", "footer": FOOTER["ja"],
           "eyebrow": "POSE-DB-01 / 02 · ポーズ参考 · 線画とデプス",
           "sub1": "顔なしグレーマネキン、各ポーズ 正面・横・斜め・上から・下から の 5 アングル。スイッチで線画と深度マップを切り替え、"
                   "拡大表示では左右に比較できます。深度マップは明るいほど手前で、ControlNet depth にそのまま使えます。"},
}


def faq(kind, use):
    return [
        ("这些图是真人吗？", f"不是。全部是 AI 生成的无脸灰色人偶{kind}，不含真实人物，也没有面部特征。"),
        ("可以用在自己的作品或商用项目里吗？",
         "原作者ギア允许免费用于作品制作，包括商用、编辑和作为参考；但禁止把图片文件本身再分发、转载或转售。"
         "本站是中文索引镜像，图片著作权归原作者，以原站条款为准。"),
        ("怎么用在 AI 绘画里？", use),
        ("线稿和深度图有什么关系？",
         "两者是同一批 288 个姿势、同一个视角的两种图，逐像素对齐。页面上的开关可以整页切换，大图里的「对比」可以拖动竖线左右对照。"),
        ("每个姿势有几张图？", "每个姿势提供正面、侧面、斜角、俯视、仰视 5 个视角（P018 缺仰视），在画廊里可以逐个切换、放大和下载 PNG。"),
    ]


def config(variant, code, source, seo, ui, seo_pages):
    """组装一个入口的 CONFIG"""
    return {
        "code": code, "source": source, **seo,
        "ui": gallery_ui({lang: {**UI_COMMON[lang], **ui[lang]} for lang in ui}),
        "seoPages": seo_pages,
        "adultMode": "hide",
        "variant": variant, "variants": VARIANTS,
        "stats": [("288", "个姿势", "ポーズ"), ("1,439", "张线稿", "枚の線画"), ("1,439", "张深度图", "枚の深度マップ"),
                  ("5", "个视角", "アングル")],
    }
