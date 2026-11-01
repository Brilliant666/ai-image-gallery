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
  下载逻辑在 shared/assets.py，档位取自 sites.json 的 tiers，Referer 取 source。
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ROOT, load_cfg, select, site_dir, dir_size, human, parse_args

sys.path.insert(0, os.path.join(ROOT, "shared"))
import assets  # noqa: E402

TIER_WORKERS = {"thumb": 16, "full": 14, "img": 14, "png": 14}


def main():
    args = parse_args(sys.argv[1:], {
        "site": "value", "tier": "value", "workers": "value",
    })
    cfg = load_cfg()
    sites = select(cfg, args.get("site"))
    only_tier = args.get("tier")

    print(f"素材下载 · {len(sites)} 个站点\n")

    any_failed = False
    for s in sites:
        sid = s["id"]
        sd = site_dir(sid)
        if s.get("imageMode") == "remote":
            print(f"  – {sid}: remote 图片由原站加载；禁止本地下载或镜像，跳过\n")
            continue

        tiers = s.get("tiers", ["thumb"])
        if only_tier:
            if only_tier not in tiers:
                print(f"  – {sid}: 无 {only_tier} 档，跳过")
                continue
            tiers = [only_tier]

        print(f"  [{sid}] {', '.join(tiers)}")
        for t in tiers:
            workers = int(args.get("workers", TIER_WORKERS.get(t, 14)))
            failed = assets.download(sd, t, s["source"], workers,
                                     log=lambda m: print("    " + m, flush=True))
            if failed:
                any_failed = True
                print(f"    ✗ {t} 失败 {len(failed)} 条，详见 sites/{sid}/failed_{t}.json")
                for i, e in failed[:10]:
                    print("      ", i, e)

        total = sum(dir_size(os.path.join(sd, d)) for d in s.get("imageDirs", [])
                    if os.path.isdir(os.path.join(sd, d)))
        print(f"    → 当前素材 {human(total)}\n")

    if any_failed:
        sys.exit("有下载失败，重跑本命令会只补失败的文件")
    print("完成")


if __name__ == "__main__":
    main()
