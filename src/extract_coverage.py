"""
Extract coverage data from README files and coverage services
"""

import re
from datetime import datetime
from typing import Optional
import os

import requests
from dotenv import load_dotenv

from src.models import RepoInfo, CoverageResult

# Load environment variables from .env file
load_dotenv()


def extract_coverage_from_readme(repo: RepoInfo) -> Optional[float]:
    """Extract coverage percentage from README.md"""
    try:
        # Fetch README from GitHub API
        url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/readme"
        headers = {"Accept": "application/vnd.github.v3.raw"}

        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            return None

        content = response.text.lower()

        # Common coverage badge patterns
        coverage_patterns = [
            # Codecov badge URLs
            r"codecov\.io/.*?(\d+)%",
            r"codecov\.io/.*?(\d+\.\d+)%",
            # Shields.io Codecov badges (need to fetch the actual badge)
            r"img\.shields\.io/codecov/c/github/([^/]+/[^/]+)",
            # Coveralls badge URLs
            r"coveralls\.io/.*?(\d+)%",
            r"coveralls\.io/.*?(\d+\.\d+)%",
            # Generic coverage badges
            r"img\.shields\.io/.*?coverage[/-](\d+)%",
            r"img\.shields\.io/.*?coverage[/-](\d+\.\d+)%",
            # Text patterns
            r"coverage:?\s*(\d+)%",
            r"coverage:?\s*(\d+\.\d+)%",
            r"test coverage:?\s*(\d+)%",
            r"test coverage:?\s*(\d+\.\d+)%",
            r"code coverage:?\s*(\d+)%",
            r"code coverage:?\s*(\d+\.\d+)%",
        ]

        for pattern in coverage_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Special handling for shields.io codecov badges
                if pattern == r"img\.shields\.io/codecov/c/github/([^/]+/[^/]+)":
                    for match in matches:
                        try:
                            # Fetch the actual badge SVG
                            badge_url = (
                                f"https://img.shields.io/codecov/c/github/{match}.svg"
                            )
                            badge_response = requests.get(badge_url, timeout=10)
                            if badge_response.status_code == 200:
                                # Extract percentage from SVG content
                                badge_matches = re.findall(
                                    r">(\d+(?:\.\d+)?)%<", badge_response.text
                                )
                                if badge_matches:
                                    coverage = float(badge_matches[0])
                                    if 0 <= coverage <= 100:
                                        return coverage
                        except Exception:
                            continue
                else:
                    try:
                        coverage = float(matches[0])
                        if 0 <= coverage <= 100:
                            return coverage
                    except ValueError:
                        continue

        return None

    except Exception:
        return None


def extract_coverage_from_coveralls(repo: RepoInfo) -> Optional[float]:
    """Extract coverage from coveralls.io"""
    try:
        url = f"https://coveralls.io/github/{repo.owner}/{repo.name}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=30)
        print(f"    Coveralls URL: {url} (Status: {response.status_code})")
        if response.status_code != 200:
            return None

        content = response.text

        # Look for coverage patterns (broader approach)
        coverage_patterns = [
            # Specific div structure mentioned by user
            r'<div class="coverageText repo-coverage-outline[^"]*"[^>]*>\s*(\d+(?:\.\d+)?)%',
            r'id="repoShowPercentage"[^>]*>\s*(\d+(?:\.\d+)?)%',
            # Simple div with percentage (what we actually found)
            r"<div[^>]*>\s*(\d+(?:\.\d+)?)%\s*</div>",
            # Any element with coverage-related content
            r'class="[^"]*coverage[^"]*"[^>]*>\s*(\d+(?:\.\d+)?)%',
            # Very broad - any percentage that looks like coverage
            r">(\d+(?:\.\d+)?)%<",
            r"(\d+(?:\.\d+)?)%",
        ]

        for pattern in coverage_patterns:
            matches = re.findall(pattern, content)
            if matches:
                for match in matches:
                    try:
                        coverage = float(match)
                        if 0 <= coverage <= 100:
                            # For broad patterns, check if it's in a coverage context
                            if pattern in [r">(\d+(?:\.\d+)?)%<", r"(\d+(?:\.\d+)?)%"]:
                                # Look for coverage-related words nearby
                                coverage_context = re.search(
                                    rf".{{0,100}}(?:coverage|covered|cover).{{0,100}}{re.escape(match)}%|{re.escape(match)}%.{{0,100}}(?:coverage|covered|cover)",
                                    content,
                                    re.IGNORECASE,
                                )
                                if coverage_context:
                                    return coverage
                            else:
                                return coverage
                    except ValueError:
                        continue

        return None

    except Exception:
        return None


def get_repo_lines_of_code(repo: RepoInfo) -> Optional[int]:
    """Get total lines of code from GitHub API using language statistics"""
    try:
        # Get languages breakdown
        url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/languages"
        headers = {}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"

        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            return None

        languages = response.json()

        # GitHub provides bytes, not lines
        # Rough estimation: average 40 bytes per line of code
        total_bytes = sum(languages.values())
        estimated_lines = total_bytes // 40

        return estimated_lines

    except Exception:
        return None


def extract_coverage_smart(repo: RepoInfo) -> CoverageResult:
    """Smart coverage extraction combining multiple sources"""
    timestamp = datetime.now().isoformat()

    # Get total lines of code
    print("  📊 Getting repository size...")
    total_lines = get_repo_lines_of_code(repo)
    if total_lines:
        print(f"  ✓ Estimated {total_lines:,} lines of code")

    # Try README first
    print("  📖 Checking README for coverage...")
    coverage = extract_coverage_from_readme(repo)
    source = "README"

    if coverage is not None:
        print(f"  ✓ Found {coverage}% coverage in README")
        return CoverageResult(
            repo=repo,
            url=f"https://github.com/{repo.owner}/{repo.name}",
            coverage_percentage=coverage,
            total_lines=total_lines,
            source=source,
            error=None,
            timestamp=timestamp,
        )

    # Try Coveralls as fallback
    print("  🔍 Checking Coveralls.io...")
    coverage = extract_coverage_from_coveralls(repo)
    source = "Coveralls.io"

    if coverage is not None:
        print(f"  ✓ Found {coverage}% coverage on Coveralls")
        return CoverageResult(
            repo=repo,
            url=f"https://github.com/{repo.owner}/{repo.name}",
            coverage_percentage=coverage,
            total_lines=total_lines,
            source=source,
            error=None,
            timestamp=timestamp,
        )

    # No coverage found
    print("  ✗ No coverage data found")
    return CoverageResult(
        repo=repo,
        url=f"https://github.com/{repo.owner}/{repo.name}",
        coverage_percentage=None,
        total_lines=total_lines,
        source=None,
        error="No coverage data found in README or Coveralls",
        timestamp=timestamp,
    )
