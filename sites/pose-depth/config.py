# -*- coding: utf-8 -*-
"""姿势模块的深度图入口（/pose-depth/）：默认显示深度图，可切换到线稿

与 /pose/ 是同一个模块（shared/pose_module.py），这里保留深度图自己的标题、说明与落地页，
让「ControlNet 深度图」的搜索继续有专门的页面。
"""
import pose_module as pm

SEO = {
    "title": "ControlNet 姿势深度图：288 个姿势、1439 张深度图，可切换线稿 · 姿势集",
    "desc": "AI 绘画人体姿势深度图库：288 个姿势、1439 张灰度深度图，每个 5 个视角，可直接用于 ControlNet depth，与线稿一键切换、左右对比。",
    "ogSite": "姿势集 · 深度图",
    "ogTitle": "ControlNet 姿势深度图 · 288 个姿势 / 1439 张",
    "ogDesc": "无脸人偶姿势的灰度深度图，每个姿势五个视角，可与线稿一键切换。",
    "twTitle": "ControlNet 姿势深度图 · 288 个姿势",
    "twDesc": "1439 张灰度深度图，每个姿势五个视角，可与线稿切换。",
    "schemaName": "姿势集 · 深度图 POSE-DB-02",
    "schemaAlt": "AI Pose Depth Gallery 中文版",
    "schemaAbout": "AI 绘画 ControlNet 深度控制・3D 建模的人体姿势深度参考",
}

UI = {
    "zh": {"title": SEO["title"], "brand1": "姿势集", "brand2": "深度图与线稿"},
    "ja": {"title": "ControlNet 向けポーズ深度マップ：288 ポーズ・1439 枚、線画に切り替え可 · ポーズ集",
           "brand1": "ポーズ集", "brand2": "深度マップと線画"},
}

SEO_PAGES = {
    "id": "pose-depth", "name": "姿势集 · 深度图", "short": "深度图", "kind": "姿势深度图",
    "tagline": "AI 绘画 ControlNet 姿势深度图库",
    "licenseNote": "图片为 AI 生成，著作权归原作者，禁止再分发图片文件本身，原站另禁止批量下载。",
    "descTail": "灰度深度图可直接用于 ControlNet depth 控制。",
    "accent": "#6b7280",
    "expandSeries": ["全身1人・標準系"],
    "skipSeries": ["2人絡み"],
    "introParas": lambda n, m: [
        f"这里是姿势集的深度图入口：{n} 个姿势、{m} 张无脸灰色人偶的灰度深度图（depth map），越亮表示越靠近镜头，"
        "可直接作为 Stable Diffusion ControlNet depth 的控制图，也适合 3D 建模与布光参考。",
        "每个姿势有正面、侧面、斜角、俯视、仰视 5 个视角，页面里可以切换到同一姿势的线稿，大图里能左右对比。"],
    "faq": pm.faq("深度图", "把深度图作为 ControlNet depth 的控制图载入，提示词里描述人物和服装即可沿用姿势与前后关系；"
                  "手指和交叠双腿的边界在深度图里较弱，需要时切到线稿配合使用。"),
}

CONFIG = pm.config("depth", "POSE-DB-02", pm.DEPTH_SRC, SEO, UI, SEO_PAGES)
