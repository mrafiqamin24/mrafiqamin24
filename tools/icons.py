"""Download monochrome brand marks from Simple Icons (CC0-1.0) for the tech-stack sheet.

    python tools/icons.py [simple-icons version]

Writes scripts/icons.json. The version is pinned in that file, so the drawing only
changes when this script is run again on purpose. A technology without a mark in
Simple Icons is drawn as a mono monogram instead.
"""

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_stack import STACK  # noqa: E402

HEADERS = {"User-Agent": "profile-readme-icons"}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as response:
        return response.read()


def main() -> None:
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        version = json.loads(get("https://registry.npmjs.org/simple-icons/latest"))["version"]
    icons: dict[str, str] = {}
    missing: list[str] = []
    for _, items in STACK:
        for slug, _label in items:
            url = f"https://cdn.jsdelivr.net/npm/simple-icons@{version}/icons/{slug}.svg"
            try:
                svg = get(url).decode("utf-8")
            except urllib.error.HTTPError:
                missing.append(slug)
                continue
            match = re.search(r'<path d="([^"]+)"', svg)
            if match:
                icons[slug] = match.group(1)
            else:
                missing.append(slug)
    out = ROOT / "scripts" / "icons.json"
    payload = {"source": f"simple-icons@{version} (CC0-1.0)", "icons": icons}
    out.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"simple-icons@{version}: {len(icons)} marks, monogram for: {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    main()
