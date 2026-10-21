#!/usr/bin/env python3
"""Turns Chime68's bitmap font into a TrueType font for the site.

Chime68 draws its setup window and menus in a 12-pixel face of its own,
in the style of the classic Mac's system font. Its glyphs are pixel art in
chime68's crates/chime68/src/ui/font.rs; this reads them from there and
writes each pixel as a square, so the font is sharp at 12, 24 or 36 px.
Only the standard library is needed.

    tools/make-font.py ../chime68/crates/chime68/src/ui/font.rs fonts/chime68.ttf
"""

import re
import struct
import sys
import time

PIXEL = 100  # font units per pixel
EM = 12 * PIXEL
CAP = 9  # rows from the cap height to the baseline
ASCENT = 10 * PIXEL
DESCENT = 3 * PIXEL
FAMILY = "Chime68"
VERSION = "Version 1.0"


def read_glyphs(path):
    """{char: [row strings]} from font.rs's ART table."""
    src = open(path, encoding="utf-8").read()
    art = src[src.index("const ART"):]
    glyphs = {}
    for m in re.finditer(r"\('((?:\\u\{[0-9a-fA-F]+\}|\\.|[^'\\]))', &\[(.*?)\]\)", art):
        c = m.group(1)
        if c.startswith("\\u{"):
            c = chr(int(c[3:-1], 16))
        elif c.startswith("\\"):
            c = c[1]
        glyphs[c] = re.findall(r'"([.#]*)"', m.group(2))
    return glyphs


def outline(rows):
    """The glyph's contours, clockwise around ink, in font units."""
    ink = {(x, r) for r, line in enumerate(rows) for x, b in enumerate(line) if b == "#"}
    edges = {}
    for x, r in ink:
        y = CAP - 1 - r  # the pixel's bottom, in pixels above the baseline
        if (x, r - 1) not in ink:
            edges.setdefault((x, y + 1), []).append((x + 1, y + 1))
        if (x + 1, r) not in ink:
            edges.setdefault((x + 1, y + 1), []).append((x + 1, y))
        if (x, r + 1) not in ink:
            edges.setdefault((x + 1, y), []).append((x, y))
        if (x - 1, r) not in ink:
            edges.setdefault((x, y), []).append((x, y + 1))
    contours = []
    while edges:
        start = min(edges)
        points = [start]
        point = start
        while True:
            nexts = edges[point]
            nxt = nexts.pop()
            if not nexts:
                del edges[point]
            if nxt == start:
                break
            points.append(nxt)
            point = nxt
        # Keep only the corners.
        corners = []
        n = len(points)
        for i, p in enumerate(points):
            a, b = points[i - 1], points[(i + 1) % n]
            if (p[0] - a[0]) * (b[1] - p[1]) != (p[1] - a[1]) * (b[0] - p[0]):
                corners.append((p[0] * PIXEL, p[1] * PIXEL))
        contours.append(corners)
    return contours


def glyf_entry(contours):
    if not contours:
        return b"", (0, 0, 0, 0), 0, 0
    xs = [p[0] for c in contours for p in c]
    ys = [p[1] for c in contours for p in c]
    box = (min(xs), min(ys), max(xs), max(ys))
    data = struct.pack(">hhhhh", len(contours), *box)
    end = -1
    for c in contours:
        end += len(c)
        data += struct.pack(">H", end)
    data += struct.pack(">H", 0)  # no instructions
    points = [p for c in contours for p in c]
    data += bytes([0x01]) * len(points)  # on the curve, long coordinates
    last = (0, 0)
    xd, yd = b"", b""
    for p in points:
        xd += struct.pack(">h", p[0] - last[0])
        yd += struct.pack(">h", p[1] - last[1])
        last = p
    data += xd + yd
    if len(data) % 2:
        data += b"\0"
    return data, box, len(points), len(contours)


