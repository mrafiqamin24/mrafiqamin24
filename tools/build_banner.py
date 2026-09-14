"""Render the profile banner: a paper sheet (light) and a blueprint sheet (dark).

    python tools/build_banner.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from drawing import MOTION_CSS, THEMES, THICK, Drawing, Theme, measure  # noqa: E402

WIDTH, HEIGHT = 1200, 400
ZONE = 22
LEFT = THICK + ZONE + 40
RIGHT_MARGIN = 40
TITLE_BLOCK_Y = 332

NAME = "MUHAMMAD RAFIQ AMIN"
LABEL = "PROFILE · WEST KALIMANTAN, INDONESIA"
DIMENSION = "8+ PRODUCTS BUILT"
ROLE = "Full-stack developer — web, mobile & self-hosted infrastructure"
STACK = ["TYPESCRIPT", "NEXT.JS", "LARAVEL", "FLUTTER", "MYSQL", "PROXMOX"]
TITLE = (
    "Muhammad Rafiq Amin, full-stack developer from West Kalimantan, Indonesia. "
    "Web, mobile and self-hosted infrastructure."
)


def render(theme: Theme) -> str:
    t = theme
    d = Drawing(WIDTH, HEIGHT, t, TITLE)
    d.style(MOTION_CSS)
    d.sheet(zone=ZONE, columns=8, rows=4)

    d.text(LABEL, LEFT, 78, 14, "bold", t.ink2, tracking=0.1)

    size = 78
    while measure(NAME, size, "display", -0.03) > WIDTH - LEFT - RIGHT_MARGIN:
        size -= 2
    name_width = d.text(NAME, LEFT, 158, size, "display", t.ink, tracking=-0.03)
    d.dimension(LEFT, LEFT + name_width, 192, 170, DIMENSION)

    d.text(ROLE, LEFT, 262, 27, "semi", t.ink)
    d.chips(STACK, LEFT, 284)

    d.title_block(
        TITLE_BLOCK_Y,
        [
            (None, "MRA", "monob"),
            ("Portfolio", "portfolio.ownertech.id", "semi"),
            ("Based in", "Kalimantan Barat, Indonesia", "semi"),
        ],
        x0=THICK + ZONE,
        x1=WIDTH - THICK,
        trailing=[
            ("Focus", "Products for local businesses", "semi"),
            ("Sheet", "01 / 01", "mono"),
        ],
    )
    return d.render()


def main() -> None:
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for theme in THEMES:
        out = assets / f"banner-{theme.name}.svg"
        out.write_text(render(theme), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
