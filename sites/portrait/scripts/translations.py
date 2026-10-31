# -*- coding: utf-8 -*-
"""日 → 中 词典：发型分类、风格描述、界面文案"""

# ── 发型分类 ──────────────────────────────────────────
HAIR_ZH = {
    "ショート": "短发",
    "ミディアム": "中发",
    "セミロング": "中长发",
    "ロング": "长发",
    "未分類": "未分类",
}

HAIR_ORDER = ["ショート", "ミディアム", "セミロング", "ロング", "未分類"]

# ── 分区 ──────────────────────────────────────────────
SECTION_ZH = {
    "face": "面部",
    "styling": "造型",
}
SECTION_NOTE_ZH = {
    "face": "正面、纯色背景的脸部参考图。需要统一角色脸部时使用。",
    "styling": "能看清服装、发质与整体氛围的完整原图，朝向各异。",
}
SECTION_NOTE_JA = {
    "face": "正面向き・無地背景の顔リファレンス。顔を揃えたいときに。",
    "styling": "服装・髪の質感・雰囲気までわかる元画像。向きはさまざまです。",
}

# ── 风格描述（50 条）──────────────────────────────────
STYLE_ZH = {
    "前下がりひし形ショートボブ（黒髪）": "前长后短菱形短波波头（黑发）",
    "耳掛けハンサムショート（前髪なし）": "耳后帅气短发（无刘海）",
    "切りっぱなしストレートボブ（前髪なし）": "齐切直发波波头（无刘海）",
    "くびれショート（襟足長め・シースルーバング）": "内收短发（颈后偏长・空气刘海）",
    "丸みショートボブ（シースルーバング・ダークブラウン）": "圆润短波波头（空气刘海・深棕）",
    "韓国風タッセルボブ（サイドバング）": "韩式流苏波波头（侧刘海）",
    "ミニボブ（オン眉ぱっつん前髪）": "迷你波波头（眉上齐刘海）",
    "マッシュショート（前髪長め）": "蘑菇短发（刘海偏长）",
    "ミニボブパーマ（くせ毛風）": "迷你波波头烫（仿自然卷）",
    "ショートウルフ（ミニウルフ）": "短狼尾剪（迷你狼尾）",
    "レイヤーショートボブ（顔まわりレイヤー）": "层次短波波头（脸周层次）",
    "内巻きワンカールボブ（ラベンダーアッシュ）": "内扣一卷波波头（薰衣草灰）",
    "ハイライト入り丸みショート": "挑染圆润短发",
    "ハイトーンミルクティーショートボブ": "浅色奶茶短波波头",
    "切りっぱなし外ハネミディアムボブ": "齐切外翻中长波波头",
    "鎖骨丈ミディアムレイヤーボブ（アッシュグレージュ）": "锁骨长层次中波波头（灰米色）",
    "艶さらストレートミディアムボブ（前髪なし）": "顺滑直发中波波头（无刘海）",
    "バタフライカット（ヘーゼルカラー）": "蝴蝶剪（榛果色）",
    "ロブレイヤー（ミントベージュ）": "长波波层次（薄荷米色）",
    "ぱっつん前髪のミディアムストレート": "齐刘海中发直发",
    "ミディアムニュアンスパーマ（コテ巻き風）": "中发氛围烫（电卷棒风）",
    "重めミディアムレイヤー（バレイヤージュ）": "厚重中发层次（渐变挑染）",
    "2wayバングのワンカールミディアムボブ": "双刘海一卷中波波头",
    "前下がりミディアムボブ（マロンベージュ）": "前长后短中波波头（栗米色）",
    "くるくるハードパーマミディアム": "螺旋硬烫中发",
    "バーガンディのシースルーレイヤー": "酒红空气层次",
    "ウェットヘアの前髪長めショートボブ": "湿发感长刘海短波波头",
    "スパイラルパーマショートボブ（黒髪）": "螺旋烫短波波头（黑发）",
    "ハイトーンミルクティーグレージュミディアム": "浅色奶茶灰米中发",
    "くびれボブ（インナーカラー）": "内收波波头（内层染）",
    "ハッシュカット（韓国ヘア）": "哈什剪（韩式）",
    "ミディアムレイヤー内巻きワンカール（まろベージュ）": "中发层次内扣一卷（柔米色）",
    "外ハネボブ（暗髪）": "外翻波波头（深色发）",
    "ミディアムウルフパーマ": "中发狼尾烫",
    "セミロングニュアンスパーマ": "中长发氛围烫",
    "セミロングウルフ（チェリーレッド）": "中长发狼尾剪（樱桃红）",
    "セミロング顔まわりレイヤー（ミルクティーベージュ）": "中长发脸周层次（奶茶米色）",
    "ハッシュカット（グレージュ）": "哈什剪（灰米色）",
    "スパイラルパーマ韓国風セミロング": "螺旋烫韩式中长发",
    "ワンカールレイヤーと後れ毛（ショコラブラウン）": "一卷层次配碎发（巧克力棕）",
    "セミロングストレート（前髪あり・暗髪）": "中长发直发（有刘海・深色发）",
    "セミロング黒髪ツヤレイヤー": "中长发黑发光泽层次",
    "2wayバングの韓国レイヤー": "双刘海韩式层次",
    "斜めバングのエアリーカール": "斜刘海轻盈卷",
    "シースルーぱっつん前髪のシャギーレイヤー": "空气齐刘海碎层",
    "ロングウルフ（クラゲヘア）": "长狼尾剪（水母头）",
    "たっぷりレイヤー（ラベンダーグレージュ）": "高层次（薰衣草灰米）",
    "ハイレイヤー×裾カラー（ブロンド）": "高层次 × 发尾染（金发）",
    "くびれセミロング（透明感カラー）": "内收中长发（透明感发色）",
    "バタフライカット（ミントベージュ・シースルーバング）": "蝴蝶剪（薄荷米色・空气刘海）",
}

