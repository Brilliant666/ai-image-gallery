# 部署手册 · 单仓多站

> 站点根 = `tools/release.py` 生成的 `dist/`。
> 与旧方案的区别：不再用 `releases/<版本>/public` + `current` 软链，改为 **git commit 即版本**。
> 线上更新时先发布到暂存目录，检查后再逐个站点原子换入 `dist/`（见 §4），旧版留作回滚。

---

## 0. 前置条件

| 项 | 要求 |
|---|---|
| 系统 | Debian 13 / Ubuntu 24.10+（原子对调需要 GNU coreutils 9.5+ 的 `mv --exchange`） |
| git | 任意版本（更新用 `tools/update.py`，见 §4） |
| Python | 3.8+；`tools/mid.py` 需要 Pillow（`apt install python3-pil`），其余只用标准库 |
| 磁盘 | ≥ 10 GB 可用（图片 6.8 GB + 中图约 290 MB；硬链接不额外占盘） |
| 内存 | ≥ 512 MB |
| 域名 | 已解析到本机 IP |

```bash
git --version
python3 --version
df -h /
free -m | head -2
```

---

## 1. 首次部署

```bash
apt update
apt install -y git python3 python3-pil nginx

git clone https://github.com/Brilliant666/ai-image-gallery.git /srv/ai-image-gallery
cd /srv/ai-image-gallery

# ① 下载图片（约 6.8 GB，只需一次）
python3 tools/fetch.py

# ② 生成灯箱中图（约 290 MB，几分钟；之后只补缺失）
python3 tools/mid.py

# ③ 用正式域名构建
python3 tools/build.py --base https://你的域名.com

# ④ 组装发布目录
python3 tools/release.py
```

**预期输出**（release 阶段）：

```
发布 · 6 个站点 → /srv/ai-image-gallery/dist
  校验通过（remote 站点仅校验元数据，未校验网络或图片文件）
  [portrait] 74 个站点文件  图片 4497 链接  → 4.8 GB
  [costume] 98 个站点文件  图片 4221 链接  → 1.4 GB
  [pose] 22 个站点文件  图片 4317 链接  → 710.3 MB
  [pose-depth] 22 个站点文件  图片 4317 链接  → 162.5 MB
  [shisei] 24 个站点文件  图片 3399 链接  → 59.1 MB
  [character] 36 个站点文件  remote 原站图片（不下载、不复制；仅发布页面、数据与 manifest）
  [hub] 10 个根级文件已复制（index.html, sitemap.xml, robots.txt, og-cover.jpg, llms.txt, favicon.ico, …）
其中 20751 个图片文件为硬链接，不额外占盘
```

> `dist/` 报告 7.0 GB，但因为是硬链接，**实际磁盘增量接近 0**。
> 若出现「退化为复制」警告，说明 `dist/` 与 `sites/` 不在同一文件系统。

---

## 2. nginx（单域名路径式）

目标拓扑：**全部站点挂在 `photoai.life` 一个域名下**，按路径区分。

```
https://photoai.life/            入口页
https://photoai.life/portrait/   人像集
https://photoai.life/costume/    服装集
https://photoai.life/pose/       姿势集（默认线稿，可切换深度图）
https://photoai.life/pose-depth/ 姿势集的深度图入口（同一模块，默认深度图）
https://photoai.life/shisei/     CC0 姿势线稿
https://photoai.life/character/  二次元角色参考（图片由原站提供）
```

### 2.1 前置：DNS 与证书

```bash
# 确认解析到本机
getent hosts photoai.life www.photoai.life

# 签发证书（首次）
certbot --nginx -d photoai.life -d www.photoai.life
```

### 2.2 启用站点配置

`deploy/nginx.conf` 是新环境模板；已有站点不要直接覆盖生效配置。新增 `/character/` 使用现有静态根目录即可。确需修改 nginx 时先备份，执行 `nginx -t` 通过后再平滑 reload。

