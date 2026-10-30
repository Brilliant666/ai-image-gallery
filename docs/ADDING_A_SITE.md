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
| `code` | 入口页封面左下角的编号 |
| `cover` | 相对站点目录的封面路径 |
| `coverPos` | 封面框是 16:10，竖图必然裁切：脸部特写用 `25%`–`35%`，全身图用 `0%`–`10%`，主体居中用 `50%` |
| `tiers` | 下载与校验的档位，对应 manifest 里的 `<tier>_url` / `<tier>_path` |
| `imageDirs` | `release.py` 硬链接的目录；含 `mid` 时 `mid.py` 会为该站生成中图 |
| `license` | `cc0` / `conditional` / `restricted`，决定入口页卡片上的授权徽章 |

站点在入口页的顺序 = `sites.json` 数组顺序。

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

- 主题切换 `[☀ Light][☾ Dark]`，默认浅色
- 语言切换 `[中文][日本語]`，默认中文，中文在左
- `<head>` 内用同步脚本应用已存偏好，避免刷新闪白
- 单文件 `index.html`，数据内嵌，零外部依赖
- 分页加 `IntersectionObserver` 预取，不一次渲染全部卡片
- 灯箱底图用清晰缩略图，不加模糊；中图到达后淡入
