"""Regression coverage for landing/release filesystem boundaries; no site assets needed."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "shared"))
import landing
import pose_seo
import release


def write(path, text="sentinel"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def link(test, target, path, directory=True):
    try:
        os.symlink(target, path, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        if directory and os.name == "nt":
            import _winapi
            try:
                _winapi.CreateJunction(str(target), str(path))
                return
            except OSError:
                pass
        test.skipTest(f"symlink unavailable: {exc}")


def site(root):
    return landing.Site(id="fixture", root=str(root), site_url="https://example.com/fixture",
                        name="测试图库", tagline="参考", license_note="CC0", author="作者",
                        author_url="https://example.org/", source="https://example.org/", faq=[])


def facet(slug="tag/参考", count=landing.MIN_ITEMS):
    return landing.Facet(slug=slug, title="参考图分类", h1="参考图分类", description="测试介绍",
                         intro=[], items=[landing.Item("thumbs/test.webp", "测试参考图片")] * count,
                         gallery_hash="tag=test")


class LandingSecurity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="landing-security-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "site"
        self.old = write(self.root / "browse" / "index.html", "old browse")
        self.outside = write(Path(self.tmp.name) / "outside" / "sentinel.txt")
        (self.root / "data").mkdir()
        self.site = site(self.root)

    def rejected(self, facets):
        with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):
            landing.write_site(self.site, facets)
        self.assertEqual(self.old.read_text(encoding="utf-8"), "old browse")
        self.assertEqual(self.outside.read_text(encoding="utf-8"), "sentinel")

    def test_rejects_traversal_absolute_and_windows_names_before_cleanup(self):
        bad = ["../outside", "/outside", "tag/../../outside", "tag/../outside", "tag//x",
               "tag/./x", "tag/", "tag\\x", "C:/outside", "C:\\outside", "//host/share",
               "tag/C:/outside", "tag/x:stream", "tag/.. ", "", "tag/evil\x00", "tag/x."]
        for slug in bad:
            with self.subTest(slug=slug):
                self.rejected([facet(), facet(slug)])

    def test_validates_facets_below_min_items(self):
        for slug in ("../outside", "tag/../outside"):
            with self.subTest(slug=slug):
                self.rejected([facet(), facet(slug, 0)])

    def test_protected_top_directories_and_files_are_rejected(self):
        for top in ("data", "thumbs", "mid", "img", "png", "scripts", ".git", "index.html", "MANIFEST.JSON"):
            with self.subTest(top=top):
                self.rejected([facet(top + "/replace")])
        self.rejected([facet("browse")])

    def test_directory_link_escape_is_rejected_before_cleanup(self):
        link(self, self.outside.parent, self.root / "tag")
        self.rejected([facet("tag/new")])

    def test_internal_top_directory_link_does_not_delete_target(self):
        target = self.root / "existing"
        sentinel = write(target / "keep.txt")
        link(self, target, self.root / "tag")
        self.rejected([facet("tag/new")])
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel")

    def test_nested_directory_link_escape_is_rejected(self):
        (self.root / "tag").mkdir()
        link(self, self.outside.parent, self.root / "tag" / "nested")
        self.rejected([facet("tag/nested/page")])

    def test_thin_facet_directory_link_is_also_rejected(self):
        link(self, self.outside.parent, self.root / "tag")
        self.rejected([facet("tag/new", 0)])

    def test_index_file_link_escape_is_rejected_before_cleanup(self):
        (self.root / "tag" / "new").mkdir(parents=True)
        link(self, self.outside, self.root / "tag" / "new" / "index.html", directory=False)
        self.rejected([facet("tag/new")])

    def test_metadata_directory_link_escape_is_rejected(self):
        (self.root / "data").rmdir()
        link(self, self.outside.parent, self.root / "data")
        self.rejected([facet()])
        self.assertFalse((self.outside.parent / "landing.json").exists())

    def test_metadata_file_link_escape_is_rejected_before_cleanup(self):
        link(self, self.outside, self.root / "data" / "landing.json", directory=False)
        self.rejected([facet()])

    def test_valid_unicode_and_nested_slugs_keep_expected_output(self):
        with contextlib.redirect_stdout(io.StringIO()):
            urls = landing.write_site(self.site, [facet(), facet("series/全身/正面"), facet("tag/thin", 1)])
        meta = json.loads((self.root / "data" / "landing.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["dirs"], ["browse", "series", "tag"])
        self.assertEqual(len(urls), 3)
        self.assertIn("参考图分类", (self.root / "series" / "全身" / "正面" / "index.html").read_text(encoding="utf-8"))
        self.assertFalse((self.root / "tag" / "thin").exists())


class LandingCallersSecurity(unittest.TestCase):
    @staticmethod
    def seo(sid):
        scripts = ROOT / "sites" / sid / "scripts"
        spec = importlib.util.spec_from_file_location("security_" + sid + "_seo", scripts / "seo.py")
        module = importlib.util.module_from_spec(spec)
        with patch.object(sys, "path", [str(scripts)] + sys.path), patch.dict(sys.modules):
            sys.modules.pop("translations", None)
            spec.loader.exec_module(module)
        return module

    def test_segment_validator_rejects_paths(self):
        for value in ("", ".", "..", "a/b", "a\\b", "/tmp", "C:foo", None, "a\x00b", "a.", "a "):
            with self.subTest(value=value), self.assertRaises(ValueError):
                landing.validate_segment(value)
        self.assertEqual(landing.validate_segment("全身・ポーズ"), "全身・ポーズ")

    def test_pose_rejects_names_before_rendering_even_if_unlisted(self):
        cases = [([], ["bad/name"], []), (["../bad"], [], []),
                 ([], [], [{"s": "safe", "c": "nested/name"}]),
                 ([], [], [{"s": "bad\\name", "c": "safe"}])]
        for series, cats, data in cases:
            with self.subTest(series=series, cats=cats, data=data), \
                    patch.object(landing, "write_site") as render, self.assertRaises(ValueError):
                pose_seo.build("unused", "https://example.com", {}, data, series, cats)
            render.assert_not_called()

    def test_costume_rejects_categories_and_tags_before_rendering(self):
        module = self.seo("costume")
        cases = [([], ["nested/name"]), ([{"c": "safe", "t": ["bad/name"]}], []),
                 ([{"c": "../bad", "t": []}], [])]
        for items, cats in cases:
            with self.subTest(items=items, cats=cats), patch.object(landing, "write_site") as render, \
                    self.assertRaises(ValueError):
                module.build("unused", "https://example.com", items, cats)
            render.assert_not_called()

    def test_portrait_rejects_sections_hair_and_styles_before_rendering(self):
        module = self.seo("portrait")
        for key in ("s", "hj", "sj"):
            item = {"s": "face", "hj": "short", "sj": "style"}
            item[key] = "nested/name"
            with self.subTest(key=key), patch.object(landing, "write_site") as render, self.assertRaises(ValueError):
                module.build("unused", "https://example.com", [item])
            render.assert_not_called()


class ReleaseSecurity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="release-security-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.sd = self.base / "source"
        self.out = self.base / "out"
        self.old = write(self.out / "fixture" / "keep.txt", "old release")
        self.outside = write(self.base / "outside" / "sentinel.txt")
        write(self.sd / "index.html", "new release")
        write(self.sd / "data" / "landing.json", json.dumps({"dirs": ["browse"]}))
        write(self.sd / "browse" / "index.html", "browse")
        self.config = {"id": "fixture", "imageMode": "remote", "imageDirs": [], "tiers": []}

    def run_release(self, sites=None, out=None, only=True):
        sites = sites or [self.config]
        argv = ["release.py", "--out", str(out or self.out), "--skip-verify"]
        if only:
            argv += ["--site", "fixture"]
        with patch.object(release, "load_cfg", return_value={"sites": sites}), \
                patch.object(release, "site_dir", side_effect=lambda sid: str(self.sd if sid == "fixture" else self.base / sid)), \
                patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            release.main()

    def rejected(self, **kwargs):
        with self.assertRaises(ValueError):
            self.run_release(**kwargs)
        self.assertEqual(self.old.read_text(encoding="utf-8"), "old release")
        self.assertEqual(self.outside.read_text(encoding="utf-8"), "sentinel")

    def test_metadata_dirs_reject_traversal_absolute_collisions_and_nonlists(self):
        for dirs in (["../outside"], ["/outside"], ["C:/outside"], ["C:\\outside"], ["nested/tag"],
                     ["tag\\nested"], [".."], [""], ["data"], ["index.html"], ["thumbs"],
                     ["scripts"], [".git"], ["browse", "BROWSE"], [None], "browse", None, {}):
            with self.subTest(dirs=dirs):
                write(self.sd / "data" / "landing.json", json.dumps({"dirs": dirs}))
                self.rejected()

    def test_landing_dirs_cannot_collide_with_custom_image_directory(self):
        self.config["imageDirs"] = ["original-images"]
        write(self.sd / "data" / "landing.json", json.dumps({"dirs": ["original-images"]}))
        self.rejected()

    def test_all_sites_are_validated_before_first_destination_is_cleared(self):
        write(self.base / "second" / "index.html")
        write(self.base / "second" / "data" / "landing.json", '{"dirs":["../outside"]}')
        second = dict(self.config, id="second")
        self.rejected(sites=[self.config, second], only=False)

    def test_source_nested_directory_escape_is_rejected_before_clearing(self):
        link(self, self.outside.parent, self.sd / "browse" / "nested")
        self.rejected()
        self.assertFalse((self.out / "fixture" / "browse").exists())

    def test_source_nested_file_escape_is_rejected_before_clearing(self):
        link(self, self.outside, self.sd / "browse" / "external.txt", directory=False)
        self.rejected()

    def test_metadata_directory_escape_is_rejected_before_clearing(self):
        (self.sd / "data" / "landing.json").unlink()
        (self.sd / "data").rmdir()
        write(self.outside.parent / "landing.json", '{"dirs":[]}')
        link(self, self.outside.parent, self.sd / "data")
        self.rejected()

    def test_metadata_file_escape_is_rejected_before_clearing(self):
        (self.sd / "data" / "landing.json").unlink()
        link(self, self.outside, self.sd / "data" / "landing.json", directory=False)
        self.rejected()

    def test_destination_directory_escape_preserves_outside_files(self):
        self.old.unlink()
        self.old.parent.rmdir()
        write(self.outside.parent / "keep.txt", "old release")
        link(self, self.outside.parent, self.out / "fixture")
        self.rejected()

    def test_destination_nested_directory_escape_is_rejected_before_clearing(self):
        link(self, self.outside.parent, self.out / "fixture" / "browse")
        self.rejected()

    def test_internal_destination_link_preserves_target(self):
        target = self.out / "unrelated"
        sentinel = write(target / "keep.txt")
        link(self, target, self.out / "fixture" / "browse")
        self.rejected()
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel")

    def test_image_tree_directory_escape_is_rejected_before_clearing(self):
        self.config.update(imageMode="local", imageDirs=["thumbs"])
        (self.sd / "thumbs").mkdir()
        link(self, self.outside.parent, self.sd / "thumbs" / "external")
        self.rejected()

    def test_output_overlapping_source_or_repository_is_rejected(self):
        for out in (self.sd, ROOT, ROOT / "sites", ROOT / "shared" / "output"):
            with self.subTest(out=str(out)):
                self.rejected(out=out)
        self.assertEqual((self.sd / "index.html").read_text(encoding="utf-8"), "new release")

    def test_dist_and_preview_output_under_repository_remain_allowed(self):
        # A fake repository keeps this check entirely inside the temporary fixture.
        repo = self.base / "repo"
        repo.mkdir()
        with patch.object(release, "ROOT", str(repo)):
            for out in (repo / "dist", repo / "_v" / "security-paths" / "release"):
                with self.subTest(out=str(out)):
                    self.run_release(out=out)
                    self.assertTrue((out / "fixture" / "browse" / "index.html").is_file())
        self.assertEqual(self.old.read_text(encoding="utf-8"), "old release")

    def test_valid_remote_release_preserves_data_and_landing_without_images(self):
        write(self.sd / "thumbs" / "unpublished.webp")
        self.run_release()
        dst = self.out / "fixture"
        self.assertEqual(sorted(p.name for p in dst.iterdir()), ["browse", "data", "index.html"])
        self.assertEqual((dst / "browse" / "index.html").read_text(encoding="utf-8"), "browse")
        self.assertEqual(self.outside.read_text(encoding="utf-8"), "sentinel")


if __name__ == "__main__":
    unittest.main(verbosity=2)