def checksum(data):
    data += b"\0" * (-len(data) % 4)
    return sum(struct.unpack(">%dI" % (len(data) // 4), data)) & 0xFFFFFFFF


def cmap_table(mapping):
    """A format 4 subtable, one segment per character."""
    codes = sorted(mapping)
    ends = codes + [0xFFFF]
    starts = codes + [0xFFFF]
    deltas = [(mapping[c] - c) & 0xFFFF for c in codes] + [1]
    seg = len(ends)
    search = 2 * 2 ** (seg.bit_length() - 1)
    body = struct.pack(">HHH", seg * 2, search, seg.bit_length() - 1) + struct.pack(">H", seg * 2 - search)
    body += struct.pack(">%dH" % seg, *ends) + b"\0\0"
    body += struct.pack(">%dH" % seg, *starts)
    body += struct.pack(">%dH" % seg, *deltas)
    body += struct.pack(">%dH" % seg, *([0] * seg))
    sub = struct.pack(">HHH", 4, 6 + len(body), 0) + body
    return struct.pack(">HHHHI", 0, 1, 3, 1, 12) + sub


def name_table():
    names = {
        0: "Glyphs drawn for Chime68 (MIT licence)",
        1: FAMILY,
        2: "Regular",
        3: FAMILY + " Regular",
        4: FAMILY,
        5: VERSION,
        6: FAMILY + "-Regular",
    }
    strings = b""
    records = b""
    for nid, text in names.items():
        enc = text.encode("utf-16-be")
        records += struct.pack(">HHHHHH", 3, 1, 0x409, nid, len(enc), len(strings))
        strings += enc
    return struct.pack(">HHH", 0, len(names), 6 + len(records)) + records + strings


def build(glyphs):
    # Glyph 0 is .notdef, drawn as the font's own '?'.
    order = [None] + sorted(glyphs)
    glyf, loca, hmtx = b"", [0], b""
    max_points = max_contours = 0
    bounds = [0, 0, 0, 0]
    advances = []
    for c in order:
        rows = glyphs["?" if c is None else c]
        data, box, npts, ncont = glyf_entry(outline(rows))
        width = len(rows[0]) if rows else 0
        advance = (width + 1) * PIXEL
        advances.append(advance)
        hmtx += struct.pack(">Hh", advance, box[0])
        glyf += data
        loca.append(len(glyf))
        max_points, max_contours = max(max_points, npts), max(max_contours, ncont)
        if data:
            bounds = [min(bounds[0], box[0]), min(bounds[1], box[1]), max(bounds[2], box[2]), max(bounds[3], box[3])]
    mapping = {ord(c): gid for gid, c in enumerate(order) if c is not None}
    # The command key and check mark sit at $11 and $12, as in Mac Roman;
    # give them their Unicode code points too.
    for ctrl, uni in (("\x11", 0x2318), ("\x12", 0x2713)):
        if ctrl in glyphs:
            mapping[uni] = order.index(ctrl)
            mapping.pop(ord(ctrl), None)
    mapping[0xA0] = order.index(" ")  # no-break space
    n = len(order)
    now = int(time.time()) + 2082844800  # seconds since 1904
    head = struct.pack(
        ">IIIIHHqqhhhhHHhhh",
        0x00010000, 0x00010000, 0, 0x5F0F3CF5, 0x000B, EM, now, now,
        *bounds, 0, 8, 2, 1, 0,
    )
    hhea = struct.pack(
        ">IhhhHhhhhhhhhhhhH",
        0x00010000, ASCENT, -DESCENT, 0, max(advances), 0, 0, bounds[2],
        1, 0, 0, 0, 0, 0, 0, 0, n,
    )
    maxp = struct.pack(">IHHHHHHHHHHHHHH", 0x00010000, n, max_points, max_contours, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0)
    codes = sorted(mapping)
    os2 = struct.pack(
        ">HhHHH" + "h" * 10 + "h" + "10s" + "IIII" + "4s" + "HHH" + "hhhHH" + "II" + "hhHHH",
        4, sum(advances) // n, 400, 5, 0,
        650, 700, 0, 140, 650, 700, 0, 480, 100, 400,
        0, b"\0" * 10, 1, 0, 0, 0, b"C68 ",
        0xC0, codes[0], min(codes[-1], 0xFFFF),
        ASCENT, -DESCENT, 0, ASCENT, DESCENT,
        1, 0,
        6 * PIXEL, CAP * PIXEL, 0, 32, 1,
    )
    post = struct.pack(">IIhhIIIII", 0x00030000, 0, -2 * PIXEL, PIXEL, 0, 0, 0, 0, 0)
    tables = {
        b"OS/2": os2,
        b"cmap": cmap_table(mapping),
        b"glyf": glyf,
        b"head": head,
        b"hhea": hhea,
        b"hmtx": hmtx,
        b"loca": struct.pack(">%dI" % len(loca), *loca),
        b"maxp": maxp,
        b"name": name_table(),
        b"post": post,
    }
    count = len(tables)
    search = 16 * 2 ** (count.bit_length() - 1)
    font = struct.pack(">IHHHH", 0x00010000, count, search, count.bit_length() - 1, count * 16 - search)
    offset = 12 + 16 * count
    directory, body = b"", b""
    head_at = 0
    for tag in sorted(tables):
        data = tables[tag]
        if tag == b"head":
            head_at = offset
        directory += struct.pack(">4sIII", tag, checksum(data), offset, len(data))
        padded = data + b"\0" * (-len(data) % 4)
        body += padded
        offset += len(padded)
    font = bytearray(font + directory + body)
    adjust = (0xB1B0AFBA - checksum(bytes(font))) & 0xFFFFFFFF
    font[head_at + 8:head_at + 12] = struct.pack(">I", adjust)
    return bytes(font)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    glyphs = read_glyphs(sys.argv[1])
    font = build(glyphs)
    with open(sys.argv[2], "wb") as f:
        f.write(font)
    print(f"{sys.argv[2]}: {len(glyphs)} glyphs, {len(font)} bytes")


if __name__ == "__main__":
    main()
