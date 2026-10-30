# -*- coding: utf-8 -*-
"""并发下载器（断点续传）

用法:
  python scripts/download.py thumb 16    # 缩略图 400×500 webp，约 37 MB
  python scripts/download.py full 14     # 原图 1122×1402 PNG，约 4.6 GB
"""
import json, os, sys, time, threading
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

base = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(base)

TIERS = {"thumb": ("thumb_path", "thumb_url"), "full": ("full_path", "full_url")}
UA = "Mozilla/5.0 (compatible; portrait-gallery-mirror/1.0)"

tier = sys.argv[1] if len(sys.argv) > 1 else "thumb"
workers = int(sys.argv[2]) if len(sys.argv) > 2 else 16

if tier not in TIERS:
    sys.exit("用法: python scripts/download.py <thumb|full> [并发数]")

path_key, url_key = TIERS[tier]
rows = json.load(open(os.path.join(root, "manifest.json"), encoding="utf-8"))

lock = threading.Lock()
done = [0]
failed = []
total_bytes = [0]
t0 = time.time()


def fetch(row):
    rel = row[path_key]
    dst = os.path.join(root, rel)
    if os.path.exists(dst) and os.path.getsize(dst) > 1024:
        with lock:
            done[0] += 1
            total_bytes[0] += os.path.getsize(dst)
        return None
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".part"
    try:
        req = urllib.request.Request(row[url_key], headers={"User-Agent": UA, "Referer": "https://ai-portrait-gallery.pages.dev/"})
        with urllib.request.urlopen(req, timeout=60) as r:
            blob = r.read()
        if len(blob) < 1024:
            raise ValueError("响应过小: %d bytes" % len(blob))
        with open(tmp, "wb") as f:
            f.write(blob)
        os.replace(tmp, dst)
        with lock:
            done[0] += 1
            total_bytes[0] += len(blob)
            if done[0] % 50 == 0 or done[0] == len(rows):
                el = time.time() - t0
                print("  %d/%d  %.1f MB  %.1f files/s" % (done[0], len(rows), total_bytes[0] / 1048576, done[0] / el), flush=True)
        return None
    except Exception as e:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except OSError: pass
        return (rel, "%s: %s" % (type(e).__name__, e))


with ThreadPoolExecutor(max_workers=workers) as ex:
    futs = [ex.submit(fetch, r) for r in rows]
    for f in as_completed(futs):
        r = f.result()
        if r:
            failed.append(r)

el = time.time() - t0
print()
print("完成 %d/%d, %.1f MB, 用时 %.0fs" % (done[0], len(rows), total_bytes[0] / 1048576, el))
if failed:
    print("失败 %d 条:" % len(failed))
    for i, e in failed[:30]:
        print("  ", i, e)
    json.dump(failed, open(os.path.join(root, "failed_%s.json" % tier), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
else:
    print("无失败")

# 有失败条目时返回非零退出码，避免自动化流程误判成功
if failed:
    sys.exit(1)
