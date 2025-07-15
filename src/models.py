from dataclasses import dataclass
from typing import Optional


@dataclass
class RepoInfo:
    owner: str
    name: str
    stars: int
    language: str
    clone_url: str


@dataclass
class CoverageResult:
    repo: RepoInfo
    coverage_percentage: Optional[float]
    lines_covered: Optional[int]
    lines_total: Optional[int]
    test_command: Optional[str]
    error: Optional[str]
    timestamp: str
