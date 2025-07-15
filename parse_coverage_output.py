import re
from typing import Optional


def parse_coverage_output(output: str, tool: str) -> Optional[float]:
    """Parse coverage percentage from output"""
    patterns = {
        "jest/nyc": [
            r"All files[^|]*\|[^|]*\|[^|]*\|\s*([\d.]+)",  # Standard Jest table
            r"Statements\s*:\s*([\d.]+)%",  # Jest coverage summary
            r"Lines\s*:\s*([\d.]+)%",  # Jest coverage summary
            r"Functions\s*:\s*([\d.]+)%",  # Jest coverage summary
            r"Branches\s*:\s*([\d.]+)%",  # Jest coverage summary
        ],
        "pytest-cov": [r"TOTAL\s+\d+\s+\d+\s+([\d.]+)%"],
        "go-cover": [r"coverage:\s*([\d.]+)%"],
        "jacoco": [r"Total[^|]*\|[^|]*\|\s*([\d.]+)%"],
    }

    if tool in patterns:
        for pattern in patterns[tool]:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                print(
                    f"DEBUG: Found coverage {match.group(1)}% using pattern: {pattern}"
                )
                return float(match.group(1))

    # Generic percentage search - look for various coverage indicators
    coverage_patterns = [
        r"Coverage:\s*([\d.]+)%",
        r"Total coverage:\s*([\d.]+)%",
        r"Overall coverage:\s*([\d.]+)%",
        r"(\d+\.?\d*)%\s*coverage",
        r"(\d+\.?\d*)%",  # Last resort - any percentage
    ]

    for pattern in coverage_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return float(match.group(1))

    return None
