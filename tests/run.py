# -*- coding: utf-8 -*-
"""不依赖图片的检查：CI 和本地都能跑（图片不进仓库，CI 拿不到）

用法:
  python tests/run.py           # 全部
  python tests/run.py -k ids    # 只跑名字含 ids 的

只用标准库 + 可选的 node（检查内联 JS 语法；没有 node 时跳过这一项）。
"""
import collections, html, json, os, re, shutil, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "shared"))

from _common import load_cfg  # noqa: E402
from mid import mid_rel  # noqa: E402

CFG = load_cfg()
SITES = [s["id"] for s in CFG["sites"]]
PAGES = ["hub/index.html", "hub/404.html", "hub/guide/index.html"] + [f"sites/{s}/{f}" for s in SITES for f in ("index.html", "404.html")]
BUILD_OUTPUT = ["hub/index.html", "hub/404.html", "hub/guide/index.html", "hub/robots.txt", "hub/sitemap.xml", "hub/llms.txt"] + [
    f"sites/{s}/{f}" for s in SITES for f in ("index.html", "404.html", "robots.txt", "sitemap.xml")] + [
    f"sites/{s}/data/landing.json" for s in SITES]


def landing_meta(root, sid):
    p = os.path.join(root, "sites", sid, "data", "landing.json")
    if not os.path.exists(p):
        return {"dirs": [], "pages": []}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def landing_pages(root=ROOT):
    """各站 data/landing.json 记录的静态落地页（相对仓库根的路径）"""
    return [f"sites/{s}/{pg}/index.html" for s in SITES for pg in landing_meta(root, s)["pages"]]


