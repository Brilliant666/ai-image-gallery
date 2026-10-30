# -*- coding: utf-8 -*-
"""data/pose.json → manifest.json + manifest.csv（逻辑在 shared/pose_source.py，域名取 config.SOURCE）"""
import os, sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(SITE)), "shared"))
sys.path.insert(0, SITE)

from pose_source import manifest  # noqa: E402
import config  # noqa: E402

manifest(SITE, config.SOURCE)
