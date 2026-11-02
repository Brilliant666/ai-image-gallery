# 分享与搜索元数据

各图库的主页面和公开分类／标签落地页由 Python 标准库构建；请修改生成器后运行 `python tools/build.py`，不要手改 HTML。默认构建域名为 example.com；发布构建使用 `--base https://photoai.life`。

## 分享封面

Character 与 Costume Anime 使用站点根目录中的原创 `og-cover.jpg`（1200×630），仅含本站文字、标识与图形，不使用原作者的角色或服装图片。素材图片仍全部从原站加载，`imageMode: remote`、空 `imageDirs` 与原站条款保持有效。独立库导出仅允许这一个原创封面文件，其他素材图片仍拒绝打包。

普通构建和 CI 直接使用已提交的封面，不需要 Pillow 或系统字体。若要编辑封面，可安装 Pillow，使用本地中日文字体运行可选作者工具：

```bash
python tools/render_share_covers.py --font /path/to/cjk-font.ttc
```

封面与生成器为本站原创，采用项目 MIT 许可；字体文件不打包。两站 NOTICE 中的原作者图片条款不受此影响。

## 结构化数据与卡片

网站实体使用 `WebSite` 和 `/#website`；首页集合页及子图库按 `CollectionPage`（或其子类型 `ImageGallery`）描述。图库实体标识为 `/<site>/#gallery`，供首页和落地页引用，避免把单个图库页又声明成另一个网站。

共享落地页和图库主页面提供 Open Graph 与显式 Twitter 标题、描述和图片。元数据可提高可解释性与分享一致性，不保证特定平台展示或搜索排名。

## 站点说明与缓存

首页页脚、七站静态介绍、全部公开分类／标签与 browse 页脚均提供 `llms.txt` 可见链接，三语 README 也提供入口。主站使用相对路径；独立导出库链接至 photoai.life 的站点说明，避免指向导出包中不存在的文件。

`/llms.txt` 提供来源、许可边界和公开索引。它是辅助说明，不是访问控制规则，不代替 robots.txt、sitemap 或正常 HTML 内链，也不保证任何 AI 服务读取或收录。

HTML 当前采用 `no-cache, must-revalidate`，允许缓存并在复用前验证。本批不调整缓存策略。`deploy/nginx.conf` 仅为部署参考模板，不能覆盖现有生产配置；HTTPS 的 www 归一化应由独立重定向服务处理，并保留路径与查询参数。

## 日文独立页面：后续独立改造

本批尚未新增日文 URL，也不添加指向同一地址的虚假 hreflang。当前日文仍是页内界面切换，部分日文已存在于原始 HTML 中。

完整改造需覆盖入口页、七站主图库、公开 browse 和分类／标签页：用同一份已校验目录生成独立日文正文和元数据、自引用 canonical、双向 zh-CN/ja hreflang、实际语言链接及 sitemap；按各站原有规则排除成人条目。语言路由须优先于浏览器旧偏好，图库图片仍指向原有素材目录或远程来源，不能因语言子目录而改变图片和下载路径。还需验证 file://、筛选 hash、两种姿势图切换、独立库导出和可复现构建。
