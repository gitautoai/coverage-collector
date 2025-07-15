import os

import requests

from models import RepoInfo


def get_top_repos(
    count: int = 100,
    min_stars: int = 1000,
    skip_repos: list[str] | None = None,
    prefer_code_langs: bool = True,
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
    page = 1

    while len(repos) < count:
        url = f"https://api.github.com/search/repositories?q=stars:>{min_stars}&sort=stars&order=desc&page={page}&per_page=100"
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            raise ValueError(f"GitHub API error: {response.status_code}")

        data = response.json()
        for item in data["items"]:
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
