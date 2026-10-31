# -*- coding: utf-8 -*-
"""站点配置：品牌文案与 SEO 元信息

两站（姿势 / 深度姿势）结构完全相同，只有这里的文案和图源不同。
由 scripts/build_gallery.py 组装成 CONFIG 传给 shared/pose_gallery.build()。
"""

CODE = "POSE-DB-01"
SOURCE = "https://ai-pose-gallery.pages.dev/"

# SEO 与社交分享文案（中文，页面 lang 为 zh-CN）
SEO = {
    "title": "AI 绘画人体姿势参考图库：288 个姿势、1439 张五视角线稿 · 姿势集",
    "desc": "AI 绘画人体姿势参考图库中文版：288 个姿势、1439 张多视角参考图，含正面・侧面・斜角・俯视・仰视，支持中日双语与浅深主题切换。",
    "ogSite": "姿势集 POSE-DB-01",
    "ogTitle": "AI 绘画人体姿势参考图 · 288 个姿势 / 1439 张五视角线稿",
    "ogDesc": "AI 绘画人体姿势参考图库中文版。每个姿势提供正面・侧面・斜角・俯视・仰视五个视角。",
    "twTitle": "AI 绘画人体姿势参考图 · 288 个姿势 / 1439 张",
    "twDesc": "AI 绘画人体姿势参考图库中文版。每个姿势提供五个视角。",
    "schemaName": "姿势集 POSE-DB-01",
    "schemaAlt": "AI Pose Gallery 中文版",
    "schemaAbout": "AI 绘画・3D・插画的人体姿势参考",
}

# 界面文案（中/日双语）
UI = {
    "ja": {
        "title": "AI イラスト向けポーズ参考画像集：288 ポーズ・1439 枚・5 アングル · POSE-DB-01",
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
        "dlPng": "PNG をダウンロード", "openFull": "原寸 PNG を開く",
        "copyLink": "画像リンクをコピー", "copied": "コピーしました", "copyFail": "コピー失敗",
        "hint": "<kbd>←</kbd><kbd>→</kbd> アングル　<kbd>↑</kbd><kbd>↓</kbd> ポーズ　<kbd>Esc</kbd> 閉じる",
        "footer": "素材元：<a href=\"https://ai-pose-gallery.pages.dev/\" target=\"_blank\" rel=\"noopener noreferrer\">ai-pose-gallery.pages.dev</a>（POSE-DB-01）。ローカルミラーは個人の参照用です。元画像の再配布・転売はご遠慮ください。",
        "themeLight": "ライト", "themeDark": "ダーク",
        "langJa": "日本語", "langZh": "中文",
        "themeAria": "表示テーマ", "langAria": "言語",
    },
    "zh": {
        "title": "AI 绘画人体姿势参考图库：288 个姿势、1439 张五视角线稿 · 姿势集",
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
        "dlPng": "下载 PNG", "openFull": "打开原寸 PNG",
        "copyLink": "复制图片链接", "copied": "已复制", "copyFail": "复制失败",
        "hint": "<kbd>←</kbd><kbd>→</kbd> 切视角　<kbd>↑</kbd><kbd>↓</kbd> 换姿势　<kbd>Esc</kbd> 关闭",
        "footer": "素材来源：<a href=\"https://ai-pose-gallery.pages.dev/\" target=\"_blank\" rel=\"noopener noreferrer\">ai-pose-gallery.pages.dev</a>（POSE-DB-01）。本地镜像仅供个人参考，请勿再分发或转售原始图片。",
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
    "id": "pose", "name": "姿势集", "short": "姿势参考", "kind": "姿势参考图",
    "tagline": "AI 绘画人体姿势参考图库",
    "licenseNote": "图片为 AI 生成，著作权归原作者，禁止再分发图片文件本身。",
    "descTail": "适合作为 Stable Diffusion / ControlNet openpose 的姿势参考。",
    "accent": "#4f7ee8",
    # 只为标准系展开到分类页；双人系列不生成落地页。成人向姿势（sites.json 的 adult 规则）
    # 不进任何落地页，所以性感系没有页面，上半身系列页只列可爱系（见 shared/pose_seo.py）
    "expandSeries": ["全身1人・標準系"],
    "skipSeries": ["2人絡み"],
    "introParas": lambda n, m: [
        f"姿势集是一个 AI 绘画人体姿势参考图库：收录 {n} 个姿势、{m} 张无脸灰色人偶线稿，"
        "每个姿势提供正面、侧面、斜角、俯视、仰视 5 个视角，适合作为 Stable Diffusion、ControlNet openpose 出图时的姿势参考。",
        "系列、分类、视角和姿势名全部译为中文，可按系列、分类、视角筛选，或按姿势名和编号搜索。"],
    "faq": _faq("线稿", "把线稿作为 ControlNet 的 openpose 或 lineart 参考图，或直接给模型看姿势；"
                "也可以按页面上的中文姿势名写提示词，例如「坐姿，侧身，回头」。"),
}

CONFIG = {
    "code": CODE,
    "source": SOURCE,
    **SEO,
    "ui": UI,
    "seoPages": SEO_PAGES,
    # 18+ 开关（shared/adult.py）：成人向姿势默认隐藏；这句说明出现在年龄确认框里
    "adultMode": "hide",
    "ageWhat": {"zh": "包括双人交缠、全身性感系，以及上半身的聚胸、性感露骨分类。", "ja": "2人絡み・全身セクシー系、上半身の胸寄せ・セクシー露骨寄りの分類が対象です。"},
}