# ── 界面文案 ──────────────────────────────────────────
UI = {
    "zh": {
        "title": "AI 绘画角色脸部一致性参考图库：1499 张 AI 人像，CC0 免费商用 · 人像集",
        "eyebrow": "PORTRAIT-DB-01 · 人像参考 · CC0",
        "h1": "人像集 · AI 模特脸库",
        "lead": "让 AI 生成图像与视频中的角色保持同一张脸。「面部」是正面、纯色背景的脸部参考，「造型」是能看清服装与氛围的完整原图，全部 CC0 免费商用。",
        "all": "全部",
        "more": "加载更多（还有 {n} 张）",
        "empty": "没有符合条件的图片。",
        "secFace": "面部",
        "secStyling": "造型",
        "secLabel": "分区",
        "hairLabel": "按发型筛选",
        "top": "人气 Top 10",
        "download": "下载原图",
        "dlOne": "下载原图 PNG",
        "openFull": "打开原图 PNG",
        "copyLink": "复制图片链接",
        "close": "关闭",
        "prev": "上一张",
        "next": "下一张",
        "countUnit": "张",
        "noFull": "（原图未下载）",
        "hint": "<kbd>←</kbd><kbd>→</kbd> 前后切换　<kbd>Esc</kbd> 关闭",
        "footer": "原站：<a href=\"https://ai-portrait-gallery.pages.dev/\" target=\"_blank\" rel=\"noopener\">AIモデル顔データベース</a> ／ 作者：<a href=\"https://x.com/agi_aibusi\" target=\"_blank\" rel=\"noopener\">あぎ</a> ／ CC0 1.0。均为 AI 生成的虚构人物，请勿用于冒充真人；原作者希望不要原样批量转载图片。",
    },
    "ja": {
        "title": "AI イラスト向け顔参考画像集：1499 枚の AI 人物、CC0 で商用可 · ポートレート集",
        "eyebrow": "PORTRAIT-DB-01 · 顔リファレンス · CC0",
        "h1": "ポートレート集 · AIモデル顔データベース",
        "lead": "AI 画像・動画でキャラクターの顔を揃えるためのリファレンス。正面・無地背景の「フェイス」と、服装や雰囲気まで分かる「スタイリング」を CC0 で配布。",
        "all": "すべて",
        "more": "さらに表示（残り {n} 枚）",
        "empty": "該当する画像がありません。",
        "secFace": "フェイス",
        "secStyling": "スタイリング",
        "secLabel": "セクション",
        "hairLabel": "髪型で絞り込み",
        "top": "人気 Top 10",
        "download": "ダウンロード",
        "dlOne": "原寸 PNG をダウンロード",
        "openFull": "原寸 PNG を開く",
        "copyLink": "画像リンクをコピー",
        "close": "閉じる",
        "prev": "前へ",
        "next": "次へ",
        "countUnit": "枚",
        "noFull": "（原寸未取得）",
        "hint": "<kbd>←</kbd><kbd>→</kbd> 前後　<kbd>Esc</kbd> 閉じる",
        "footer": "元サイト：<a href=\"https://ai-portrait-gallery.pages.dev/\" target=\"_blank\" rel=\"noopener\">AIモデル顔データベース</a> ／ 作者：<a href=\"https://x.com/agi_aibusi\" target=\"_blank\" rel=\"noopener\">あぎ</a> ／ CC0 1.0。すべて AI 生成の架空の人物です。実在人物のなりすましには使わないでください。画像そのものの一括転載はご遠慮ください。",
    },
}


# ── 英文（配方拼提示词用）──────────────────────────────
HAIR_EN = {"ショート": "short hair", "ミディアム": "medium-length hair", "セミロング": "shoulder-length hair",
           "ロング": "long hair", "未分類": "hair"}
