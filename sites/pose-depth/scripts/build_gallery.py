# -*- coding: utf-8 -*-
"""构建深度姿势集（POSE-DB-02）

页面逻辑在 shared/pose_gallery.py —— 姿势集与深度姿势集结构完全相同，
只有品牌文案与图源不同，那些放在 sites/pose-depth/config.py。

用法：
  SITE_URL=https://your-domain.com python scripts/build_gallery.py
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
