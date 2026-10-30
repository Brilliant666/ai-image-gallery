# -*- coding: utf-8 -*-
"""生成 manifest.json / manifest.csv（含原站 URL 与本地路径）"""
import json, os, csv

base = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(base)

SITE = "https://ai-portrait-gallery.pages.dev/"
data = json.load(open(os.path.join(root, "data", "portrait.json"), encoding="utf-8"))

rows = []
for it in data:
    i = it["id"]
    rows.append({
        "id": i,
        "分区": it["section"],
        "发型": it["hair"],
        "风格": it.get("style", ""),
        "宽": it["w"], "高": it["h"],
        "原图字节": it.get("bytes", 0),
        # 固定用正斜杠，避免 Windows 上生成反斜杠路径
        "thumb_url": SITE + it["thumb"],
        "full_url": SITE + it["full"],
        "thumb_path": "/".join(["thumbs", i + ".webp"]),
        "full_path": "/".join(["img", i + ".png"]),
    })

json.dump(rows, open(os.path.join(root, "manifest.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

with open(os.path.join(root, "manifest.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

from collections import Counter
print("条目:", len(rows))
print("分区:", dict(Counter(r["分区"] for r in rows)))
print("发型:", dict(Counter(r["发型"] for r in rows)))
print("原图合计: %.1f GB" % (sum(r["原图字节"] for r in rows) / 1073741824))
print("写出 manifest.json / manifest.csv")
