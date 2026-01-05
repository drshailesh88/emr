"""
Security Validator

Runs bandit security linter on source code.
"""

import subprocess
from pathlib import Path
from typing import Tuple


class SecurityValidator:
    """Run bandit security linter"""

    name = "Security Validator (bandit)"

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    def validate(self) -> Tuple[bool, str]:
        """Run bandit on src/"""
        src_dir = self.project_root / 'src'

        if not src_dir.exists():
            return True, "No src/ directory to check"

        # Check if bandit is installed
        try:
            subprocess.run(['bandit', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return True, "bandit not installed, skipping security checks"

        # Run bandit
        result = subprocess.run(
            [
                'bandit',
                '-r', 'src/',
                '-f', 'txt',
                '--severity-level', 'medium',
                '--skip', 'B101',  # assert_used is OK
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        # Bandit returns:
        # 0 - no issues
        # 1 - issues found
        # 2 - error
        if result.returncode == 2:
            return False, f"Bandit error: {result.stderr}"

        if result.returncode == 1:
            # Parse output to count issues
            lines = result.stdout.split('\n')
            issue_lines = [l for l in lines if 'Issue:' in l or 'Severity:' in l]

            message = "Security issues found:\n"
            message += "\n".join(f"  {line}" for line in issue_lines[:10])
            if len(issue_lines) > 10:
                message += f"\n  ... and more"

            return False, message

        return True, "No security issues found"
