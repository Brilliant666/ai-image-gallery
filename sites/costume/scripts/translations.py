# -*- coding: utf-8 -*-
"""衣装集 日→中 翻译表：分类 / 86 个标签（按语义分 6 组）/ 界面文案"""

CAT_ZH = {
    "春": "春",
    "夏": "夏",
    "秋": "秋",
    "冬": "冬",
    "ランジェリー": "内衣",
    "セクシー": "性感",
    "水着": "泳装",
    "パーティ": "派对",
}

# 标签分组：key -> (日文组名, 中文组名, [标签...])
TAG_GROUPS = [
    ("color", "色", "颜色", [
        "black", "white", "ivory", "beige", "cream", "grey", "brown",
        "red", "burgundy", "orange", "yellow", "gold",
        "green", "olive", "mint", "blue", "navy", "lavender", "purple", "pink", "silver", "khaki",
    ]),
    ("item", "アイテム", "单品", [
        "dress", "skirt", "shirt", "blouse", "camisole", "cardigan", "sweater", "turtleneck",
        "jacket", "coat", "pants", "jeans", "shorts", "vest", "hoodie", "robe", "apron",
        "bra", "briefs", "corset", "swimsuit",
    ]),
    ("shoe", "靴・靴下", "鞋袜", [
        "boots", "heels", "pumps", "sandals", "sneakers", "loafers",
        "socks", "stockings", "tights",
    ]),
    ("acc", "アクセサリー", "配饰", [
        "bag", "tote", "belt", "hat", "beret", "beanie", "headband",
        "necklace", "choker", "gloves", "sunglasses", "scarf", "muffler", "ribbon",
    ]),
    ("mat", "素材・柄", "材质・图案", [
        "knit", "lace", "leather", "suede", "satin", "velvet", "denim", "wool", "fur",
        "corduroy", "chiffon", "tulle", "mesh", "pleated", "frill", "floral", "polka-dot",
    ]),
    ("len", "丈", "长度", [
        "mini", "midi", "maxi",
    ]),
]

TAG_ZH = {
    # 颜色
    "black": "黑", "white": "白", "ivory": "象牙白", "beige": "米色", "cream": "奶油色",
    "grey": "灰", "brown": "棕", "red": "红", "burgundy": "酒红", "orange": "橙",
    "yellow": "黄", "gold": "金", "green": "绿", "olive": "橄榄绿", "mint": "薄荷绿",
    "blue": "蓝", "navy": "藏青", "lavender": "薰衣草紫", "purple": "紫", "pink": "粉",
    "silver": "银", "khaki": "卡其",
    # 单品
    "dress": "连衣裙", "skirt": "半身裙", "shirt": "衬衫", "blouse": "女式衬衫",
    "camisole": "吊带衫", "cardigan": "开衫", "sweater": "毛衣", "turtleneck": "高领衫",
    "jacket": "夹克", "coat": "大衣", "pants": "长裤", "jeans": "牛仔裤",
    "shorts": "短裤", "vest": "背心", "hoodie": "连帽衫", "robe": "长袍",
    "apron": "围裙", "bra": "文胸", "briefs": "内裤", "corset": "束身衣", "swimsuit": "泳衣",
    # 鞋袜
    "boots": "靴子", "heels": "高跟鞋", "pumps": "单鞋", "sandals": "凉鞋",
    "sneakers": "运动鞋", "loafers": "乐福鞋", "socks": "短袜",
    "stockings": "长筒袜", "tights": "连裤袜",
    # 配饰
    "bag": "包", "tote": "托特包", "belt": "腰带", "hat": "帽子", "beret": "贝雷帽",
    "beanie": "毛线帽", "headband": "发箍", "necklace": "项链", "choker": "颈链",
    "gloves": "手套", "sunglasses": "墨镜", "scarf": "围巾", "muffler": "围脖",
    "ribbon": "缎带",
    # 材质・图案
    "knit": "针织", "lace": "蕾丝", "leather": "皮革", "suede": "麂皮", "satin": "缎面",
    "velvet": "天鹅绒", "denim": "牛仔布", "wool": "羊毛", "fur": "毛皮",
    "corduroy": "灯芯绒", "chiffon": "雪纺", "tulle": "薄纱", "mesh": "网纱",
    "pleated": "百褶", "frill": "荷叶边", "floral": "花卉", "polka-dot": "波点",
    # 长度
    "mini": "迷你", "midi": "中长", "maxi": "长款",
}

