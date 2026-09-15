"""Render the profile banner in the same visual system as mra1.my.id:
white paper, one ink, one green dot for what is live, Mona Sans as paths.

    python tools/build_banner.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from monatext import THEMES, text, text_path  # noqa: E402

WIDTH, HEIGHT = 1200, 420
NAME = "Muhammad Rafiq Amin"
ROLE = "Full-Stack Web Developer · DevOps Engineer"
LEAD = ["I build web and mobile products for real businesses", "and run the production server they live on."]
META = "D3 IT student · West Kalimantan, Indonesia · open to internship, freelance, full-time"
RELEASES = [("Sep 2026", "Crypt-Man", "Live"), ("Sep 2026", "Production server", "Live"), ("Aug 2026", "MR Hotel", "Live")]
BUTTON = "mra1.my.id"
TITLE = ("Muhammad Rafiq Amin, full-stack web developer and DevOps engineer from West Kalimantan, Indonesia. "
         "Builds web and mobile products for real businesses and runs the production server they live on. "
         "Latest releases: Crypt-Man, production server, MR Hotel, all live. Portfolio at mra1.my.id.")


def render(t: dict) -> str:
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="t d">',
        f'<title id="t">{TITLE}</title>',
        '<desc id="d">Banner in the style of the portfolio site: name, role, one sentence, and the three latest releases with a green Live dot.</desc>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="10" fill="{t["bg"]}" stroke="{t["rule2"]}"/>',
    ]
    left, y = 56, 118
    out.append(text(left, y, NAME, 62, 600, t["ink"])[0])
    out.append(text(left, y + 44, ROLE, 24, 500, t["ink2"])[0])
    out.append(text(left, y + 104, LEAD[0], 23, 450, t["ink"])[0])
    out.append(text(left, y + 136, LEAD[1], 23, 450, t["ink"])[0])
    out.append(text(left, y + 176, META, 15, 400, t["ink2"])[0])

    # one action: the whole image links to the portfolio
    by, pad = 340, 20
    d, bw = text_path(BUTTON, 16, 600)
    out.append(f'<rect x="{left}" y="{by}" width="{bw + pad * 2 + 22:.0f}" height="44" rx="6" fill="{t["btn"]}"/>')
    out.append(f'<g fill="{t["btntext"]}" transform="translate({left + pad} {by + 28})">{d}</g>')
    ax = left + pad + bw + 10
    out.append(f'<path d="M{ax} {by + 16} l6 6 l-6 6 M{ax - 6} {by + 22} h12" fill="none" stroke="{t["btntext"]}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')

    # right: the three latest releases as the site's log rows
    rx, ry = 800, 110
    out.append(text(rx, ry - 44, "Latest releases", 15, 600, t["ink2"])[0])
    out.append(f'<line x1="{rx}" y1="{ry - 28}" x2="{WIDTH - 56}" y2="{ry - 28}" stroke="{t["rule"]}"/>')
    for i, (when, what, status) in enumerate(RELEASES):
        yy = ry + i * 74
        out.append(text(rx, yy, when, 14, 500, t["ink2"])[0])
        g, w = text(rx, yy + 30, what, 22, 600, t["ink"])
        out.append(g)
        px = rx + w + 14
        d, pw = text_path(status, 13, 500)
        out.append(f'<rect x="{px:.1f}" y="{yy + 13}" width="{pw + 34:.1f}" height="24" rx="12" fill="{t["bg"]}" stroke="{t["liveborder"]}"/>')
        out.append(f'<circle cx="{px + 12:.1f}" cy="{yy + 25}" r="3.5" fill="{t["dot"]}"/>')
        out.append(f'<g fill="{t["live"]}" transform="translate({px + 22:.1f} {yy + 29.5})">{d}</g>')
        out.append(f'<line x1="{rx}" y1="{yy + 46}" x2="{WIDTH - 56}" y2="{yy + 46}" stroke="{t["rule"]}"/>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for name, theme in THEMES.items():
        out = assets / f"banner-{name}.svg"
        out.write_text(render(theme), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
