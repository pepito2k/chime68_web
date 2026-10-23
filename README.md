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

The font's glyphs are the ones Chime68 draws its setup window and menus
with (`crates/chime68/src/ui/font.rs` in the emulator). To make it again
after they change:

```sh
tools/make-font.py ../chime68/crates/chime68/src/ui/font.rs fonts/chime68.ttf
```

The icon comes from the emulator's `scripts/make-icon.py`, and the
screenshots from its headless runs (`--frames` with `--screenshot`) and its
setup window. No ROMs or disk images are kept here.
