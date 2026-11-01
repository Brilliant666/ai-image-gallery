<div align="center">

# AI Image Reference Library

**Five AI art reference galleries with six site entries, built from one repo and served from one directory**

Portrait · Pose (line art and depth) · Costume · CC0 Pose Line Art · Character · Chinese / Japanese UI · Light / Dark

15,241 locally hosted image files (including size variants); Character adds 843 base entries and 184 hair-color variants. Its remote images are excluded from the file total.

[![CI](https://github.com/Brilliant666/ai-image-gallery/actions/workflows/ci.yml/badge.svg)](https://github.com/Brilliant666/ai-image-gallery/actions/workflows/ci.yml)
[![online](https://img.shields.io/badge/online-photoai.life-2563eb?style=flat-square)](https://photoai.life/)
[![sites](https://img.shields.io/badge/sites-6-0ea5e9?style=flat-square)](#sites)
[![images](https://img.shields.io/badge/image_files-15%2C241-8b5cf6?style=flat-square)](#sites)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776ab?style=flat-square&logo=python&logoColor=white)](#quick-start)
[![License](https://img.shields.io/badge/code-MIT-22c55e?style=flat-square)](#license-and-credits)

### [Browse online · photoai.life →](https://photoai.life/)

[简体中文](README.md) · **English** · [日本語](README_ja.md)

[Sites](#sites) · [Quick start](#quick-start) · [Image loading](#image-loading) · [Deployment](#deployment) · [Documentation](#documentation)

</div>

![Hub](docs/screenshots/hub-light.jpg)

<details>
<summary>📷 More screenshots: portraits, poses, depth maps, costumes</summary>

![Portrait grid](docs/screenshots/portrait-grid.jpg)

![Portrait lightbox](docs/screenshots/portrait-lightbox.jpg)

![Pose gallery, dark theme](docs/screenshots/pose-grid.jpg)

![Pose lightbox](docs/screenshots/pose-lightbox.jpg)

![Pose depth gallery](docs/screenshots/pose-depth-grid.jpg)

![Costume tag filters](docs/screenshots/costume-filter.jpg)

![Costume lightbox](docs/screenshots/costume-lightbox.jpg)

Screenshots are taken from the live site to show the UI. The artwork belongs to its original authors; do not crop images out of the screenshots for other use.

</details>

## Sites

| Site | Content | Size | Image license |
| --- | --- | --- | :---: |
| [Portrait](https://photoai.life/portrait/) | Face references for character consistency, filterable by hairstyle | 1,499 | **CC0** |
| [Pose](https://photoai.life/pose/) | Faceless gray mannequin line art, 5 angles per pose | 1,439 | No redistribution |
| [Pose Depth](https://photoai.life/pose-depth/) | Grayscale depth maps of the same poses, for ControlNet | 1,439 | No redistribution |
| [Costume](https://photoai.life/costume/) | Outfits without models, 86 faceted tags | 1,407 items / 4,221 files | No redistribution |
| [Shisei line art](https://photoai.life/shisei/) | Faceless mannequin line art, 4 series, up to 5 angles; adult content hidden by default | 280 poses / 1,133 | **CC0** |
| [Character](https://photoai.life/character/) | Hairstyle, outfit and pose references, loaded from the source | 843 base entries + 184 hair-color variants; 281 pose line drawings | No redistribution of original or processed images |

Six physical sites appear as five galleries in navigation because Pose and Pose Depth share one gallery. Character has 122 hair and eye entries, 440 outfits and 281 poses (843 base entries); including hair-color variants there are 1,027 entries, with line art counted separately. These remote items are excluded from the 15,241 locally hosted image files.

Every gallery has batched grids, filters and search, image enlargement, and theme and language switches. Locally hosted galleries also support lightbox arrow keys, touch swipes and original downloads. Character links to source originals and line art; `Esc` closes its detail view. A shared top bar holds the gallery links and the 18+, light / dark and language switches; preferences apply across all galleries. Press `?` for shortcuts and `/` to jump to search. Pose has one switch between line art and depth maps, and the lightbox can compare both with a draggable divider. Adult-oriented items are hidden by default on Pose, Pose Depth, Costume, Shisei and Character (Character initially offers 791 base entries, with 184 hair-color variants available through previews); the 18+ switch in the top bar shows them after a one-time age check, shared across all sites. They never appear on static landing pages or in the sitemap. Each page is a single `index.html` with embedded data and no framework, CDN or web fonts.

> **Portrait and Shisei images are CC0.** The other sites forbid redistribution. Character allows commercial artwork, reference use and modifications, but forbids redistributing original or processed images and using them to represent real people or minors. Shisei's pose list follows ai-pose-gallery and is credited only. See `sites/<id>/NOTICE.md`.

### Character gallery

This is a resource library, with no image-generation service, API-key settings or multi-part tag assembly. Character uses square white image areas and provides:

- Hair and eyes, outfits, and poses, with visible category buttons and counts; adult-only categories are marked 18+ while hidden.
- Five color swatches on each hairstyle card, independent of other cards. Detail color changes update the card; the global color menu resets previews and Reset returns to brown.
- Exact single-entry English tag copying and browser-local favorites that store the displayed variant. Preview changes do not rewrite saved favorites.
- Offline metadata, search, categories and tag copying. Images require the source site and are never downloaded, packaged or mirrored by the tools.

See [Character notes](sites/character/README.md) for usage and catalog maintenance, and [source terms](sites/character/NOTICE.md) for image conditions.

## Quick start

This repo contains no source image files. `tools/fetch.py` downloads images for locally hosted sites and explicitly skips Character (`imageMode: "remote"`); its thumbnails, originals and line art must not be downloaded or mirrored. Local pages, source data and manifests remain available, while image URLs point directly to the source and need a network connection even under `file://`. Requires **Python 3.8+**. `tools/mid.py`, which generates lightbox previews, also needs Pillow (`pip install pillow`); every other script uses only the standard library.

```bash
git clone https://github.com/Brilliant666/ai-image-gallery.git
cd ai-image-gallery

python tools/fetch.py      # download locally hosted images; skip Character (~6.8 GB first time, then only missing files)
python tools/mid.py        # generate lightbox previews (~290 MB)
python tools/build.py      # build six site entries (five galleries) and the hub
python tools/release.py    # assemble dist/ (images are hard links, no extra disk)
python tools/serve.py      # preview at http://127.0.0.1:8080/
```

To try the UI only, run `python tools/fetch.py --tier thumb` to fetch thumbnails (~90 MB).

Check the result through `serve.py`, not by opening `dist/index.html` directly: `file://` differs from `http://` in relative paths, Content-Type and caching.

<details>
<summary>Common commands</summary>

| Command | Purpose |
| --- | --- |
| `python tools/fetch.py --site pose` | Download one site |
| `python tools/mid.py --site portrait` | Generate previews for one site |
| `python tools/verify.py` | Check local images/previews; validate only metadata for Character |
| `python tools/build.py --site character` | Rebuild Character and the hub without image network access |
| `python tools/build.py --site pose` | Rebuild one site |
| `python tools/build.py --base https://x.com` | Set the public domain for canonical / og / sitemap |
| `python tools/release.py --out <dir>` | Release into another directory |
| `python tools/serve.py --root sites/pose` | Preview one site |
| `python tests/run.py` | Checks that need no images: build output up to date, duplicate ids, inline JS syntax, manifests, doc links (CI runs it on every push) |

`release.py` verifies local images first and stops if any are missing (add `--skip-verify` if you fetched only some tiers). Remote sites receive metadata validation only; network availability, image existence and decoding are not verified. Their releases contain pages, `data/` and manifests, with no remote image assets. It deletes and recreates each target site directory. `--no-images` copies site files only; it does not keep old images in place.

</details>

## Image loading

Locally hosted galleries normally have three tiers: thumbnails for the grid, previews for the lightbox, originals for download only. Character uses remote source thumbnails, originals and optional line art; `tiers: []` and `imageDirs: []` disable local fetching and image packaging.

| Tier | Portrait | Pose | Pose Depth | Costume |
| --- | ---: | ---: | ---: | ---: |
| Thumbnail | ~20 KB | ~17 KB | ~11 KB | ~10 KB |
| Preview | ~150 KB | ~33 KB | ~10 KB | ~90 KB |
| Original | ~3.2 MB | ~450 KB | ~95 KB | ~1 MB |

The following preview and prefetch behavior applies to locally hosted galleries. Character loads source originals directly in its detail view.

- The lightbox shows the sharp thumbnail at once and fades in the preview when it arrives. Switching images hides the previous one immediately.
- Previews are prefetched after 120 ms of hover, on pointer down, or on keyboard focus; once open, the next and previous images are prefetched too.
- Costume previews come from the original site. The other three are generated by `tools/mid.py` (longest edge 1600 px, WebP quality 82). If a preview is missing, the lightbox falls back to the original.

Measured on the Portrait site at 1.5 MB/s and 150 ms latency: a direct click shows the preview after about 0.6 s; after hovering for about 1 s, the preview shows as soon as the lightbox opens.

## Deployment

Point the web root at `dist/`. It is flat (`index.html` + `portrait/` + `pose/` + …), so the hub's relative links work without nginx `alias`.

```bash
# Server update: drops build output; stops and lists any hand-edited files instead of overwriting them
python3 tools/update.py
python3 tools/mid.py
python3 tools/build.py --base https://your-domain
python3 tools/release.py --out dist-stage   # stage first, check, then swap sites into dist/ atomically
```

First-time setup, nginx, atomic swaps and rollback: [deploy/DEPLOY.md](deploy/DEPLOY.md) (Chinese).

## Project layout

```
ai-image-gallery/
├── sites.json          # single manifest: sites, order, licenses, image tiers
├── sites/<id>/         # each site: scripts, data, build output, NOTICE
├── shared/             # download and verify for all sites; page generator, source parser and JA→ZH dictionary for Pose and Pose Depth
├── hub/                # hub page generator (also writes root sitemap / robots)
├── tools/              # fetch / mid / verify / build / release / serve / update
├── deploy/             # deployment guide and nginx template
├── tests/              # checks that need no images (python tests/run.py)
└── docs/               # documentation and screenshots
```

Images stay out of git: 6.8 GB of binaries would make every clone huge, and most site licenses do not allow it. `release.py` hard-links 20,751 image files into `dist/`, which costs no extra disk on the same file system.

## Documentation

[Deployment guide](deploy/DEPLOY.md) · [Adding a site](docs/ADDING_A_SITE.md) · [nginx template](deploy/nginx.conf) · Per-site notes: [Portrait](sites/portrait/README.md) · [Pose](sites/pose/README.md) · [Pose Depth](sites/pose-depth/README.md) · [Costume](sites/costume/README.md) · [Shisei](sites/shisei/README.md) · [Character](sites/character/README.md)

The deployment guide and adding-a-site guide are in Chinese.

## License and credits

| Scope | License |
| --- | --- |
| Code: `tools/`, `hub/`, `shared/`, each site's `scripts/`, and the HTML/CSS/JS in `index.html` | [MIT](LICENSE) |
| Images | Differs per site, see `sites/<id>/NOTICE.md` |
| Independently written Chinese translations in `data/` and the Character name map | CC BY 4.0 |
| Character source catalog fields and images | Original author terms; not relicensed by this repository. See [NOTICE](sites/character/NOTICE.md) |

Images come from the original sites. Portrait by [あぎ](https://x.com/agi_aibusi) ([original](https://ai-portrait-gallery.pages.dev/)); Pose, Pose Depth and Costume by [ギア](https://x.com/giaaibusi) ([pose](https://ai-pose-gallery.pages.dev/) · [pose depth](https://ai-pose-depth-gallery.pages.dev/) · [costume](https://ai-costume-gallery.pages.dev/)). Shisei line art comes from [wquguru/shisei](https://github.com/wquguru/shisei) (CC0). Character comes from [たき AI](https://x.com/taki_auto)'s [キャラ組み立てDB](https://charadb-2fi.pages.dev/), with images loaded only from the source. This project is a personal Chinese-language index for learning.
