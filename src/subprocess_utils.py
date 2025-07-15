import subprocess
from typing import Optional
from pathlib import Path


def run_command_safely(
    command: list[str], cwd: Optional[Path] = None, timeout: int = 300
) -> tuple[bool, str]:
    """Run a subprocess command safely with consistent error handling
    Returns (success, error_message)"""
    try:
        subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            timeout=timeout,
            text=True,
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        error_msg = f"Exit code {e.returncode}. stderr: {e.stderr.strip()}"
        # Don't print verbose npm errors, just return them
        return False, error_msg
    except subprocess.TimeoutExpired:
        error_msg = f"Timeout after {timeout}s"
        return False, error_msg
    except OSError as e:
        error_msg = f"OS error: {e}"
        return False, error_msg
