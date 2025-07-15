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
    total_lines: Optional[int]
    source: Optional[str]
    error: Optional[str]
    timestamp: str
