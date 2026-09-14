"""Engineering-sheet primitives shared by the banner and the activity card.

The look follows the portfolio's DESIGN.md ("The Drawing Set"): paper and ink in three
line weights, dimension blue for anything that measures or links, revision red only
for stamps, square corners, no shadows, and one draw-on animation. The dark theme is
the portfolio's cyanotype sheet, where blue and red both collapse to white.

Text is drawn from glyph outlines in glyphs.json because GitHub serves repository
SVGs under `Content-Security-Policy: default-src 'none'`, which blocks @font-face.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

ATLAS = json.loads(Path(__file__).with_name("glyphs.json").read_text(encoding="utf-8"))

HAIR, MEDIUM, THICK = 1, 1.5, 3
RULE_OPACITY = 0.42
STAMP_STROKE = 2


@dataclass(frozen=True)
class Theme:
    name: str
    paper: str
    ink: str
    ink2: str
    dim: str
    rev: str
    blueprint: bool


LIGHT = Theme("light", "#fbfbf8", "#111111", "#3b3b3b", "#0b57d0", "#d3271b", False)
DARK = Theme("dark", "#0f2f5f", "#ffffff", "#bcd0ee", "#ffffff", "#ffffff", True)
THEMES = (LIGHT, DARK)

MOTION_CSS = (
    ".draw{stroke-dasharray:1;stroke-dashoffset:1;"
    "animation:draw .9s cubic-bezier(.16,1,.3,1) .25s forwards}"
    ".fade{opacity:0;animation:fade .35s ease-out 1.05s forwards}"
    "@keyframes draw{to{stroke-dashoffset:0}}"
    "@keyframes fade{to{opacity:1}}"
    "@media (prefers-reduced-motion:reduce){"
    ".draw{animation:none;stroke-dashoffset:0}.fade{animation:none;opacity:1}}"
)


def fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def measure(text: str, size: float, face: str, tracking: float = 0.0) -> float:
    """Width in user units of `text` set at `size` with `tracking` in em."""
    font = ATLAS[face]
    glyphs = font["glyphs"]
    space = glyphs[" "][0]
    units = sum(glyphs[ch][0] if ch in glyphs else space for ch in text)
    units += tracking * font["upm"] * max(len(text) - 1, 0)
    return units * size / font["upm"]


class Drawing:
    def __init__(self, width: int, height: int, theme: Theme, title: str) -> None:
        self.width = width
        self.height = height
        self.theme = theme
        self.title = title
        self._glyphs: dict[str, str] = {}
        self._defs: list[str] = []
        self._body: list[str] = []
        self._css: list[str] = []

    # -- raw markup ---------------------------------------------------------
    def add(self, markup: str) -> None:
        self._body.append(markup)

    def define(self, markup: str) -> None:
        self._defs.append(markup)

    def style(self, css: str) -> None:
        if css not in self._css:
            self._css.append(css)

    # -- text -----------------------------------------------------------------
    def text(
        self,
        text: str,
        x: float,
        y: float,
        size: float,
        face: str,
        fill: str,
        tracking: float = 0.0,
        anchor: str = "start",
        cls: str = "",
    ) -> float:
        """Set `text` with its baseline at `y`; returns the set width."""
        font = ATLAS[face]
        glyphs = font["glyphs"]
        upm = font["upm"]
        width = measure(text, size, face, tracking)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        cursor = 0.0
        uses = []
        for ch in text:
            advance, path = glyphs.get(ch, glyphs[" "])
            if path:
                gid = f"{face}-{ord(ch):x}"
                self._glyphs.setdefault(gid, path)
                uses.append(f'<use href="#{gid}" x="{cursor:.0f}"/>')
            cursor += advance + tracking * upm
        klass = f' class="{cls}"' if cls else ""
        self.add(
            f'<g{klass} fill="{fill}" transform="translate({fmt(x)} {fmt(y)}) '
            f'scale({size / upm:.5f})">{"".join(uses)}</g>'
        )
        return width

    # -- linework -------------------------------------------------------------
    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str,
        width: float = HAIR,
        opacity: float = 1.0,
        cls: str = "",
    ) -> None:
        klass = f' class="{cls}" pathLength="1"' if cls else ""
        alpha = f' stroke-opacity="{opacity}"' if opacity != 1 else ""
        self.add(
            f'<path{klass} d="M{fmt(x1)} {fmt(y1)}L{fmt(x2)} {fmt(y2)}" fill="none" '
            f'stroke="{stroke}" stroke-width="{width}"{alpha} stroke-linecap="square"/>'
        )

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "none",
        stroke: str = "none",
        width: float = HAIR,
    ) -> None:
        self.add(
            f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
        )

    # -- components -----------------------------------------------------------
    def sheet(self, zone: int = 0, columns: int = 8, rows: int = 4) -> None:
        """A 3px sheet frame; with `zone` > 0, numbered and lettered zone strips."""
        t = self.theme
        fill = t.paper
        if t.blueprint:
            self.define(
                '<radialGradient id="ground" cx="28%" cy="18%" r="95%">'
                '<stop offset="0" stop-color="#16407a"/><stop offset="1" stop-color="#0f2f5f"/>'
                "</radialGradient>"
            )
            fill = "url(#ground)"
        edge = THICK / 2
        self.rect(edge, edge, self.width - THICK, self.height - THICK, fill, t.ink, THICK)
        if not zone:
            return
        left, top = THICK, THICK
        right, bottom = self.width - THICK, self.height - THICK
        self.line(left, top + zone, right, top + zone, t.ink, HAIR, RULE_OPACITY)
        self.line(left + zone, top, left + zone, bottom, t.ink, HAIR, RULE_OPACITY)
        span = (right - left - zone) / columns
        for i in range(columns):
            x = left + zone + span * i
            if i:
                self.line(x, top, x, top + zone, t.ink, HAIR, RULE_OPACITY)
            self.text(str(i + 1), x + span / 2, top + zone - 7, 11, "mono", t.ink2, anchor="middle")
        span = (bottom - top - zone) / rows
        for i in range(rows):
            y = top + zone + span * i
            if i:
                self.line(left, y, left + zone, y, t.ink, HAIR, RULE_OPACITY)
            self.text("ABCDEF"[i], left + zone / 2, y + span / 2 + 4, 11, "mono", t.ink2, anchor="middle")

    def chips(self, labels: list[str], x: float, y: float, size: float = 13, height: float = 28) -> None:
        """Bill-of-materials call-outs: 1px outline, tracked caps, no fill."""
        t = self.theme
        for label in labels:
            w = measure(label, size, "bold", 0.1) + 20
            self.rect(x, y, w, height, stroke=t.ink, width=HAIR)
            self.text(label, x + 10, y + height / 2 + size * 0.36, size, "bold", t.ink, tracking=0.1)
            x += w + 8

    def dimension(self, x1: float, x2: float, y: float, extension_top: float, label: str) -> None:
        """A dimension line with extension lines that draws itself on once."""
        t = self.theme
        for x in (x1, x2):
            self.line(x, extension_top, x, y + 8, t.dim, HAIR, cls="draw")
        self.line(x1, y, x2, y, t.dim, MEDIUM, cls="draw")
        head, half = 12, 4
        self.add(
            f'<path class="fade" fill="{t.dim}" d="M{fmt(x1)} {fmt(y)}l{head} {-half}v{2 * half}z'
            f'M{fmt(x2)} {fmt(y)}l{-head} {-half}v{2 * half}z"/>'
        )
        self.text(label, (x1 + x2) / 2, y + 26, 15, "monob", t.dim, tracking=0.1, anchor="middle", cls="fade")

    def stamp(self, word: str, sub: str, cx: float, cy: float) -> None:
        """Rubber stamp in revision red, rotated -3deg."""
        t = self.theme
        w = max(measure(word, 17, "display", 0.1), measure(sub, 11, "monob", 0.1)) + 28
        h = 46
        self.add(f'<g transform="rotate(-3 {fmt(cx)} {fmt(cy)})">')
        self.rect(cx - w / 2, cy - h / 2, w, h, stroke=t.rev, width=STAMP_STROKE)
        self.text(word, cx, cy + 1, 17, "display", t.rev, tracking=0.1, anchor="middle")
        self.text(sub, cx, cy + 16, 11, "monob", t.rev, tracking=0.1, anchor="middle")
        self.add("</g>")

    def title_block(
        self,
        y: float,
        cells: list[tuple[str | None, str, str]],
        x0: float,
        x1: float,
        trailing: list[tuple[str | None, str, str]] | None = None,
        stamp: tuple[str, str] | None = None,
    ) -> None:
        """Bottom title block.

        `cells` run from the left edge and `trailing` cells sit against the right edge;
        a key of None makes the square mono mark. An optional stamp is centred in the
        open space between the two groups.
        """
        t = self.theme
        self.line(x0, y, x1, y, t.ink, THICK)
        height = self.height - THICK - y
        x = x0
        for key, value, face in cells:
            x += self._title_cell(key, value, face, x, y, height)
            self.line(x, y, x, y + height, t.ink, MEDIUM)
        right = x1
        for key, value, face in reversed(trailing or []):
            right -= self._cell_width(key, value, face, height)
            self.line(right, y, right, y + height, t.ink, MEDIUM)
            self._title_cell(key, value, face, right, y, height)
        if stamp:
            self.stamp(stamp[0], stamp[1], (x + right) / 2, y + height / 2)

    @staticmethod
    def _cell_width(key: str | None, value: str, face: str, height: float) -> float:
        if key is None:
            return height
        return max(measure(key.upper(), 12, "bold", 0.1), measure(value, 15, face)) + 36

    def _title_cell(self, key: str | None, value: str, face: str, x: float, y: float, height: float) -> float:
        t = self.theme
        w = self._cell_width(key, value, face, height)
        if key is None:
            self.text(value, x + w / 2, y + height / 2 + 8, 22, "monob", t.ink, tracking=0.1, anchor="middle")
        else:
            self.text(key.upper(), x + 18, y + 26, 12, "bold", t.ink2, tracking=0.1)
            self.text(value, x + 18, y + 50, 15, face, t.ink)
        return w

    # -- output ---------------------------------------------------------------
    def render(self) -> str:
        glyph_defs = "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in sorted(self._glyphs.items()))
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" '
            f'width="{self.width}" height="{self.height}" role="img" aria-labelledby="title">'
            f'<title id="title">{escape(self.title)}</title>'
            f'<style>{"".join(self._css)}</style>'
            f'<defs>{"".join(self._defs)}{glyph_defs}</defs>'
            f'{"".join(self._body)}</svg>\n'
        )
