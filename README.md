<div align="center">

# AI 图片素材库 · 单仓多站

**五个 AI 绘画参考图库、六个站点入口，一个仓库构建，一个目录部署**

人像 · 姿势（线稿与深度图） · 服装 · CC0 姿势线稿 · 二次元角色库 · 中日双语 · 浅色 / 深色

15,241 个本地托管图片文件（含不同尺寸）；角色库另有 843 个基础条目 + 184 个发色变体，远程图片不计入文件总数。

[![CI](https://github.com/Brilliant666/ai-image-gallery/actions/workflows/ci.yml/badge.svg)](https://github.com/Brilliant666/ai-image-gallery/actions/workflows/ci.yml)
[![online](https://img.shields.io/badge/online-photoai.life-2563eb?style=flat-square)](https://photoai.life/)
[![sites](https://img.shields.io/badge/sites-6-0ea5e9?style=flat-square)](#站点与图库)
[![images](https://img.shields.io/badge/image_files-15%2C241-8b5cf6?style=flat-square)](#站点与图库)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776ab?style=flat-square&logo=python&logoColor=white)](#快速开始)
[![License](https://img.shields.io/badge/code-MIT-22c55e?style=flat-square)](#许可与致谢)

### [在线浏览 · photoai.life →](https://photoai.life/)

**简体中文** · [English](README_en.md) · [日本語](README_ja.md)

[站点与图库](#站点与图库) · [快速开始](#快速开始) · [图片加载](#图片加载) · [部署](#部署) · [文档](#文档)

</div>

![入口页](docs/screenshots/hub-light.jpg)

<details>
<summary>📷 更多截图：人像、姿势、深度姿势、服装</summary>

![人像集 · 网格](docs/screenshots/portrait-grid.jpg)

![人像集 · 灯箱](docs/screenshots/portrait-lightbox.jpg)

![姿势集 · 深色](docs/screenshots/pose-grid.jpg)

![姿势集 · 灯箱](docs/screenshots/pose-lightbox.jpg)

![姿势集 · 深度图](docs/screenshots/pose-depth-grid.jpg)

![服装集 · 分面筛选](docs/screenshots/costume-filter.jpg)

![服装集 · 灯箱](docs/screenshots/costume-lightbox.jpg)

截图来自线上页面，用于演示界面。素材著作权归各原作者所有，不能从截图中裁取素材另作他用。

</details>

## 站点与图库

| 站点 | 内容 | 规模 | 素材授权 |
| --- | --- | --- | :---: |
| [人像集](https://photoai.life/portrait/) | 保持角色脸部一致性的人脸参考，按发型筛选 | 1,499 张 | **CC0** |
| [姿势集](https://photoai.life/pose/) | 无脸灰色人偶线稿，每个姿势 5 个视角 | 1,439 张 | 禁止再分发 |
| [姿势集 · 深度图](https://photoai.life/pose-depth/) | 同一模块的深度图入口，灰度深度图可直接用于 ControlNet | 1,439 张 | 禁止再分发 |
| [服装集](https://photoai.life/costume/) | 不含真人的服装图，86 个标签分面筛选 | 1,407 件 / 4,221 张 | 禁止再分发 |
| [Shisei 姿势线稿](https://photoai.life/shisei/) | 无脸人偶线稿，四个系列、每个姿势最多 5 个视角，成人向默认隐藏 | 280 个姿势 / 1,133 张 | **CC0** |
| [二次元角色库](https://photoai.life/character/) | 发型、服装、姿势参考，图片从原站加载 | 843 基础条目 + 184 发色变体；281 张姿势线稿 | 禁止再分发原图及加工图 |

六个物理站点对应五个顶部导航图库：姿势线稿和深度图合并为一个图库。角色库基础条目为头发与眼睛 122、服装 440、姿势 281；含发色变体共 1,027 条，线稿单独计算。这些远程条目不计入 15,241 个本地图片文件。

每个图库都有网格分批加载、筛选与搜索、图片放大、主题与语言切换。本地托管图库还支持灯箱 `←` `→` 翻页、手机滑动和原图下载；角色库通过原站链接查看原图与线稿，`Esc` 关闭详情。页首是全站共用的顶部栏：图库切换、18+、深浅色、中 / 日都在上面，偏好全站通用；`?` 查看快捷键、`/` 跳到搜索框。姿势集用一个开关在线稿和深度图之间切换，大图里可以拖动竖线左右对比。
姿势、深度姿势、服装、Shisei 和角色库的成人向内容默认隐藏（角色库默认可浏览 791 个基础条目，184 个发色变体通过换色预览）；顶部栏的「18+」确认一次年龄后打开，各图库通用。成人向内容不进任何静态落地页和 sitemap。页面是单个 `index.html`，数据内嵌，没有框架、CDN 和外部字体。

> **人像集和 Shisei 是 CC0**，其余站点的素材禁止再分发。二次元角色库允许商用作品制作、参考与修改，但禁止再分发原图或加工图，禁止用于表现真实人物或未成年人。Shisei 的姿势目录沿用 ai-pose-gallery，只注明出处。详见各站的 `sites/<id>/NOTICE.md`。

### 二次元角色库

本站保持纯资源图库，不提供生图、Key 设置或多部件标签组装。角色库使用白底方形图片展示，并提供：

- 头发与眼睛、服装、姿势三个分区；带数量的分类按钮直接切换，成人分类默认标记为 18+。
- 每张发型卡片下的棕、黑、金、粉、银五个色点，互不影响；详情换色同步对应卡片。顶部统一发色会重设预览，重置恢复棕色。
- 卡片和详情复制当前条目的原始英文标签；收藏保存当前展示版本，保存在本浏览器，换色不改写已有收藏。
- 元数据、搜索、分类和标签复制可离线使用；图片始终依赖原站网络，不下载、打包或镜像。

使用和目录维护见 [角色库说明](sites/character/README.md)，图片条件见 [来源与许可](sites/character/NOTICE.md)。

## 快速开始

本仓库不含素材图片文件。`tools/fetch.py` 下载本地托管站点的图片，遇到 `imageMode: "remote"` 的角色库会明确跳过，不下载或镜像其原图、缩略图或线稿。角色库保留本地页面、源数据和 manifest，图片 URL 直接指向原站；从 `file://` 打开也需要联网加载图片。需要 **Python 3.8+**。生成中图的 `tools/mid.py` 另需 Pillow（`pip install pillow`），其余脚本只用标准库。

```bash
git clone https://github.com/Brilliant666/ai-image-gallery.git
cd ai-image-gallery

python tools/fetch.py      # 下载本地托管图库的图片，跳过角色库（首次约 6.8 GB，之后只补缺失）
python tools/mid.py        # 生成灯箱中图（约 290 MB）
python tools/build.py      # 构建六个站点入口（五个图库）+ 入口页
python tools/release.py    # 组装 dist/（图片硬链接，不额外占盘）
python tools/serve.py      # 预览 http://127.0.0.1:8080/
```

只想看页面效果，用 `python tools/fetch.py --tier thumb` 只下缩略图（约 90 MB）。

验收请用 `serve.py`，不要直接双击 `dist/index.html`：`file://` 和 `http://` 在相对路径、Content-Type、缓存上都有差异。

<details>
<summary>常用命令</summary>

| 命令 | 作用 |
| --- | --- |
| `python tools/fetch.py --site pose` | 只下载一个站 |
| `python tools/mid.py --site portrait` | 只生成一个站的中图 |
| `python tools/verify.py` | 本地图库检查图片与中图；角色库仅检查远程元数据 |
| `python tools/build.py --site character` | 重建角色库及首页；不访问图片网络 |
| `python tools/build.py --site pose` | 只重建一个站 |
| `python tools/build.py --base https://x.com` | 指定正式域名，写入 canonical / og / sitemap |
| `python tools/release.py --out <目录>` | 发布到指定目录 |
| `python tools/serve.py --root sites/pose` | 预览单个站点 |
| `python tests/run.py` | 不依赖图片的检查：构建产物是否最新、重复 id、内联 JS 语法、manifest、文档链接（CI 每次推送都跑） |

`release.py` 发布前会先校验本地图片，缺图就中止（只下了部分档位时加 `--skip-verify`）。remote 站点只验证 manifest 元数据，不验证网络、图片存在性或解码；发布时保留页面、`data/` 和 manifest，不包含远程图片。它会先删除再重建目标站点目录。`--no-images` 只放站点文件、不放图片，不能用来保留线上旧图。

</details>

## 图片加载

本地托管图库通常有三档：网格用缩略图，灯箱用中图，原图只在下载时用到。角色库使用原站远程缩略图、原图和可用的线稿，不生成本地中图；`tiers: []`、`imageDirs: []` 阻止下载与图片打包。

| 档位 | 人像 | 姿势 | 深度姿势 | 服装 |
| --- | ---: | ---: | ---: | ---: |
| 缩略图 | 约 20 KB | 约 17 KB | 约 11 KB | 约 10 KB |
| 中图 | 约 150 KB | 约 33 KB | 约 10 KB | 约 90 KB |
| 原图 | 约 3.2 MB | 约 450 KB | 约 95 KB | 约 1 MB |

以下预取与中图行为适用于本地托管图库；角色库详情直接读取原站图片。

- 灯箱打开时先显示清晰的缩略图，中图到达后淡入；换图时上一张立即隐藏。
- 鼠标在卡片上停留 120 ms、手指按下或键盘选中时开始预取中图；打开后再预取前后各一张。
- 服装集的中图来自原站，另外三站由 `tools/mid.py` 从原图生成（最长边 1600px，WebP 质量 82）。中图缺失时灯箱退回原图。

在 1.5 MB/s、150 ms 延迟下实测人像集：直接点击约 0.6 秒换成中图；悬停约 1 秒后再点，打开就是中图。

## 部署

站点根指向 `dist/`。`dist/` 是扁平结构（`index.html` + `portrait/` + `pose/` + …），入口页的相对链接直接命中，nginx 不需要 `alias`。

```bash
# 服务器更新：丢弃构建产物；有手改文件时中止并列出，不会悄悄覆盖
python3 tools/update.py
python3 tools/mid.py
python3 tools/build.py --base https://你的域名
python3 tools/release.py --out dist-stage   # 先发到暂存目录，检查后逐站原子换入 dist/
```

首次部署、nginx 配置、原子切换和回滚见 [deploy/DEPLOY.md](deploy/DEPLOY.md)。

## 项目结构

```
ai-image-gallery/
├── sites.json          # 唯一清单：站点、顺序、授权、图片档位
├── sites/<id>/         # 各站：脚本、数据、构建产物、NOTICE
├── shared/             # 各站共用的下载与校验；姿势 / 深度姿势共用的页面生成器、原站解析、日中词典
├── hub/                # 入口页生成器（同时生成根 sitemap / robots）
├── tools/              # fetch / mid / verify / build / release / serve / update
├── deploy/             # 部署手册与 nginx 模板
├── tests/              # 不依赖图片的检查（python tests/run.py）
└── docs/               # 文档与截图
```

图片不进 git：6.8 GB 二进制放进仓库，每次 clone 都要拉一遍，各站授权也不允许。`release.py` 把 20,751 个图片文件硬链接进 `dist/`，同一文件系统下不额外占盘。

## 文档

[部署手册](deploy/DEPLOY.md) · [加第 N 个站](docs/ADDING_A_SITE.md) · [nginx 模板](deploy/nginx.conf) · 各站说明：[人像](sites/portrait/README.md) · [姿势](sites/pose/README.md) · [深度姿势](sites/pose-depth/README.md) · [服装](sites/costume/README.md) · [Shisei](sites/shisei/README.md) · [角色](sites/character/README.md)

## 许可与致谢

| 范围 | 许可 |
| --- | --- |
| 代码：`tools/`、`hub/`、`shared/`、各站 `scripts/`，以及 `index.html` 里的 HTML/CSS/JS | [MIT](LICENSE) |
| 图片素材 | 各站不同，见 `sites/<id>/NOTICE.md` |
| 本站独立整理的中文译文（`data/` 及角色库中文短名表） | CC BY 4.0 |
| 角色库原站目录字段与图片 | 依原作者条件；不随本站代码或译文重新许可，见 [NOTICE](sites/character/NOTICE.md) |

素材来自各原站：人像集作者 [あぎ](https://x.com/agi_aibusi)（[原站](https://ai-portrait-gallery.pages.dev/)），姿势集、深度姿势集、服装集作者 [ギア](https://x.com/giaaibusi)（[姿势](https://ai-pose-gallery.pages.dev/) · [深度姿势](https://ai-pose-depth-gallery.pages.dev/) · [服装](https://ai-costume-gallery.pages.dev/)）。Shisei 线稿来自 [wquguru/shisei](https://github.com/wquguru/shisei)（CC0）。二次元角色库来自 [たき AI](https://x.com/taki_auto) 的 [キャラ組み立てDB](https://charadb-2fi.pages.dev/)，图片仅由原站加载。本项目是个人学习用途的中文索引。
