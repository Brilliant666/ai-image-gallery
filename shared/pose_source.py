# -*- coding: utf-8 -*-
"""姿势 / 深度姿势共用：从原站存档解析数据、生成 manifest

两站原站结构完全相同，只有域名不同（各站 config.py 的 SOURCE）。
由 sites/<id>/scripts/extract.py、manifest.py 调用：

    extract(<站点根>)              raw/index.html → data/pose.json
    manifest(<站点根>, SOURCE)     data/pose.json → manifest.json + manifest.csv

raw/ 是原站整站存档，因版权原因不入库；只在需要重新解析原站数据时才用到。
"""
import csv, json, os, re, sys
from collections import Counter

RAW_MISSING = """找不到 raw/index.html。

这是原站的整站存档，包含原作者的全部数据与样式，
因版权原因不随仓库分发，因此新克隆的仓库里没有这个文件。

本脚本仅在需要重新从原站解析数据时使用，普通使用不需要它：
  - 仓库已包含解析好的 data/pose.json
  - 想直接看画廊，只需运行 python tools/fetch.py 下载图片

若确实要重新解析，请自行访问原站并保存其 HTML 到 raw/index.html。"""


def grab_array(src, name):
    key = "const %s=[" % name
    i = src.find(key)
    if i < 0:
        key = "const %s = [" % name
        i = src.find(key)
    if i < 0:
        return None
    j = src.index("[", i)
    depth = 0
    in_str = False
    esc = False
    quote = ""
    for k in range(j, len(src)):
        ch = src[k]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            continue
        if ch in "\"'":
            in_str = True
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return src[j:k+1]
    return None

def to_json(s):
    # JS object literal -> JSON: quote bare keys
    s = re.sub(r'([{,]\s*)([A-Za-z_\u3040-\u30ff\u4e00-\u9fff][A-Za-z0-9_\u3040-\u30ff\u4e00-\u9fff]*)\s*:', r'\1"\2":', s)
    s = s.replace("'", '"')
    s = re.sub(r',(\s*[\]}])', r'\1', s)
    return json.loads(s)


def extract(root):
    src_path = os.path.join(root, "raw", "index.html")
    if not os.path.exists(src_path):
        sys.exit(RAW_MISSING)
    html = open(src_path, encoding="utf-8").read()
    out = {}
    for name in ["D", "ANG", "POSES", "t", "c", "n", "tabs"]:
        arr = grab_array(html, name)
        if arr is None:
            print("MISS", name)
            continue
        try:
            data = to_json(arr)
            out[name] = data
            print("OK", name, "len=", len(data))
        except Exception as e:
            print("FAIL", name, e, arr[:200])

    os.makedirs(os.path.join(root, "data"), exist_ok=True)
    json.dump(out, open(os.path.join(root, "data", "pose.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n写出 data/pose.json")
    print("--- sample D[0] ---")
    print(json.dumps(out["D"][0], ensure_ascii=False, indent=1))


def manifest(root, source):
    """source 末尾带 /，例如 https://ai-pose-gallery.pages.dev/"""
    data = json.load(open(os.path.join(root, "data", "pose.json"), encoding="utf-8"))
    D = data["D"]

    def safe(s):
        s = re.sub(r'[\\/:*?"<>|]', "_", s)
        return s.strip().rstrip(".")

    rows = []
    for d in D:
        series = safe(d["系統"])
        cat = safe(d["分類"])
        pid = safe(d["ポーズ番号"])
        ang = safe(d["アングル"])
        # 固定用正斜杠，避免在 Windows 上生成反斜杠路径（Linux 上无法使用）
        rel_thumb = "/".join(["thumbs", series, cat, pid, ang + ".jpg"])
        rel_full = "/".join(["img", series, cat, pid, ang + ".png"])
        rows.append({
            "id": d["id"], "系列": d["系統"], "分類": d["分類"], "编号": d["ポーズ番号"],
            "姿势名": d["ポーズ名"], "视角": d["アングル"],
            "thumb_url": source + d["サムネ"],
            "full_url": source + d["原寸"],
            "thumb_path": rel_thumb, "full_path": rel_full,
        })

    # manifest json
    json.dump(rows, open(os.path.join(root, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # csv (utf-8-sig for Excel)
    with open(os.path.join(root, "manifest.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "系列", "分類", "编号", "姿势名", "视角", "thumb_url", "full_url", "thumb_path", "full_path"])
        w.writeheader()
        w.writerows(rows)

    # stats
    from collections import Counter, defaultdict
    print("总条目:", len(rows))
    print("\n系列分布:")
    for k, v in Counter(r["系列"] for r in rows).most_common():
        print(f"  {k}: {v}")
    print("\n分类分布:")
    for k, v in Counter(r["分類"] for r in rows).most_common():
        print(f"  {k}: {v}")
    print("\n系列 × 分类:")
    for s in Counter(r["系列"] for r in rows):
        cats = Counter(r["分類"] for r in rows if r["系列"] == s)
        print(f"  [{s}] " + " / ".join(f"{c}:{n}" for c, n in cats.most_common()))

    poses = {(r["系列"], r["分类"] if "分类" in r else r["分類"], r["编号"]) for r in rows}
    print("\n唯一姿势数(系列+分类+编号):", len(poses))
    uniq_pose_id = {(r["系列"], r["编号"]) for r in rows}
    print("唯一姿势数(系列+编号):", len(uniq_pose_id))
