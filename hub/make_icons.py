# -*- coding: utf-8 -*-
"""生成 photoai.life 根级图标：favicon.svg / favicon.ico / apple-touch-icon.png / icon-512.png

图案：入口页的蓝紫渐变底 + 2×2 四个圆角方块（四个图库）。产物入库，平时不需要重跑；
改图案时运行一次：python hub/make_icons.py（需要 Pillow）。
"""
import os
from PIL import Image, ImageDraw

HUB = os.path.dirname(os.path.abspath(__file__))
C1, C2 = (37, 99, 235), (124, 58, 237)          # 与入口页 --grad 一致：#2563eb → #7c3aed

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2563eb"/><stop offset="1" stop-color="#7c3aed"/></linearGradient></defs>
<rect width="64" height="64" rx="14" fill="url(#g)"/>
<rect x="14" y="14" width="16" height="16" rx="4" fill="#fff"/>
<rect x="34" y="14" width="16" height="16" rx="4" fill="#fff" fill-opacity=".72"/>
<rect x="14" y="34" width="16" height="16" rx="4" fill="#fff" fill-opacity=".72"/>
<rect x="34" y="34" width="16" height="16" rx="4" fill="#fff" fill-opacity=".45"/>
</svg>
"""


def draw(size, radius_ratio=14 / 64, full_bleed=False):
    """按 64 格的坐标画，放大 4 倍再缩小以抗锯齿。full_bleed=True 时不留圆角（iOS 自己会切圆角）。"""
    s = size * 4
    k = s / 64
    grad = Image.new("RGB", (s, s))
    px = grad.load()
    for y in range(s):
        for x in range(s):
            t = (x + y) / (2 * (s - 1))
            px[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(C1, C2))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=0 if full_bleed else round(14 * k), fill=255)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x, y, a in ((14, 14, 255), (34, 14, 184), (14, 34, 184), (34, 34, 115)):
        d.rounded_rectangle([x * k, y * k, (x + 16) * k - 1, (y + 16) * k - 1], radius=round(4 * k), fill=(255, 255, 255, a))
    img = Image.alpha_composite(img, layer)
    return img.resize((size, size), Image.LANCZOS)


def main():
    with open(os.path.join(HUB, "favicon.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(SVG)
    draw(64).save(os.path.join(HUB, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    draw(180, full_bleed=True).convert("RGB").save(os.path.join(HUB, "apple-touch-icon.png"), optimize=True)
    draw(512).save(os.path.join(HUB, "icon-512.png"), optimize=True)
    for fn in ("favicon.svg", "favicon.ico", "apple-touch-icon.png", "icon-512.png"):
        print(fn, os.path.getsize(os.path.join(HUB, fn)), "bytes")


if __name__ == "__main__":
    main()
