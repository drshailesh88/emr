#!/usr/bin/env python3
"""
DocAssist EMR Test Runner

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Unit tests only
    python run_tests.py --integration      # Integration tests only
    python run_tests.py --load             # Load tests only
    python run_tests.py --security         # Security tests only
    python run_tests.py --smoke            # Smoke tests only
    python run_tests.py --coverage         # With coverage report
    python run_tests.py --quick            # Fast tests only (<1s each)
    python run_tests.py --ci               # CI mode (strict, report artifacts)
    python run_tests.py --watch            # Watch mode (re-run on file changes)
    python run_tests.py --failed           # Re-run only failed tests from last run
    python run_tests.py --parallel         # Run tests in parallel
    python run_tests.py --verbose          # Verbose output

Examples:
    python run_tests.py --unit --coverage
    python run_tests.py --smoke --quick
    python run_tests.py --ci --parallel
"""

import argparse
import sys
import time
import subprocess
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_runner_config import TEST_CONFIG, COVERAGE_CONFIG
from tests.reporter import TestReporter


class TestRunner:
    """Main test runner for DocAssist EMR"""

    def __init__(self, args):
        self.args = args
        self.reporter = TestReporter()
        self.start_time = None
        self.end_time = None
        self.results = {}

    def build_pytest_args(self) -> List[str]:
        """Build pytest command arguments based on user options"""
        pytest_args = ['pytest']

        # Test selection
        if self.args.unit:
            pytest_args.extend(['-m', 'unit or not (integration or load or security or smoke)'])
            pytest_args.extend(TEST_CONFIG['unit']['paths'])
        elif self.args.integration:
            pytest_args.extend(['-m', 'integration'])
            pytest_args.extend(TEST_CONFIG['integration']['paths'])
        elif self.args.load:
            pytest_args.extend(['-m', 'load'])
            pytest_args.extend(TEST_CONFIG['load']['paths'])
        elif self.args.security:
            pytest_args.extend(['-m', 'security'])
            pytest_args.extend(TEST_CONFIG['security']['paths'])
        elif self.args.smoke:
            pytest_args.extend(['-m', 'smoke'])
            pytest_args.extend(TEST_CONFIG['smoke']['paths'])
        else:
            # Run all tests
            pytest_args.append('tests/')

        # Quick mode - skip slow tests
        if self.args.quick:
            pytest_args.extend(['-m', 'not slow'])

        # Coverage
        if self.args.coverage or self.args.ci:
            pytest_args.extend([
                '--cov=src',
                '--cov-report=html',
                '--cov-report=xml',
                '--cov-report=term-missing',
                f'--cov-fail-under={COVERAGE_CONFIG["fail_under"]}'
            ])

        # Parallel execution
        if self.args.parallel:
            # Only parallelize if safe (not integration tests that share DB)
            if not self.args.integration:
                import multiprocessing
                num_cores = multiprocessing.cpu_count()
                pytest_args.extend(['-n', str(num_cores)])

        # CI mode
        if self.args.ci:
            pytest_args.extend([
                '--junitxml=test_results/junit.xml',
                '--strict-markers',
                '--tb=short',
                '--maxfail=0',  # Don't stop on first failure in CI
            ])

        # Verbose
        if self.args.verbose:
            pytest_args.append('-vv')
        else:
            pytest_args.append('-v')

        # Re-run failed tests
        if self.args.failed:
            pytest_args.append('--lf')  # Last failed

        # Watch mode (handled separately)
        # Performance timing
        pytest_args.append('--durations=10')

        return pytest_args

    def run_validators(self) -> bool:
        """Run pre-test validators"""
        if not self.args.ci and not self.args.validate:
            return True

        print("\n" + "="*70)
        print("Running Pre-Test Validators")
        print("="*70)

        validators = []

        if self.args.validate or self.args.ci:
            from tests.validators.import_validator import ImportValidator
            from tests.validators.syntax_validator import SyntaxValidator

            validators.extend([
                ImportValidator(),
                SyntaxValidator(),
            ])

        if self.args.ci:
            from tests.validators.type_validator import TypeValidator
            from tests.validators.security_validator import SecurityValidator

            validators.extend([
                TypeValidator(),
                SecurityValidator(),
            ])

        all_passed = True
        for validator in validators:
            print(f"\n→ Running {validator.name}...")
            passed, message = validator.validate()
            if passed:
                print(f"  ✓ {message}")
            else:
                print(f"  ✗ {message}")
                all_passed = False

        return all_passed

    def run_tests(self) -> int:
        """Run the tests and return exit code"""
        self.start_time = time.time()

        # Run validators first
        if not self.run_validators():
            print("\n❌ Validators failed! Fix issues before running tests.")
            return 1

        # Build pytest command
        pytest_args = self.build_pytest_args()

        print("\n" + "="*70)
        print("Running Tests")
        print("="*70)
        print(f"Command: {' '.join(pytest_args)}\n")

        # Run pytest
        result = subprocess.run(
            pytest_args,
            cwd=PROJECT_ROOT,
            env={**subprocess.os.environ, 'PYTHONPATH': str(PROJECT_ROOT)}
        )

        self.end_time = time.time()

        # Generate reports
        if self.args.ci or self.args.coverage:
            self._generate_reports()

        # Print summary
        self._print_summary(result.returncode)

        return result.returncode

    def _generate_reports(self):
        """Generate test reports"""
        print("\n" + "="*70)
        print("Generating Reports")
        print("="*70)

        # Ensure directories exist
        (PROJECT_ROOT / 'test_results').mkdir(exist_ok=True)
        (PROJECT_ROOT / 'coverage_report').mkdir(exist_ok=True)

        # Generate HTML report
        if (PROJECT_ROOT / 'htmlcov').exists():
            print("  ✓ Coverage HTML report: htmlcov/index.html")

        # Generate JUnit XML
        if (PROJECT_ROOT / 'test_results' / 'junit.xml').exists():
            print("  ✓ JUnit XML report: test_results/junit.xml")

        # Generate custom reports
        try:
            summary = self.reporter.generate_summary_report()
            summary_path = PROJECT_ROOT / 'test_results' / 'summary.txt'
            summary_path.write_text(summary)
            print(f"  ✓ Summary report: {summary_path}")
        except Exception as e:
            print(f"  ⚠ Could not generate summary: {e}")

    def _print_summary(self, exit_code: int):
        """Print test run summary"""
        duration = self.end_time - self.start_time

        print("\n" + "="*70)
        print("Test Run Summary")
        print("="*70)
        print(f"Duration: {duration:.2f}s")
        print(f"Status: {'✓ PASSED' if exit_code == 0 else '✗ FAILED'}")

        if exit_code == 0:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed. Check output above for details.")
            print("\nTip: Use --failed to re-run only failed tests")


