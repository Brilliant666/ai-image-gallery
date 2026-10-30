# -*- coding: utf-8 -*-
"""本地预览：以 dist/ 为站点根启动 HTTP 服务，模拟 nginx 的部署形态

用法:
  python tools/serve.py                  # http://127.0.0.1:8080/
  python tools/serve.py --port 9000
  python tools/serve.py --root sites/pose   # 预览单个站点

为什么不用直接双击 index.html:
  file:// 与 http:// 的行为不同（相对路径解析、缓存、Content-Type 都可能不一样）。
  验收应当用 HTTP 服务跑 dist/ —— 这就是 nginx 将要服务的那个目录。

停止: Ctrl+C
"""
import functools, os, socket, sys, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ROOT, parse_args


class Handler(SimpleHTTPRequestHandler):
    """在默认处理器上加两处更贴近生产的行为。"""

    def end_headers(self):
        # nginx 会给 HTML 加 no-cache；本地同样处理，避免改完刷新看不到
        if self.path.endswith(("/", ".html")):
            self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        # 只报 4xx/5xx，避免刷屏
        code = args[1] if len(args) > 1 else ""
        if str(code).startswith(("4", "5")):
            sys.stderr.write("  %s %s\n" % (self.command, self.path))


def free_port(start=8080):
    for p in range(start, start + 40):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    sys.exit("找不到空闲端口")


def main():
    args = parse_args(sys.argv[1:], {"port": "value", "root": "value"})
    root = os.path.abspath(args.get("root", os.path.join(ROOT, "dist")))

    if not os.path.isdir(root):
        sys.exit(f"目录不存在: {root}\n请先运行 python tools/build.py && python tools/release.py")

    idx = os.path.join(root, "index.html")
    if not os.path.exists(idx):
        print(f"⚠️  {root} 下没有 index.html，可能还没构建")

    port = int(args["port"]) if args.get("port") else free_port()

    handler = functools.partial(Handler, directory=root)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)

    sites = sorted(d for d in os.listdir(root)
                   if os.path.isdir(os.path.join(root, d)))

    print()
    print("  站点根: " + root)
    if sites:
        print("  子站:   " + "  ".join(sites))
    print()
    print("  入口页  http://127.0.0.1:%d/" % port)
    for s in sites:
        print("    └─   http://127.0.0.1:%d/%s/" % (port, s))
    print()
    print("  Ctrl+C 停止")
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  已停止")


if __name__ == "__main__":
    main()
