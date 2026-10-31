# -*- coding: utf-8 -*-
"""站点配置：品牌文案与 SEO 元信息

两站（姿势 / 深度姿势）结构完全相同，只有这里的文案和图源不同。
由 scripts/build_gallery.py 组装成 CONFIG 传给 shared/pose_gallery.build()。
"""

CODE = "POSE-DB-02"
SOURCE = "https://ai-pose-depth-gallery.pages.dev/"

# SEO 与社交分享文案（中文，页面 lang 为 zh-CN）
SEO = {
    "title": "AI 绘画姿势深度图库：288 个姿势、1439 张 ControlNet 深度图 · 深度姿势集",
    "desc": "AI 绘画人体姿势深度图库中文版：288 个姿势、1439 张多视角深度图，含正面・侧面・斜角・俯视・仰视，适用于 ControlNet 深度控制与 3D 建模参考。",
    "ogSite": "深度姿势集 POSE-DB-02",
    "ogTitle": "ControlNet 姿势深度图 · 288 个姿势 / 1439 张五视角深度图",
    "ogDesc": "AI 绘画人体姿势深度图库中文版。每个姿势提供五个视角的灰度深度图。",
    "twTitle": "ControlNet 姿势深度图 · 288 个姿势 / 1439 张",
    "twDesc": "AI 绘画人体姿势深度图库中文版。每个姿势提供五个视角的灰度深度图。",
    "schemaName": "深度姿势集 POSE-DB-02",
    "schemaAlt": "AI Pose Depth Gallery 中文版",
    "schemaAbout": "AI 绘画 ControlNet 深度控制・3D 建模的人体姿势深度参考",
}

# 界面文案（中/日双语）
UI = {
    "ja": {
        "title": "ControlNet 向けポーズ深度マップ集：288 ポーズ・1439 枚・5 アングル · POSE-DB-02",
        "home": "参照素材集", "homeAria": "参照素材集のトップへ",
        "eyebrow": "POSE-DB-02 · 深度参照用ポーズ集 · ローカルミラー",
        "brand1": "デプス",
        "brand2": "ポーズ集",
        "sub1": "顔なしグレーマネキンの深度マップ（3:4）。奥行きがグレースケールで表現され、ControlNet の depth 制御や 3D モデリングの参考に使えます。",
        "sub2": "各カード下部のアングル帯にカーソルを合わせると主画像が切り替わり、クリックでそのアングルが開きます。元画像は PNG でダウンロードできます。",
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
        "dlPng": "PNG をダウンロード", "openFull": "原寸 PNG を開く",
        "copyLink": "画像リンクをコピー", "copied": "コピーしました", "copyFail": "コピー失敗",
        "hint": "<kbd>←</kbd><kbd>→</kbd> アングル　<kbd>↑</kbd><kbd>↓</kbd> ポーズ　<kbd>Esc</kbd> 閉じる",
        "footer": "素材元：<a href=\"https://ai-pose-depth-gallery.pages.dev/\" target=\"_blank\" rel=\"noopener noreferrer\">ai-pose-depth-gallery.pages.dev</a>（POSE-DB-02）。ローカルミラーは個人の参照用です。元画像の再配布・転売はご遠慮ください。",
        "themeLight": "ライト", "themeDark": "ダーク",
        "langJa": "日本語", "langZh": "中文",
        "themeAria": "表示テーマ", "langAria": "言語",
    },
    "zh": {
        "title": "AI 绘画姿势深度图库：288 个姿势、1439 张 ControlNet 深度图 · 深度姿势集",
        "home": "参考素材库", "homeAria": "返回参考素材库首页",
        "eyebrow": "POSE-DB-02 · 深度参照用姿势集 · 本地镜像",
        "brand1": "深度",
        "brand2": "姿势集",
        "sub1": "无脸部灰色人偶深度图（3:4）。远近以灰度表示，可用于 ControlNet 深度控制、3D 建模与布光参考。",
        "sub2": "鼠标悬停卡片底部的视角条可即时切换主图，点击即打开该视角大图，可下载原尺寸 PNG。",
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
        "dlPng": "下载 PNG", "openFull": "打开原寸 PNG",
        "copyLink": "复制图片链接", "copied": "已复制", "copyFail": "复制失败",
        "hint": "<kbd>←</kbd><kbd>→</kbd> 切视角　<kbd>↑</kbd><kbd>↓</kbd> 换姿势　<kbd>Esc</kbd> 关闭",
        "footer": "素材来源：<a href=\"https://ai-pose-depth-gallery.pages.dev/\" target=\"_blank\" rel=\"noopener noreferrer\">ai-pose-depth-gallery.pages.dev</a>（POSE-DB-02）。本地镜像仅供个人参考，请勿再分发或转售原始图片。",
        "themeLight": "浅色", "themeDark": "深色",
        "langJa": "日本語", "langZh": "中文",
        "themeAria": "主题", "langAria": "语言",
    },
}

def _faq(kind, use):
    return [
        ("这些图是真人吗？", f"不是。全部是 AI 生成的无脸灰色人偶{kind}，不含真实人物，也没有面部特征。"),
        ("可以用在自己的作品或商用项目里吗？",
         "原作者ギア允许免费用于作品制作，包括商用、编辑和作为参考；但禁止把图片文件本身再分发、转载或转售。"
         "本站是中文索引镜像，图片著作权归原作者，以原站条款为准。"),
        ("怎么用在 AI 绘画里？", use),
        ("每个姿势有几张图？", "每个姿势提供正面、侧面、斜角、俯视、仰视 5 个视角（P018 缺仰视），在画廊里可以逐个切换、放大和下载 PNG。"),
        ("和原站有什么不同？", "原站为日文。本站把系列、分类、视角和 288 个姿势名全部译成中文，支持中日双语切换、组合筛选和关键词搜索。"),
    ]


SEO_PAGES = {
    "id": "pose-depth", "name": "深度姿势集", "short": "深度图", "kind": "姿势深度图",
    "tagline": "AI 绘画 ControlNet 姿势深度图库",
    "licenseNote": "图片为 AI 生成，著作权归原作者，禁止再分发图片文件本身，原站另禁止批量下载。",
    "descTail": "灰度深度图可直接用于 ControlNet depth 控制。",
    "accent": "#6b7280",
    # 只为标准系展开到分类页；双人系列不生成落地页。成人向姿势（sites.json 的 adult 规则）
    # 不进任何落地页，所以性感系没有页面，上半身系列页只列可爱系（见 shared/pose_seo.py）
    "expandSeries": ["全身1人・標準系"],
    "skipSeries": ["2人絡み"],
    "introParas": lambda n, m: [
        f"深度姿势集是一个 AI 绘画姿势深度图库：收录 {n} 个姿势、{m} 张无脸灰色人偶的灰度深度图（depth map），"
        "越亮表示越靠近镜头，可直接作为 Stable Diffusion ControlNet depth 的控制图，也适合 3D 建模与布光参考。",
        "每个姿势有正面、侧面、斜角、俯视、仰视 5 个视角，系列、分类和姿势名全部译为中文。"],
    "faq": _faq("深度图", "把深度图作为 ControlNet depth 的控制图载入，提示词里描述人物和服装即可沿用姿势与前后关系；"
                "手指和交叠双腿的边界在深度图里较弱，需要时配合线稿版（姿势集）使用。"),
}

CONFIG = {
    "code": CODE,
    "source": SOURCE,
    **SEO,
    "ui": UI,
    "seoPages": SEO_PAGES,
}
