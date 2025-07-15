# pylint: disable=broad-exception-caught

from pathlib import Path
from models import RepoInfo
from subprocess_utils import run_command_safely


def clone_repo(repo: RepoInfo, target_dir: Path) -> tuple[bool, str]:
    """Clone repository. Returns (success, error_message)"""
    command = ["git", "clone", "--depth", "1", repo.clone_url, str(target_dir)]
    success, error_msg = run_command_safely(command, timeout=300)
    return success, error_msg
