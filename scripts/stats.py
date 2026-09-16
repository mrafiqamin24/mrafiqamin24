#!/usr/bin/env python3
"""Render the activity card (light + dark) from the GitHub GraphQL API, in the
same visual system as mra1.my.id: white paper, one ink, Mona Sans as paths.

Needs fontTools (pip install fonttools) for the text outlines; see monatext.py.

Token: STATS_TOKEN if set (a read-only token that can see private repositories),
otherwise GITHUB_TOKEN. GITHUB_TOKEN sees public repositories only, so the language
mix then falls back to the last snapshot taken by a token that could see everything.
Contribution counts come from the public profile either way; they include private
work only when "Include private contributions on my profile" is switched on.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from monatext import THEMES, text, text_path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SNAPSHOT = ASSETS / "languages.json"
WIDTH, HEIGHT = 1200, 300
PAD = 40
TOP_LANGUAGES = 4

QUERY = """
query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      nodes {
        isPrivate
        languages(first: 20) { edges { size node { name } } }
      }
    }
  }
}
"""


def fetch(token: str, login: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-activity-card"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    user = (payload.get("data") or {}).get("user")
    if payload.get("errors") or not user:
        raise RuntimeError(f"GitHub API returned no user data: {payload.get('errors')}")
    return user


def streaks(days: list[tuple[str, int]]) -> tuple[int, int, int]:
    """Active days, longest run, and the run that is still going."""
    active = sum(1 for _, count in days if count)
    longest = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    index = len(days) - 1
    if index >= 0 and days[index][1] == 0:  # today is not over yet
        index -= 1
    current = 0
    while index >= 0 and days[index][1]:
        current += 1
        index -= 1
    return active, longest, current


def language_totals(user: dict, today: str) -> tuple[dict[str, int], str | None]:
    nodes = user["repositories"]["nodes"]
    totals: dict[str, int] = {}
    for node in nodes:
        for edge in node["languages"]["edges"]:
            name = edge["node"]["name"]
            totals[name] = totals.get(name, 0) + edge["size"]
    if any(node["isPrivate"] for node in nodes):
        snapshot = {"date": today, "bytes": dict(sorted(totals.items()))}
        SNAPSHOT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        return totals, None
    if SNAPSHOT.exists():
        snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        return snapshot["bytes"], snapshot["date"]
    return totals, None


def shares(totals: dict[str, int]) -> list[tuple[str, float]]:
    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda item: -item[1])
    parts = [(name, size / total) for name, size in ranked[:TOP_LANGUAGES]]
    rest = sum(size for _, size in ranked[TOP_LANGUAGES:]) / total
    if rest > 0:
        parts.append(("Other", rest))
    return parts


def render(t: dict, name: str, stats: dict) -> str:
    parts = stats["languages"]
    mix = ", ".join(f"{lang} {share * 100:.0f}%" for lang, share in parts)
    title = (
        f"GitHub activity, last 12 months: {stats['contributions']:,} contributions, "
        f"{stats['active']} active days, longest streak {stats['longest']} days, "
        f"current streak {stats['current']} days. Languages: {mix}."
    )
    # one ink in five tints for the language bar; the first segment is the ink itself
    tints = ["#111318", "#5b6068", "#a4a9b3", "#d3d6db", "#e6e8eb"] if name == "light" else ["#ffffff", "#a4a9b3", "#6b7079", "#3a3f47", "#2a2e36"]

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="t">',
        f'<title id="t">{title}</title>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="10" fill="{t["bg"]}" stroke="{t["rule2"]}"/>',
    ]
    out.append(text(PAD, 48, "Activity, last 12 months", 17, 600, t["ink"])[0])
    out.append(text(WIDTH - PAD, 48, f"Updated {stats['updated']}", 14, 500, t["ink2"], anchor="end")[0])
    out.append(f'<line x1="{PAD}" y1="66" x2="{WIDTH - PAD}" y2="66" stroke="{t["rule"]}"/>')

    figures = [
        ("Contributions", f"{stats['contributions']:,}"),
        ("Active days", str(stats["active"])),
        ("Longest streak, days", str(stats["longest"])),
        ("Current streak, days", str(stats["current"])),
    ]
    cell = (WIDTH - 2 * PAD) / len(figures)
    for i, (key, value) in enumerate(figures):
        x = PAD + cell * i
        if i:
            out.append(f'<line x1="{x:.0f}" y1="84" x2="{x:.0f}" y2="160" stroke="{t["rule"]}"/>')
        out.append(text(x + (18 if i else 0), 100, key, 14, 500, t["ink2"])[0])
        out.append(text(x + (18 if i else 0), 150, value, 44, 600, t["ink"])[0])
    out.append(f'<line x1="{PAD}" y1="176" x2="{WIDTH - PAD}" y2="176" stroke="{t["rule"]}"/>')

    caption = "Languages across all my repositories"
    if stats["languages_as_of"]:
        caption += f", as of {stats['languages_as_of']}"
    out.append(text(PAD, 206, caption, 14, 500, t["ink2"])[0])

    bar_x, bar_y, bar_w, bar_h = PAD, 220, WIDTH - 2 * PAD, 14
    out.append(f'<clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="7"/></clipPath>')
    x = float(bar_x)
    out.append('<g clip-path="url(#bar)">')
    for i, (_, share) in enumerate(parts):
        w = bar_w * share
        out.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" fill="{tints[i]}"/>')
        x += w
    out.append("</g>")

    x = float(PAD)
    for i, (lang, share) in enumerate(parts):
        out.append(f'<rect x="{x:.1f}" y="258" width="12" height="12" rx="3" fill="{tints[i]}" stroke="{t["rule2"]}"/>')
        x += 20
        g, w = text(x, 269, lang, 15, 600, t["ink"])
        out.append(g)
        x += w + 8
        g, w = text(x, 269, f"{share * 100:.0f}%", 14, 500, t["ink2"])
        out.append(g)
        x += w + 28
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    token = os.environ.get("STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    login = os.environ.get("STATS_LOGIN") or os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not token or not login:
        sys.exit("Set STATS_LOGIN and GITHUB_TOKEN (or STATS_TOKEN).")

    user = fetch(token, login)
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = sorted(
        (day["date"], day["contributionCount"])
        for week in calendar["weeks"]
        for day in week["contributionDays"]
        if day["date"] <= today
    )
    active, longest, current = streaks(days)
    totals, as_of = language_totals(user, today)

    stats = {
        "contributions": calendar["totalContributions"],
        "active": active,
        "longest": longest,
        "current": current,
        "languages": shares(totals),
        "languages_as_of": as_of,
        "updated": today,
    }
    ASSETS.mkdir(exist_ok=True)
    for name, theme in THEMES.items():
        (ASSETS / f"stats-{name}.svg").write_text(render(theme, name, stats), encoding="utf-8")
    mix = ", ".join(f"{lang} {share * 100:.0f}%" for lang, share in stats["languages"])
    print(
        f"contributions={stats['contributions']} active={active} longest={longest} "
        f"current={current} languages=[{mix}] as_of={as_of or 'live'}"
    )


if __name__ == "__main__":
    main()
