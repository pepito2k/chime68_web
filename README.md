# chime68_web

The website for [Chime68](https://github.com/pepito2k/chime68), a classic
Macintosh emulator written in Rust. It is a static page, plain HTML and
CSS with no build step, served by GitHub Pages from the root of `main`.

To look at it locally:

```sh
python3 -m http.server 8000
```

and open http://localhost:8000.

## What's here

| Path | What it is |
|---|---|
| `index.html`, `style.css`, `script.js` | The page, and its scroll reveals |
| `fonts/chime68.ttf` | Chime68's own system font, used for small labels |
| `img/` | Screenshots from the emulator, and its icon |
| `tools/make-font.py` | Makes the font from Chime68's bitmap glyphs |
| `downloads/` | The current release's builds, checksums and notes, and `latest.json` |
| `tools/publish-release.sh` | Copies a release's builds here and updates the download links |

The font's glyphs are the ones Chime68 draws its setup window and menus
with (`crates/chime68/src/ui/font.rs` in the emulator). To make it again
after they change:

```sh
tools/make-font.py ../chime68/crates/chime68/src/ui/font.rs fonts/chime68.ttf
```

## Publishing a new release

The emulator repo is private, so the site hosts the builds itself, under
`downloads/vX.Y.Z/`. After a release is out on pepito2k/chime68:

```sh
git switch -c release-X.Y.Z
tools/publish-release.sh X.Y.Z
git add -A downloads index.html && git commit -m "feat: Chime68 X.Y.Z downloads"
```

The script downloads the five assets with `gh`, replaces the old
`downloads/v*/` folder (earlier builds stay in git history), writes
`SHA256SUMS`, `release-notes.txt` and `downloads/latest.json`, and rewrites
the download card between the `downloads:begin`/`downloads:end` markers in
`index.html`. It stops if any file is near GitHub's 100 MB per-file limit;
files must be plain git, not LFS, since Pages doesn't serve LFS files.

The icon comes from the emulator's `scripts/make-icon.py`, and the
screenshots from its headless runs (`--frames` with `--screenshot`) and its
setup window. No ROMs or disk images are kept here.
