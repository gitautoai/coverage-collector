#!/usr/bin/env python3
"""
Coverage Collector - Main entry point
"""

import json
import sys
import os
from dotenv import load_dotenv
from src.get_top_repos import get_top_repos
from src.extract_coverage import extract_coverage_smart
from src.models import CoverageResult, RepoInfo

# Load environment variables from .env file
load_dotenv()


def load_existing_coverage() -> set[str]:
    """Load existing coverage data and return set of repo names that already have coverage"""
    coverage_file = "coverage_results.json"
    if not os.path.exists(coverage_file):
        return set()

    try:
        with open(coverage_file, "r", encoding="utf-8") as f:
            existing_results = json.load(f)
            return {result["repo"] for result in existing_results}
    except (json.JSONDecodeError, KeyError, IOError):
        return set()


def main():
    """Main entry point"""
    # Parse command line arguments
    num_repos = 5  # Default

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--repo":
            if i + 1 >= len(sys.argv):
                print("Error: --repo requires a repository name")
                sys.exit(1)
            repo_name = sys.argv[i + 1]
            if "/" not in repo_name:
                print("Error: repo format should be 'owner/name'")
                sys.exit(1)
            owner, name = repo_name.split("/", 1)
            test_repo = RepoInfo(
                owner=owner,
                name=name,
                stars=0,
                language="Unknown",
                clone_url=f"https://github.com/{repo_name}.git",
            )
            print(f"Testing single repo: {repo_name}")
            result = extract_coverage_smart(test_repo)
            if result.coverage_percentage is not None:
                print(f"✓ Success! Coverage: {result.coverage_percentage:.1f}%")
            else:
                print(f"✗ Error: {result.error}")
            return
        elif arg == "--count":
            if i + 1 >= len(sys.argv):
                print("Error: --count requires a number")
                sys.exit(1)
            try:
                num_repos = int(sys.argv[i + 1])
                i += 1
            except ValueError:
                print(f"Error: '{sys.argv[i + 1]}' is not a valid number for --count")
                sys.exit(1)
        elif arg.isdigit():
            # Backward compatibility - first number is count
            num_repos = int(arg)
        else:
            print(f"Error: Unknown argument '{arg}'")
            sys.exit(1)
        i += 1

    print(f"Coverage Collector - Processing top {num_repos} GitHub repos\n")

    # Load existing coverage data
    existing_coverage = load_existing_coverage()
    if existing_coverage:
        print(
            f"📋 Found existing coverage data for {len(existing_coverage)} repositories"
        )

    # Calculate starting rank - start from where we left off
    start_rank = len(existing_coverage) + 1

    # Skip known problematic repos
    skip_list = [
        "freeCodeCamp/freeCodeCamp",  # ESLint dependency conflicts
        "EbookFoundation/free-programming-books",  # Documentation, no tests
        "public-apis/public-apis",  # API list, no tests
        "kamranahmedse/developer-roadmap",  # Learning paths, no tests
        "donnemartin/system-design-primer",  # Educational content
        "vinta/awesome-python",  # Curated list
        # Documentation and educational repos (not actual code projects)
        "Snailclimb/JavaGuide",  # Documentation
        "521xueweihan/HelloGitHub",  # Curation list
        "airbnb/javascript",  # Style guide
        "avelino/awesome-go",  # Awesome list
        "f/awesome-chatgpt-prompts",  # Prompts collection
        "yangshun/tech-interview-handbook",  # Interview guide
        "Chalarangelo/30-seconds-of-code",  # Code snippets
        "ryanmcdermott/clean-code-javascript",  # Style guide
        "microsoft/Web-Dev-For-Beginners",  # Educational content
        "jaywcjlove/awesome-mac",  # Awesome list
        "GrowingGit/GitHub-Chinese-Top-Charts",  # Statistics/charts
        "krahets/hello-algo",  # Algorithm tutorials
        "bregman-arie/devops-exercises",  # Exercises
        "MisterBooo/LeetCodeAnimation",  # Educational content
        "doocs/advanced-java",  # Documentation
        "fighting41love/funNLP",  # Resource collection
        "josephmisiti/awesome-machine-learning",  # Awesome list
        "danielmiessler/SecLists",  # Security lists
    ]

    # Get top repos starting from our position
    print(
        f"🔍 Searching GitHub starting from rank {start_rank} for {num_repos} repositories..."
    )
    repos = get_top_repos(
        count=num_repos * 3,
        skip_repos=skip_list,
        prefer_code_langs=True,
        start_rank=start_rank,
    )
    print(f"\n📊 Found {len(repos)} code repositories")

    # Filter repos: skip existing coverage data
    repos_to_process = []
    skipped_count = 0

    for repo in repos:
        repo_name = f"{repo.owner}/{repo.name}"
        if repo_name in existing_coverage:
            skipped_count += 1
            print(f"⏭️  Skipping {repo_name} (already has coverage data)")
        else:
            repos_to_process.append(repo)

        if len(repos_to_process) >= num_repos:
            break

    if skipped_count > 0:
        print(f"\n🔄 Skipped {skipped_count} repositories with existing coverage data")

    # Show which repos we'll analyze
    target_repos = repos_to_process[:num_repos]
    print(f"\n🎯 Will analyze these {len(target_repos)} repositories:")
    for i, repo in enumerate(target_repos, 1):
        print(f"  {i}. {repo.owner}/{repo.name} ({repo.stars:,} ⭐, {repo.language})")

    print("\n🚀 Starting coverage analysis...\n")

    # Collect coverage
    results: list[CoverageResult] = []
    for i, repo in enumerate(target_repos, 1):
        print(
            f"[{i}/{len(target_repos)}] Processing {repo.owner}/{repo.name} ({repo.stars:,} stars, {repo.language})..."
        )
        result = extract_coverage_smart(repo)
        results.append(result)

        if result.coverage_percentage is not None:
            print(f"  ✓ Coverage: {result.coverage_percentage:.1f}%")
        else:
            print(f"  ✗ Error: {result.error}")

    # Save results (append to existing data)
    if results:
        # Load existing results
        all_results = []
        if os.path.exists("coverage_results.json"):
            try:
                with open("coverage_results.json", "r", encoding="utf-8") as f:
                    all_results = json.load(f)
            except (json.JSONDecodeError, IOError):
                all_results = []

        # Add new results
        new_results = [
            {
                "repo": f"{r.repo.owner}/{r.repo.name}",
                "url": r.url,
                "stars": r.repo.stars,
                "language": r.repo.language,
                "coverage": r.coverage_percentage,
                "total_lines": r.total_lines,
                "source": r.source,
                "error": r.error,
                "timestamp": r.timestamp,
            }
            for r in results
        ]
        all_results.extend(new_results)

        # Save combined results
        with open("coverage_results.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

        print(f"\nAdded {len(new_results)} new results to coverage_results.json")
    else:
        print("\nNo new results to save")

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