def generated_files(root):
    """落地页目录里实际存在的全部文件，用来发现多出或缺少的页面"""
    out = set()
    for s in SITES:
        for d in landing_meta(root, s)["dirs"]:
            for dp, _, fns in os.walk(os.path.join(root, "sites", s, d)):
                out |= {os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/") for fn in fns}
    return out


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def scripts(html):
    return re.findall(r"<script>(.*?)</script>", html, re.S)


def page_db(html):
    """取出页面里内联的 const DB = {...}"""
    k = "const DB = "
    i = html.index(k) + len(k)
    obj, _ = json.JSONDecoder().raw_decode(html, i)
    return obj


class Build(unittest.TestCase):
    """仓库里提交的构建产物，必须等于用当前源码重新构建的结果。
    防止改了模板 / 数据却忘了重新构建、提交。"""

    def test_committed_output_matches_fresh_build(self):
        tmp = tempfile.mkdtemp(prefix="gallery-build-")
        try:
            # 复制源码到临时目录构建，不碰工作区；图片目录不需要
            ignore = shutil.ignore_patterns("thumbs", "mid", "img", "png", "raw", "dist*", ".git",
                                            "__pycache__", "failed_*.json")
            dst = os.path.join(tmp, "repo")
            shutil.copytree(ROOT, dst, ignore=ignore)
            # 删掉复制过去的落地页，确认它们完全由构建重新生成
            for f in generated_files(dst):
                os.remove(os.path.join(dst, f))
            env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
            r = subprocess.run([sys.executable, os.path.join("tools", "build.py")], cwd=dst, env=env,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
            committed, fresh = generated_files(ROOT), generated_files(dst)
            self.assertEqual(sorted(committed - fresh), [], "这些落地页已不再生成，请重新构建并删掉旧文件")
            self.assertEqual(sorted(fresh - committed), [], "这些落地页还没提交，请运行 python tools/build.py")
            stale = []
            for rel in BUILD_OUTPUT + sorted(fresh):
                with open(os.path.join(ROOT, rel), encoding="utf-8") as a, \
                        open(os.path.join(dst, rel), encoding="utf-8") as b:
                    if a.read().replace("\r\n", "\n") != b.read().replace("\r\n", "\n"):
                        stale.append(rel)
            self.assertEqual(stale, [], "这些文件和重新构建的结果不同，请运行 python tools/build.py 并提交")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class Pages(unittest.TestCase):

    def test_ids_unique(self):
        # 2026-10-30：姿势集筛选区和分页按钮都叫 id="more"，分页停在 60 组
        for rel in PAGES:
            ids = re.findall(r'\sid="([^"]+)"', read(rel))
            dup = [k for k, v in collections.Counter(ids).items() if v > 1]
            self.assertEqual(dup, [], f"{rel} 有重复 id")

    def test_js_selectors_exist(self):
        for rel in PAGES:
            h = read(rel)
            js = "".join(scripts(h))
            refs = set(re.findall(r"\$\('#([\w-]+)'\)", js)) | set(re.findall(r"getElementById\('([\w-]+)'\)", js))
            ids = set(re.findall(r'\sid="([^"]+)"', h))
            self.assertEqual(sorted(refs - ids), [], f"{rel} 的 JS 引用了不存在的 id")

    def test_canonical_and_no_placeholder_leak(self):
        # 仓库里的构建产物约定用 example.com；正式域名只在服务器上 --base 构建
        for s in SITES:
            h = read(f"sites/{s}/index.html")
            self.assertIn(f'rel="canonical" href="https://example.com/{s}/"', h)
            self.assertNotIn("photoai.life/" + s + "/\"", h.split("<body")[0].replace("og:", ""),
                             "head 里不应写死正式域名")
        self.assertIn('rel="canonical" href="https://example.com/"', read("hub/index.html"))

    def test_sitemaps_list_every_site(self):
        sm = read("hub/sitemap.xml")
        for s in SITES:
            self.assertIn(f"https://example.com/{s}/", sm)

    def test_no_unused_inline_data(self):
        # 2026-10-30：pose 页面内联了 390 KB 从未被读取的 flat 数组
        for s in SITES:
            h = read(f"sites/{s}/index.html")
            js = "".join(scripts(h))
            for key in page_db(h):
                self.assertRegex(js, r"DB\." + re.escape(key) + r"\b", f"{s} 的 DB.{key} 内联了但页面没用")

    def test_page_size_budget(self):
        # 2026-10-31 起图片路径按规则在页面里拼，画廊页都在 220 KB 以内；预算留一点余量，防止回涨
        for s in SITES:
            size = os.path.getsize(os.path.join(ROOT, f"sites/{s}/index.html"))
            self.assertLess(size, 240 * 1024, f"{s}/index.html {size // 1024} KB，超出 240 KB")
        # 入口页带配方栏与生图（约 55 KB 脚本与样式），在首页也能直接生成
        self.assertLess(os.path.getsize(os.path.join(ROOT, "hub/index.html")), 130 * 1024)

    def test_json_ld_parses(self):
        # 所有页面里的 JSON-LD 都能解析；CC0 图库的结构化数据带 license
        cc0 = {s["id"] for s in CFG["sites"] if s["license"] == "cc0"}
        for rel in PAGES + landing_pages():
            h = read(rel)
            for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
                obj = json.loads(block)
                sid = rel.split("/")[1] if rel.startswith("sites/") else None
                if sid in cc0 and rel.endswith("/index.html") and "ImageGallery" in block:
                    self.assertIn("creativecommons.org/publicdomain/zero", json.dumps(obj), f"{rel} 缺 CC0 license")

    def test_title_and_description_length(self):
        # 标题约 32 个全角字以内（搜索结果里不被截断），描述 40～160 字
        for rel in [f"sites/{s}/index.html" for s in SITES] + ["hub/index.html"] + landing_pages():
            h = read(rel)
            title = html.unescape(re.search(r"<title>(.*?)</title>", h).group(1))
            desc = html.unescape(re.search(r'name="description" content="([^"]*)"', h).group(1))
            width = sum(2 if ord(c) > 0x2e7f else 1 for c in title)
            self.assertLessEqual(width, 72, f"{rel} 标题太长：{title}")
            self.assertTrue(40 <= len(desc) <= 160, f"{rel} 描述 {len(desc)} 字：{desc[:40]}…")

    def test_inline_js_syntax(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("没有 node")
        for rel in PAGES:
            for i, js in enumerate(scripts(read(rel))):
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
                    f.write(js)
                try:
                    r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, f"{rel} 第 {i + 1} 段脚本语法错误:\n{r.stderr[-800:]}")
                finally:
                    os.remove(f.name)


class Landing(unittest.TestCase):
    """shared/landing.py 生成的静态落地页"""

    def setUp(self):
        self.pages = landing_pages()

    def site_pages(self, sid):
        return [p for p in self.pages if p.startswith(f"sites/{sid}/")]

    def test_every_site_has_landing_pages(self):
        for s in SITES:
            self.assertTrue(self.site_pages(s), f"{s} 没有落地页")

    def test_head_and_body_basics(self):
        titles = collections.Counter()
        for rel in self.pages:
            h = read(rel)
            sid, path = rel.split("/")[1], "/".join(rel.split("/")[2:-1])
            t = re.search(r"<title>(.*?)</title>", h)
            self.assertTrue(t and 10 <= len(t.group(1)) <= 80, f"{rel} title 缺失或长度异常")
            titles[t.group(1)] += 1
            d = re.search(r'name="description" content="([^"]*)"', h)
            self.assertTrue(d and 40 <= len(d.group(1)) <= 220, f"{rel} description 缺失或长度异常")
            self.assertIn(f'rel="canonical" href="https://example.com/{sid}/{path}/"', h, rel)
            self.assertEqual(h.count("<h1>"), 1, f"{rel} 应有且只有一个 h1")
            for img in re.findall(r"<img[^>]*>", h):
                self.assertRegex(img, r'alt="[^"]{6,}"', f"{rel} 有缺 alt 的图片")
        self.assertEqual([t for t, n in titles.items() if n > 1], [], "落地页 title 重复")

    def test_links_resolve(self):
        # 页面里的相对链接都要指向仓库里存在的页面；sites/ 之上就是 photoai.life 根，对应仓库的 hub/
        problems = []
        sites_dir = os.path.normpath(os.path.join(ROOT, "sites"))
        for rel in self.pages:
            base = os.path.dirname(os.path.join(ROOT, rel))
            for href in re.findall(r'href="([^"#]+)', read(rel)):
                if re.match(r"[a-z]+:", href):
                    continue
                if href.startswith("/"):
                    # 站点根的绝对路径（图标等）：photoai.life 根对应仓库的 hub/
                    target = os.path.join(ROOT, "hub", html.unescape(href).lstrip("/"))
                    if not os.path.exists(target):
                        problems.append(f"{rel} → {href}")
                    continue
                target = os.path.normpath(os.path.join(base, html.unescape(href)))
                if target == sites_dir:
                    target = os.path.join(ROOT, "hub")
                elif os.path.dirname(target) == sites_dir and os.path.basename(target) not in SITES:
                    target = os.path.join(ROOT, "hub", os.path.basename(target))
                if href.endswith("/"):
                    target = os.path.join(target, "index.html")
                if not os.path.exists(target):
                    problems.append(f"{rel} → {href}")
        self.assertEqual(problems, [])

    def test_thumbs_are_in_manifest(self):
        for s in SITES:
            thumbs = {r["thumb_path"] for r in json.loads(read(f"sites/{s}/manifest.json"))}
            for rel in self.site_pages(s):
                up = "../" * (rel.count("/") - 2)
                for src in re.findall(r'<img src="([^"]+)"', read(rel)):
                    self.assertTrue(src.startswith(up), f"{rel} 图片路径层级不对: {src}")
                    self.assertIn(src[len(up):], thumbs, f"{rel} 引用了不在 manifest 的图: {src}")

    def test_only_thumbnails_exposed(self):
        # 落地页只用缩略图，不暴露中图和原图（三站禁止再分发）
        for rel in self.pages:
            self.assertFalse(re.findall(r'<img src="[^"]*/(mid|img|png)/', read(rel)), rel)

    def test_gallery_hash_params_known(self):
        # 「在画廊中查看」带的 #参数必须是画廊能识别的
        for rel in self.pages:
            for hsh in re.findall(r'class="cta" href="[^"]*#([^"]+)"', read(rel)):
                for kv in html.unescape(hsh).split("&"):
                    self.assertIn(kv.split("=")[0], {"cat", "tag", "series", "sec", "hair"}, f"{rel}: {hsh}")

    def test_adult_series_not_expanded(self):
        # 姿势两站：双人与性感系不生成落地页，上半身不展开到分类
        for s in ("pose", "pose-depth"):
            pages = self.site_pages(s)
            self.assertFalse([p for p in pages if "2人絡み" in p or "セクシー" in p], f"{s} 不应有双人或性感系落地页")
            deep = [p for p in pages if "/series/上半身1人/" in p and not p.endswith("/series/上半身1人/index.html")]
            self.assertFalse(deep, f"{s} 的上半身不应展开到分类页")

    def test_no_adult_thumbs_on_landing_pages(self):
        # 2026-10-31：sitemap 里有 4 个成人向页面，27 个服装标签页带内衣 / 性感缩略图。
        # sites.json 的 adult 规则命中的图，不得出现在任何可收录的落地页上
        sys.path.insert(0, os.path.join(ROOT, "shared"))
        import adult
        for s in SITES:
            rule = adult.rules(s)
            rows = json.loads(read(f"sites/{s}/manifest.json"))
            bad = {r["thumb_path"] for r in rows if adult.is_adult(r, rule)}
            if rule:
                self.assertTrue(bad, f"{s} 的 adult 规则一张图都没命中，字段名或取值写错了")
            for rel in self.site_pages(s):
                up = "../" * (rel.count("/") - 2)
                hit = [src for src in re.findall(r'<img src="([^"]+)"', read(rel)) if src[len(up):] in bad]
                self.assertEqual(hit, [], f"{rel} 出现了成人向缩略图")
            # 分类 / 系列名本身就是成人向的，不生成页面
            for k, vs in rule.items():
                for v in vs:
                    self.assertFalse([p for p in self.site_pages(s) if f"/{v}/" in p], f"{s} 不应有「{v}」的落地页")

    def test_hub_does_not_inline_adult_rules(self):
        self.assertNotIn('"adult":', read("hub/index.html"))

    def test_site_bar(self):
        # 全站顶部栏（shared/ui.py）：入口页与各图库都有；链到首页和顶部栏里的图库（pose-depth 并进姿势，不单列），
        # 当前站高亮且只有一个（pose-depth 高亮「姿势」）；18+、深浅色、语言、快捷键都在栏上
        sys.path.insert(0, os.path.join(ROOT, "shared"))
        import ui
        shown = [s["id"] for s in ui.nav_sites()]
        self.assertNotIn("pose-depth", shown)
        for rel, cur, up in [("hub/index.html", None, "./")] + [(f"sites/{s}/index.html", s, "../") for s in SITES]:
            h = read(rel)
            bar = re.search(r'<header class="pl-bar".*?</header>', h, re.S)
            self.assertIsNotNone(bar, f"{rel} 缺顶部栏"); bar = bar.group(0)
            self.assertIn(f'class="pl-brand" href="{up}"', bar, rel)
            for o in shown:
                self.assertIn(f'href="{up}{o}/"', bar, f"{rel} 的顶部栏缺 {o}")
            want = [] if cur is None else [ui.sites()[[x["id"] for x in ui.sites()].index(cur)].get("mergedInto", cur)]
            self.assertEqual(re.findall(r'href="[^"]*?([^"/]+)/" aria-current="page"', bar), want, rel)
            for el in ('id="plAdult"', 'id="plTheme"', 'id="plLang"', 'id="plInfo"', 'id="plMenu"', 'id="plHelpBtn"',
                       f'href="{up}guide/"', f'href="{up}guide/#notes"', f'href="{ui.REPO_URL}"', f'href="{ui.REPO_URL}/issues"'):
                self.assertIn(el, bar, f"{rel} 顶部栏缺 {el}")
            # 1–4 按顶部栏顺序对应各图库
            self.assertEqual(re.findall(r'href="[^"]*?([^"/]+)/"(?: aria-current="page")? aria-keyshortcuts="(\d)"', bar),
                             [(o, str(i)) for i, o in enumerate(shown, 1)], rel)
            for el in ('id="plHelp"', 'id="plAge"'):
                self.assertIn(el, h, rel)
            self.assertLess(h.index('class="pl-bar"'), h.index("<h1"), f"{rel} 顶部栏应在标题之前")

    def test_recipe_wired(self):
        # 配方：各画廊与入口页都有胶囊和面板；画廊大图有「加入配方」「复制提示词」；画风预设与 shared/recipe.py 一致；
        # 成人向姿势不内联英文名（不能加入配方，也就用不到）
        import recipe
        styles = json.dumps(recipe.STYLES, ensure_ascii=False)
        for rel in ["hub/index.html"] + [f"sites/{s}/index.html" for s in SITES]:
            h = read(rel)
            for el in ('id="rc"', 'id="rcBody"', 'id="rcGo"', 'id="rcRun"', 'id="rcCopy"', 'id="rcBoard"', 'id="rcSet"', 'PL.gen = {'):
                self.assertIn(el, h, f"{rel} 缺 {el}")
            self.assertIn(styles, h, f"{rel} 的画风预设与 shared/recipe.py 不一致")
            if rel.startswith("sites/"):
                for el in ('id="mrec"', 'id="mprompt"', "PL.recipe.grid(", "PL.recipe.button("):
                    self.assertIn(el, h, f"{rel} 缺 {el}")
        for s in ("pose", "pose-depth", "shisei"):
            poses = page_db(read(f"sites/{s}/index.html"))["poses"]
            self.assertFalse([p["p"] for p in poses if p.get("x") and ("e" in p or "ed" in p)], f"{s} 成人向姿势不应带英文")
            self.assertGreater(sum(1 for p in poses if p.get("e")), 90, f"{s} 英文姿势名太少")
        # 服装标签内联成下标，标签表覆盖所有下标
        db = page_db(read("sites/costume/index.html"))
        self.assertTrue(all(isinstance(n, int) and 0 <= n < len(db["tags"]) for x in db["items"] for n in x["t"]))
        # 人像每种风格都有英文名
        sys.path.insert(0, os.path.join(ROOT, "sites", "portrait", "scripts"))
        import translations as ptr
        self.assertEqual(sorted(set(ptr.STYLE_ZH) - set(ptr.STYLE_EN)), [])

    def test_gen_providers(self):
        # 实际运行请求构造与响应解析，验证中转的 JSON/multipart、多图、地址归一化和 Key 存储。
        import gen
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "gen.js")
            with open(p, "w", encoding="utf-8") as f:
                f.write(gen.JS.replace("<script>", "").replace("</script>", ""))
            r = subprocess.run([node, os.path.join(ROOT, "tests", "gen_providers.js"), p], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_gen_service_worker(self):
        # 生图中继：根目录有 gen-sw.js 并随发布复制；它不拦截任何请求（没有 fetch 处理），只接受 https 地址；
        # 页面不把 API Key 写进任务记录
        sw = read("hub/gen-sw.js")
        self.assertNotIn("addEventListener('fetch'", sw)
        self.assertNotIn('addEventListener("fetch"', sw)
        self.assertIn("/^https:\\/\\//i.test(q.url)", sw)
        self.assertIn('"gen-sw.js"', read("tools/release.py"))
        h = read("sites/pose/index.html")
        self.assertIn("register(up + 'gen-sw.js'", h)
        put = re.search(r"await put\(\{id, at: Date\.now\(\)(.*?)\}\);", h)
        self.assertIsNotNone(put)
        self.assertNotIn("key", put.group(1).lower(), "任务记录里不应有 Key")
        node = shutil.which("node")
        if node:
            r = subprocess.run([node, "--check", os.path.join(ROOT, "hub", "gen-sw.js")], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_guide_page(self):
        # 使用说明页：带顶部栏、各章节锚点（顶部栏的「注意事项」链到 #notes）、进了根 sitemap 与 llms.txt、发布时一起复制
        h = read("hub/guide/index.html")
        self.assertIn('class="pl-bar"', h)
        for a in ("libs", "browse", "viewer", "pose", "recipe", "adult", "keys", "notes", "feedback"):
            self.assertIn(f'<section id="{a}">', h)
        self.assertIn('rel="canonical" href="https://example.com/guide/"', h)
        for s in CFG["sites"]:
            self.assertIn(s["source"], h, f"使用说明缺 {s['id']} 的原站")
        self.assertIn("<loc>https://example.com/guide/</loc>", read("hub/sitemap.xml"))
        self.assertIn("https://example.com/guide/", read("hub/llms.txt"))
        self.assertIn('HUB_DIRS = ["guide"]', read("tools/release.py"))

    def test_shared_prefs(self):
        # 主题、语言全站共用 pl.theme / pl.lang；页面不再读写各站自己的旧键（只在迁移代码里出现前缀表）
        for rel in ["hub/index.html"] + [f"sites/{s}/index.html" for s in SITES]:
            h = read(rel)
            self.assertIn("localStorage.getItem('pl.theme')", h, rel)
            for old in ("hub", "pt", "cg", "pg", "ss"):
                for k in ("theme", "lang", "unblur"):
                    self.assertNotIn(f"'{old}.{k}'", h, f"{rel} 还在用旧键 {old}.{k}")

    def test_pose_module(self):
        # 姿势与深度姿势合成一个模块：两站图片 id 与路径一一对应；两页内联同一份姿势数据，
        # 各自的默认版本不同，另一版本的图片前缀指向对方目录；页面有线稿 / 深度图开关与大图对比
        ma = json.loads(read("sites/pose/manifest.json")); mb = json.loads(read("sites/pose-depth/manifest.json"))
        self.assertEqual({(r["id"], r["thumb_path"], r["full_path"]) for r in ma},
                         {(r["id"], r["thumb_path"], r["full_path"]) for r in mb}, "线稿与深度图不再一一对应")
        da, dbb = page_db(read("sites/pose/index.html")), page_db(read("sites/pose-depth/index.html"))
        self.assertEqual(da["poses"], dbb["poses"])
        self.assertEqual((da["variant"], dbb["variant"]), ("line", "depth"))
        self.assertEqual(da["vars"]["depth"]["pre"], "../pose-depth/"); self.assertEqual(da["vars"]["line"]["pre"], "")
        self.assertEqual(dbb["vars"]["line"]["pre"], "../pose/"); self.assertEqual(dbb["vars"]["depth"]["pre"], "")
        for s in ("pose", "pose-depth"):
            h = read(f"sites/{s}/index.html")
            for el in ('id="vsw"', 'id="mview"', 'id="cmp"', 'id="cmpR"'):
                self.assertIn(el, h, f"{s} 缺 {el}")
        self.assertNotIn('id="vsw"', read("sites/shisei/index.html"))

    def test_path_rules_match_manifest(self):
        # 页面里按规则拼的图片路径（/*PATHS*/ 段）必须与 manifest 逐条一致；规则不成立时生成器会改为逐张内联
        node = shutil.which("node")
        if not node:
            self.skipTest("没有 node")
        cases = {"pose": ("thumb_path", "full_path"), "pose-depth": ("thumb_path", "full_path"), "shisei": ("thumb_path", "full_path"),
                 "costume": ("thumb_path", "img_path", "png_path"), "portrait": ("thumb_path", "full_path")}
        for s, cols in cases.items():
            h = read(f"sites/{s}/index.html")
            js = [x for x in scripts(h) if "const DB = " in x][0]
            seg = re.search(r"/\*PATHS\*/(.*?)/\*END PATHS\*/", js, re.S)
            self.assertIsNotNone(seg, f"{s} 缺 PATHS 段")
            db = json.dumps(page_db(h), ensure_ascii=False)
            if s in ("costume", "portrait"):
                probe = "[DB.items.map(x => x.i), DB.items.map(x => pathOf(x))]"
                key = lambda r: r["id"]
            else:
                probe = ("[DB.poses.flatMap(p => p.v.map(v => [p.s, p.c, p.p, v.a].join('|'))),"
                         " DB.poses.flatMap(p => p.v.map(v => pathOf(p, v)))]")
                key = lambda r: "|".join([r["系列"], r["分類"], r["编号"], r["视角"]])
            code = f"const DB = {db};\nlet VAR = DB.variant || null;\nconst VARS = DB.vars || null;\n{seg.group(1)}\nconsole.log(JSON.stringify({probe}));"
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
                f.write(code)
            try:
                r = subprocess.run([node, f.name], capture_output=True, text=True, encoding="utf-8")
            finally:
                os.remove(f.name)
            self.assertEqual(r.returncode, 0, f"{s}: {r.stderr[-600:]}")
            keys, paths = json.loads(r.stdout)
            rows = json.loads(read(f"sites/{s}/manifest.json"))
            want = {key(row): [row[c] for c in cols] for row in rows}
            got = dict(zip(keys, paths))
            self.assertEqual(len(got), len(want), s)
            bad = [k for k in want if got.get(k) != want[k]]
            self.assertEqual(bad[:5], [], f"{s} 页面拼出的图片路径与 manifest 不一致")

    def test_404_pages(self):
        # 根目录与各站都有 404：不被收录、有图标、CSS 里没有字符串格式化留下的 %%
        for rel in ["hub/404.html"] + [f"sites/{s}/404.html" for s in SITES]:
            h = read(rel)
            self.assertIn('name="robots" content="noindex"', h, rel)
            self.assertIn('href="/favicon.svg"', h, rel)
            self.assertNotIn("%%", h, rel)
        self.assertIn('"404.html"', read("tools/release.py"))

    def test_shisei_suggestive(self):
        # Shisei：全身・性感、双人系列与上游标为 suggestive 的姿势带成人向标记，18+ 关闭时隐藏，不出现在任何落地页
        if "shisei" not in SITES:
            self.skipTest("没有 shisei")
        rows = json.loads(read("sites/shisei/manifest.json"))
        sugg = {r["编号"] for r in rows if r["rating"] == "suggestive" or r["系列"] in ("全身・セクシー", "ふたり")}
        db = page_db(read("sites/shisei/index.html"))
        self.assertEqual({p["p"] for p in db["poses"] if p.get("x")}, sugg)
        self.assertEqual({p["s"] for p in db["poses"] if not p.get("x")}, {"全身・標準", "上半身"})
        self.assertIn("const ADULT_MODE = 'hide';", read("sites/shisei/index.html"))
        for rel in self.site_pages("shisei"):
            shown = set(re.findall(r"<figcaption>([A-Z]\d+) ", read(rel)))
            self.assertFalse(shown & sugg, f"{rel} 出现了 suggestive 姿势: {sorted(shown & sugg)[:5]}")
            self.assertFalse(re.search(r"ふたり|セクシー", rel), f"{rel} 不应为双人或性感系列生成落地页")

    def test_adult_markers_in_galleries(self):
        # 18+：有 adult 规则的站点，内联数据里的成人向标记与规则一致；姿势 / 服装默认隐藏，Shisei 模糊
        sys.path.insert(0, os.path.join(ROOT, "shared"))
        import adult
        mode = {"pose": "hide", "pose-depth": "hide", "shisei": "hide"}
        for s in SITES:
            rule = adult.rules(s)
            if not rule:
                continue
            h = read(f"sites/{s}/index.html")
            db = page_db(h)
            rows = json.loads(read(f"sites/{s}/manifest.json"))
            if s == "costume":
                want = {r["id"] for r in rows if adult.is_adult(r, rule)}
                got = {x["i"] for x in db["items"] if x.get("x")}
                self.assertIn("PL.adult ? ITEMS : ITEMS.filter(x => !x.x)", h)
            else:
                want = {(r["系列"], r["编号"]) for r in rows if adult.is_adult(r, rule)}
                got = {(p["s"], p["p"]) for p in db["poses"] if p.get("x")}
                self.assertIn(f"const ADULT_MODE = '{mode[s]}';", h, s)
            self.assertEqual(got, want, f"{s} 的成人向标记与 sites.json 规则不一致")
            for lang in ("zh", "ja"):
                self.assertTrue(db["ui"][lang].get("adultEmptyTitle"), f"{s} 缺 {lang} 的 18+ 提示文案")

    def test_sitemaps_cover_landing_pages(self):
        # 站点地图是合法 XML、网址已百分号编码、每条都有 lastmod，并且覆盖全部落地页
        import urllib.parse
        import xml.etree.ElementTree as ET
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        def locs(rel):
            tree = ET.fromstring(read(rel).encode("utf-8"))
            urls = tree.findall("s:url", ns)
            self.assertTrue(all(u.find("s:lastmod", ns) is not None for u in urls), f"{rel} 有网址缺 lastmod")
            out = [u.find("s:loc", ns).text for u in urls]
            self.assertFalse([u for u in out if re.search(r"[^\x21-\x7e]", u)], f"{rel} 有未编码的网址")
            return {urllib.parse.unquote(u) for u in out}

        root_sm = locs("hub/sitemap.xml")
        for s in SITES:
            sm = locs(f"sites/{s}/sitemap.xml")
            for rel in self.site_pages(s):
                url = "https://example.com/" + rel[len("sites/"):-len("index.html")]
                self.assertIn(url, sm, f"{s}/sitemap.xml 缺 {url}")
                self.assertIn(url, root_sm, f"根 sitemap 缺 {url}")

    def test_llms_txt(self):
        t = read("hub/llms.txt")
        self.assertTrue(t.startswith("# photoai.life\n"))
        for s in SITES:
            self.assertIn(f"https://example.com/{s}/", t)
        self.assertIn("CC0", t)
        self.assertIn("禁止再分发", t)

    def test_static_intro_on_gallery_pages(self):
        # 主画廊页在不执行 JS 时也要有可读内容和 FAQ 结构化数据
        for rel in ["hub/index.html"] + [f"sites/{s}/index.html" for s in SITES]:
            h = read(rel)
            body = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
            text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
            self.assertGreater(len(text), 500, f"{rel} 去掉 JS 后可读文字太少")
            self.assertIn('"@type":"FAQPage"', h, f"{rel} 缺 FAQPage")
            # 介绍卡片：FAQ 收在折叠里，不直接铺满页面底部
            self.assertEqual(h.count('class="seo-intro"'), 1, rel)
            self.assertIn('<details class="seo-more">', h, rel)

    def test_icons(self):
        # 入口页与落地页引用根级图标，文件都在 hub/ 里且会被 release.py 发布
        icons = ["favicon.ico", "favicon.svg", "apple-touch-icon.png"]
        for fn in icons + ["icon-512.png"]:
            self.assertGreater(os.path.getsize(os.path.join(ROOT, "hub", fn)), 300, fn)
        rel_src = read("tools/release.py")
        for fn in icons:
            self.assertIn(f'"{fn}"', rel_src, f"release.py 没发布 {fn}")
        for rel in ["hub/index.html"] + self.pages:
            h = read(rel)
            for fn in icons:
                self.assertIn(f'href="/{fn}"', h, f"{rel} 没引用 {fn}")


class Manifests(unittest.TestCase):

    def test_tier_fields_present(self):
        # tools/fetch.py / verify.py 只靠 <tier>_url / <tier>_path 工作
        for s in CFG["sites"]:
            rows = json.loads(read(f"sites/{s['id']}/manifest.json"))
            self.assertTrue(rows, s["id"])
            for t in s["tiers"]:
                for k in (t + "_url", t + "_path"):
                    bad = [r.get("id") for r in rows if not r.get(k)]
                    self.assertEqual(bad, [], f"{s['id']} 缺 {k}")

    def test_paths_portable_and_unique(self):
        for s in CFG["sites"]:
            rows = json.loads(read(f"sites/{s['id']}/manifest.json"))
            for t in s["tiers"]:
                paths = [r[t + "_path"] for r in rows]
                self.assertFalse([p for p in paths if "\\" in p or p.startswith("/") or ".." in p],
                                 f"{s['id']} {t} 有反斜杠、绝对路径或 ..")
                self.assertEqual(len(paths), len(set(paths)), f"{s['id']} {t} 路径重复")

    def test_urls_point_to_source(self):
        # 图片地址要在原站下；图片另有出处的站点（如 Shisei 用上游 GitHub 固定标签）写 imageBase
        for s in CFG["sites"]:
            base = s.get("imageBase", s["source"])
            rows = json.loads(read(f"sites/{s['id']}/manifest.json"))
            for t in s["tiers"]:
                off = [r[t + "_url"] for r in rows if not r[t + "_url"].startswith(base)]
                self.assertEqual(off, [], f"{s['id']} {t} 的 URL 不在 {base} 下")

    def test_image_dirs_match_paths(self):
        # release.py 只硬链接 imageDirs；manifest 里的图片都应落在这些目录里
        for s in CFG["sites"]:
            rows = json.loads(read(f"sites/{s['id']}/manifest.json"))
            dirs = set(s["imageDirs"])
            for t in s["tiers"]:
                tops = {r[t + "_path"].split("/")[0] for r in rows}
                self.assertTrue(tops <= dirs, f"{s['id']} {t} 用到 {tops - dirs}，不在 imageDirs 里")

    def test_cover_in_manifest(self):
        for s in CFG["sites"]:
            rows = json.loads(read(f"sites/{s['id']}/manifest.json"))
            thumbs = {r["thumb_path"] for r in rows}
            self.assertIn(s["cover"], thumbs, f"{s['id']} 的封面 {s['cover']} 不在 manifest 里")


class MidRule(unittest.TestCase):
    """中图路径规则在 Python（tools/mid.py）和页面 JS（midOf）各写了一份，必须一致。"""

    def test_python_and_js_agree(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("没有 node")
        for s in CFG["sites"]:
            if "mid" not in s["imageDirs"]:
                continue
            h = read(f"sites/{s['id']}/index.html")
            m = re.search(r"const midOf = .*?;", h)
            self.assertIsNotNone(m, f"{s['id']} 页面里没有 midOf")
            rows = json.loads(read(f"sites/{s['id']}/manifest.json"))[:50]
            src = [r["full_path"] for r in rows]
            js = m.group(0) + "\nconsole.log(JSON.stringify(" + json.dumps(src, ensure_ascii=False) + ".map(midOf)));"
            r = subprocess.run([node, "-e", js], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout), [mid_rel(p) for p in src], s["id"])


class Docs(unittest.TestCase):

    DOCS = ["README.md", "README_en.md", "README_ja.md", "docs/ADDING_A_SITE.md", "deploy/DEPLOY.md"] + \
           [f"sites/{s}/{f}" for s in SITES for f in ("README.md", "NOTICE.md")]

    @staticmethod
    def slug(h):
        h = re.sub(r"`|\*", "", h.strip().lower())
        return re.sub(r"[^\w\- ]", "", h).replace(" ", "-")

    def test_relative_links_and_anchors(self):
        problems = []
        for rel in self.DOCS:
            text = read(rel)
            base = os.path.dirname(rel)
            body = re.sub(r"```.*?```", "", text, flags=re.S)       # 代码块里的不算链接
            heads = {self.slug(h) for h in re.findall(r"^#{1,6} (.+)$", body, re.M)}
            for target in re.findall(r"\]\(([^)\s]+)\)", body):
                if re.match(r"[a-z]+:", target):
                    continue
                path, _, anchor = target.partition("#")
                if path:
                    if not os.path.exists(os.path.normpath(os.path.join(ROOT, base, path))):
                        problems.append(f"{rel}: 链接不存在 {target}")
                elif anchor and anchor not in heads:
                    problems.append(f"{rel}: 锚点不存在 #{anchor}")
        self.assertEqual(problems, [])

    def test_no_removed_scripts_referenced(self):
        gone = ["scripts/download.py", "scripts/verify.py", "build_dist.sh"]
        hits = [f"{rel}: {g}" for rel in self.DOCS for g in gone if g in read(rel)]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
