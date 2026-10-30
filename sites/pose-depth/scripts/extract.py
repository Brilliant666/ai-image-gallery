# -*- coding: utf-8 -*-
"""从原站存档 raw/index.html 解析数据 → data/pose.json（逻辑在 shared/pose_source.py）"""
import os, sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(SITE)), "shared"))

from pose_source import extract  # noqa: E402

extract(SITE)