```bash
cp deploy/nginx.conf /etc/nginx/sites-available/photoai
ln -sf /etc/nginx/sites-available/photoai /etc/nginx/sites-enabled/
nginx -t
```

**`nginx -t` 必须通过再 reload。**

### 2.3 迁移旧子域名

服务器上原有的 `pose.photoai.life` / `costume.photoai.life` 已在运行，
新配置里为它们保留 301 跳转到新路径，证书沿用。

确认跳转生效后，停用旧配置：

```bash
rm -f /etc/nginx/sites-enabled/refsite-pose /etc/nginx/sites-enabled/refsite-costume
nginx -t && systemctl reload nginx
```

> 旧配置停用前，新旧两套同时启用会因 `server_name` 冲突导致不确定行为。
> **先加新配置并验证路径站可用，再删旧配置。**

### 2.4 为什么不用 alias

`dist/` 是扁平结构（`index.html` + `portrait/` + `pose/` + …），
`root` 直接指过去即可，入口页的 `./portrait/` 相对链接天然命中，**不需要任何 alias**。

---

## 3. 验收

```bash
# 图片完整性（release.py 发布前也会自动跑一遍）
python3 tools/verify.py

# 文件与体积
du -sh /srv/ai-image-gallery/dist
find /srv/ai-image-gallery/dist -name '*.jpg' -o -name '*.webp' -o -name '*.png' | wc -l
# 期望 20751 张图片（含 4377 张生成的中图与 Shisei 的 1133 张上游中图）

# HTTP
for p in / /portrait/ /costume/ /pose/ /pose-depth/ /shisei/ /character/ /404.html; do
  printf "%-14s " "$p"; curl -s -o /dev/null -w "%{http_code}\n" "https://实际域名.com$p"
done

# 缓存头
curl -sI "https://实际域名.com/pose/thumbs/全身1人・セクシー系/立ち/P001/正面.jpg" | grep -i cache-control
# 期望 public, max-age=604800（7 天；图片 URL 不带内容哈希，所以不用一年 immutable）

curl -sI "https://实际域名.com/pose/" | grep -i cache-control
# 期望 no-cache, must-revalidate

# 域名替换是否生效
curl -s https://实际域名.com/pose/ | grep -o 'rel="canonical" href="[^"]*"'
# 不应出现 example.com
```

浏览器逐站确认：

- [ ] 入口页五个图库入口正常显示（姿势卡左半线稿、右半深度图）
- [ ] 点击进入各站，图片能加载
- [ ] 顶部栏的深浅色、中 / 日、18+、`?` 都有效；在一个图库里切换后，其他图库也跟着变
- [ ] 姿势集的「线稿 / 深度图」开关整页切换，大图里「对比」可以拖动竖线
- [ ] 本地图库卡片点开灯箱：立即显示清晰缩略图，随后换成中图（开发者工具 Network 里应是 `mid/*.webp`，不是 `img/*.png`）
- [ ] 本地图库灯箱 `←` `→` 翻页，`Esc` 关闭；连续翻页时不会闪出上一张图
- [ ] 本地图库滚到底部自动加载；角色库用「显示更多」继续浏览
- [ ] 角色库分类按钮、单张五色点、统一发色、复制标签、收藏及姿势线稿均可用；默认隐藏条目经18+确认后展示
- [ ] 角色库图片请求指向原站；暂断上游图片网络后，名称、分类与标签仍可用。metadata 校验通过不代表上游网络通过

---

## 4. 更新

服务器上的 `sites/*/index.html`、`hub/index.html`、`robots.txt`、`sitemap.xml`
都是**构建产物**，每次 `build.py --base` 都会按正式域名重写。
也就是说：**构建完，工作区必然是「脏」的。**

所以**不要用 `git pull`**——它会在这些文件上报本地改动冲突而中止。
也**不要直接 `git reset --hard`**——它会连手改过的源码一起覆盖，且不留痕迹
（2026-10-30 只打在服务器上的分页补丁就是这样丢的）。用 `tools/update.py`：

