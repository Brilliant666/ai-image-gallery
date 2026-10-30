# -*- coding: utf-8 -*-
"""从原站存档解析数据 → data/portrait.json 与 data/ranking.json

原站数据以 JS 全局变量形式提供：
  data/images.js  →  window.GALLERY_IMAGES  = [ {...}, ... ]
  data/ranking.js →  window.GALLERY_RANKING = {...}
"""
import json, os, re, sys

base = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(base)

SRC_IMG = os.path.join(root, "raw", "data", "images.js")
SRC_RANK = os.path.join(root, "raw", "data", "ranking.js")

for p in (SRC_IMG, SRC_RANK):
    if not os.path.exists(p):
        sys.exit(
            "找不到 %s。\n\n"
            "这是原站存档，因版权与体积原因不随仓库分发。\n"
            "普通使用不需要本脚本：仓库已含解析好的 data/portrait.json，\n"
            "想直接看图库，只需在仓库根目录运行 python tools/fetch.py 下载图片。" % os.path.relpath(p, root)
        )


def load_js_array(path):
    s = open(path, encoding="utf-8").read()
    i, j = s.index("["), s.rindex("]")
    return json.loads(s[i:j + 1])


def load_js_object(path):
    s = open(path, encoding="utf-8").read()
    i, j = s.index("{"), s.rindex("}")
    return json.loads(s[i:j + 1])


items = load_js_array(SRC_IMG)
ranking = load_js_object(SRC_RANK)

# 规范化：补齐缺失字段，统一 section 取值
for it in items:
    it.setdefault("style", "")
    if it.get("section") not in ("face", "styling"):
        it["section"] = "face"

items.sort(key=lambda x: (x["section"] != "face", x["hair"], x["id"]))

os.makedirs(os.path.join(root, "data"), exist_ok=True)
json.dump(items, open(os.path.join(root, "data", "portrait.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump(ranking, open(os.path.join(root, "data", "ranking.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

from collections import Counter
print("条目数:", len(items))
print("分区:", dict(Counter(i["section"] for i in items)))
print("发型:", dict(Counter(i["hair"] for i in items)))
print("唯一风格:", len({i["style"] for i in items if i["style"]}))
print("排名分类:", ranking.get("cats"))
print("写出 data/portrait.json, data/ranking.json")
