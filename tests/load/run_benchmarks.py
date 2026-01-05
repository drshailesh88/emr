#!/usr/bin/env python3
"""Enhanced benchmark runner with baseline comparison and regression detection.

This script runs all load tests, compares against baseline results,
and flags performance regressions.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.load.benchmarks import BENCHMARKS, MEMORY_BENCHMARKS, CONCURRENCY_BENCHMARKS


class BenchmarkRunner:
    """Enhanced benchmark runner with regression detection."""

    def __init__(self, output_dir: str = "test_results/load"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_file = self.output_dir / 'baseline.json'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'benchmarks': {},
            'test_suites': [],
            'regressions': [],
            'improvements': [],
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'regressions_found': 0,
                'improvements_found': 0
            }
        }

    def run_test_suite(self, test_file: str, suite_name: str) -> bool:
        """Run a single test suite and capture results.

        Args:
            test_file: Test file name
            suite_name: Name of the test suite

        Returns:
            True if tests passed, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"Running: {suite_name}")
        print(f"{'='*70}\n")

        test_path = Path(__file__).parent / test_file

        # Run pytest
        cmd = [
            'pytest',
            str(test_path),
            '-v',
            '-s',
            '--tb=short',
        ]

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=False)
        duration = time.time() - start_time

        suite_result = {
            'name': suite_name,
            'file': test_file,
            'duration_seconds': duration,
            'exit_code': result.returncode,
            'passed': result.returncode == 0
        }

        self.results['test_suites'].append(suite_result)

        if result.returncode == 0:
            self.results['summary']['passed'] += 1
            print(f"\n✓ {suite_name} PASSED")
        else:
            self.results['summary']['failed'] += 1
            print(f"\n✗ {suite_name} FAILED")

        self.results['summary']['total_tests'] += 1

        return result.returncode == 0

    def run_all_benchmarks(self, include_slow: bool = False):
        """Run all benchmark test suites.

        Args:
            include_slow: Whether to include slow tests (50K+ patients)
        """
        print("\n" + "="*70)
        print("DocAssist EMR - Enhanced Benchmark Suite")
        print("="*70)

        test_suites = [
            ('test_startup_time.py', 'startup_time'),
            ('test_database_scale.py', 'database_scale'),
            ('test_database_performance.py', 'database_performance'),
            ('test_search_performance.py', 'search_performance'),
            ('test_concurrent_users.py', 'concurrent_users'),
            ('test_memory_usage.py', 'memory_usage'),
            ('test_llm_performance.py', 'llm_performance'),
        ]

        if not include_slow:
            print("\nSkipping slow tests (50K+ patients). Use --include-slow to run them.")

        overall_start = time.time()

        for test_file, suite_name in test_suites:
            try:
                # Skip slow tests unless requested
                if 'scale' in suite_name and not include_slow:
                    # Run with marker to skip slow tests
                    print(f"\n{'='*70}")
                    print(f"Running: {suite_name} (skipping slow tests)")
                    print(f"{'='*70}\n")

                    test_path = Path(__file__).parent / test_file
                    cmd = ['pytest', str(test_path), '-v', '-s', '-m', 'not slow']

                    start_time = time.time()
                    result = subprocess.run(cmd, capture_output=False)
                    duration = time.time() - start_time

                    suite_result = {
                        'name': suite_name,
                        'file': test_file,
                        'duration_seconds': duration,
                        'exit_code': result.returncode,
                        'passed': result.returncode == 0
                    }
                    self.results['test_suites'].append(suite_result)

                    if result.returncode == 0:
                        self.results['summary']['passed'] += 1
                    else:
                        self.results['summary']['failed'] += 1

                    self.results['summary']['total_tests'] += 1
                else:
                    self.run_test_suite(test_file, suite_name)

            except Exception as e:
                print(f"\nError running {suite_name}: {e}")
                self.results['test_suites'].append({
                    'name': suite_name,
                    'file': test_file,
                    'error': str(e),
                    'passed': False
                })
                self.results['summary']['failed'] += 1
                self.results['summary']['total_tests'] += 1

        self.results['total_duration_seconds'] = time.time() - overall_start

    def load_baseline(self) -> Optional[Dict]:
        """Load baseline benchmark results.

        Returns:
            Baseline results dict or None if not found
        """
        if not self.baseline_file.exists():
            return None

        try:
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load baseline: {e}")
            return None

    def save_baseline(self):
        """Save current results as baseline."""
        try:
            with open(self.baseline_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\nBaseline saved to: {self.baseline_file}")
        except Exception as e:
            print(f"Warning: Could not save baseline: {e}")

    def compare_with_baseline(self) -> bool:
        """Compare current results with baseline.

        Returns:
            True if no regressions found, False otherwise
        """
        baseline = self.load_baseline()
        if not baseline:
            print("\nNo baseline found. Run with --save-baseline to create one.")
            return True

        print("\n" + "="*70)
        print("Baseline Comparison")
        print("="*70)

        baseline_timestamp = baseline.get('timestamp', 'Unknown')
        print(f"\nBaseline: {baseline_timestamp}")
        print(f"Current: {self.results['timestamp']}")

        # Compare test suite durations
        baseline_suites = {s['name']: s for s in baseline.get('test_suites', [])}
        current_suites = {s['name']: s for s in self.results['test_suites']}

        regression_threshold = 1.20  # 20% slower is a regression
        improvement_threshold = 0.80  # 20% faster is an improvement

        for suite_name, current in current_suites.items():
            if suite_name not in baseline_suites:
                continue

            baseline_duration = baseline_suites[suite_name].get('duration_seconds', 0)
            current_duration = current.get('duration_seconds', 0)

            if baseline_duration == 0:
                continue

            ratio = current_duration / baseline_duration

            if ratio >= regression_threshold:
                # Performance regression
                degradation = (ratio - 1) * 100
                self.results['regressions'].append({
                    'suite': suite_name,
                    'baseline_seconds': baseline_duration,
                    'current_seconds': current_duration,
                    'degradation_percent': degradation
                })
                self.results['summary']['regressions_found'] += 1

                print(f"\n⚠ REGRESSION: {suite_name}")
                print(f"  Baseline: {baseline_duration:.2f}s")
                print(f"  Current: {current_duration:.2f}s")
                print(f"  Degradation: {degradation:+.1f}%")

            elif ratio <= improvement_threshold:
                # Performance improvement
                improvement = (1 - ratio) * 100
                self.results['improvements'].append({
                    'suite': suite_name,
                    'baseline_seconds': baseline_duration,
                    'current_seconds': current_duration,
                    'improvement_percent': improvement
                })
                self.results['summary']['improvements_found'] += 1

                print(f"\n✓ IMPROVEMENT: {suite_name}")
                print(f"  Baseline: {baseline_duration:.2f}s")
                print(f"  Current: {current_duration:.2f}s")
                print(f"  Improvement: {improvement:.1f}%")

        if not self.results['regressions'] and not self.results['improvements']:
            print("\nNo significant performance changes detected.")

        return len(self.results['regressions']) == 0

    def generate_report(self):
        """Generate comprehensive benchmark report."""
        report_path = self.output_dir / 'benchmark_report.md'

        with open(report_path, 'w') as f:
            f.write("# DocAssist EMR - Load Test Benchmark Report\n\n")
            f.write(f"**Generated:** {self.results['timestamp']}\n\n")
            f.write(f"**Duration:** {self.results.get('total_duration_seconds', 0):.2f} seconds\n\n")

            # Summary
            f.write("## Summary\n\n")
            summary = self.results['summary']
            f.write(f"- **Total Test Suites:** {summary['total_tests']}\n")
            f.write(f"- **Passed:** {summary['passed']} ✓\n")
            f.write(f"- **Failed:** {summary['failed']} ✗\n")
            f.write(f"- **Regressions Found:** {summary['regressions_found']} ⚠\n")
            f.write(f"- **Improvements Found:** {summary['improvements_found']} ↑\n\n")

            # Test Results
            f.write("## Test Suite Results\n\n")
            f.write("| Test Suite | Status | Duration |\n")
            f.write("|------------|--------|----------|\n")

            for suite in self.results['test_suites']:
                status = "✓ PASS" if suite.get('passed', False) else "✗ FAIL"
                duration = suite.get('duration_seconds', 0)
                f.write(f"| {suite['name']} | {status} | {duration:.2f}s |\n")

            f.write("\n")

            # Regressions
            if self.results['regressions']:
                f.write("## ⚠ Performance Regressions\n\n")
                f.write("| Test Suite | Baseline | Current | Degradation |\n")
                f.write("|------------|----------|---------|-------------|\n")

                for reg in self.results['regressions']:
                    f.write(f"| {reg['suite']} | "
                           f"{reg['baseline_seconds']:.2f}s | "
                           f"{reg['current_seconds']:.2f}s | "
                           f"+{reg['degradation_percent']:.1f}% |\n")

                f.write("\n")

            # Improvements
            if self.results['improvements']:
                f.write("## ↑ Performance Improvements\n\n")
                f.write("| Test Suite | Baseline | Current | Improvement |\n")
                f.write("|------------|----------|---------|-------------|\n")

                for imp in self.results['improvements']:
                    f.write(f"| {imp['suite']} | "
                           f"{imp['baseline_seconds']:.2f}s | "
                           f"{imp['current_seconds']:.2f}s | "
                           f"-{imp['improvement_percent']:.1f}% |\n")

                f.write("\n")

            # Benchmark Targets
            f.write("## Performance Targets\n\n")
            f.write("### Time Benchmarks (milliseconds)\n\n")
            f.write("| Operation | Target | Maximum | Description |\n")
            f.write("|-----------|--------|---------|-------------|\n")

            for op_name, bench in BENCHMARKS.items():
                f.write(f"| {op_name} | "
                       f"{bench['target_ms']}ms | "
                       f"{bench['max_ms']}ms | "
                       f"{bench['description']} |\n")

            f.write("\n")

            f.write("### Memory Benchmarks (MB)\n\n")
            f.write("| Operation | Target | Maximum | Description |\n")
            f.write("|-----------|--------|---------|-------------|\n")

            for op_name, bench in MEMORY_BENCHMARKS.items():
                f.write(f"| {op_name} | "
                       f"{bench['target_mb']}MB | "
                       f"{bench['max_mb']}MB | "
                       f"{bench['description']} |\n")

            f.write("\n")

        print(f"\nBenchmark report generated: {report_path}")
        return report_path

    def save_json_report(self):
        """Save results as JSON."""
        json_path = self.output_dir / 'benchmark_results.json'
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"JSON report saved: {json_path}")
        return json_path

    def print_summary(self):
        """Print summary to console."""
        print("\n" + "="*70)
        print("BENCHMARK SUMMARY")
        print("="*70)

        summary = self.results['summary']
        print(f"\nTotal Test Suites: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✓")
        print(f"Failed: {summary['failed']} ✗")
        print(f"Duration: {self.results.get('total_duration_seconds', 0):.2f} seconds")

        if summary['regressions_found'] > 0:
            print(f"\n⚠ Performance Regressions: {summary['regressions_found']}")
            print("  WARNING: Some tests are slower than baseline!")

        if summary['improvements_found'] > 0:
            print(f"\n↑ Performance Improvements: {summary['improvements_found']}")

        print("\nTest Suite Results:")
        for suite in self.results['test_suites']:
            status = "✓ PASS" if suite.get('passed', False) else "✗ FAIL"
            duration = suite.get('duration_seconds', 0)
            print(f"  {status} - {suite['name']} ({duration:.2f}s)")

        print("\n" + "="*70 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run DocAssist EMR load test benchmarks'
    )
    parser.add_argument(
        '--output-dir',
        default='test_results/load',
        help='Output directory for test results'
    )
    parser.add_argument(
        '--save-baseline',
        action='store_true',
        help='Save current results as baseline for future comparisons'
    )
    parser.add_argument(
        '--include-slow',
        action='store_true',
        help='Include slow tests (50K+ patients)'
    )
    parser.add_argument(
        '--suite',
        help='Run specific test suite only'
    )

    args = parser.parse_args()

    runner = BenchmarkRunner(output_dir=args.output_dir)

    if args.suite:
        # Run specific suite
        suite_files = {
            'startup': 'test_startup_time.py',
            'scale': 'test_database_scale.py',
            'database': 'test_database_performance.py',
            'search': 'test_search_performance.py',
            'concurrent': 'test_concurrent_users.py',
            'memory': 'test_memory_usage.py',
            'llm': 'test_llm_performance.py',
        }

        if args.suite in suite_files:
            runner.run_test_suite(suite_files[args.suite], args.suite)
        else:
            print(f"Unknown test suite: {args.suite}")
            print(f"Available suites: {', '.join(suite_files.keys())}")
            sys.exit(1)
    else:
        # Run all benchmarks
        runner.run_all_benchmarks(include_slow=args.include_slow)

    # Generate reports
    runner.save_json_report()
    runner.generate_report()

    # Compare with baseline
    no_regressions = runner.compare_with_baseline()

    # Save baseline if requested
    if args.save_baseline:
        runner.save_baseline()

    # Print summary
    runner.print_summary()

    # Exit with error if tests failed or regressions found
    if runner.results['summary']['failed'] > 0:
        print("❌ Some tests failed!")
        sys.exit(1)

    if not no_regressions:
        print("⚠ Performance regressions detected!")
        sys.exit(1)

    print("✓ All benchmarks passed!")
    sys.exit(0)


if __name__ == '__main__':
    main()