```bash
cd /srv/ai-image-gallery
python3 tools/update.py           # fetch，丢弃构建产物；发现手改文件就中止并列出
python3 tools/mid.py              # 只补新增的中图
python3 tools/build.py --base https://实际域名.com
python3 tools/release.py --out dist-stage
```

**不要直接 `release.py` 到线上 `dist/`。** 它会先删除再重建站点目录，重建期间该站会 404。
先发布到暂存目录，检查 canonical、图片数量和页面后，再逐个站点原子对调：

```bash
test ! -e dist-prev || exit 1
for x in index.html 404.html sitemap.xml robots.txt llms.txt portrait costume pose pose-depth shisei character; do
  if [ -e "dist/$x" ]; then mv -T --exchange "dist-stage/$x" "dist/$x" || break
  else mv -T "dist-stage/$x" "dist/$x"; fi
done
mv -T dist-stage dist-prev        # 对调后暂存目录里是旧版，留作回滚
```

`mv --exchange` 需要 GNU coreutils 9.5+（Debian 13 自带 9.7），而且**必须带 `-T`**，
否则目标会被当成父目录，命令报错退出。线上还没有的项（例如第一次发布的 `404.html`）直接 `mv -T` 放进去，这时 `dist-prev` 里没有它，回滚时手动删掉即可。只更新了部分站点时，循环里只写那几个。
首次添加角色库时，旧目录里没有 `character/`，它不会出现在 `dist-prev`。回滚整个版本时，核对备份确实没有该站后需另行移除新入口，避免留下不属于旧版的页面。
对调完成后不需要 reload nginx。

`update.py` 把改动分两类：`build.py` 会重写的构建产物直接丢弃；其他文件（源码、配置）
默认**中止并列出**，什么都不改。确认要丢弃时加 `--force`，脚本会先把 diff 和原文件备份到
`../ai-image-gallery-update-backups/<时间>-<旧提交>/` 再对齐。`--check` 只检查不改动。

服务器上需要的修改，**一律提交进仓库**再部署，不要只改服务器上的文件。

`update.py` 底层仍是 `git reset --hard`，只作用于仓库跟踪的文件，
**不会碰图片目录**——`sites/*/{thumbs,mid,img,png,raw}` 都在 `.gitignore` 里，`dist-*/` 也不受影响。

**图片不需要重新下载** —— `fetch.py` 幂等，已存在文件跳过。
新增本地托管站点时才需要再跑一次 `python3 tools/fetch.py --site <新站id>`。角色库为 remote 模式：fetch 明确跳过，mid 不生成图片，只发布页面与元数据。

漏跑 `mid.py` 也不会坏：灯箱会在中图 404 后退回加载原图，只是慢。

只改了一个站时：

```bash
python3 tools/build.py --site pose --base https://实际域名.com --no-hub
python3 tools/release.py --site pose --out dist-stage
# 然后按上面的方法只对调 pose
```

---

## 5. 回滚

上一次更新留下的 `dist-prev` 就是回滚源，对调回去即可，秒级、不用重建：

```bash
cd /srv/ai-image-gallery
for x in index.html 404.html sitemap.xml robots.txt llms.txt portrait costume pose pose-depth shisei character; do
  [ -e "dist-prev/$x" ] && { mv -T --exchange "dist-prev/$x" "dist/$x" || break; }
done
```

需要回到更早的版本时，按提交重建再对调：

```bash
python3 tools/update.py --ref <目标提交>
python3 tools/build.py --base https://实际域名.com
python3 tools/release.py --out dist-stage
# 检查后按 §4 对调
```

---

## 6. 加新站之后

```bash
python3 tools/update.py
python3 tools/fetch.py --site <新站id>      # 只下新站的图
python3 tools/mid.py --site <新站id>        # imageDirs 含 mid 时
python3 tools/build.py --base https://实际域名.com
python3 tools/release.py --out dist-stage
```

角色库不执行图片下载或中图生成；`verify.py --site character` 仅校验 manifest，不检查网络或图片文件。首次角色库上线仍需全量构建，以同步各旧图库的顶部导航；发布所有涉及页面后逐站对调，不能只发布角色库而漏掉共享导航。

