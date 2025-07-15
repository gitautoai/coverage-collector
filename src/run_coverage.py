import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from models import RepoInfo, CoverageResult
from detect_test_command import detect_test_command
from clone_repo import clone_repo
from install_dependencies import install_dependencies, has_link_dependencies
from parse_coverage_output import parse_coverage_output


def _check_coverage_files(
    coverage_pct: float | None, repo_path: Path, coverage_tool: str
) -> float | None:
    """Helper function to check coverage files and reduce nesting"""
    if coverage_pct is not None:
        return coverage_pct

    coverage_files = [
        repo_path / "coverage" / "lcov-report" / "index.html",
        repo_path / "coverage" / "lcov.info",
        repo_path / "coverage.json",
        repo_path / "coverage" / "coverage-summary.json",
    ]
    for cov_file in coverage_files:
        if cov_file.exists():
            try:
                content = cov_file.read_text()
                coverage_pct = parse_coverage_output(content, coverage_tool)
                if coverage_pct:
                    return coverage_pct
            except Exception:
                continue
    return coverage_pct


def run_coverage(repo: RepoInfo) -> CoverageResult:
    """Run tests and collect coverage for a repository"""
    timestamp = datetime.now().isoformat()

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / repo.name

        # Clone repo
        clone_success, clone_error = clone_repo(repo, repo_path)
        if not clone_success:
            return CoverageResult(
                repo,
                None,
                None,
                None,
                None,
                f"Failed to clone: {clone_error}",
                timestamp,
            )

        # Detect test command
        test_info = detect_test_command(repo_path)
        if not test_info:
            return CoverageResult(
                repo, None, None, None, None, "No test command detected", timestamp
            )

        test_command, coverage_tool = test_info

        # Check if repo has link: dependencies to determine if we should use yarn
        use_yarn = has_link_dependencies(repo_path)

        # Adjust test command for yarn if needed
        if use_yarn and test_command.startswith("npm "):
            test_command = test_command.replace("npm ", "yarn ", 1).replace(" -- ", " ")

        # Install dependencies
        deps_success, deps_error = install_dependencies(repo_path)
        if not deps_success:
            return CoverageResult(
                repo,
                None,
                None,
                None,
                test_command,
                f"Failed to install dependencies: {deps_error}",
                timestamp,
            )

        # Run tests with coverage
        try:
            result = subprocess.run(
                test_command.split(),
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes timeout
                check=False,
            )

            # Parse coverage from output and files even if some tests failed
            # Many repos have flaky tests but still generate useful coverage data
            coverage_pct = parse_coverage_output(result.stdout, coverage_tool)
            if coverage_pct is None:
                coverage_pct = parse_coverage_output(result.stderr, coverage_tool)

            # Also check for coverage files that might have been generated
            coverage_pct = _check_coverage_files(coverage_pct, repo_path, coverage_tool)

            # Return result whether we have coverage or not, with appropriate error message
            if result.returncode != 0 and coverage_pct is None:
                return CoverageResult(
                    repo,
                    None,
                    None,
                    None,
                    test_command,
                    f"Tests failed: {result.stderr[:500]}...",
                    timestamp,
                )
            return CoverageResult(
                repo, coverage_pct, None, None, test_command, None, timestamp
            )

        except subprocess.TimeoutExpired:
            return CoverageResult(
                repo, None, None, None, test_command, "Test timeout", timestamp
            )
        except (subprocess.CalledProcessError, OSError) as e:
            return CoverageResult(
                repo, None, None, None, test_command, str(e), timestamp
            )
