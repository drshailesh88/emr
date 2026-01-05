"""
Type Validator

Runs mypy type checking on source code.
"""

import subprocess
from pathlib import Path
from typing import Tuple


class TypeValidator:
    """Run mypy type checking"""

    name = "Type Validator (mypy)"

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    def validate(self) -> Tuple[bool, str]:
        """Run mypy on src/"""
        src_dir = self.project_root / 'src'

        if not src_dir.exists():
            return True, "No src/ directory to check"

        # Check if mypy is installed
        try:
            subprocess.run(['mypy', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return True, "mypy not installed, skipping type checking"

        # Run mypy
        result = subprocess.run(
            ['mypy', 'src/', '--ignore-missing-imports', '--no-error-summary'],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Parse errors
            error_lines = [line for line in result.stdout.split('\n') if line.strip()]
            error_count = len(error_lines)

            message = f"Found {error_count} type error(s):\n"
            message += "\n".join(f"  - {line}" for line in error_lines[:5])
            if error_count > 5:
                message += f"\n  ... and {error_count - 5} more"

            return False, message

        return True, "No type errors found"
