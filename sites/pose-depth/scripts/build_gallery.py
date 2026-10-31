# -*- coding: utf-8 -*-
"""构建姿势模块的深度图入口（/pose-depth/，POSE-DB-02）

页面逻辑在 shared/pose_gallery.py，两个入口共用的文案与开关在 shared/pose_module.py，
本入口的标题、说明与落地页在 config.py。

用法：
  python tools/build.py --site pose-depth --base https://your-domain.com   # 仓库根目录
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)                      # 站点根
REPO = os.path.dirname(os.path.dirname(SITE))     # 仓库根

sys.path.insert(0, os.path.join(REPO, "shared"))
sys.path.insert(0, SITE)

from pose_gallery import build                     # noqa: E402
import config                                      # noqa: E402

build(SITE, config.CONFIG)
