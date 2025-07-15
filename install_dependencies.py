import json
from typing import Any
from pathlib import Path
from subprocess_utils import run_command_safely


def has_link_dependencies(repo_path: Path) -> bool:
    """Check if package.json has link: dependencies"""
    if not (repo_path / "package.json").exists():
        return False
    try:
        with open(repo_path / "package.json", "r", encoding="utf-8") as f:
            pkg_data: dict[str, Any] = json.load(f)
            dependencies = pkg_data.get("dependencies", {}) or {}
            dev_dependencies = pkg_data.get("devDependencies", {}) or {}
            all_deps = {**dependencies, **dev_dependencies}
            return any("link:" in str(dep) for dep in all_deps.values())
    except Exception:
        return False


def install_dependencies(repo_path: Path) -> tuple[bool, str]:
    """Install project dependencies. Returns (success, error_message)"""
    if (repo_path / "package.json").exists():
        # Check for monorepo with link: dependencies (React-style)
        if has_link_dependencies(repo_path):
            return run_command_safely(
                ["yarn", "install", "--ignore-scripts"],
                cwd=repo_path,
                timeout=300,
            )
        # Try npm ci first if package-lock.json exists
        if (repo_path / "package-lock.json").exists():
            success, error = run_command_safely(
                ["npm", "ci"], cwd=repo_path, timeout=600
            )
            if success:
                return success, error
            # If npm ci fails, try with --legacy-peer-deps
            success, error = run_command_safely(
                ["npm", "ci", "--legacy-peer-deps"], cwd=repo_path, timeout=600
            )
            if success:
                return success, error
            # If still fails, try with --force (last resort)
            return run_command_safely(
                ["npm", "ci", "--force"], cwd=repo_path, timeout=600
            )

        # Try npm install first
        success, error = run_command_safely(
            ["npm", "install"], cwd=repo_path, timeout=600
        )
        if success:
            return success, error
        # If npm install fails, try with --legacy-peer-deps
        success, error = run_command_safely(
            ["npm", "install", "--legacy-peer-deps"], cwd=repo_path, timeout=600
        )
        if success:
            return success, error
        # If still fails, try with --force (last resort)
        success, error = run_command_safely(
            ["npm", "install", "--force"], cwd=repo_path, timeout=600
        )
        if success:
            return success, error
        # For monorepos, try npm workspaces directly (skips link: dependencies)
        success, error = run_command_safely(
            ["npm", "install", "--workspaces=false", "--legacy-peer-deps"],
            cwd=repo_path,
            timeout=300,
        )
        if success:
            return success, error
        # Last resort: yarn but with very short timeout
        return run_command_safely(
            ["yarn", "install", "--ignore-scripts", "--frozen-lockfile"],
            cwd=repo_path,
            timeout=120,
        )
    if (repo_path / "requirements.txt").exists():
        return run_command_safely(
            ["pip", "install", "-r", "requirements.txt"], cwd=repo_path, timeout=600
        )
    if (repo_path / "pom.xml").exists():
        return run_command_safely(
            ["mvn", "install", "-DskipTests"], cwd=repo_path, timeout=600
        )
    if (repo_path / "go.mod").exists():
        return run_command_safely(["go", "mod", "download"], cwd=repo_path, timeout=300)
    return True, ""
