# 部署手册 · 单仓多站

> 站点根 = `tools/release.py` 生成的 `dist/`。
> 与旧方案的区别：不再用 `releases/<版本>/public` + `current` 软链，
> 改为**git commit 即版本**，回滚 = `git checkout <commit>` 后重新 release。

---

## 0. 前置条件

| 项 | 要求 |
|---|---|
| 系统 | Ubuntu 20.04+ / Debian 11+ |
| Python | 3.8+（仅标准库，无需 pip install） |
| 磁盘 | ≥ 10 GB 可用（图片 6.8 GB + 硬链接余量） |
| 内存 | ≥ 512 MB |
| 域名 | 已解析到本机 IP |

```bash
python3 --version
df -h /
free -m | head -2
```

---

## 1. 首次部署

```bash
apt update
apt install -y git python3 nginx

git clone https://github.com/Brilliant666/ai-image-gallery.git /srv/ai-image-gallery
cd /srv/ai-image-gallery

# ① 下载图片（约 6.8 GB，只需一次）
python3 tools/fetch.py

# ② 用正式域名构建
python3 tools/build.py --base https://你的域名.com

# ③ 组装发布目录
python3 tools/release.py
```

**预期输出**（release 阶段）：

```
发布 · 4 个站点 → /srv/ai-image-gallery/dist
  [portrait] 12 个站点文件  图片 2998 链接  → 4.6 GB
  [pose] 11 个站点文件  图片 2878 链接  → 662.6 MB
  [pose-depth] 11 个站点文件  图片 2878 链接  → 148.3 MB
  [costume] 11 个站点文件  图片 4221 链接  → 1.4 GB
  [hub] index.html 已复制
其中 12975 个图片文件为硬链接，不额外占盘
```

> `dist/` 报告 6.8 GB，但因为是硬链接，**实际磁盘增量接近 0**。
> 若出现「退化为复制」警告，说明 `dist/` 与 `sites/` 不在同一文件系统。

---

## 2. nginx（单域名路径式）

目标拓扑：**全部站点挂在 `photoai.life` 一个域名下**，按路径区分。

```
https://photoai.life/            入口页
https://photoai.life/portrait/   人像集
https://photoai.life/costume/    服装集
https://photoai.life/pose/       姿势集
https://photoai.life/pose-depth/ 深度姿势集
```

### 2.1 前置：DNS 与证书

```bash
# 确认解析到本机
getent hosts photoai.life www.photoai.life

# 签发证书（首次）
certbot --nginx -d photoai.life -d www.photoai.life
```

### 2.2 启用站点配置

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
# 文件与体积
du -sh /srv/ai-image-gallery/dist
find /srv/ai-image-gallery/dist -name '*.jpg' -o -name '*.webp' -o -name '*.png' | wc -l
# 期望 12975 张图片

# HTTP
for p in / /portrait/ /pose/ /pose-depth/ /costume/; do
  printf "%-14s " "$p"; curl -s -o /dev/null -w "%{http_code}\n" "https://实际域名.com$p"
done

# 缓存头
curl -sI "https://实际域名.com/pose/thumbs/全身1人・セクシー系/立ち/P001/正面.jpg" | grep -i cache-control
# 期望 public, max-age=31536000, immutable

curl -sI "https://实际域名.com/pose/" | grep -i cache-control
# 期望 no-cache, must-revalidate

# 域名替换是否生效
curl -s https://实际域名.com/pose/ | grep -o 'rel="canonical" href="[^"]*"'
# 不应出现 example.com
```

浏览器逐站确认：

- [ ] 入口页四张卡封面正常显示
- [ ] 点击进入各站，图片能加载
- [ ] 主题切换 ☀/☾ 有效，默认浅色
- [ ] 语言切换 中文/日本語 有效，默认中文
- [ ] 卡片点开灯箱，`←` `→` 翻页，`Esc` 关闭
- [ ] 滚到底部能自动加载下一页

---

## 4. 更新

```bash
cd /srv/ai-image-gallery
git pull
python3 tools/build.py --base https://实际域名.com
python3 tools/release.py
```

**图片不需要重新下载** —— `fetch.py` 幂等，已存在文件跳过。
新增站点时才需要再跑一次 `python3 tools/fetch.py --site <新站id>`。

只改了一个站时：

```bash
python3 tools/build.py --site pose --base https://实际域名.com
python3 tools/release.py --site pose
```

---

## 5. 回滚

```bash
cd /srv/ai-image-gallery
git log --oneline -5
git checkout <目标提交>
python3 tools/build.py --base https://实际域名.com
python3 tools/release.py
git checkout main          # 回滚验证完再切回
```

因为 `release.py` 会重建 `dist/`，回滚就是重建一次，几十秒。

---

## 6. 加新站之后

```bash
git pull
python3 tools/fetch.py --site <新站id>      # 只下新站的图
python3 tools/build.py --base https://实际域名.com
python3 tools/release.py
```

`release.py` 会重建全部站点目录（图片仍是硬链接，很快）。

---

## 7. 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `dist/` 里有「退化为复制」 | 跨文件系统 | 把 `dist/` 放到 `sites/` 同盘，或改用 `--no-images` 让服务器保留旧图 |
| 入口页封面空白 | 对应站的图片没下载 | `python3 tools/fetch.py --site <id> --tier thumb` |
| 子站 404 | `dist/` 未生成对应目录 | 重跑 `tools/release.py` |
| canonical 还是 example.com | 构建时没传 `--base` | 带 `--base` 重跑 `tools/build.py` |
| 磁盘暴涨 | 图片被复制而非硬链接 | `df -h` 对比 `du -sh dist`；确认同盘 |
| `fetch.py` 大量失败 | 原站不可达或被限速 | 降并发 `--workers 4` |

---

## 8. 授权提醒

四个站授权不同，**公开部署前务必确认**：

| 站点 | 授权 | 可否公开 |
|---|---|---|
| 人像集 | CC0 1.0 | ✅ 可自由分发 |
| 姿势集 | 禁止再分发 | ⚠️ 公开可访问在性质上接近再分发 |
| 深度姿势集 | 禁止再分发 + **禁止批量下载** | ⚠️ 同上，且 `fetch.py` 属被禁止行为 |
| 服装集 | 禁止再分发 | ⚠️ 同姿势集 |

建议：如需公开，至少加访问控制（`nginx.conf` 末尾有配置示例）。