新站在线上 `dist/` 里还不存在，直接 `mv -T dist-stage/<新站id> dist/<新站id>` 即可；入口页 `index.html` 和根级 `sitemap.xml` 也要对调，否则首页不显示新卡片。

---

## 7. 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `dist/` 里有「退化为复制」 | 跨文件系统 | 把 `dist/` 放到 `sites/` 同盘。不要用 `--no-images` 代替：它不会保留旧图，站点目录会先被删掉 |
| 入口页封面空白 | 本地站图片没下载，或角色库原站图片网络不可用 | 本地站运行 `python3 tools/fetch.py --site <id> --tier thumb`；角色库检查原站可达性，不用下载补图 |
| 子站 404 | `dist/` 未生成对应目录 | 重跑 `tools/release.py` |
| canonical 还是 example.com | 构建时没传 `--base` | 带 `--base` 重跑 `tools/build.py` |
| 磁盘暴涨 | 图片被复制而非硬链接 | `df -h` 对比 `du -sh dist`；确认同盘 |
| `fetch.py` 大量失败 | 原站不可达或被限速 | 降并发 `--workers 4`；失败条目写在 `sites/<id>/failed_<档位>.json`，重跑只补失败的 |
| `release.py` 报「图片校验未通过」 | 有图片缺失或损坏 | `python3 tools/verify.py` 看具体文件；中图缺失跑 `tools/mid.py`，其余跑 `tools/fetch.py` |
| `detected dubious ownership` | 目录属主与执行用户不一致（常见于从别处 rsync 过来的目录） | `git config --global --add safe.directory /srv/ai-image-gallery` |
| `git pull` 报本地改动冲突 | 构建产物被 `--base` 重写过 | 改用 `python3 tools/update.py`（见 §4） |
| `update.py` 中止并列出文件 | 服务器上有手改的源码或配置 | 需要保留就提交进仓库；确认可丢弃再加 `--force`（会先备份） |
| `git: command not found` | 服务器没装 git | `apt-get update && apt-get install -y git` |
| `Connecting to … port 22` 后立刻 `kex_exchange_identification: Connection closed` | ① 连的不是当前源站 IP；② 本机开着 Clash 等 TUN 模式，SSH 被代理断开 | ① 核对 `~/.ssh/config` 的 `HostName`；② 临时关闭 TUN，或让 SSH 直连物理网卡 |
| 灯箱一直显示缩略图、Network 里 `mid/*.webp` 404 | 没跑 `mid.py`，或 `sites.json` 的 `imageDirs` 没有 `mid` | 跑 `python3 tools/mid.py` 后重新 release |

---

## 8. 授权提醒

六个站点授权不同，**公开部署前务必确认**：

| 站点 | 授权 | 可否公开 |
|---|---|---|
| 人像集 | CC0 1.0 | ✅ 可自由分发 |
| 姿势集 | 禁止再分发 | ⚠️ 公开可访问在性质上接近再分发 |
| 姿势集 · 深度图 | 禁止再分发 + **禁止批量下载** | ⚠️ 同上，且 `fetch.py` 属被禁止行为 |
| 服装集 | 禁止再分发 | ⚠️ 同姿势集 |
| Shisei 姿势线稿 | 图片 CC0 1.0；姿势目录仅注明出处 | ✅ 图片可自由分发；性感、双人系列和 suggestive 姿势默认隐藏，不进落地页与 sitemap |
| 二次元角色库 | 商用作品制作与参考可；禁止再分发原图和加工图，禁止表现真实人物或未成年人 | 图片仅由原站加载，没有额外镜像/再分发授权；见 [NOTICE](../sites/character/NOTICE.md) |

成人向内容（姿势的双人与性感系列、服装的内衣与性感两类、Shisei 的性感/双人与 suggestive 内容、角色库泳装及审定的偏性感条目）在画廊里默认隐藏，不进任何落地页与 sitemap（`sites.json` 的 `adult` 规则）。