STYLE_EN = {
    "2wayバングのワンカールミディアムボブ": "medium bob with a single curl and two-way bangs",
    "2wayバングの韓国レイヤー": "Korean layered cut with two-way bangs",
    "くびれショート（襟足長め・シースルーバング）": "curved short layered cut, longer nape, see-through bangs",
    "くびれセミロング（透明感カラー）": "curved shoulder-length layers, translucent hair color",
    "くびれボブ（インナーカラー）": "curved bob with peekaboo inner color",
    "くるくるハードパーマミディアム": "medium hair with tight hard-perm curls",
    "たっぷりレイヤー（ラベンダーグレージュ）": "heavily layered cut, lavender greige",
    "ぱっつん前髪のミディアムストレート": "medium straight hair with blunt bangs",
    "ウェットヘアの前髪長めショートボブ": "short bob with long bangs, wet-look styling",
    "ショートウルフ（ミニウルフ）": "short wolf cut (mini wolf)",
    "シースルーぱっつん前髪のシャギーレイヤー": "shaggy layers with see-through blunt bangs",
    "スパイラルパーマショートボブ（黒髪）": "short bob with spiral perm, black hair",
    "スパイラルパーマ韓国風セミロング": "Korean-style shoulder-length hair with spiral perm",
    "セミロングウルフ（チェリーレッド）": "shoulder-length wolf cut, cherry red",
    "セミロングストレート（前髪あり・暗髪）": "shoulder-length straight hair with bangs, dark hair",
    "セミロングニュアンスパーマ": "shoulder-length hair with a soft textured perm",
    "セミロング顔まわりレイヤー（ミルクティーベージュ）": "shoulder-length hair with face-framing layers, milk-tea beige",
    "セミロング黒髪ツヤレイヤー": "glossy layered shoulder-length black hair",
    "ハイトーンミルクティーグレージュミディアム": "medium hair, light milk-tea greige",
    "ハイトーンミルクティーショートボブ": "short bob, light milk-tea color",
    "ハイライト入り丸みショート": "rounded short cut with highlights",
    "ハイレイヤー×裾カラー（ブロンド）": "high layers with blonde-dyed ends",
    "ハッシュカット（グレージュ）": "hush cut, greige",
    "ハッシュカット（韓国ヘア）": "Korean hush cut",
    "バタフライカット（ヘーゼルカラー）": "butterfly cut, hazel",
    "バタフライカット（ミントベージュ・シースルーバング）": "butterfly cut with see-through bangs, mint beige",
    "バーガンディのシースルーレイヤー": "airy burgundy layers",
    "マッシュショート（前髪長め）": "mushroom short cut with long bangs",
    "ミディアムウルフパーマ": "medium wolf cut with a perm",
    "ミディアムニュアンスパーマ（コテ巻き風）": "medium hair with soft curling-iron waves",
    "ミディアムレイヤー内巻きワンカール（まろベージュ）": "medium layers with an inward curl, soft beige",
    "ミニボブパーマ（くせ毛風）": "mini bob with a natural-wave perm",
    "ミニボブ（オン眉ぱっつん前髪）": "mini bob with blunt bangs above the eyebrows",
    "レイヤーショートボブ（顔まわりレイヤー）": "layered short bob with face-framing layers",
    "ロブレイヤー（ミントベージュ）": "layered lob, mint beige",
    "ロングウルフ（クラゲヘア）": "long wolf cut (jellyfish haircut)",
    "ワンカールレイヤーと後れ毛（ショコラブラウン）": "layers with a single curl and loose face strands, chocolate brown",
    "丸みショートボブ（シースルーバング・ダークブラウン）": "rounded short bob with see-through bangs, dark brown",
    "内巻きワンカールボブ（ラベンダーアッシュ）": "bob with an inward curl, lavender ash",
    "切りっぱなしストレートボブ（前髪なし）": "blunt straight bob, no bangs",
    "切りっぱなし外ハネミディアムボブ": "blunt medium bob with flipped-out ends",
    "前下がりひし形ショートボブ（黒髪）": "A-line diamond-shaped short bob, black hair",
    "前下がりミディアムボブ（マロンベージュ）": "A-line medium bob, marron beige",
    "外ハネボブ（暗髪）": "flipped-out bob, dark hair",
    "斜めバングのエアリーカール": "airy curls with side-swept bangs",
    "耳掛けハンサムショート（前髪なし）": "short cut tucked behind the ears, no bangs",
    "艶さらストレートミディアムボブ（前髪なし）": "glossy sleek straight medium bob, no bangs",
    "重めミディアムレイヤー（バレイヤージュ）": "heavy medium layers with balayage",
    "鎖骨丈ミディアムレイヤーボブ（アッシュグレージュ）": "collarbone-length layered bob, ash greige",
    "韓国風タッセルボブ（サイドバング）": "Korean tassel bob with side bangs",
}


def style_en(s):
    return STYLE_EN.get(s, "")


def hair_en(h):
    return HAIR_EN.get(h, "hair")


def style_zh(s):
    return STYLE_ZH.get(s, s)


def hair_zh(h):
    return HAIR_ZH.get(h, h)