# 日文标签名（源数据キーワード为英文，此表用于日文模式显示；英文仍保留在 title 里便于复制做提示词）
TAG_JA = {
    # 色
    "black": "黒", "white": "白", "ivory": "アイボリー", "beige": "ベージュ", "cream": "クリーム",
    "grey": "グレー", "brown": "ブラウン", "red": "赤", "burgundy": "バーガンディ", "orange": "オレンジ",
    "yellow": "黄", "gold": "ゴールド", "green": "緑", "olive": "オリーブ", "mint": "ミント",
    "blue": "青", "navy": "ネイビー", "lavender": "ラベンダー", "purple": "紫", "pink": "ピンク",
    "silver": "シルバー", "khaki": "カーキ",
    # アイテム
    "dress": "ワンピース", "skirt": "スカート", "shirt": "シャツ", "blouse": "ブラウス",
    "camisole": "キャミソール", "cardigan": "カーディガン", "sweater": "セーター",
    "turtleneck": "タートルネック", "jacket": "ジャケット", "coat": "コート",
    "pants": "パンツ", "jeans": "ジーンズ", "shorts": "ショートパンツ", "vest": "ベスト",
    "hoodie": "パーカー", "robe": "ローブ", "apron": "エプロン",
    "bra": "ブラ", "briefs": "ショーツ", "corset": "コルセット", "swimsuit": "水着",
    # 靴・靴下
    "boots": "ブーツ", "heels": "ヒール", "pumps": "パンプス", "sandals": "サンダル",
    "sneakers": "スニーカー", "loafers": "ローファー", "socks": "ソックス",
    "stockings": "ストッキング", "tights": "タイツ",
    # アクセサリー
    "bag": "バッグ", "tote": "トートバッグ", "belt": "ベルト", "hat": "ハット",
    "beret": "ベレー帽", "beanie": "ニット帽", "headband": "ヘアバンド",
    "necklace": "ネックレス", "choker": "チョーカー", "gloves": "手袋",
    "sunglasses": "サングラス", "scarf": "スカーフ", "muffler": "マフラー", "ribbon": "リボン",
    # 素材・柄
    "knit": "ニット", "lace": "レース", "leather": "レザー", "suede": "スエード",
    "satin": "サテン", "velvet": "ベロア", "denim": "デニム", "wool": "ウール",
    "fur": "ファー", "corduroy": "コーデュロイ", "chiffon": "シフォン", "tulle": "チュール",
    "mesh": "メッシュ", "pleated": "プリーツ", "frill": "フリル", "floral": "花柄",
    "polka-dot": "ドット柄",
    # 丈
    "mini": "ミニ", "midi": "ミディ", "maxi": "マキシ",
}

UI = {
    "ja": {
        "title": "AI イラスト向け衣装参考画像集：1407 着の衣装とタグ検索 · 衣装集",
        "eyebrow": "COSTUME-DB-01 · 衣装参考 · ミラー",
        "h1": "衣装集",
        "sub1": "人物の入っていない衣装だけの画像（2:3）。色・アイテム・素材など 86 タグで組み合わせて絞り込め、タグはそのままプロンプトに使えます。",
        "all": "すべて",
        "search": "キーワード・番号・タグで検索",
        "filter": "タグで絞り込み",
        "sortCat": "分類 → 番号",
        "sortId": "番号順",
        "sortTag": "タグ数",
        "sortLabel": "並べ替え",
        "count": "<b>{n}</b> 件 · <b>{t}</b> タグ選択中",
        "countNoTag": "<b>{n}</b> 件",
        "more": "さらに表示（残り {n} 件）",
        "emptyTitle": "条件に合う衣装がありません",
        "emptyDesc": "タグを減らすか、キーワードを変えてください。",
        "kCat": "分類",
        "kId": "番号",
        "kTagN": "タグ数",
        "tagUnit": "個",
        "dlPng": "PNG をダウンロード",
        "openFull": "原寸 PNG を開く",
        "dlOne": "原寸 PNG をダウンロード",
        "copyLink": "画像リンクをコピー",
        "close": "閉じる",
        "prev": "前へ",
        "next": "次へ",
        "hint": "<kbd>←</kbd><kbd>→</kbd> 前後　<kbd>Esc</kbd> 閉じる　タグをクリックで絞り込み",
        "footer": "素材元：<a href=\"https://ai-costume-gallery.pages.dev/\" target=\"_blank\" rel=\"noopener noreferrer\">ai-costume-gallery.pages.dev</a>（COSTUME-DB-01）。ローカルミラーは個人の参照用です。元画像の再配布・転売はご遠慮ください。",
        "clearTags": "タグを全解除",
    },
    "zh": {
        "title": "AI 绘画服装参考图库：1407 套服装、86 个标签组合筛选 · 服装集",
        "eyebrow": "COSTUME-DB-01 · 服装参考 · 镜像",
        "h1": "服装集",
        "sub1": "不含真人的纯服装参考图（2:3）。86 个标签按颜色、单品、鞋袜、配饰、材质、长度组合筛选，标签保留英文关键词，可直接作提示词。",
        "all": "全部",
        "search": "搜索关键词 / 编号 / 标签",
        "filter": "按标签筛选",
        "sortCat": "分类 → 编号",
        "sortId": "编号顺序",
        "sortTag": "标签数",
        "sortLabel": "排序",
        "count": "<b>{n}</b> 件 · 已选 <b>{t}</b> 个标签",
        "countNoTag": "<b>{n}</b> 件",
        "more": "加载更多（还有 {n} 件）",
        "emptyTitle": "没有符合条件的服装",
        "emptyDesc": "减少标签，或换个关键词。",
        "kCat": "分类",
        "kId": "编号",
        "kTagN": "标签数",
        "tagUnit": "个",
        "dlPng": "下载 PNG",
        "openFull": "打开原图 PNG",
        "dlOne": "下载原图 PNG",
        "copyLink": "复制图片链接",
        "close": "关闭",
        "prev": "上一张",
        "next": "下一张",
        "hint": "<kbd>←</kbd><kbd>→</kbd> 前后切换　<kbd>Esc</kbd> 关闭　点标签加入筛选",
        "footer": "素材来源：<a href=\"https://ai-costume-gallery.pages.dev/\" target=\"_blank\" rel=\"noopener noreferrer\">ai-costume-gallery.pages.dev</a>（COSTUME-DB-01）。本地镜像仅供个人参考，请勿再分发或转售原始图片。",
        "clearTags": "清除全部标签",
    },
}
