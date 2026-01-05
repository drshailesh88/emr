#!/usr/bin/env python3
"""
CI/CD Setup Verification Script for DocAssist EMR

This script verifies that all CI/CD files are properly configured.
Run: python verify_cicd_setup.py
"""

import os
import sys
from pathlib import Path


def check_file(filepath, description):
    """Check if a file exists and is not empty."""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ MISSING: {description}")
        print(f"   Expected: {filepath}")
        return False
    elif path.stat().st_size == 0:
        print(f"⚠️  EMPTY: {description}")
        print(f"   File: {filepath}")
        return False
    else:
        size_kb = path.stat().st_size / 1024
        print(f"✅ FOUND: {description} ({size_kb:.1f} KB)")
        return True


def main():
    """Main verification function."""
    print("=" * 70)
    print("DocAssist EMR - CI/CD Setup Verification")
    print("=" * 70)
    print()

    checks = []

    # GitHub Workflows
    print("📋 GitHub Workflows")
    print("-" * 70)
    checks.append(check_file(".github/workflows/ci.yml", "CI Pipeline"))
    checks.append(check_file(".github/workflows/security.yml", "Security Scanning"))
    checks.append(check_file(".github/workflows/release.yml", "Release Pipeline"))
    checks.append(check_file(".github/workflows/nightly.yml", "Nightly Tests"))
    print()

    # GitHub Configuration
    print("📋 GitHub Configuration")
    print("-" * 70)
    checks.append(check_file(".github/CODEOWNERS", "Code Owners"))
    checks.append(check_file(".github/pull_request_template.md", "PR Template"))
    checks.append(check_file(".github/README.md", "CI/CD Documentation"))
    checks.append(check_file(".github/CICD_QUICKSTART.md", "Quick Start Guide"))
    print()

    # Root Configuration Files
    print("📋 Root Configuration Files")
    print("-" * 70)
    checks.append(check_file("Makefile", "Makefile"))
    checks.append(check_file("pyproject.toml", "Project Configuration (pyproject.toml)"))
    checks.append(check_file(".pre-commit-config.yaml", "Pre-commit Hooks"))
    checks.append(check_file(".secrets.baseline", "Secrets Baseline"))
    print()

    # Dependency Files
    print("📋 Dependency Files")
    print("-" * 70)
    checks.append(check_file("requirements.txt", "Production Dependencies"))
    checks.append(check_file("requirements-dev.txt", "Development Dependencies"))
    print()

    # Summary
    print("=" * 70)
    total = len(checks)
    passed = sum(checks)
    failed = total - passed

    print(f"Total Checks: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print("=" * 70)
    print()

    if failed == 0:
        print("🎉 SUCCESS! All CI/CD files are properly configured.")
        print()
        print("Next Steps:")
        print("1. Install dependencies: make install")
        print("2. Install pre-commit hooks: make pre-commit-install")
        print("3. Run tests: make test")
        print("4. Run all checks: make check-all")
        print()
        print("📖 Read the Quick Start Guide: .github/CICD_QUICKSTART.md")
        return 0
    else:
        print("⚠️  WARNING: Some CI/CD files are missing or empty.")
        print("Please review the missing files and create them.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
