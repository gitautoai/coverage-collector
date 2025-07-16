import os

import requests
from dotenv import load_dotenv

from src.models import RepoInfo

# Load environment variables from .env file
load_dotenv()


def get_top_repos(
    count: int = 100,
    min_stars: int = 1000,
    skip_repos: list[str] | None = None,
    prefer_code_langs: bool = True,
    start_rank: int = 1,
) -> list[RepoInfo]:
    """Fetch top repos by stars from GitHub"""
    if skip_repos is None:
        skip_repos = []

    # Languages likely to have test suites
    code_languages = {
        "JavaScript",
        "TypeScript",
        "Python",
        "Java",
        "Go",
        "Rust",
        "C++",
        "C#",
        "Ruby",
        "PHP",
        "Kotlin",
        "Swift",
        "Scala",
        "Dart",
        "C",
    }

    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    repos: list[RepoInfo] = []
    # Calculate starting page based on start_rank
    start_page = ((start_rank - 1) // 100) + 1
    page = start_page
    items_to_skip = (start_rank - 1) % 100

    while len(repos) < count:
        # If we're beyond page 10 or start_rank > 1000, use different search strategies
        if page > 10 or start_rank > 1000:
            # Use language-specific searches with lower thresholds to find different repos
            languages = [
                "JavaScript",
                "Python",
                "TypeScript",
                "Java",
                "Go",
                "Rust",
                "C++",
                "C#",
                "PHP",
                "Ruby",
            ]
            lang_idx = (
                (page - 11) % len(languages)
                if page > 10
                else (start_rank // 100) % len(languages)
            )
            search_lang = languages[lang_idx]
            search_stars = max(500, 5000 - (page - 10) * 500)
            url = f"https://api.github.com/search/repositories?q=language:{search_lang}+stars:{search_stars}..{search_stars + 2000}&sort=stars&order=desc&page=1&per_page=100"
        else:
            url = f"https://api.github.com/search/repositories?q=stars:>{min_stars}&sort=stars&order=desc&page={page}&per_page=100"

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(
                f"GitHub API error: {response.status_code}, trying different search..."
            )
            page += 1
            if page > 20:  # Prevent infinite loop
                break
            continue

        data = response.json()
        items = data["items"]

        # Skip items on the first page if we have an offset
        if page == start_page and items_to_skip > 0:
            items = items[items_to_skip:]
            items_to_skip = 0  # Only skip on first page

        for item in items:
            repo_full_name = f"{item['owner']['login']}/{item['name']}"
            language = item.get("language")
            stars = item["stargazers_count"]

            # Skip repos in the skip list
            if repo_full_name in skip_repos:
                print(
                    f"⏭️  Skipping {repo_full_name} ({stars:,} ⭐, {language}) - in skip list"
                )
                continue

            # If prefer_code_langs is True, skip non-code languages
            if prefer_code_langs and language not in code_languages:
                print(
                    f"⏭️  Skipping {repo_full_name} ({stars:,} ⭐, {language}) - not a code language"
                )
                continue

            print(f"✅ Found {repo_full_name} ({stars:,} ⭐, {language})")
            repos.append(
                RepoInfo(
                    owner=item["owner"]["login"],
                    name=item["name"],
                    stars=stars,
                    language=language or "Unknown",
                    clone_url=item["clone_url"],
                )
            )

        if len(data["items"]) < 100:
            break
        page += 1

    return repos[:count]
