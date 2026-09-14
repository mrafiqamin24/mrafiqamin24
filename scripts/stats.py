#!/usr/bin/env python3
"""Render the activity card (light + dark) from the GitHub GraphQL API.

Standard library only, so the workflow needs nothing but a Python runtime.

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

from drawing import HAIR, MEDIUM, THEMES, THICK, Drawing, Theme, fmt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SNAPSHOT = ASSETS / "languages.json"
WIDTH, HEIGHT = 1200, 310
PAD = 28
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


def define_hatches(d: Drawing, t: Theme) -> list[str]:
    """Section hatching instead of colour: solid dimension blue, then ink hatches."""
    d.define(
        f'<pattern id="hatch-diagonal" width="7" height="7" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(45)"><path d="M0 0V7" stroke="{t.ink}" stroke-width="1.5"/></pattern>'
    )
    d.define(
        f'<pattern id="hatch-cross" width="7" height="7" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(45)"><path d="M0 0V7M0 0H7" stroke="{t.ink}" stroke-width="1"/></pattern>'
    )
    d.define(
        f'<pattern id="hatch-dots" width="6" height="6" patternUnits="userSpaceOnUse">'
        f'<circle cx="3" cy="3" r="1.1" fill="{t.ink}"/></pattern>'
    )
    return [t.dim, "url(#hatch-diagonal)", "url(#hatch-cross)", "url(#hatch-dots)", "none"]


def render(t: Theme, stats: dict) -> str:
    parts = stats["languages"]
    mix = ", ".join(f"{name} {share * 100:.0f}%" for name, share in parts)
    title = (
        f"GitHub activity, last 12 months: {stats['contributions']:,} contributions, "
        f"{stats['active']} active days, longest streak {stats['longest']} days, "
        f"current streak {stats['current']} days. Languages: {mix}."
    )
    d = Drawing(WIDTH, HEIGHT, t, title)
    d.sheet()
    fills = define_hatches(d, t)
    left, right = THICK, WIDTH - THICK

    d.text("ACTIVITY · LAST 12 MONTHS", PAD, 40, 14, "bold", t.ink, tracking=0.1)
    d.text(f"UPDATED {stats['updated']}", WIDTH - PAD, 40, 13, "mono", t.ink2, anchor="end")
    d.line(left, 62, right, 62, t.ink, MEDIUM)

    figures = [
        ("Contributions", f"{stats['contributions']:,}"),
        ("Active days", str(stats["active"])),
        ("Longest streak · days", str(stats["longest"])),
        ("Current streak · days", str(stats["current"])),
    ]
    cell = (right - left) / len(figures)
    for i, (key, value) in enumerate(figures):
        x = left + cell * i
        if i:
            d.line(x, 62, x, 176, t.ink, MEDIUM)
        d.text(key.upper(), x + PAD, 94, 12, "bold", t.ink2, tracking=0.1)
        d.text(value, x + PAD, 152, 46, "monob", t.ink)
    d.line(left, 176, right, 176, t.ink, MEDIUM)

    caption = "LANGUAGES · ALL MY REPOSITORIES"
    if stats["languages_as_of"]:
        caption += f" · AS OF {stats['languages_as_of']}"
    d.text(caption, PAD, 208, 12, "bold", t.ink2, tracking=0.1)

    bar_x, bar_y, bar_w, bar_h = PAD, 222, WIDTH - 2 * PAD, 26
    x = bar_x
    for i, (_, share) in enumerate(parts):
        w = bar_w * share
        d.rect(x, bar_y, w, bar_h, fill=fills[i])
        if i:
            d.line(x, bar_y, x, bar_y + bar_h, t.ink, HAIR)
        x += w
    d.rect(bar_x, bar_y, bar_w, bar_h, stroke=t.ink, width=MEDIUM)

    x = PAD
    for i, (name, share) in enumerate(parts):
        d.rect(x, 268, 16, 16, fill=fills[i], stroke=t.ink, width=HAIR)
        x += 24
        x += d.text(name, x, 282, 15, "semi", t.ink) + 8
        x += d.text(f"{share * 100:.0f}%", x, 282, 14, "mono", t.ink2) + 30
    return d.render()


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
    for theme in THEMES:
        (ASSETS / f"stats-{theme.name}.svg").write_text(render(theme, stats), encoding="utf-8")
    mix = ", ".join(f"{name} {share * 100:.0f}%" for name, share in stats["languages"])
    print(
        f"contributions={stats['contributions']} active={active} longest={longest} "
        f"current={current} languages=[{mix}] as_of={as_of or 'live'}"
    )


if __name__ == "__main__":
    main()
