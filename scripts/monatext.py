"""Mona Sans text as SVG paths, for images that GitHub renders without web fonts.

The variable TTF (Google Fonts copy of Mona Sans, OFL) lives next to this file.
Weights are instanced on demand; glyph outlines come from fontTools, so the
result looks the same everywhere GitHub shows the SVG.
"""

from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONT = Path(__file__).resolve().parent / "MonaSans.ttf"
_instances: dict[int, TTFont] = {}


def face(weight: int) -> TTFont:
    if weight not in _instances:
        _instances[weight] = instancer.instantiateVariableFont(TTFont(FONT), {"wght": weight, "wdth": 100})
    return _instances[weight]


def text_path(text: str, size: float, weight: int = 400, tracking: float = 0.0) -> tuple[str, float]:
    """(SVG path markup, advance width in px) for `text` with its origin on the baseline."""
    font = face(weight)
    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    hmtx = font["hmtx"]
    scale = size / upem
    x = 0.0
    parts = []
    for ch in text:
        name = cmap.get(ord(ch)) or cmap.get(ord("?"))
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        d = pen.getCommands()
        if d:
            parts.append(f'<path transform="translate({x:.2f} 0) scale({scale:.5f} {-scale:.5f})" d="{d}"/>')
        x += hmtx[name][0] * scale + tracking * size
    return "".join(parts), x


def measure(text: str, size: float, weight: int = 400, tracking: float = 0.0) -> float:
    return text_path(text, size, weight, tracking)[1]


def text(x: float, y: float, s: str, size: float, weight: int, fill: str, anchor: str = "start", tracking: float = 0.0) -> tuple[str, float]:
    """A positioned text run. Returns (markup, width)."""
    d, w = text_path(s, size, weight, tracking)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    return f'<g fill="{fill}" transform="translate({x:.2f} {y:.2f})">{d}</g>', w


# The portfolio's tokens (style.css :root), plus a dark rendition for prefers-color-scheme: dark.
THEMES = {
    "light": dict(bg="#ffffff", bg2="#f6f7f8", ink="#111318", ink2="#5b6068", rule="#e6e8eb", rule2="#d3d6db",
                  live="#0f7b3f", dot="#1fa35a", liveborder="#b7dcc6", btn="#111318", btntext="#ffffff"),
    "dark": dict(bg="#111318", bg2="#1b1e24", ink="#ffffff", ink2="#a4a9b3", rule="#2a2e36", rule2="#3a3f47",
                 live="#5fd08a", dot="#5fd08a", liveborder="#2f5a3d", btn="#ffffff", btntext="#111318"),
}
