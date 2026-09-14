"""Render the tech-stack sheet in two layouts (desktop, phone) and two themes.

    python tools/icons.py        # once, or whenever STACK gains a technology
    python tools/build_stack.py

Every entry is taken from the repositories themselves (package.json, composer.json,
pubspec.yaml, Dockerfiles, CI workflows) or from the self-hosted server; nothing is
listed that is not actually in use.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from drawing import HAIR, MEDIUM, THEMES, THICK, Drawing, Theme, fmt, measure  # noqa: E402

STACK: list[tuple[str, list[tuple[str, str]]]] = [
    ("Frontend", [
        ("typescript", "TypeScript"), ("react", "React"), ("nextdotjs", "Next.js"),
        ("tailwindcss", "Tailwind CSS"), ("vite", "Vite"), ("inertia", "Inertia"), ("threedotjs", "Three.js"),
    ]),
    ("Backend", [
        ("php", "PHP"), ("laravel", "Laravel"), ("filament", "Filament"), ("nodedotjs", "Node.js"),
        ("prisma", "Prisma"), ("authjs", "Auth.js"), ("zod", "Zod"), ("googleappsscript", "Apps Script"),
    ]),
    ("Mobile", [
        ("flutter", "Flutter"), ("dart", "Dart"), ("riverpod", "Riverpod"), ("sqlite", "SQLite"),
    ]),
    ("Database", [
        ("mysql", "MySQL"), ("redis", "Redis"),
    ]),
    ("Infrastructure", [
        ("proxmox", "Proxmox"), ("debian", "Debian"), ("docker", "Docker"), ("nginx", "Nginx"),
        ("cloudflare", "Cloudflare"), ("tailscale", "Tailscale"), ("wireguard", "WireGuard"),
        ("mikrotik", "MikroTik"), ("githubactions", "GitHub Actions"),
    ]),
    ("Testing", [
        ("vitest", "Vitest"), ("playwright", "Playwright"), ("pest", "Pest"), ("phpunit", "PHPUnit"),
    ]),
]

LAYOUTS = {
    "": {
        "width": 1200, "pad": 28, "label_col": 230, "head": 64, "head_size": 14,
        "chip_h": 40, "icon": 20, "text": 17, "gap": 10, "row_pad": 18, "label_size": 13, "stacked": False,
    },
    "-mobile": {
        "width": 640, "pad": 24, "label_col": 0, "head": 72, "head_size": 18,
        "chip_h": 54, "icon": 28, "text": 23, "gap": 12, "row_pad": 22, "label_size": 17, "stacked": True,
    },
}


def chip_width(label: str, lay: dict) -> float:
    return 12 + lay["icon"] + 10 + measure(label, lay["text"], "semi") + 14


def plan(lay: dict) -> tuple[list[dict], float]:
    """Place every chip first, so the sheet height is known before drawing."""
    width, pad = lay["width"], lay["pad"]
    y = THICK + lay["head"]
    rows = []
    for category, items in STACK:
        top = y
        if lay["stacked"]:
            label_base = top + lay["row_pad"] + lay["label_size"] * 0.72
            line_top = label_base + 16
            x_start = pad
        else:
            label_base = None
            line_top = top + lay["row_pad"]
            x_start = lay["label_col"] + 24
        x = x_start
        chips = []
        for slug, label in items:
            w = chip_width(label, lay)
            if x + w > width - pad and x > x_start:
                x = x_start
                line_top += lay["chip_h"] + lay["gap"]
            chips.append((slug, label, x, line_top, w))
            x += w + lay["gap"]
        bottom = line_top + lay["chip_h"] + lay["row_pad"]
        rows.append({"category": category, "top": top, "bottom": bottom, "label_base": label_base, "chips": chips})
        y = bottom
    return rows, y + THICK


# Drawn as a monogram even when Simple Icons has a mark: at 20px the MySQL dolphin
# and the Filament mark turn into specks. The rest have no mark in Simple Icons.
MONOGRAMS = {
    "authjs": "AJ", "riverpod": "RP", "playwright": "PW", "pest": "PE",
    "phpunit": "PU", "mysql": "MY", "filament": "FI",
}


def monogram(slug: str, label: str) -> str:
    return MONOGRAMS.get(slug) or label[:2].upper()


def render(theme: Theme, lay: dict, icons: dict[str, str]) -> str:
    t = theme
    rows, height = plan(lay)
    total = sum(len(items) for _, items in STACK)
    title = "Tech stack. " + " ".join(
        f"{category}: {', '.join(label for _, label in items)}." for category, items in STACK
    )
    d = Drawing(lay["width"], int(round(height)), t, title)
    d.sheet()
    pad, width = lay["pad"], lay["width"]
    head_y = THICK + lay["head"]

    d.text("TECH STACK", pad, head_y - 24, lay["head_size"], "bold", t.ink, tracking=0.1)
    d.text(
        f"{len(STACK)} GROUPS · {total} TOOLS", width - pad, head_y - 24,
        lay["head_size"] - 1, "mono", t.ink2, anchor="end",
    )
    d.line(THICK, head_y, width - THICK, head_y, t.ink, MEDIUM)
    if not lay["stacked"]:
        d.line(lay["label_col"], head_y, lay["label_col"], height - THICK, t.ink, MEDIUM)

    s = lay["icon"]
    for index, row in enumerate(rows):
        if index:
            d.line(THICK, row["top"], width - THICK, row["top"], t.ink, MEDIUM)
        label = row["category"].upper()
        if lay["stacked"]:
            d.text(label, pad, row["label_base"], lay["label_size"], "bold", t.ink2, tracking=0.1)
        else:
            base = (row["top"] + row["bottom"]) / 2 + lay["label_size"] * 0.36
            d.text(label, pad, base, lay["label_size"], "bold", t.ink2, tracking=0.1)
        for slug, name, x, y, w in row["chips"]:
            d.rect(x, y, w, lay["chip_h"], stroke=t.ink, width=HAIR)
            ix, iy = x + 12, y + (lay["chip_h"] - s) / 2
            if slug in icons and slug not in MONOGRAMS:
                d.add(
                    f'<path fill="{t.ink}" transform="translate({fmt(ix)} {fmt(iy)}) scale({s / 24:.4f})" '
                    f'd="{icons[slug]}"/>'
                )
            else:
                d.rect(ix, iy, s, s, stroke=t.ink, width=HAIR)
                d.text(monogram(slug, name), ix + s / 2, iy + s / 2 + s * 0.45 * 0.36, s * 0.45, "monob", t.ink, anchor="middle")
            d.text(name, ix + s + 10, y + lay["chip_h"] / 2 + lay["text"] * 0.36, lay["text"], "semi", t.ink)
    return d.render()


def main() -> None:
    icons = json.loads((ROOT / "scripts" / "icons.json").read_text(encoding="utf-8"))["icons"]
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for suffix, lay in LAYOUTS.items():
        for theme in THEMES:
            out = assets / f"stack{suffix}-{theme.name}.svg"
            out.write_text(render(theme, lay, icons), encoding="utf-8")
            print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
