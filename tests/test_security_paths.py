"""清单路径与下载来源的安全回归；网络响应全部在进程内模拟。"""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.request
import urllib.response
from email.message import Message

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "shared"), str(ROOT / "tools")]
import assets
import mid
import verify


class SecurityPaths(unittest.TestCase):
    def test_relative_paths_and_cross_platform_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir()
            for rel in ("", ".", "..", "../outside", "img/../../outside", "/outside",
                        "\\outside", "C:/outside", "C:outside", "\\\\server\\share\\x",
                        "img\\..\\outside", "img//a", "img/./a", "img/.. /a", "img/x:stream",
                        "img/x\x00.png", "img/x\n.png"):
                with self.subTest(rel=rel), self.assertRaises(ValueError):
                    assets.safe_under(root, rel)
            expected = os.path.realpath(root / "thumbs" / "春" / "A001.webp")
            self.assertEqual(assets.safe_under(root, "thumbs/春/A001.webp"), expected)
            self.assertEqual(assets.safe_under(root, "thumbs\\春\\A001.webp"), expected)

    def link(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except OSError as exc:
            if directory and os.name == "nt":
                import _winapi
                _winapi.CreateJunction(str(target), str(path))
            else:
                self.skipTest("符号链接不可用: %s" % exc)

    def test_resolved_directory_and_file_symlinks_cannot_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            outside = Path(tmp) / "site-other"
            root.mkdir(); outside.mkdir()
            sentinel = outside / "keep.txt"
            sentinel.write_text("unchanged")
            self.link(root / "img", outside, True)
            for rel in ("img/keep.txt", "img/not-created.png"):
                with self.assertRaises(ValueError):
                    assets.safe_under(root, rel)
            self.assertEqual(sentinel.read_text(), "unchanged")

    def test_manifest_file_symlink_cannot_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir()
            outside = Path(tmp) / "outside.json"
            outside.write_text("[]")
            self.link(root / "manifest.json", outside)
            with self.assertRaises(ValueError):
                assets.load_manifest(root)
            self.assertEqual(outside.read_text(), "[]")

    def write_manifest(self, root, rows):
        (root / "manifest.json").write_text(json.dumps(rows), encoding="utf-8")

    def test_download_rejects_entire_batch_before_network_or_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir()
            valid = {"id": "good", "thumb_path": "thumbs/good.webp", "thumb_url": "https://source.example/good.webp"}
            for overrides in ({"thumb_path": "../escape.webp"},
                              {"thumb_url": "file:///etc/passwd"},
                              {"thumb_url": "http://source.example/a"},
                              {"thumb_url": "https://source.example.evil/a"},
                              {"thumb_url": "https://127.0.0.1/a"}):
                self.write_manifest(root, [valid, dict(valid, **overrides)])
                with self.subTest(overrides=overrides), patch.object(assets.urllib.request, "build_opener") as opened:
                    with self.assertRaises(ValueError):
                        assets.download(root, "thumb", "https://source.example/", allowed_hosts={"source.example"})
                    opened.assert_not_called()
                    self.assertFalse((root / "thumbs").exists())
            self.assertFalse((Path(tmp) / "escape.webp").exists())

    def test_download_rejects_part_symlink_before_touching_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            (root / "thumbs").mkdir(parents=True)
            outside = Path(tmp) / "outside"
            outside.write_bytes(b"keep")
            self.link(root / "thumbs/a.webp.part", outside)
            self.write_manifest(root, [{"thumb_path": "thumbs/a.webp", "thumb_url": "https://source.example/a"}])
            with patch.object(assets.urllib.request, "build_opener") as opened, self.assertRaises(ValueError):
                assets.download(root, "thumb", "https://source.example/", allowed_hosts={"source.example"})
            opened.assert_not_called()
            self.assertEqual(outside.read_bytes(), b"keep")

    def test_verify_rejects_paths_before_reading_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_manifest(root, [{"thumb_path": "../outside", "thumb_url": "https://source.example/a"}])
            with patch.object(assets, "image_dims") as image_read, self.assertRaises(ValueError):
                assets.verify(root, ["thumb"])
            image_read.assert_not_called()

    def test_mid_source_destination_and_temporary_path_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir()
            with self.assertRaises(ValueError):
                mid.mid_paths(root, "../outside.png")
            with self.assertRaises(ValueError):
                mid.convert((root, "img/../../outside.png"))
            src, dst, partial = mid.mid_paths(root, "img/春/a.png")
            self.assertEqual(dst, os.path.realpath(root / "mid/春/a.webp"))
            self.assertEqual(partial, dst + ".tmp")
            outside = Path(tmp) / "outside"
            outside.mkdir()
            self.link(root / "mid", outside, True)
            with self.assertRaises(ValueError):
                mid.mid_paths(root, "img/a.png")
            self.assertEqual(list(outside.iterdir()), [])

    def test_mid_verify_cannot_bypass_source_validation_with_only_mid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_manifest(root, [{"full_path": "../outside.png"}])
            with patch.object(verify, "site_dir", return_value=str(root)), self.assertRaises(ValueError):
                verify.check_site({"id": "fixture", "tiers": ["full"], "imageDirs": ["mid"]}, "mid")


class SecurityDownloadURLs(unittest.TestCase):
    def test_initial_urls_require_exact_https_host(self):
        for url in ("file:///etc/passwd", "http://source.example/a", "ftp://source.example/a",
                    "https://source.example.evil/a", "https://source.example@evil.example/a",
                    "https://user:pass@source.example/a", "https://source.example:8443/a",
                    "https://source.example\\@evil.example/a", " https://source.example/a",
                    "https://source.example\n/a", "https://127.0.0.1/a"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                assets.require_image_url(url, {"source.example"})
        self.assertEqual(assets.require_image_url("https://SOURCE.example:443/a", {"source.example"}),
                         "https://SOURCE.example:443/a")

    def test_configured_sources_cover_all_current_manifest_urls(self):
        config = json.loads((ROOT / "sites.json").read_text(encoding="utf-8"))
        for site in config["sites"]:
            hosts = assets.image_hosts(site)
            if site["id"] == "shisei":
                self.assertIn("raw.githubusercontent.com", hosts)
            rows = assets.load_manifest(ROOT / "sites" / site["id"])
            for row in rows:
                for tier in site["tiers"]:
                    assets.require_image_url(row[tier + "_url"], hosts)
                    assets.safe_under(ROOT / "sites" / site["id"], row[tier + "_path"])
        with self.assertRaises(ValueError):
            assets.image_hosts({"source": "http://source.example/"})

    def opener(self, responses, seen):
        class Transport(urllib.request.HTTPSHandler):
            def https_open(self, req):
                seen.append(req.full_url)
                status, location, body = responses[req.full_url]
                headers = Message()
                if location:
                    headers["Location"] = location
                response = urllib.response.addinfourl(io.BytesIO(body), headers, req.full_url, status)
                response.msg = "fixture"
                return response
        return urllib.request.build_opener(Transport(), assets.ImageRedirectHandler({"source.example"}))

    def test_redirect_hops_block_before_disallowed_request(self):
        for status in (301, 302, 303, 307, 308):
            for target in ("https://evil.example/private", "http://source.example/plain"):
                with self.subTest(status=status, target=target):
                    seen = []
                    opener = self.opener({"https://source.example/start": (status, "/next", b""),
                                          "https://source.example/next": (status, target, b"")}, seen)
                    if status == 308 and not hasattr(urllib.request.HTTPRedirectHandler, "http_error_308"):
                        # Python 3.8–3.10 不跟随 308；也不会向 Location 发出请求。
                        with self.assertRaises(urllib.error.HTTPError):
                            opener.open("https://source.example/start")
                        self.assertEqual(seen, ["https://source.example/start"])
                    else:
                        with self.assertRaises(ValueError):
                            opener.open("https://source.example/start")
                        self.assertEqual(seen, ["https://source.example/start", "https://source.example/next"])

    def test_allowed_redirect_download_writes_only_validated_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = {"id": "A001", "thumb_path": "thumbs/春/A001.webp", "thumb_url": "https://source.example/start"}
            (root / "manifest.json").write_text(json.dumps([row]), encoding="utf-8")
            seen = []
            blob = b"image fixture" * 100
            opener = self.opener({row["thumb_url"]: (302, "/image", b""),
                                  "https://source.example/image": (200, None, blob)}, seen)
            with patch.object(assets.urllib.request, "build_opener", return_value=opener):
                self.assertEqual(assets.download(root, "thumb", "https://source.example/", workers=1,
                                                allowed_hosts={"source.example"}, log=lambda _: None), [])
            self.assertEqual((root / row["thumb_path"]).read_bytes(), blob)
            self.assertFalse((root / (row["thumb_path"] + ".part")).exists())
            self.assertEqual(seen, [row["thumb_url"], "https://source.example/image"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
