# -*- coding: utf-8 -*-
"""构建 Shisei（CC0 姿势线稿）

页面逻辑在 shared/pose_gallery.py（与姿势集、深度姿势集共用），本站的文案、
系列与视角顺序、模糊规则等放在 sites/shisei/config.py。

用法：
  python tools/build.py --site shisei --base https://your-domain.com   # 仓库根目录
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
