"""
Auto-updates the TOP-REPOS section in README.md
with the user's most-forked public repositories.

Triggered by GitHub Actions daily.
"""

import os
import re
import requests

# ── Config ────────────────────────────────────────────────
USERNAME   = os.environ.get("GITHUB_USERNAME", "mr-afrix")
TOKEN      = os.environ.get("GITHUB_TOKEN", "")
MAX_REPOS  = 6          # how many repos to show
README     = "README.md"
START_TAG  = "<!-- TOP-REPOS:START -->"
END_TAG    = "<!-- TOP-REPOS:END -->"
# ──────────────────────────────────────────────────────────

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}

def fetch_repos():
    """Fetch all public repos for the user."""
    all_repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?type=public&per_page=100&page={page}"
        )
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_repos.extend(batch)
        page += 1
    return all_repos

def build_table(repos):
    """Build a markdown table of top repos sorted by forks, then stars."""
    # Skip the profile repo itself from the ranking
    filtered = [r for r in repos if r["name"] != USERNAME]

    # Sort: primary = forks desc, secondary = stars desc
    sorted_repos = sorted(
        filtered,
        key=lambda r: (r.get("forks_count", 0), r.get("stargazers_count", 0)),
        reverse=True,
    )

    top = sorted_repos[:MAX_REPOS]

    # If the user has fewer repos than MAX_REPOS, just show what we have
    if not top:
        return "| — | *No public repositories yet.* | — | — |\n"

    header = (
        "| 📦 Project | 📝 Description | ⭐ Stars | 🍴 Forks |\n"
        "|:-----------|:--------------|:-------:|:-------:|\n"
    )
    rows = ""
    for repo in top:
        name  = repo["name"]
        url   = repo["html_url"]
        desc  = (repo.get("description") or "No description provided.").strip()
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        lang  = repo.get("language") or ""
        lang_badge = f"![{lang}](https://img.shields.io/badge/-{lang}-555?style=flat-square)" if lang else ""
        rows += f"| [**{name}**]({url}) {lang_badge} | {desc} | {stars} | {forks} |\n"

    return header + rows

def update_readme(table_md):
    """Replace the section between START_TAG and END_TAG in README.md."""
    with open(README, "r", encoding="utf-8") as f:
        content = f.read()

    new_section = f"{START_TAG}\n\n{table_md}\n{END_TAG}"
    pattern = re.escape(START_TAG) + r".*?" + re.escape(END_TAG)
    updated = re.sub(pattern, new_section, content, flags=re.DOTALL)

    if updated == content:
        print("ℹ️  No changes detected — README is already up to date.")
        return

    with open(README, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"✅  README updated with top {MAX_REPOS} repos.")

def main():
    print(f"🔍  Fetching repos for @{USERNAME} ...")
    repos = fetch_repos()
    print(f"    Found {len(repos)} public repo(s).")

    table = build_table(repos)
    update_readme(table)

if __name__ == "__main__":
    main()
