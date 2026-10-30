#!/usr/bin/env bash
# 生成部署目录 dist/
#
#   bash scripts/build_dist.sh                 # 仅站点文件（不含图片，约 400 KB）
#   bash scripts/build_dist.sh --with-images   # 连同图片一起拷（约 4.6 GB）
set -euo pipefail
cd "$(dirname "$0")/.."

WITH_IMAGES=0
[[ "${1:-}" == "--with-images" ]] && WITH_IMAGES=1

SITE_FILES=(index.html robots.txt sitemap.xml 404.html og-cover.jpg manifest.json manifest.csv)

for f in "${SITE_FILES[@]}"; do
  [[ -f "$f" ]] || { echo "缺少 $f，请先运行: python scripts/build_gallery.py" >&2; exit 1; }
done

rm -rf dist
mkdir -p dist
cp "${SITE_FILES[@]}" dist/
[[ -d data ]] && cp -r data dist/

if [[ $WITH_IMAGES -eq 1 ]]; then
  echo "拷贝图片…"
  [[ -d thumbs ]] && cp -r thumbs dist/
  [[ -d img ]]    && cp -r img    dist/
fi

echo "dist/ 完成：$(find dist -type f | wc -l) 个文件，$(du -sh dist | cut -f1)"
