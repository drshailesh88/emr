#!/usr/bin/env python3
"""
Platform compatibility test runner.

Runs all platform-specific tests and generates a compatibility report.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.platform_utils import get_platform_name, get_platform_info


class PlatformTestRunner:
    """Runs platform-specific tests and generates reports."""

    def __init__(self):
        self.platform = get_platform_name()
        self.platform_info = get_platform_info()
        self.results: Dict[str, Any] = {}
        self.test_dir = Path(__file__).parent

    def run_common_tests(self) -> Dict[str, Any]:
        """Run cross-platform common tests."""
        print("=" * 70)
        print("Running Cross-Platform Common Tests...")
        print("=" * 70)

        test_file = self.test_dir / "test_common.py"

        # Run pytest programmatically
        exit_code = pytest.main([
            str(test_file),
            "-v",
            "--tb=short",
            f"--junit-xml={self.test_dir / 'common_results.xml'}",
        ])

        return {
            "name": "Common Tests",
            "file": str(test_file),
            "exit_code": exit_code,
            "passed": exit_code == 0,
        }

    def run_platform_specific_tests(self) -> Dict[str, Any]:
        """Run tests specific to the current platform."""
        print("\n" + "=" * 70)
        print(f"Running {self.platform.upper()}-Specific Tests...")
        print("=" * 70)

        # Map platform to test file
        test_files = {
            "windows": "test_windows.py",
            "macos": "test_macos.py",
            "linux": "test_linux.py",
        }

        test_file_name = test_files.get(self.platform)

        if not test_file_name:
            print(f"Warning: No platform-specific tests for '{self.platform}'")
            return {
                "name": f"{self.platform} Tests",
                "file": None,
                "exit_code": -1,
                "passed": False,
                "error": f"Unknown platform: {self.platform}",
            }

        test_file = self.test_dir / test_file_name

        if not test_file.exists():
            print(f"Warning: Test file not found: {test_file}")
            return {
                "name": f"{self.platform} Tests",
                "file": str(test_file),
                "exit_code": -1,
                "passed": False,
                "error": "Test file not found",
            }

        # Run pytest programmatically
        exit_code = pytest.main([
            str(test_file),
            "-v",
            "--tb=short",
            f"--junit-xml={self.test_dir / f'{self.platform}_results.xml'}",
        ])

        return {
            "name": f"{self.platform} Tests",
            "file": str(test_file),
            "exit_code": exit_code,
            "passed": exit_code == 0,
        }

    def run_all_platform_tests_with_skip(self) -> List[Dict[str, Any]]:
        """
        Run tests for all platforms (will skip non-matching platforms).

        This runs all test files but they will automatically skip
        if not on the correct platform.
        """
        print("\n" + "=" * 70)
        print("Running All Platform Tests (with auto-skip)...")
        print("=" * 70)

        test_files = [
            ("windows", "test_windows.py"),
            ("macos", "test_macos.py"),
            ("linux", "test_linux.py"),
        ]

        results = []

        for platform_name, test_file_name in test_files:
            test_file = self.test_dir / test_file_name

            if not test_file.exists():
                results.append({
                    "name": f"{platform_name} Tests",
                    "file": str(test_file),
                    "exit_code": -1,
                    "passed": False,
                    "skipped": False,
                    "error": "Test file not found",
                })
                continue

            print(f"\nRunning {test_file_name}...")

            # Run pytest - will skip if wrong platform
            exit_code = pytest.main([
                str(test_file),
                "-v",
                "--tb=short",
                f"--junit-xml={self.test_dir / f'{platform_name}_all_results.xml'}",
            ])

            # Exit code 5 means all tests were skipped
            # Exit code 0 means tests passed
            # Other codes mean failures/errors

            results.append({
                "name": f"{platform_name} Tests",
                "file": str(test_file),
                "exit_code": exit_code,
                "passed": exit_code == 0,
                "skipped": exit_code == 5,
            })

        return results

    def generate_compatibility_report(self, results: Dict[str, Any]) -> str:
        """Generate a detailed compatibility report."""
        report_lines = []

        report_lines.append("=" * 70)
        report_lines.append("DOCASSIST EMR - PLATFORM COMPATIBILITY REPORT")
        report_lines.append("=" * 70)
        report_lines.append("")

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_lines.append(f"Generated: {timestamp}")
        report_lines.append("")

        # Platform Information
        report_lines.append("PLATFORM INFORMATION")
        report_lines.append("-" * 70)
        for key, value in self.platform_info.items():
            report_lines.append(f"  {key:20s}: {value}")
        report_lines.append("")

        # Test Results Summary
        report_lines.append("TEST RESULTS SUMMARY")
        report_lines.append("-" * 70)

        common_result = results.get("common")
        platform_result = results.get("platform_specific")
        all_platforms_results = results.get("all_platforms", [])

        # Common tests
        if common_result:
            status = "✓ PASSED" if common_result["passed"] else "✗ FAILED"
            report_lines.append(f"Common Tests:           {status}")
            report_lines.append(f"  File:     {common_result['file']}")
            report_lines.append(f"  Exit Code: {common_result['exit_code']}")
            report_lines.append("")

        # Platform-specific tests
        if platform_result:
            status = "✓ PASSED" if platform_result["passed"] else "✗ FAILED"
            report_lines.append(f"{self.platform.upper()} Tests:      {status}")
            report_lines.append(f"  File:     {platform_result.get('file', 'N/A')}")
            report_lines.append(f"  Exit Code: {platform_result['exit_code']}")
            if "error" in platform_result:
                report_lines.append(f"  Error:    {platform_result['error']}")
            report_lines.append("")

        # All platforms (with skip)
        if all_platforms_results:
            report_lines.append("ALL PLATFORMS (with auto-skip):")
            for result in all_platforms_results:
                if result.get("skipped"):
                    status = "⊘ SKIPPED"
                elif result["passed"]:
                    status = "✓ PASSED"
                else:
                    status = "✗ FAILED"

                platform_name = result["name"].split()[0]
                report_lines.append(f"  {platform_name:12s}: {status}")

            report_lines.append("")

        # Overall Status
        report_lines.append("OVERALL STATUS")
        report_lines.append("-" * 70)

        all_passed = True

        if common_result and not common_result["passed"]:
            all_passed = False
            report_lines.append("  ✗ Common tests failed")

        if platform_result and not platform_result["passed"]:
            all_passed = False
            report_lines.append(f"  ✗ {self.platform} tests failed")

        if all_passed:
            report_lines.append("  ✓ All tests passed!")
            report_lines.append("")
            report_lines.append(f"  DocAssist EMR is COMPATIBLE with {self.platform.upper()}")
        else:
            report_lines.append("  ✗ Some tests failed")
            report_lines.append("")
            report_lines.append("  Review test output for details")

        report_lines.append("=" * 70)

        return "\n".join(report_lines)

    def save_report(self, report: str, filename: str = "compatibility_report.txt"):
        """Save the report to a file."""
        report_path = self.test_dir / filename
        report_path.write_text(report)
        print(f"\nReport saved to: {report_path}")

    def save_json_report(self, results: Dict[str, Any], filename: str = "compatibility_report.json"):
        """Save the results as JSON."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "platform_info": self.platform_info,
            "results": results,
        }

        report_path = self.test_dir / filename
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"JSON report saved to: {report_path}")

    def flag_platform_issues(self, results: Dict[str, Any]) -> List[str]:
        """Flag any platform-specific issues found."""
        issues = []

        common_result = results.get("common")
        if common_result and not common_result["passed"]:
            issues.append("Cross-platform common tests failed - basic compatibility issue")

        platform_result = results.get("platform_specific")
        if platform_result:
            if "error" in platform_result:
                issues.append(f"{self.platform}: {platform_result['error']}")
            elif not platform_result["passed"]:
                issues.append(f"{self.platform}-specific tests failed")

        return issues

    def run_all(self, skip_other_platforms: bool = False) -> int:
        """
        Run all tests and generate reports.

        Args:
            skip_other_platforms: If True, only run current platform tests.
                                 If False, run all platforms (will auto-skip).

        Returns:
            Exit code (0 = success, non-zero = failure)
        """
        print("DocAssist EMR - Platform Compatibility Test Runner")
        print(f"Current Platform: {self.platform.upper()}")
        print()

        results = {}

        # Run common tests (always)
        results["common"] = self.run_common_tests()

        # Run platform-specific tests
        results["platform_specific"] = self.run_platform_specific_tests()

        # Optionally run all platform tests with skip
        if not skip_other_platforms:
            results["all_platforms"] = self.run_all_platform_tests_with_skip()

        # Generate and save reports
        report = self.generate_compatibility_report(results)
        print("\n" + report)

        self.save_report(report)
        self.save_json_report(results)

        # Flag issues
        issues = self.flag_platform_issues(results)

        if issues:
            print("\n" + "!" * 70)
            print("PLATFORM ISSUES DETECTED:")
            print("!" * 70)
            for issue in issues:
                print(f"  • {issue}")
            print("!" * 70)

        # Determine exit code
        common_passed = results["common"]["passed"]
        platform_passed = results["platform_specific"]["passed"]

        if common_passed and platform_passed:
            return 0
        else:
            return 1


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run platform compatibility tests for DocAssist EMR"
    )
    parser.add_argument(
        "--current-only",
        action="store_true",
        help="Only run tests for current platform (skip other platforms)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only generate JSON report (no text report)",
    )

    args = parser.parse_args()

    runner = PlatformTestRunner()
    exit_code = runner.run_all(skip_other_platforms=args.current_only)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
