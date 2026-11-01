# 加第 N 个站

新站点只要满足下面的约定，`tools/` 下的 fetch / mid / verify / build / release 都不用改。
下载和校验是共用的（`shared/assets.py`），各站不需要自己的下载或校验脚本。

## 1. 建目录

```
sites/<新站id>/
├── scripts/
│   ├── build_gallery.py    # 必填
│   ├── extract.py          # 按需：从原站存档解析 data/
│   └── manifest.py         # 按需：data/ → manifest.json
├── data/                   # 结构化数据（入库）
├── index.html              # 构建产物（入库，便于直接预览）
├── LICENSE
├── NOTICE.md               # 该站单独的授权说明
└── README.md
```

| 文件 | 约定 |
|---|---|
| `scripts/build_gallery.py` | 读环境变量 `SITE_URL`，输出 `index.html`、`data/`、`robots.txt`、`sitemap.xml`、`404.html`。站点根用 `dirname(dirname(__file__))` 自己算，不依赖当前目录 |
| `manifest.json` | 每条记录对 `sites.json` 里的每个档位 `<tier>` 都有 `<tier>_url` 和 `<tier>_path`（例如 `thumb_url` / `thumb_path`）。`tools/fetch.py` 和 `tools/verify.py` 只靠这条规则工作 |

结构和姿势集相同的站，直接复用 `shared/pose_gallery.py` 与 `shared/pose_source.py`，只写一份 `config.py`（参考 `sites/pose/config.py`）。
数据来自别的项目、系列和名称不同的，参考 `sites/shisei/config.py`：系列与视角顺序、中文名表、作者、`adultMode`（成人向默认隐藏 `hide` 或模糊 `blur`）都在配置里。

## 2. 在 `sites.json` 追加一条

```json
{
  "id": "new-site",
  "code": "NEW-DB-01",
  "name": { "zh": "新站名", "ja": "新サイト名" },
  "desc": { "zh": "一句话说明。", "ja": "一文で説明。" },
  "stats": [{ "v": "1234", "l": { "zh": "图片", "ja": "画像" } }],
  "license": "cc0",
  "source": "https://new-site.pages.dev/",
  "cover": "thumbs/cover.webp",
  "coverPos": "center 30%",
  "tiers": ["thumb", "full"],
  "imageDirs": ["thumbs", "mid", "img"]
}
```

| 字段 | 说明 |
|---|---|
| `id` | 唯一标识，同时是目录名和 URL 路径 |
| `source` | 原站地址，下载时作为 Referer |
| `imageBase` | 本地站点可选；remote 模式必填，以 `/` 结尾的 HTTPS 图片根地址。测试据此核对 manifest 的 URL |
| `imageMode` | 可选，默认本地托管。`remote` 表示浏览器直接加载原站图片，fetch/mid 不处理图片，verify 仅校验元数据，release 不包含图片 |
| `code` | 站点编号，写在画廊页头的小标题里 |
| `mergedInto` | 可选。并入另一个站点的模块时填对方 id（如 `pose-depth` → `pose`）：入口页与顶部栏不单独列出，下载、校验、发布照常 |
| `updated` | 站点数据最近更新的日期，写进 sitemap 的 lastmod |
| `cover` | 本地模式相对站点目录；remote 模式相对 `imageBase`，须对应 manifest 的 `thumb_path` |
| `coverPos` | 入口页封面框是 4:5，横图必然裁切：脸部特写用 `25%`–`35%`，全身图用 `0%`–`10%`，主体居中用 `50%` |
| `tiers` | 下载与校验的档位，对应 manifest 里的 `<tier>_url` / `<tier>_path` |
| `imageDirs` | `release.py` 硬链接的目录；含 `mid` 时 `mid.py` 会为该站生成中图（`tiers` 里已有 `mid` 的站点由上游提供，不生成） |
| `license` | `cc0` / `conditional` / `restricted`，决定入口页卡片上的授权徽章 |
| `adult` | 可选。成人向内容的判定规则：`{manifest 字段名: [取值, …]}`，任一字段命中即算成人向，例如 `{"分类": ["ランジェリー"]}`。命中的图不进任何静态落地页；画廊里默认隐藏，工具栏「18+」开关打开后显示。`tests/run.py` 会检查（见 `shared/adult.py`） |

站点在入口页的顺序 = `sites.json` 数组顺序。

### 远程图片站点

不能镜像图片的图库可参考 [角色库](../sites/character/README.md)。仅将 `imageMode` 改为 `remote` 不等于取得图片展示许可，先记录原作者条件。配置还须包含：

```json
{
  "imageMode": "remote",
  "imageBase": "https://source.example/",
  "cover": "thumb/A001.webp",
  "tiers": [],
  "imageDirs": []
}
```

manifest 仍需非空的 `thumb_path`/`thumb_url`、`full_path`/`full_url`，线稿如有则同时提供 `line_path`/`line_url`。路径为可移植相对路径，URL 必须等于 `imageBase + path`；verify 不访问网络，不证明上游图片存在或可解码。

画廊内嵌元数据与脚本；静态落地页的 `landing.Item.thumb` 使用原站 HTTPS URL。`landing.Site.share_image` 指向实际可用的原站分享图，`gallery_features` 填写本图库实际支持的功能，避免沿用本地图库的下载说明。浏览器离线时仍可检索元数据，图片无法显示。图片不得通过 fetch、mid、release 或新建的下载脚本变成本地托管。

新增落地页目录时同步 `tools/update.py` 的 `BUILD_OUTPUT`；发布读取 `data/landing.json` 的目录清单。角色库使用 `cat/`。

## 3. 构建

```bash
python tools/fetch.py --site new-site
python tools/mid.py --site new-site      # imageDirs 含 mid 时
python tools/verify.py --site new-site
python tools/build.py
python tools/release.py
python tools/serve.py
python tests/run.py                      # 提交前跑一遍；CI 也会跑
```

`tests/run.py` 会自动覆盖 `sites.json` 里的新站：构建产物是否最新、重复 id、JS 引用的 id 是否存在、
内联数据是否都被页面使用、页面体积上限、manifest 的档位字段与路径、封面是否在 manifest 里。

上线到已有服务器的步骤见 [DEPLOY.md](../deploy/DEPLOY.md) §6。

## 设计约定

新站点请保持一致：

- 页面骨架用 `shared/ui.py`：`<head>` 放 `head_script()` 和 `head_css()`，`<body>` 开头放 `bar(<站点id>)`，末尾放 `dialogs()` 和 `body_script()`。顶部栏里的短名在 `ui.LABELS` 里加一条
- 深浅色、语言、18+ 都在顶部栏，偏好全站共用（`pl.theme` / `pl.lang` / `hub.adult`），页面监听 `pl:lang`、`pl:adult` 事件更新自己
- 静态中日文写成 `<span class="zh">…</span><span class="ja">…</span>`，动态文案放进站点的 UI 表
- 单文件 `index.html`，数据与脚本内嵌，不依赖前端框架、外部脚本或字体；remote 图片联网加载
- 分批渲染卡片，使用自动加载或显式「显示更多」，不一次渲染全部目录
- 本地图库的灯箱底图用清晰缩略图，不加模糊；中图到达后淡入。remote 图库直接引用原站图片，不生成或预取本地中图