def main():
    parser = argparse.ArgumentParser(
        description='DocAssist EMR Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Test selection
    test_group = parser.add_argument_group('Test Selection')
    test_group.add_argument('--unit', action='store_true',
                           help='Run unit tests only')
    test_group.add_argument('--integration', action='store_true',
                           help='Run integration tests only')
    test_group.add_argument('--load', action='store_true',
                           help='Run load tests only')
    test_group.add_argument('--security', action='store_true',
                           help='Run security tests only')
    test_group.add_argument('--smoke', action='store_true',
                           help='Run smoke tests only')

    # Test modes
    mode_group = parser.add_argument_group('Test Modes')
    mode_group.add_argument('--quick', action='store_true',
                           help='Skip slow tests (>1s)')
    mode_group.add_argument('--failed', action='store_true',
                           help='Re-run only failed tests from last run')
    mode_group.add_argument('--watch', action='store_true',
                           help='Watch mode - re-run on file changes')

    # Reporting
    report_group = parser.add_argument_group('Reporting')
    report_group.add_argument('--coverage', action='store_true',
                             help='Generate coverage report')
    report_group.add_argument('--verbose', action='store_true',
                             help='Verbose output')

    # Execution
    exec_group = parser.add_argument_group('Execution')
    exec_group.add_argument('--parallel', action='store_true',
                           help='Run tests in parallel')
    exec_group.add_argument('--ci', action='store_true',
                           help='CI mode (strict, generate all reports)')
    exec_group.add_argument('--validate', action='store_true',
                           help='Run validators before tests')

    args = parser.parse_args()

    # Watch mode
    if args.watch:
        print("Starting test watcher...")
        from tests.test_watch import TestWatcher
        watcher = TestWatcher()
        watcher.run()
        return 0

    # Run tests
    runner = TestRunner(args)
    exit_code = runner.run_tests()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
