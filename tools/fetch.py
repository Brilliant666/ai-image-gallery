# -*- coding: utf-8 -*-
"""下载站点图片素材（幂等，已存在的文件自动跳过）

用法:
  python tools/fetch.py                       # 全部站点，全部档位
  python tools/fetch.py --site pose           # 只下载姿势集
  python tools/fetch.py --tier thumb          # 只下载缩略图
  python tools/fetch.py --workers 8           # 降低并发

说明:
  图片不进 git，首次部署时需要下载一次。之后重跑本脚本只会补缺失文件，
  已存在且大于 1KB 的文件会被跳过——原站不产生重复流量。
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ROOT, load_cfg, select, site_dir, run, dir_size, human, parse_args

TIER_WORKERS = {"thumb": "16", "full": "14", "img": "14", "png": "14"}


def main():
    args = parse_args(sys.argv[1:], {
        "site": "value", "tier": "value", "workers": "value",
    })
    cfg = load_cfg()
    sites = select(cfg, args.get("site"))
    only_tier = args.get("tier")

    print(f"素材下载 · {len(sites)} 个站点\n")

    for s in sites:
        sid = s["id"]
        sd = site_dir(sid)
        script = os.path.join(sd, "scripts", "download.py")
        if not os.path.exists(script):
            print(f"  ✗ {sid}: 缺少 scripts/download.py，跳过")
            continue

        tiers = s.get("tiers", ["thumb"])
        if only_tier:
            if only_tier not in tiers:
                print(f"  – {sid}: 无 {only_tier} 档，跳过")
                continue
            tiers = [only_tier]

        print(f"  [{sid}] {', '.join(tiers)}")
        for t in tiers:
            run([sys.executable, script, t, args.get("workers", TIER_WORKERS.get(t, "14"))],
                cwd=sd)

        total = sum(dir_size(os.path.join(sd, d)) for d in s.get("imageDirs", [])
                    if os.path.isdir(os.path.join(sd, d)))
        print(f"    → 当前素材 {human(total)}\n")

    print("完成")


if __name__ == "__main__":
    main()
