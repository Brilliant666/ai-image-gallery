# -*- coding: utf-8 -*-
"""站点配置：品牌文案与 SEO 元信息

两站（姿势 / 深度姿势）结构完全相同，只有这里的文案和图源不同。
由 scripts/build_gallery.py 组装成 CONFIG 传给 shared/pose_gallery.build()。
"""

CODE = "POSE-DB-01"
SOURCE = "https://ai-pose-gallery.pages.dev/"

# SEO 与社交分享文案（中文，页面 lang 为 zh-CN）
SEO = {
        "title": "姿势集 POSE-DB-01 · 离线索引",
    "desc": "AI 绘画人体姿势参考图库中文版：288 个姿势、1439 张多视角参考图，含正面・侧面・斜角・俯视・仰视，支持中日双语与浅深主题切换。",
    "ogSite": "姿势集 POSE-DB-01",
    "ogTitle": "姿势集 POSE-DB-01 · 288 姿势 / 1439 张参考图",
    "ogDesc": "AI 绘画人体姿势参考图库中文版。每个姿势提供正面・侧面・斜角・俯视・仰视五个视角。",
    "twTitle": "姿势集 POSE-DB-01 · 288 姿势 / 1439 张参考图",
    "twDesc": "AI 绘画人体姿势参考图库中文版。每个姿势提供五个视角。",
    "schemaName": "姿势集 POSE-DB-01",
    "schemaAlt": "AI Pose Gallery 中文版",
    "schemaAbout": "AI 绘画・3D・插画的人体姿势参考",
}

# 界面文案（中/日双语）
UI = {
    "ja": {
        "title": "ポーズ集 POSE-DB-01 · オフライン索引",
        "home": "参照素材集", "homeAria": "参照素材集のトップへ",
        "eyebrow": "POSE-DB-01 · 画像参照用ポーズ集 · ローカルミラー",
        "brand1": "ポーズ集",
        "brand2": "データベース",
        "sub1": "顔なしグレーマネキンの線画（3:4）。正面・上から・下から・横・斜めのアングルで見比べられます。",
        "sub2": "各カード下部のアングル帯にカーソルを合わせると主画像が切り替わり、クリックでそのアングルが開きます。",
        "statPose": "ポーズ", "statImg": "画像", "statSer": "シリーズ", "statCat": "分類",
        "all": "すべて",
        "search": "ポーズ名・番号・分類で検索",
        "filter": "絞り込み",
        "catAll": "すべての分類",
        "sortSeries": "シリーズ → 番号", "sortPid": "番号順 P001→P080",
        "sortCat": "分類 → 番号", "sortName": "ポーズ名",
        "angAll": "すべて",
        "viewPose": "ポーズごと", "viewCard": "1枚ずつ",
        "countPose": "<b>{n}</b> ポーズ · <b>{m}</b> 枚",
        "countImg": "<b>{n}</b> 枚",
        "emptyTitle": "条件に合う画像がありません",
        "emptyDesc": "キーワードを変えるか、絞り込みを緩めてください。",
        "kSeries": "シリーズ", "kCat": "分類", "kPid": "番号", "kAng": "アングル", "kAngN": "アングル数",
        "angUnit": "個",
        "openFull": "原寸 PNG を開く",
        "copyPath": "パスをコピー", "copied": "コピーしました", "copyFail": "コピー失敗",
        "hint": "<kbd>←</kbd><kbd>→</kbd> アングル　<kbd>↑</kbd><kbd>↓</kbd> ポーズ　<kbd>Esc</kbd> 閉じる",
        "footer": "素材元：<a href=\"https://ai-pose-gallery.pages.dev/\" target=\"_blank\" rel=\"noopener noreferrer\">ai-pose-gallery.pages.dev</a>（POSE-DB-01）。ローカルミラーは個人の参照用です。元画像の再配布・転売はご遠慮ください。",
        "themeLight": "ライト", "themeDark": "ダーク",
        "langJa": "日本語", "langZh": "中文",
        "themeAria": "表示テーマ", "langAria": "言語",
    },
    "zh": {
        "title": "姿势集 POSE-DB-01 · 离线索引",
        "home": "参考素材库", "homeAria": "返回参考素材库首页",
        "eyebrow": "POSE-DB-01 · 图像参照用姿势集 · 本地镜像",
        "brand1": "姿势集",
        "brand2": "数据库",
        "sub1": "无脸部灰色人偶线稿（3:4）。提供正面・俯视・仰视・侧面・斜角五种视角，便于对照。",
        "sub2": "鼠标悬停卡片底部的视角条可即时切换主图，点击即打开该视角大图。",
        "statPose": "姿势", "statImg": "图片", "statSer": "系列", "statCat": "分类",
        "all": "全部",
        "search": "搜索姿势名 / 编号 / 分类",
        "filter": "筛选",
        "catAll": "全部分类",
        "sortSeries": "系列 → 编号", "sortPid": "编号顺序 P001→P080",
        "sortCat": "分类 → 编号", "sortName": "姿势名",
        "angAll": "全部",
        "viewPose": "按姿势", "viewCard": "单张",
        "countPose": "<b>{n}</b> 姿势 · <b>{m}</b> 图",
        "countImg": "<b>{n}</b> 张",
        "emptyTitle": "没有匹配的姿势",
        "emptyDesc": "换个关键词，或把筛选条件放宽一些。",
        "kSeries": "系列", "kCat": "分类", "kPid": "编号", "kAng": "视角", "kAngN": "该姿势视角数",
        "angUnit": "个",
        "openFull": "打开原寸 PNG",
        "copyPath": "复制本地路径", "copied": "已复制", "copyFail": "复制失败",
        "hint": "<kbd>←</kbd><kbd>→</kbd> 切视角　<kbd>↑</kbd><kbd>↓</kbd> 换姿势　<kbd>Esc</kbd> 关闭",
        "footer": "素材来源：<a href=\"https://ai-pose-gallery.pages.dev/\" target=\"_blank\" rel=\"noopener noreferrer\">ai-pose-gallery.pages.dev</a>（POSE-DB-01）。本地镜像仅供个人参考，请勿再分发或转售原始图片。",
        "themeLight": "浅色", "themeDark": "深色",
        "langJa": "日本語", "langZh": "中文",
        "themeAria": "主题", "langAria": "语言",
    },
}

CONFIG = {
    "code": CODE,
    "source": SOURCE,
    **SEO,
    "ui": UI,
}
