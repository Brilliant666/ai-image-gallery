# 二次元角色库

原生页面路径：`/character/`。收录 [たき AI 的角色组装 DB 公开版](https://charadb-2fi.pages.dev/)，本站独立编写界面与中文短名，保留日文名称及英文标签。

- 843 个基础条目：头发与眼睛 122、服装 440、姿势 281。
- 184 个发型换色版本单独计算，不重复作为基础卡片；姿势侧视图按原目录作为独立条目。
- 281 个姿势的原站线稿入口。
- 791 个基础条目默认可见，52 个泳装或偏性感条目需顶部 18+ 确认。普通双人日常动作不整类隐藏。
- 中日名称、英文标签和 ID 检索；分类、收藏、发型颜色预览、放大；八个标签槽（发型、刘海、发色、发饰、眼睛颜色、眼睛形状、服装、姿势）。
- 复制时合并重复标签，双人标签会移除冲突的 `solo`、`1girl` 等单人标签并提示。其他语义冲突仍需自行检查。

## 图片与许可

图片通过浏览器从原站 HTTPS 地址读取，仓库与发布目录不保存这些图片，不提供批量下载或拼图导出。原图、线稿均链接原站。远程读取不代表获得图片再分发许可，原作者条件见 [NOTICE.md](NOTICE.md)。

联网且原站可用时显示图片；原站故障或离线时，名称、搜索、收藏和标签组装仍能使用。`index.html` 内嵌全部目录及脚本，直接 `file://` 打开不需要 fetch 元数据。收藏保存在 `pl.character.favorites.v1`，组装保存在 `pl.character.v1`；成人向隐藏时，已选成人条目不展示图片，也不加入输出。

不调用生图 API，不配置 Key，不保证同一组文字能在所有模型中固定角色身份。服装/姿势的英文标签不额外添加示例角色的棕发与棕眼。

## 构建与目录更新

从仓库根目录构建：

```bash
python tools/build.py --site character
```

`data/catalog.json` 是 2026-11-01 原站 `data.js` 公开版的字段白名单快照，记录原文件 SHA-256。原文件仅作 JSON 解析，不执行 JavaScript，不保留社区或额外下载入口。

维护者可手动保存新公开版 `data.js`，再导入：

```bash
python -I sites/character/scripts/import_catalog.py /path/to/data.js
```

新增条目须在 `scripts/translations.py` 添加自己的中文短名，审核 `scripts/build_gallery.py` 的默认隐藏规则，并更新 `sites.json` 数量。导入器拒绝非 public tier、重复 ID、未知 ID 与缺失父条目；不要用镜像仓库的汉化文件直接覆盖本站翻译。

```bash
python tests/test_character.py
```

```bash
node tests/character.js
```
