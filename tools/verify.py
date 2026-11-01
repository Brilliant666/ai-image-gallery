# -*- coding: utf-8 -*-
"""校验站点图片：存在、体积、可读宽高；remote 模式仅校验元数据

用法:
  python tools/verify.py                  # 全部站点、全部档位（含中图）
  python tools/verify.py --site pose      # 只校验一个站
  python tools/verify.py --tier thumb     # 只校验缩略图（只下了缩略图时用）

有缺失、损坏或元数据错误时退出码为 1。release.py 发布前会调用同一套检查。
remote 模式不会访问网络，也不检查图片文件存在、大小或可解码性。
"""
import os, sys
from urllib.parse import unquote, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ROOT, load_cfg, select, site_dir, parse_args

sys.path.insert(0, os.path.join(ROOT, "shared"))
import assets  # noqa: E402
from mid import mid_rel  # noqa: E402


def remote_metadata_errors(s, rows):
    """仅检查 remote 配置与 manifest；路径仍保留为可移植相对路径，URL 指向原站。"""
    errors = []
    for key in ("tiers", "imageDirs"):
        if s.get(key) != []:
            errors.append(f"remote 模式要求 {key}: []")
    base = s.get("imageBase", "")
    parts = urlsplit(base)
    if (parts.scheme != "https" or not parts.netloc or not base.endswith("/")
            or parts.query or parts.fragment):
        errors.append("imageBase 必须为以 / 结尾的绝对 HTTPS 地址")
    if not isinstance(rows, list) or not rows:
        return errors + ["manifest 必须是非空数组"]
    paths = {t: set() for t in ("thumb", "full", "line")}
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"第 {i + 1} 条 manifest 不是对象")
            continue
        label = row.get("id", i + 1)
        for tier in paths:
            path, url = row.get(tier + "_path"), row.get(tier + "_url")
            if tier == "line" and not path and not url:
                continue
            if not isinstance(path, str) or not path or not isinstance(url, str) or not url:
                errors.append(f"{label}: 缺 {tier}_path / {tier}_url")
                continue
            decoded = unquote(path)
            if ("\\" in decoded or ":" in decoded or "?" in decoded or "#" in decoded
                    or any(p in ("", ".", "..") for p in decoded.split("/"))):
                errors.append(f"{label}: {tier}_path 不是可移植相对路径: {path}")
            if path in paths[tier]:
                errors.append(f"{label}: {tier}_path 重复: {path}")
            paths[tier].add(path)
            if not url.startswith(base) or unquote(url) != unquote(base + path):
                errors.append(f"{label}: {tier}_url 与 imageBase + {tier}_path 不一致")
    if s.get("cover") not in paths["thumb"]:
        errors.append("cover 不在 manifest 的 thumb_path 中")
    return errors


def check_site(s, only_tier=None, log=print):
    """返回 (缺失数, 损坏或元数据错误数)。remote 不校验网络 / 图片文件。"""
    sd = site_dir(s["id"])
    if s.get("imageMode") == "remote":
        try:
            rows = assets.load_manifest(sd)
            errors = remote_metadata_errors(s, rows)
        except (OSError, ValueError) as e:
            errors = [f"manifest 无法读取: {e}"]
        log("    [remote] 仅校验配置与 manifest 元数据；未校验网络或图片文件（NOT network/files verified）")
        for error in errors[:5]:
            log("            " + error)
        log(f"            元数据错误 {len(errors)}")
        return 0, len(errors)
    tiers = s.get("tiers", ["thumb"])
    if only_tier:
        tiers = [t for t in tiers if t == only_tier]
    total, report = assets.verify(sd, tiers)
    missing = broken = 0
    for tier, t in report.items():
        log("    [%-5s] 完好 %d / %d  |  %.1f MB" % (tier, t["ok"], total, t["bytes"] / 1048576))
        if t["dims"]:
            top = sorted(t["dims"].items(), key=lambda x: -x[1])[:4]
            log("            分辨率: " + ", ".join("%s×%d" % kv for kv in top))
        for label, lst in (("缺失", t["missing"]), ("损坏", t["broken"])):
            if lst:
                log("            %s %d，前 3：%s" % (label, len(lst), lst[:3]))
        missing += len(t["missing"]); broken += len(t["broken"])

    # 中图：imageDirs 含 mid 的站点，每张原图都应有对应的 mid/*.webp
    if "mid" in s.get("imageDirs", []) and only_tier in (None, "mid"):
        rows = assets.load_manifest(sd)
        lost = [mid_rel(r["full_path"]) for r in rows
                if not os.path.exists(os.path.join(sd, mid_rel(r["full_path"])))]
        log("    [mid  ] 完好 %d / %d" % (len(rows) - len(lost), len(rows)))
        if lost:
            log("            缺失 %d，前 3：%s（运行 python tools/mid.py 补齐）" % (len(lost), lost[:3]))
        missing += len(lost)
    return missing, broken


def main():
    args = parse_args(sys.argv[1:], {"site": "value", "tier": "value"})
    sites = select(load_cfg(), args.get("site"))
    bad = 0
    for s in sites:
        print(f"  [{s['id']}]")
        m, b = check_site(s, args.get("tier"))
        bad += m + b
    print()
    if bad:
        sys.exit(f"校验失败：共 {bad} 项缺失、损坏或元数据错误")
    print("校验通过：本地站点已检查所选图片档位；remote 站点仅检查元数据，未校验网络或图片文件")


if __name__ == "__main__":
    main()
