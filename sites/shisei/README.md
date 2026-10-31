# Shisei · CC0 姿势线稿（中文镜像）

**280 个姿势 / 1133 张五视角线稿，四个系列，CC0 可商用、可再分发**

在线浏览：[photoai.life/shisei/](https://photoai.life/shisei/) · 上游项目：[wquguru/shisei](https://github.com/wquguru/shisei)（v0.3.0）

## 内容

| 系列 | 姿势 | 线稿 | 说明 |
|---|---:|---:|---|
| 全身・标准 | 71 | 287 | 2 个姿势为 suggestive |
| 上半身 | 80 | 337 | 性感系、胸线强调系多为 suggestive |
| 全身・性感 | 80 | 323 | 几乎全部 suggestive |
| 双人 | 49 | 186 | 几乎全部 suggestive |

- 每个姿势最多 5 个视角：正面、斜角、侧面、俯视、仰视。没通过上游质检的视角不收录。
- 图片三档直接取自上游：缩略图 300px、中图 600px（灯箱）、原图 900px（下载）。
- 上游标为 `suggestive` 的姿势默认模糊，点开或打开「取消模糊」即可查看；它们不出现在静态落地页和 sitemap 里。
- 姿势名、分类的中文译名取自上游 catalog（v0.3.0）。

## 和姿势集的区别

姿势集（`sites/pose/`）是 ギア 的原图，禁止再分发。Shisei 是另一个项目按同一份姿势目录**重新绘制**的线稿，图片 CC0，
可以商用、再分发和打包。两者的姿势编号与名称同源，图不同。

## 构建

在仓库根目录：

```bash
python sites/shisei/scripts/manifest.py      # data/catalog.json → manifest.json（只在升级上游版本时需要）
python tools/fetch.py --site shisei          # 下载三档图片（约 57 MB）
python tools/verify.py --site shisei
python tools/build.py --site shisei
python tools/serve.py --root sites/shisei
```

升级上游版本：把 `scripts/manifest.py` 里的 `TAG` 改成新标签，替换 `data/catalog.json`，重跑上面几步。

## 授权

图片 CC0 1.0；姿势目录仅注明出处；本站代码 MIT。详见 [NOTICE.md](NOTICE.md)。
