"""Build a glyph atlas (SVG path per character) from the portfolio fonts.

GitHub serves repository SVGs with `Content-Security-Policy: default-src 'none'`, so
`@font-face` inside an SVG never loads and the text falls back to a system font.
Shipping each glyph as a path keeps the banner and stats card in the portfolio's
own lettering (Saira + B612 Mono) everywhere.

Run locally (reading woff2 needs the `brotli` module):
    python tools/glyphs.py <portfolio fonts dir> assets/glyphs.json
"""

import json
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FACES = {
    "display": "saira-800",
    "bold": "saira-700",
    "semi": "saira-600",
    "mono": "b612mono-400",
    "monob": "b612mono-700",
}
CHARS = [chr(c) for c in range(32, 127)] + ["·", "—", "–", "→"]


def build_face(path: Path) -> dict:
    font = TTFont(path)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    glyphs = {}
    for ch in CHARS:
        name = cmap.get(ord(ch))
        if name is None:
            continue
        pen = SVGPathPen(glyph_set, ntos=lambda v: f"{v:.0f}")
        # Font units are y-up; SVG is y-down.
        glyph_set[name].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
        glyphs[ch] = [hmtx[name][0], pen.getCommands()]
    return {"upm": font["head"].unitsPerEm, "glyphs": glyphs}


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: python tools/glyphs.py <fonts dir> <output json>")
    fonts_dir, output = Path(sys.argv[1]), Path(sys.argv[2])
    atlas = {key: build_face(fonts_dir / f"{name}.woff2") for key, name in FACES.items()}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(atlas, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    sizes = {key: len(face["glyphs"]) for key, face in atlas.items()}
    print(f"wrote {output} ({output.stat().st_size // 1024} KiB) glyphs per face: {sizes}")


if __name__ == "__main__":
    main()
