# -*- coding: utf-8 -*-
"""四站共用的图片下载与校验

档位 → manifest 字段的对应只有一条规则：<tier>_url / <tier>_path。
  portrait / pose / pose-depth：thumb、full
  costume：thumb、img、png
各站只需在 sites.json 里写 tiers 和 source（下载时作为 Referer）。

下载幂等：已存在且大于 1 KB 的文件跳过；先写 .part 再改名，中断不会留下半个文件。
"""
import json, ntpath, os, struct, threading, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
MIN_BYTES = 1024
RETRIES = 4


def safe_under(root, rel):
    """只接受根目录内的相对路径，兼容两种分隔符并检查现有符号链接。"""
    if not isinstance(rel, str) or not rel or ntpath.splitdrive(rel)[0]:
        raise ValueError("不安全的相对路径: %r" % (rel,))
    parts = rel.replace("\\", "/").split("/")
    if any(p in ("", ".", "..") or p.endswith((" ", "."))
           or any(ord(c) < 32 or c in ':<>"|?*' for c in p) for p in parts):
        raise ValueError("不安全的相对路径: %r" % rel)
    base = os.path.realpath(root)
    path = os.path.realpath(os.path.join(base, *parts))
    if (os.path.normcase(path) == os.path.normcase(base)
            or os.path.normcase(os.path.commonpath([base, path])) != os.path.normcase(base)):
        raise ValueError("路径超出站点目录: %r" % rel)
    return path


def asset_path(root, rel, allowed_dirs):
    """图片只能位于配置的图片目录内，不能借站点内链接覆盖源码。"""
    safe_under(root, rel)
    parts = rel_path(rel).split("/")
    if len(parts) < 2 or parts[0] not in allowed_dirs:
        raise ValueError("图片路径不在允许的图片目录: %r" % rel)
    logical = os.path.join(os.path.realpath(root), parts[0])
    image_root = safe_under(root, parts[0])
    if os.path.normcase(image_root) != os.path.normcase(os.path.abspath(logical)):
        raise ValueError("图片目录不能通过链接重定向: %r" % rel)
    return safe_under(image_root, "/".join(parts[1:]))


def require_image_url(url, allowed_hosts):
    """初始地址与每次重定向都必须使用配置授权的 HTTPS 主机。"""
    if not isinstance(url, str) or any(c.isspace() or ord(c) < 32 for c in url) or "\\" in url:
        raise ValueError("不安全的图片 URL")
    parts = urllib.parse.urlsplit(url)
    if (parts.scheme != "https" or not parts.hostname or parts.hostname not in allowed_hosts
            or parts.username is not None or parts.password is not None or parts.port not in (None, 443)):
        raise ValueError("图片 URL 必须使用授权主机的 HTTPS 地址: %r" % url)
    return url


def image_hosts(site):
    """白名单只来自受信任的站点配置，不从 manifest 中推导。"""
    hosts = set()
    for url in [site["source"]] + ([site["imageBase"]] if site.get("imageBase") else []):
        host = urllib.parse.urlsplit(url).hostname
        require_image_url(url, {host})
        hosts.add(host)
    return hosts


class ImageRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts):
        self.allowed_hosts = frozenset(allowed_hosts)

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_image_url(newurl, self.allowed_hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def load_manifest(site_dir):
    with open(safe_under(site_dir, "manifest.json"), encoding="utf-8") as f:
        return json.load(f)


def tier_keys(rows, tier):
    url_key, path_key = tier + "_url", tier + "_path"
    if rows and (url_key not in rows[0] or path_key not in rows[0]):
        raise KeyError(f"manifest 里没有 {url_key} / {path_key}")
    return url_key, path_key


def rel_path(p):
    # manifest 里的路径一律当作 / 分隔，Windows 上 os.path.join 也能正确处理
    return p.replace("\\", "/")


# ── 下载 ────────────────────────────────────────────

def download(site_dir, tier, referer, workers=12, log=print, *, allowed_hosts, allowed_dirs):
    """下载一档图片；整档路径与来源验证通过后才开始读写。"""
    rows = load_manifest(site_dir)
    url_key, path_key = tier_keys(rows, tier)
    allowed_hosts = frozenset(allowed_hosts)
    allowed_dirs = frozenset(allowed_dirs)
    failed_path = safe_under(site_dir, "failed_%s.json" % tier)
    for row in rows:
        asset_path(site_dir, row[path_key], allowed_dirs)
        asset_path(site_dir, row[path_key] + ".part", allowed_dirs)
        require_image_url(row[url_key], allowed_hosts)
    opener = urllib.request.build_opener(ImageRedirectHandler(allowed_hosts))
    total = len(rows)
    lock = threading.Lock()
    state = {"done": 0, "bytes": 0}
    failed = []
    t0 = time.time()

    def tick(n_bytes):
        with lock:
            state["done"] += 1
            state["bytes"] += n_bytes
            n = state["done"]
        if n % 200 == 0 or n == total:
            el = max(time.time() - t0, 0.001)
            log("  %d/%d  %.1f MB  %.1f files/s" % (n, total, state["bytes"] / 1048576, n / el))

    def fetch(r):
        dst = asset_path(site_dir, r[path_key], allowed_dirs)
        if os.path.exists(dst) and os.path.getsize(dst) > MIN_BYTES:
            tick(os.path.getsize(dst))
            return
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = asset_path(site_dir, r[path_key] + ".part", allowed_dirs)
        last = None
        for attempt in range(RETRIES):
            try:
                req = urllib.request.Request(r[url_key], headers={"User-Agent": UA, "Referer": referer})
                with opener.open(req, timeout=60) as resp:
                    blob = resp.read()
                if len(blob) < MIN_BYTES // 2:
                    raise IOError("响应过小: %d bytes" % len(blob))
                with open(tmp, "wb") as f:
                    f.write(blob)
                os.replace(tmp, dst)
                tick(len(blob))
                return
            except Exception as e:  # 网络错误、HTTP 错误、写盘错误都重试
                last = e
                time.sleep(1.2 * (attempt + 1))
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except OSError: pass
        with lock:
            failed.append((r.get("id"), "%s: %s" % (type(last).__name__, last)))

    log("tier=%s workers=%d total=%d" % (tier, workers, total))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(fetch, rows))
    log("完成 %d/%d, %.1f MB, 用时 %.0fs" % (state["done"], total, state["bytes"] / 1048576, time.time() - t0))
    if failed:
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed, f, ensure_ascii=False, indent=1)
    return failed


# ── 校验 ────────────────────────────────────────────

def image_dims(path):
    """从文件头读宽高，支持 JPEG / PNG / WebP；读不出返回 None。"""
    with open(path, "rb") as f:
        head = f.read(32)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            fmt = head[12:16]
            if fmt == b"VP8 ":
                w, h = struct.unpack("<HH", head[26:30])
                return (w & 0x3FFF, h & 0x3FFF)
            if fmt == b"VP8L":
                v = int.from_bytes(head[21:25], "little")
                return ((v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1)
            if fmt == b"VP8X":
                return (int.from_bytes(head[24:27], "little") + 1, int.from_bytes(head[27:30], "little") + 1)
            return None
        if head[:2] == b"\xff\xd8":
            f.seek(2)
            while True:
                b = f.read(1)
                if not b:
                    return None
                if b != b"\xff":
                    continue
                m = f.read(1)
                while m == b"\xff":
                    m = f.read(1)
                if not m:
                    return None
                m = m[0]
                if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
                    continue
                seg = f.read(2)
                if len(seg) < 2:
                    return None
                n = struct.unpack(">H", seg)[0]
                if m in (0xC0, 0xC1, 0xC2):
                    d = f.read(5)
                    h, w = struct.unpack(">HH", d[1:5])
                    return (w, h)
                f.seek(n - 2, 1)
    return None


def verify(site_dir, tiers, *, allowed_dirs):
    """逐档检查存在、体积、可读宽高。返回 {tier: {ok, bytes, dims, missing, broken}}。"""
    rows = load_manifest(site_dir)
    report = {}
    for tier in tiers:
        _, path_key = tier_keys(rows, tier)
        t = {"ok": 0, "bytes": 0, "dims": {}, "missing": [], "broken": []}
        for r in rows:
            rel = rel_path(r[path_key])
            p = asset_path(site_dir, rel, allowed_dirs)
            if not os.path.exists(p):
                t["missing"].append(rel); continue
            sz = os.path.getsize(p)
            if sz < MIN_BYTES:
                t["broken"].append((rel, "size %d" % sz)); continue
            d = image_dims(p)
            if not d:
                t["broken"].append((rel, "not an image")); continue
            t["ok"] += 1
            t["bytes"] += sz
            k = "%dx%d" % tuple(d)
            t["dims"][k] = t["dims"].get(k, 0) + 1
        report[tier] = t
    return len(rows), report
