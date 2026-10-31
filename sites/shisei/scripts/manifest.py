# -*- coding: utf-8 -*-
"""data/catalog.json（Shisei v0.3.0）→ manifest.json + manifest.csv

只收质检通过、catalog 里有文件名的线稿视角（views 里为 null 的是生成失败或没过质检）。
图片三档取自上游 GitHub 仓库固定的 v0.3.0 标签：
  thumb ← images/line/w300   mid ← images/line/w600   full ← images/line/w900
w900 是上游仓库里最大的一档（全尺寸原图只在 Release zip 里）。

字段对齐 shared/pose_gallery.py 与 tools/fetch.py：系列 / 分類 / 编号 / 姿势名 / 视角 用日文原文，
另带 姿势名_zh、rating，以及 <tier>_url / <tier>_path。
"""
import csv, json, os

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = "v0.3.0"
RAW = f"https://raw.githubusercontent.com/wquguru/shisei/{TAG}/images/line"
VIEW_JA = {"front": "正面", "diag": "斜め", "side": "横", "above": "上から", "below": "下から"}
SERIES_JA = {"std": "全身・標準", "upper": "上半身", "sexy": "全身・セクシー", "duo": "ふたり"}

catalog = json.load(open(os.path.join(SITE, "data", "catalog.json"), encoding="utf-8"))
rows = []
for p in catalog:
    for view, fn in (p.get("views") or {}).items():
        if not fn:
            continue
        rows.append({
            "id": fn.rsplit(".", 1)[0],
            "系列": SERIES_JA[p["series"]], "分類": p["class_jp"], "编号": p["id"],
            "姿势名": p["name_jp"], "姿势名_zh": p["name_cn"], "视角": VIEW_JA[view],
            "rating": p["rating"],
            "thumb_url": f"{RAW}/w300/{fn}", "mid_url": f"{RAW}/w600/{fn}", "full_url": f"{RAW}/w900/{fn}",
            "thumb_path": f"thumbs/{fn}", "mid_path": f"mid/{fn}", "full_path": f"img/{fn}",
        })

with open(os.path.join(SITE, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
with open(os.path.join(SITE, "manifest.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

poses = {r["编号"] for r in rows}
print(f"manifest: {len(rows)} 张 / {len(poses)} 个姿势（catalog 共 {len(catalog)} 个，{len(catalog) - len(poses)} 个姿势没有任何视角通过质检）")
