# -*- coding: utf-8 -*-
"""组装发布目录 dist/（可直接作为站点根）

用法:
  python tools/release.py                     # 站点文件 + 图片（图片用硬链接，不额外占盘）
  python tools/release.py --no-images         # 只放站点文件，不放图片（不会保留目标里的旧图）
  python tools/release.py --skip-verify       # 跳过发布前的图片校验（只下了部分档位时）
  python tools/release.py --out dist          # 自定义输出目录
  python tools/release.py --site pose         # 只发布一个站

产物结构:
  dist/
  ├── index.html          ← 入口页
  ├── guide/              ← 使用说明
  ├── portrait/
  ├── costume/
  ├── pose/
  ├── pose-depth/
  └── shisei/

说明:
  图片使用硬链接（同文件系统），不复制、不额外占盘。若跨文件系统则退化为复制。
  站点文件（html/json/csv/og-cover）每次覆盖。
"""
import json, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ROOT, load_cfg, select, site_dir, dir_size, human, parse_args

# 站点根目录下的文件（不递归）
SITE_FILES = ["index.html", "robots.txt", "sitemap.xml", "404.html", "og-cover.jpg",
              "manifest.json", "manifest.csv"]
# 站点根目录下的子目录
SITE_DIRS = ["data"]


def landing_dirs(sd):
    """shared/landing.py 生成的静态落地页目录（browse/、tag/、category/ …），记录在 data/landing.json"""
    p = os.path.join(sd, "data", "landing.json")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)["dirs"]

# 入口页与根级文件（sitemap / robots / 社交分享图）
HUB_FILES = ["index.html", "404.html", "sitemap.xml", "robots.txt", "og-cover.jpg", "llms.txt",
             "favicon.ico", "favicon.svg", "apple-touch-icon.png", "icon-512.png"]
# 入口页旁的根级页面目录（使用说明）
HUB_DIRS = ["guide"]


def link_or_copy(src, dst):
    """优先硬链接，失败则复制。返回 'link' / 'copy'。"""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
        return "link"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def copy_tree_links(src, dst):
    """递归把 src 的目录结构建到 dst，文件用硬链接。"""
    n_link = n_copy = 0
    for dp, _, fns in os.walk(src):
        rel = os.path.relpath(dp, src)
        target_dir = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(target_dir, exist_ok=True)
        for fn in fns:
            r = link_or_copy(os.path.join(dp, fn), os.path.join(target_dir, fn))
            if r == "link":
                n_link += 1
            else:
                n_copy += 1
    return n_link, n_copy


def main():
    args = parse_args(sys.argv[1:], {
        "site": "value", "out": "value", "no-images": "flag", "skip-verify": "flag",
    })
    cfg = load_cfg()
    sites = select(cfg, args.get("site"))
    out = os.path.abspath(args.get("out", os.path.join(ROOT, "dist")))
    with_images = not args.get("no-images")

    print(f"发布 · {len(sites)} 个站点 → {out}\n")

    # 发布前校验图片：缺图的版本不应该被发布出去
    if with_images and not args.get("skip-verify"):
        from verify import check_site
        bad = 0
        for s in sites:
            m, b = check_site(s, log=lambda _: None)
            if m or b:
                print(f"  ✗ {s['id']}: 缺失 {m}、损坏 {b}")
                bad += m + b
        if bad:
            sys.exit("\n图片校验未通过，已中止，目标目录未改动。"
                     "\n详情: python tools/verify.py；确认要发布可加 --skip-verify")
        print("  图片校验通过\n")

    # 清空目标里本次涉及的站点目录（保留其它站）
    os.makedirs(out, exist_ok=True)

    total_link = total_copy = 0

    for s in sites:
        sid = s["id"]
        sd = site_dir(sid)
        dst = os.path.join(out, sid)

        if not os.path.exists(os.path.join(sd, "index.html")):
            print(f"  ✗ {sid}: 尚未构建，请先运行 python tools/build.py")
            continue

        # 站点文件
        shutil.rmtree(dst, ignore_errors=True)
        os.makedirs(dst, exist_ok=True)

        n_files = 0
        for fn in SITE_FILES:
            src = os.path.join(sd, fn)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(dst, fn))
                n_files += 1
        for dn in SITE_DIRS + landing_dirs(sd):
            src = os.path.join(sd, dn)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(dst, dn))
                n_files += sum(len(f) for _, _, f in os.walk(src))

        # 图片
        img_note = ""
        if with_images:
            nl = nc = 0
            for dn in s.get("imageDirs", []):
                src = os.path.join(sd, dn)
                if os.path.isdir(src):
                    a, b = copy_tree_links(src, os.path.join(dst, dn))
                    nl += a
                    nc += b
            total_link += nl
            total_copy += nc
            img_note = f"  图片 {nl} 链接" + (f" / {nc} 复制" if nc else "")
        else:
            img_note = "  图片未包含"

        size = dir_size(dst)
        print(f"  [{sid}] {n_files} 个站点文件{img_note}  → {human(size)}")

    # 入口页与根级 SEO 文件
    if not args.get("site"):
        n = 0
        for fn in HUB_FILES:
            src = os.path.join(ROOT, "hub", fn)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(out, fn))
                n += 1
        for dn in HUB_DIRS:
            src = os.path.join(ROOT, "hub", dn)
            if os.path.isdir(src):
                shutil.rmtree(os.path.join(out, dn), ignore_errors=True)
                shutil.copytree(src, os.path.join(out, dn))
                n += sum(len(f) for _, _, f in os.walk(src))
        if n:
            print(f"\n  [hub] {n} 个根级文件已复制（{', '.join(HUB_FILES + [d + '/' for d in HUB_DIRS])}）")

    print(f"\n发布目录: {out}")
    print(f"总体积: {human(dir_size(out))}")
    if total_link:
        print(f"其中 {total_link} 个图片文件为硬链接，不额外占盘")
    if total_copy:
        print(f"⚠️  {total_copy} 个文件因跨文件系统退化为复制")


if __name__ == "__main__":
    main()
