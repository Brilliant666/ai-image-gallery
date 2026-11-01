# -*- coding: utf-8 -*-
"""服务器更新：拉取上游，但不悄悄覆盖手改过的文件

用法:
  python3 tools/update.py                    # 对齐 origin/main
  python3 tools/update.py --ref <提交>       # 对齐到指定提交（回滚用）
  python3 tools/update.py --check            # 只检查，不改任何东西
  python3 tools/update.py --force            # 有手改文件也继续（先备份）

流程:
  1. git fetch
  2. 把工作区改动分成两类：
     - 构建产物：build.py 每次都会按 --base 重写的文件（见 BUILD_OUTPUT），可以丢弃
     - 其他改动：手改过的源码、配置等。默认中止并列出来，不覆盖
  3. 备份：完整 diff + 改动文件原样拷一份，放到 ../<仓库名>-update-backups/<时间>-<旧提交>/
  4. git reset --hard <目标>

之后照常 mid.py → build.py --base → release.py --out。
未跟踪文件（dist-*/、图片目录）不受 reset 影响，脚本不碰。
"""
import datetime, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ROOT, parse_args

# build.py 会重写的已跟踪文件。改了构建脚本、多出新的产物时同步这里。
BUILD_OUTPUT = re.compile(
    r"^(hub/(index\.html|404\.html|robots\.txt|sitemap\.xml|llms\.txt)"
    r"|sites/[^/]+/(index\.html|404\.html|robots\.txt|sitemap\.xml"
    r"|data/(meta\.json|translations\.csv|landing\.json|[a-z-]+-zh\.json)"
    # shared/landing.py 生成的静态落地页
    r"|(browse|tag|cat|category|series|section|style)/.*index\.html))$"
)


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, text=True, encoding="utf-8",
                       capture_output=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} 失败:\n{r.stderr.strip()}")
    return r.stdout


def changed_files():
    """已跟踪且有改动的文件（含已暂存）。"""
    out = git("status", "--porcelain", "-z", "--untracked-files=no")
    files = []
    for entry in out.split("\0"):
        if not entry:
            continue
        files.append(entry[3:])
    return files


def main():
    args = parse_args(sys.argv[1:], {
        "ref": "value", "check": "flag", "force": "flag", "no-fetch": "flag",
    })
    if not args.get("no-fetch"):
        git("fetch", "--quiet", "origin")
    target = args.get("ref", "origin/main")
    target_sha = git("rev-parse", "--verify", target + "^{commit}").strip()
    head_sha = git("rev-parse", "HEAD").strip()

    files = changed_files()
    build = [f for f in files if BUILD_OUTPUT.match(f)]
    other = [f for f in files if not BUILD_OUTPUT.match(f)]

    print(f"当前 {head_sha[:7]} → 目标 {target_sha[:7]} ({target})")
    print(f"构建产物改动 {len(build)} 个（可丢弃）")
    if other:
        print(f"\n⚠️  其他改动 {len(other)} 个，reset 会覆盖它们：")
        for f in other:
            print("   ", f)

    if args.get("check"):
        sys.exit(1 if other else 0)

    if other and not args.get("force"):
        print("\n已中止，什么都没改。请先处理上面的文件：")
        print("  - 需要保留：提交进仓库（推荐），或手动备份")
        print("  - 确认可以丢弃：加 --force，脚本会先备份再覆盖")
        sys.exit(1)

    if files:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        bdir = os.path.join(os.path.dirname(ROOT), os.path.basename(ROOT) + "-update-backups",
                            f"{stamp}-{head_sha[:7]}")
        os.makedirs(bdir)
        with open(os.path.join(bdir, "worktree.diff"), "w", encoding="utf-8") as f:
            f.write(git("diff", "HEAD"))
        for rel in files:
            src = os.path.join(ROOT, rel)
            if os.path.isfile(src):
                dst = os.path.join(bdir, "files", rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        with open(os.path.join(bdir, "README.txt"), "w", encoding="utf-8") as f:
            f.write(f"update.py 备份\n旧提交 {head_sha}\n目标 {target_sha}\n"
                    f"非构建产物改动: {len(other)}\n" + "".join(f"  {x}\n" for x in other))
        print(f"\n已备份到 {bdir}")

    git("reset", "--hard", "--quiet", target_sha)
    print(f"已对齐到 {target_sha[:7]}")
    print("\n下一步:")
    print("  python3 tools/mid.py")
    print("  python3 tools/build.py --base https://你的域名")
    print("  python3 tools/release.py --out dist-stage")


if __name__ == "__main__":
    main()
