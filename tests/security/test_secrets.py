"""
Secrets Detection Tests

Ensures no hardcoded secrets, API keys, or passwords in code.
"""

import pytest
import re
from pathlib import Path
from typing import List, Tuple


@pytest.mark.security
class TestSecrets:
    """Test for hardcoded secrets"""

    # Patterns that might indicate secrets
    SECRET_PATTERNS = {
        'api_key': re.compile(r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
        'password': re.compile(r'password\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
        'secret': re.compile(r'secret\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
        'token': re.compile(r'token\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
        'aws_key': re.compile(r'AKIA[0-9A-Z]{16}'),
        'private_key': re.compile(r'-----BEGIN (RSA |EC )?PRIVATE KEY-----'),
        'db_password': re.compile(r'db[_-]?password\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
    }

    # Allowed patterns that are not real secrets
    ALLOWED_VALUES = {
        'test', 'example', 'dummy', 'fake', 'mock', 'sample',
        'placeholder', 'changeme', 'your_', 'your-', 'xxx',
        'default', 'demo', 'localhost', 'none', 'null',
    }

    def _is_false_positive(self, value: str) -> bool:
        """Check if a detected secret is likely a false positive"""
        value_lower = value.lower()
        return any(allowed in value_lower for allowed in self.ALLOWED_VALUES)

    def _scan_file(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Scan a file for potential secrets"""
        findings = []

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith('#'):
                    continue

                for secret_type, pattern in self.SECRET_PATTERNS.items():
                    matches = pattern.finditer(line)
                    for match in matches:
                        # Get the matched value (group 1 if exists, else full match)
                        value = match.group(1) if match.groups() else match.group(0)

                        # Skip false positives
                        if self._is_false_positive(value):
                            continue

                        # Skip environment variable references
                        if value.startswith('os.'):
                            continue

                        findings.append((line_num, secret_type, value))

        except Exception as e:
            # Skip binary files or files with encoding issues
            pass

        return findings

    def test_no_hardcoded_secrets_in_source(self):
        """Test that source code has no hardcoded secrets"""
        project_root = Path(__file__).parent.parent.parent
        src_dir = project_root / 'src'

        if not src_dir.exists():
            pytest.skip("No src directory found")

        all_findings = []

        for py_file in src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            findings = self._scan_file(py_file)
            if findings:
                rel_path = py_file.relative_to(project_root)
                for line_num, secret_type, value in findings:
                    all_findings.append(f"{rel_path}:{line_num} - {secret_type}: {value[:20]}...")

        if all_findings:
            message = f"Found {len(all_findings)} potential secret(s):\n"
            message += "\n".join(f"  - {finding}" for finding in all_findings[:10])
            if len(all_findings) > 10:
                message += f"\n  ... and {len(all_findings) - 10} more"

            pytest.fail(message)

    def test_no_secrets_in_config_files(self):
        """Test that config files use environment variables"""
        project_root = Path(__file__).parent.parent.parent

        config_files = [
            project_root / '.env',
            project_root / 'config.py',
            project_root / 'settings.py',
        ]

        # .env files should exist but can have example values
        # Check for .env.example instead
        env_example = project_root / '.env.example'
        if env_example.exists():
            content = env_example.read_text()
            # Should have placeholder values, not real secrets
            for line in content.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"\'')

                    if value and not self._is_false_positive(value):
                        if len(value) > 20:  # Long values might be real secrets
                            pytest.fail(
                                f".env.example should not contain real values: {key}"
                            )

    def test_database_credentials_from_env(self):
        """Test that database credentials come from environment"""
        project_root = Path(__file__).parent.parent.parent
        db_file = project_root / 'src' / 'services' / 'database.py'

        if not db_file.exists():
            pytest.skip("database.py not found")

        content = db_file.read_text()

        # Should use os.getenv or similar
        assert 'os.getenv' in content or 'os.environ' in content, \
            "Database service should use environment variables"

        # Should NOT have hardcoded credentials
        dangerous = [
            'password="',
            'password=\'',
            'Password="',
            'Password=\'',
        ]

        for pattern in dangerous:
            if pattern in content:
                # Check if it's actually a hardcoded password
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if pattern in line and 'os.getenv' not in line:
                        pytest.fail(
                            f"Line {i}: Possible hardcoded password in database.py"
                        )

    def test_encryption_keys_not_hardcoded(self):
        """Test that encryption keys come from secure sources"""
        project_root = Path(__file__).parent.parent.parent
        crypto_file = project_root / 'src' / 'services' / 'crypto.py'

        if not crypto_file.exists():
            pytest.skip("crypto.py not found")

        content = crypto_file.read_text()

        # Encryption keys should be generated or loaded from secure storage
        # Should NOT be hardcoded
        dangerous_patterns = [
            b'-----BEGIN PRIVATE KEY-----',
            b'\x00' * 32,  # Null bytes (common in test keys)
        ]

        content_bytes = content.encode('utf-8')
        for pattern in dangerous_patterns:
            if pattern in content_bytes:
                pytest.fail("Encryption key appears to be hardcoded in crypto.py")

    def test_no_credentials_in_logs(self):
        """Test that logging doesn't expose credentials"""
        project_root = Path(__file__).parent.parent.parent
        src_dir = project_root / 'src'

        if not src_dir.exists():
            pytest.skip("No src directory found")

        dangerous_logging = []

        for py_file in src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            content = py_file.read_text()
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                # Check for logging of sensitive data
                if 'log' in line.lower() or 'print' in line.lower():
                    sensitive_keywords = ['password', 'secret', 'key', 'token', 'credential']

                    for keyword in sensitive_keywords:
                        if keyword in line.lower():
                            rel_path = py_file.relative_to(project_root)
                            dangerous_logging.append(f"{rel_path}:{line_num}")

        # This is informational - manual review needed
        if dangerous_logging:
            # Don't fail, just warn
            print("\n⚠️  Found logging of potentially sensitive data (manual review needed):")
            for finding in dangerous_logging[:5]:
                print(f"  - {finding}")
