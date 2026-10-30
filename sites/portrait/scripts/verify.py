# -*- coding: utf-8 -*-
"""校验图片完整性：存在性、体积、图片头解码、分辨率分布"""
import json, os, struct, sys

base = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(base)
rows = json.load(open(os.path.join(root, "manifest.json"), encoding="utf-8"))


def webp_dims(p):
    with open(p, "rb") as f:
        head = f.read(30)
    if len(head) < 30 or head[:4] != b"RIFF" or head[8:12] != b"WEBP":
        return None
    fmt = head[12:16]
    if fmt == b"VP8 ":
        w, h = struct.unpack("<HH", head[26:30])
        return (w & 0x3FFF, h & 0x3FFF)
    if fmt == b"VP8L":
        b = head[21:25]
        v = int.from_bytes(b, "little")
        return ((v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1)
    if fmt == b"VP8X":
        w = int.from_bytes(head[24:27], "little") + 1
        h = int.from_bytes(head[27:30], "little") + 1
        return (w, h)
    return None


def png_dims(p):
    with open(p, "rb") as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


TIERS = [("thumb", "thumb_path", webp_dims), ("full", "full_path", png_dims)]
report = {}

for tier, key, fn in TIERS:
    ok = bad = 0
    total = 0
    dims = {}
    missing, broken = [], []
    for r in rows:
        p = os.path.join(root, r[key])
        if not os.path.exists(p):
            missing.append(r[key]); continue
        sz = os.path.getsize(p)
        if sz < 1024:
            broken.append((r[key], "size %d" % sz)); continue
        d = fn(p)
        if not d:
            broken.append((r[key], "not an image")); continue
        ok += 1
        total += sz
        k = "%dx%d" % d
        dims[k] = dims.get(k, 0) + 1
    bad = len(missing) + len(broken)
    report[tier] = {"ok": ok, "bad": bad, "missing": missing, "broken": broken, "bytes": total}
    print("[%-5s] 完好 %d / %d  |  %.1f MB" % (tier, ok, len(rows), total / 1048576))
    if dims:
        top = sorted(dims.items(), key=lambda x: -x[1])[:4]
        print("        分辨率: " + ", ".join("%s×%d" % (k, v) for k, v in top))
    if missing:
        print("        缺失 %d 项，前 3：%s" % (len(missing), missing[:3]))
    if broken:
        print("        损坏 %d 项，前 3：%s" % (len(broken), broken[:3]))

print()
_missing = sum(len(report[k]["missing"]) for k in report)
_bad = sum(len(report[k]["broken"]) for k in report)
if _missing or _bad:
    print("校验失败：缺失 %d 项，损坏 %d 项" % (_missing, _bad))
    sys.exit(1)
print("校验通过：全部文件存在且可解码")
