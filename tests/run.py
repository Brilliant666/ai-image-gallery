# -*- coding: utf-8 -*-
"""不依赖图片的检查：CI 和本地都能跑（图片不进仓库，CI 拿不到）

用法:
  python tests/run.py           # 全部
  python tests/run.py -k ids    # 只跑名字含 ids 的

只用标准库 + 可选的 node（检查内联 JS 语法；没有 node 时跳过这一项）。
"""
import collections, json, os, re, shutil, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "shared"))

from _common import load_cfg  # noqa: E402
from mid import mid_rel  # noqa: E402

CFG = load_cfg()
SITES = [s["id"] for s in CFG["sites"]]
PAGES = ["hub/index.html"] + [f"sites/{s}/{f}" for s in SITES for f in ("index.html", "404.html")]
BUILD_OUTPUT = ["hub/index.html", "hub/robots.txt", "hub/sitemap.xml"] + [
    f"sites/{s}/{f}" for s in SITES for f in ("index.html", "404.html", "robots.txt", "sitemap.xml")]


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
            r = subprocess.run([sys.executable, os.path.join("tools", "build.py")], cwd=dst,
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
            stale = []
            for rel in BUILD_OUTPUT:
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
        for s in SITES:
            size = os.path.getsize(os.path.join(ROOT, f"sites/{s}/index.html"))
            self.assertLess(size, 450 * 1024, f"{s}/index.html {size // 1024} KB，超出 450 KB")

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
        for s in CFG["sites"]:
            rows = json.loads(read(f"sites/{s['id']}/manifest.json"))
            for t in s["tiers"]:
                off = [r[t + "_url"] for r in rows if not r[t + "_url"].startswith(s["source"])]
                self.assertEqual(off, [], f"{s['id']} {t} 的 URL 不在原站 {s['source']} 下")

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
