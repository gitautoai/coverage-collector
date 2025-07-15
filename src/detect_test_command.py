import json
from pathlib import Path
from typing import Optional, Tuple


def detect_test_command(repo_path: Path) -> Optional[Tuple[str, str]]:
    """Return (test_command, coverage_tool) or None"""

    # JavaScript/TypeScript (Node.js)
    if (repo_path / "package.json").exists():
        with open(repo_path / "package.json", encoding="utf-8") as f:
            package = json.load(f)
            scripts = package.get("scripts", {})

            # Check for coverage scripts
            if "coverage" in scripts:
                return ("npm run coverage", "jest/nyc")
            if "test:coverage" in scripts:
                return ("npm run test:coverage", "jest/nyc")
            # Check if there's a specific coverage script or jest config
            if "test-coverage" in scripts:
                return ("npm run test-coverage", "jest/nyc")
            if "test" in scripts and (
                "jest" in str(scripts) or "mocha" in str(scripts)
            ):
                return ("npm test -- --coverage", "jest/nyc")

    # Python
    if (repo_path / "setup.py").exists() or (repo_path / "pyproject.toml").exists():
        if (repo_path / "pytest.ini").exists() or (repo_path / "setup.cfg").exists():
            return ("pytest --cov=. --cov-report=json", "pytest-cov")
        if (repo_path / "tox.ini").exists():
            return ("tox -e coverage", "coverage.py")

    # Java (Maven)
    if (repo_path / "pom.xml").exists():
        return ("mvn test jacoco:report", "jacoco")

    # Java (Gradle)
    if (repo_path / "build.gradle").exists() or (
        repo_path / "build.gradle.kts"
    ).exists():
        return ("./gradlew test jacocoTestReport", "jacoco")

    # Go
    if (repo_path / "go.mod").exists():
        return ("go test -coverprofile=coverage.out ./...", "go-cover")

    # Ruby
    if (repo_path / "Gemfile").exists():
        return ("bundle exec rspec --format json --out rspec.json", "simplecov")

    # Rust
    if (repo_path / "Cargo.toml").exists():
        return ("cargo tarpaulin --out Xml", "tarpaulin")

    return None
