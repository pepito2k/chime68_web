#!/bin/sh
# Copy a Chime68 release's builds into this site and point the download
# links at them, so visitors don't need access to the (private) emulator repo.
#
#   tools/publish-release.sh 0.89.1
#
# Needs the GitHub CLI (`gh`), signed in with read access to pepito2k/chime68.
# It replaces downloads/v*/ with the new version's files, writes SHA256SUMS,
# release-notes.txt and downloads/latest.json, and rewrites the block between
# the `downloads:begin` and `downloads:end` markers in index.html.
# Review with `git diff`, then commit and open a PR.
set -eu

REPO=pepito2k/chime68
LIMIT=$((95 * 1024 * 1024))   # GitHub rejects files over 100 MB

v=${1:?usage: tools/publish-release.sh VERSION (e.g. 0.89.1)}
v=${v#v}
tag=v$v
cd "$(dirname "$0")/.."

mac=Chime68-$tag-macos.zip
arm=chime68-$tag-macos-arm64.tar.gz
x86=chime68-$tag-macos-x86_64.tar.gz
lin=chime68-$tag-linux-x86_64.tar.gz
win=chime68-$tag-windows-x86_64.zip

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
gh release download "$tag" -R "$REPO" -D "$tmp" \
  -p "$mac" -p "$arm" -p "$x86" -p "$lin" -p "$win"
gh release view "$tag" -R "$REPO" --json body -q .body > "$tmp/release-notes.txt"

for f in "$mac" "$arm" "$x86" "$lin" "$win"; do
  [ -f "$tmp/$f" ] || { echo "missing asset: $f" >&2; exit 1; }
  size=$(wc -c < "$tmp/$f" | tr -d ' ')
  [ "$size" -lt "$LIMIT" ] || {
    echo "$f is $size bytes, too big to commit; publish it as a release instead" >&2
    exit 1
  }
done

rm -rf downloads/v*/
dir=downloads/$tag
mkdir -p "$dir"
mv "$tmp"/* "$dir/"
(cd "$dir" && shasum -a 256 "$mac" "$arm" "$x86" "$lin" "$win" > SHA256SUMS)

cat > downloads/latest.json <<EOF
{
  "version": "$v",
  "tag": "$tag",
  "files": {
    "macos-app": "$dir/$mac",
    "macos-arm64": "$dir/$arm",
    "macos-x86_64": "$dir/$x86",
    "linux-x86_64": "$dir/$lin",
    "windows-x86_64": "$dir/$win"
  },
  "sha256sums": "$dir/SHA256SUMS",
  "release_notes": "$dir/release-notes.txt"
}
EOF

block=$tmp/block.html
cat > "$block" <<EOF
          <!-- downloads:begin (written by tools/publish-release.sh) -->
          <p>Version $v, ready-made for macOS, Linux and Windows. On a Mac, Chime68.app runs on Apple silicon and Intel: unzip it, put it in Applications and double-click it.</p>
          <p>The Mac builds are signed and notarized by Apple, so macOS opens them without any extra steps.</p>
          <ul class="downloads">
            <li><a href="$dir/$mac">Chime68.app</a><span>macOS, Apple silicon and Intel</span></li>
            <li><a href="$dir/$arm">chime68</a><span>macOS command line, Apple silicon</span></li>
            <li><a href="$dir/$x86">chime68</a><span>macOS command line, Intel</span></li>
            <li><a href="$dir/$lin">chime68</a><span>Linux, x86-64</span></li>
            <li><a href="$dir/$win">chime68.exe</a><span>Windows, x86-64</span></li>
          </ul>
          <div class="buttons"><a class="button" href="$dir/release-notes.txt">Release notes</a><a class="button" href="$dir/SHA256SUMS">Checksums</a></div>
          <!-- downloads:end -->
EOF

grep -q 'downloads:begin' index.html && grep -q 'downloads:end' index.html || {
  echo "index.html has no downloads:begin/end markers" >&2; exit 1; }
awk -v block="$block" '
  /downloads:begin/ { while ((getline line < block) > 0) print line; skip = 1; next }
  /downloads:end/   { skip = 0; next }
  !skip
' index.html > "$tmp/index.html"
mv "$tmp/index.html" index.html

echo "Published $tag into $dir:"
ls -l "$dir"
