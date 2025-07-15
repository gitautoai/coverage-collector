#!/usr/bin/env python3
"""
Coverage Collector - Main entry point
"""

import json
import sys
from src.get_top_repos import get_top_repos
from src.run_coverage import run_coverage
from src.models import CoverageResult, RepoInfo


def main():
    """Main entry point"""
    # Check for --repo flag for single repo testing
    if len(sys.argv) > 2 and sys.argv[1] == "--repo":
        repo_name = sys.argv[2]
        if "/" not in repo_name:
            print("Error: repo format should be 'owner/name'")
            sys.exit(1)
        owner, name = repo_name.split("/", 1)
        test_repo = RepoInfo(owner=owner, name=name, stars=0, language="Unknown", clone_url=f"https://github.com/{repo_name}.git")
        print(f"Testing single repo: {repo_name}")
        result = run_coverage(test_repo)
        if result.coverage_percentage is not None:
            print(f"✓ Success! Coverage: {result.coverage_percentage:.1f}%")
        else:
            print(f"✗ Error: {result.error}")
        return

    # Get number of repos to process from command line argument
    num_repos = 5  # Default
    if len(sys.argv) > 1:
        try:
            num_repos = int(sys.argv[1])
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid number")
            sys.exit(1)

    print(f"Coverage Collector - Processing top {num_repos} GitHub repos\n")

    # Skip known problematic repos
    skip_list = [
        "freeCodeCamp/freeCodeCamp",  # ESLint dependency conflicts
        "EbookFoundation/free-programming-books",  # Documentation, no tests
        "public-apis/public-apis",  # API list, no tests
        "kamranahmedse/developer-roadmap",  # Learning paths, no tests
        "donnemartin/system-design-primer",  # Educational content
        "vinta/awesome-python",  # Curated list
    ]

    # Get top repos
    print("🔍 Searching GitHub for top repositories with code languages...")
    repos = get_top_repos(count=100, skip_repos=skip_list, prefer_code_langs=True)
    print(f"\n📊 Found {len(repos)} code repositories")

    # Show which repos we'll analyze
    target_repos = repos[:num_repos]
    print(f"\n🎯 Will analyze these {len(target_repos)} repositories:")
    for i, repo in enumerate(target_repos, 1):
        print(f"  {i}. {repo.owner}/{repo.name} ({repo.stars:,} ⭐, {repo.language})")

    print("\n🚀 Starting coverage analysis...\n")

    # Collect coverage
    results: list[CoverageResult] = []
    for i, repo in enumerate(target_repos, 1):
        print(
            f"[{i}/{num_repos}] Processing {repo.owner}/{repo.name} ({repo.stars:,} stars, {repo.language})..."
        )
        result = run_coverage(repo)
        results.append(result)

        if result.coverage_percentage is not None:
            print(f"  ✓ Coverage: {result.coverage_percentage:.1f}%")
        else:
            print(f"  ✗ Error: {result.error}")

    # Save results
    with open("coverage_results.json", "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "repo": f"{r.repo.owner}/{r.repo.name}",
                    "stars": r.repo.stars,
                    "language": r.repo.language,
                    "coverage": r.coverage_percentage,
                    "test_command": r.test_command,
                    "error": r.error,
                    "timestamp": r.timestamp,
                }
                for r in results
            ],
            f,
            indent=2,
        )

    print("\nResults saved to coverage_results.json")

    # Summary
    successful = [r for r in results if r.coverage_percentage is not None]
    print(
        f"\nSummary: {len(successful)}/{len(results)} repositories analyzed successfully"
    )
    if successful:
        coverage_values = [
            r.coverage_percentage
            for r in successful
            if r.coverage_percentage is not None
        ]
        avg_coverage = sum(coverage_values) / len(coverage_values)
        print(f"Average coverage: {avg_coverage:.1f}%")


if __name__ == "__main__":
    main()
