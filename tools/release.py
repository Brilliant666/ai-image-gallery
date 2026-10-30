# -*- coding: utf-8 -*-
"""组装发布目录 dist/（可直接作为站点根）

用法:
  python tools/release.py                     # 站点文件 + 图片（图片用硬链接，不额外占盘）
  python tools/release.py --no-images         # 只放站点文件，图片沿用服务器上的旧版
  python tools/release.py --out dist          # 自定义输出目录
  python tools/release.py --site pose         # 只发布一个站

产物结构:
  dist/
  ├── index.html          ← 入口页
  ├── portrait/
  ├── pose/
  ├── pose-depth/
  └── costume/

说明:
  图片使用硬链接（同文件系统），不复制、不额外占盘。若跨文件系统则退化为复制。
  站点文件（html/json/csv/og-cover）每次覆盖。
"""
import os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ROOT, load_cfg, select, site_dir, dir_size, human, parse_args

# 站点根目录下的文件（不递归）
SITE_FILES = ["index.html", "robots.txt", "sitemap.xml", "404.html", "og-cover.jpg",
              "manifest.json", "manifest.csv"]
# 站点根目录下的子目录
SITE_DIRS = ["data"]


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
        "site": "value", "out": "value", "no-images": "flag",
    })
    cfg = load_cfg()
    sites = select(cfg, args.get("site"))
    out = os.path.abspath(args.get("out", os.path.join(ROOT, "dist")))
    with_images = not args.get("no-images")

    print(f"发布 · {len(sites)} 个站点 → {out}\n")

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
        for dn in SITE_DIRS:
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

    # 入口页
    hub = os.path.join(ROOT, "hub", "index.html")
    if os.path.exists(hub) and not args.get("site"):
        shutil.copy2(hub, os.path.join(out, "index.html"))
        print("\n  [hub] index.html 已复制")

    print(f"\n发布目录: {out}")
    print(f"总体积: {human(dir_size(out))}")
    if total_link:
        print(f"其中 {total_link} 个图片文件为硬链接，不额外占盘")
    if total_copy:
        print(f"⚠️  {total_copy} 个文件因跨文件系统退化为复制")


if __name__ == "__main__":
    main()
