# -*- coding: utf-8 -*-
"""Recreate original, image-free social covers (optional authoring tool).

Requires Pillow only when editing the covers; ordinary builds use committed JPGs.
Pass a local CJK font, e.g. python tools/render_share_covers.py --font /path/font.ttc.
No source gallery images or network requests are used.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render(font_path):
    from PIL import Image, ImageDraw, ImageFont

    for sid, title, subtitle, detail, color in [
        ('character', '二次元角色参考', '髪型・衣装・ポーズ', '843 base entries  /  Chinese + Japanese', '#2563eb'),
        ('costume-anime', '二次元服装参考', 'アニメ衣装・タグ検索', '1,320 outfits  /  86 tags', '#7c3aed'),
    ]:
        image = Image.new('RGB', (1200, 630), '#f7f8fc')
        draw = ImageDraw.Draw(image)
        font = lambda size: ImageFont.truetype(str(font_path), size)
        draw.rounded_rectangle((60, 54, 116, 110), radius=13, fill=color)
        for x, y in [(72, 66), (94, 66), (72, 88), (94, 88)]:
            draw.rounded_rectangle((x, y, x + 10, y + 10), radius=2, fill='white')
        draw.text((138, 53), 'photoai.life', font=font(34), fill='#111827')
        draw.text((60, 188), title, font=font(78), fill='#111827')
        draw.text((65, 304), subtitle, font=font(36), fill='#475569')
        draw.text((65, 400), detail, font=font(27), fill=color)
        draw.line((65, 508, 1135, 508), fill='#d9dfea', width=2)
        draw.text((65, 535), 'AI reference gallery', font=font(23), fill='#475569')
        draw.text((790, 535), '/' + sid + '/', font=font(23), fill='#475569')
        image.save(str(ROOT / 'sites' / sid / 'og-cover.jpg'), quality=92, subsampling=0, optimize=True)
        print(sid + ': original 1200 x 630 cover written')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', type=Path, required=True)
    render(parser.parse_args().font)
