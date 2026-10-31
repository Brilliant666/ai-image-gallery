# -*- coding: utf-8 -*-
"""姿势模块的线稿入口（/pose/）：默认显示线稿，可切换到深度图

模块本身见 shared/pose_module.py（两个入口共用文案与开关），页面由 shared/pose_gallery.py 生成。
"""
import pose_module as pm

SEO = {
    "title": "AI 绘画人体姿势参考：288 个姿势的线稿与深度图 · 姿势集",
    "desc": "AI 绘画人体姿势参考图库：288 个无脸人偶姿势，每个 5 个视角，线稿与 ControlNet 深度图一键切换、左右对比，中日双语。",
    "ogSite": "姿势集 · 线稿与深度图",
    "ogTitle": "AI 绘画人体姿势参考 · 288 个姿势的线稿与深度图",
    "ogDesc": "无脸人偶姿势参考，每个姿势五个视角，线稿与深度图一键切换。",
    "twTitle": "AI 绘画人体姿势参考 · 线稿与深度图",
    "twDesc": "288 个姿势、每个五个视角，线稿与深度图一键切换。",
    "schemaName": "姿势集 POSE-DB-01",
    "schemaAlt": "AI Pose Gallery 中文版",
    "schemaAbout": "AI 绘画・3D・插画的人体姿势参考（线稿与深度图）",
}

UI = {
    "zh": {"title": SEO["title"], "brand1": "姿势集", "brand2": "线稿与深度图"},
    "ja": {"title": "AI イラスト向けポーズ参考：288 ポーズの線画と深度マップ · ポーズ集", "brand1": "ポーズ集", "brand2": "線画と深度マップ"},
}

SEO_PAGES = {
    "id": "pose", "name": "姿势集", "short": "姿势参考", "kind": "姿势参考图",
    "tagline": "AI 绘画人体姿势参考图库（线稿与深度图）",
    "licenseNote": "图片为 AI 生成，著作权归原作者，禁止再分发图片文件本身。",
    "descTail": "可作为 Stable Diffusion / ControlNet 的姿势参考，页面里可切换深度图。",
    "accent": "#2563eb",
    # 只为标准系展开到分类页；双人系列不生成落地页。成人向姿势（sites.json 的 adult 规则）
    # 不进任何落地页，所以性感系没有页面，上半身系列页只列可爱系（见 shared/pose_seo.py）
    "expandSeries": ["全身1人・標準系"],
    "skipSeries": ["2人絡み"],
    "introParas": lambda n, m: [
        f"姿势集是一个 AI 绘画人体姿势参考图库：收录 {n} 个姿势、{m} 张无脸灰色人偶线稿，每个姿势提供正面、侧面、斜角、"
        "俯视、仰视 5 个视角；同一批姿势另有灰度深度图，页面里一键切换。",
        "系列、分类、视角和姿势名全部译为中文，可按系列、分类、视角筛选，或按姿势名和编号搜索。"],
    "faq": pm.faq("线稿", "把线稿作为 ControlNet 的 openpose 或 lineart 参考图，或直接给模型看姿势；"
                  "需要前后关系时切到深度图，作为 ControlNet depth 的控制图。"),
}

CONFIG = pm.config("line", "POSE-DB-01", pm.LINE_SRC, SEO, UI, SEO_PAGES)
