# 二次元服装独立公开库

主仓库负责 `costume-anime` 图库的源码、目录、页面与共用导航。独立仓库 [Brilliant666/ai-costume-anime-gallery-cn](https://github.com/Brilliant666/ai-costume-anime-gallery-cn) 是可独立运行的导出快照，提供搜索入口，并通过 README、仓库主页和页面品牌链接返回 [photoai.life](https://photoai.life/)。主站路径为 `/costume-anime/`，仓库发布与生产部署是独立步骤。

## 导出内容

- 1,320 条目录与 manifest、中文 / 日文标签、图库脚本和 HTML，以及非成人向分类和标签落地页。
- 最小共用组件 `shared/ui.py`、`landing.py`、`adult.py`、`assets.py`，以及现有服装库的标签词典。
- 只含本图库的 `sites.json`、根目录使用说明、MIT 代码许可、来源说明和 `build.py`。
- `docs/screenshots/` 中三张清晰的非成人界面截图：桌面目录、组合筛选和手机布局。
- 不包含其他图库的数据、素材图片文件、批量图片下载器、账号、API Key 或生图功能。

原站为 <https://ai-costume-anime-gallery.pages.dev/>，原作者为ギア。原站图片 URL 与目录字段不因本站代码或译文许可而重新许可。原站禁止批量下载和再分发图片，图库只在浏览器中引用原站资源，不下载或打包素材图片；文档截图用于演示界面，不改变截图内素材的条件。详细条件见 [NOTICE](../sites/costume-anime/NOTICE.md)。

## 从主仓库更新

修改主仓库中的 `sites/costume-anime/` 后先构建、测试，再导出到一个不存在的新目录：

```bash
python tools/build.py
```

```bash
python tests/run.py
```

```bash
python tools/export_costume_anime.py --out _v/costume-anime/standalone-next
```

导出脚本拒绝覆盖已有目录，自动忽略主仓库本地 `.gitignore` 图片目录（`thumbs/`、`img/`、`png/`），将导出目录中的 `sites.json` 设为 `imageMode: "remote"`、`tiers: []`、`imageDirs: []`，并以 `COSTUME_ANIME_REMOTE=1` 运行独立构建，随后校验导出目录中除原创 `og-cover.jpg` 与三张文档界面截图外不含任何素材图片。独立库 README 与截图由主仓库统一维护；截图来自 `docs/screenshots/costume-anime-standalone/{grid,filter,mobile}.jpg`，导出时复制到独立库 `docs/screenshots/`。三张截图缺失时中止导出，避免发布缺图 README。

导出完成后，直接打开独立库 `index.html`，按链接进入图库；也可打开 `sites/costume-anime/index.html`。重新构建：

```bash
python build.py
```

更新截图时先导出到新目录，打开导出的单库页面，在 18+ 关闭状态下拍摄桌面目录、`ivory` + `knit` 筛选和手机布局，保留正常清晰度。将截图保存回主仓库后重新导出，确认 README 图片全部可访问。

审核目录差异、构建 HTML 和页面截图后，按主题提交 PR 到独立仓库，由维护者手动合并。不要在两个仓库分别长期修改同一份生成器；优先在主仓库修正后重新导出。

独立页面的 canonical 和 sitemap 使用 `https://photoai.life/costume-anime/`，让索引指向主站入口；原始图片仍从作者站点请求。仓库发布不会自动开通 GitHub Pages，也不代替生产部署。
