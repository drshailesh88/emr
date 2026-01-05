#!/usr/bin/env python3
"""Load test runner with reporting.

This script runs all load tests and generates a comprehensive HTML report
with charts showing performance metrics against benchmarks.
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class LoadTestRunner:
    """Runs load tests and generates reports."""

    def __init__(self, output_dir: str = "test_results/load"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {
            'start_time': datetime.now().isoformat(),
            'test_suites': [],
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'duration_seconds': 0
            }
        }

    def run_test_suite(self, test_file: str, suite_name: str):
        """Run a single test suite."""
        print(f"\n{'='*70}")
        print(f"Running: {suite_name}")
        print(f"{'='*70}\n")

        test_path = Path(__file__).parent / test_file

        # Run pytest with JSON report
        cmd = [
            'pytest',
            str(test_path),
            '-v',
            '-s',
            '--tb=short',
            f'--json-report',
            f'--json-report-file={self.output_dir}/{suite_name}.json'
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

        return result.returncode == 0

    def run_all_tests(self):
        """Run all load test suites."""
        print("\n" + "="*70)
        print("DocAssist EMR - Load Test Suite")
        print("="*70)

        test_suites = [
            ('test_database_performance.py', 'database_performance'),
            ('test_search_performance.py', 'search_performance'),
            ('test_report_generation.py', 'report_generation'),
            ('test_concurrent_users.py', 'concurrent_users'),
            ('test_memory_usage.py', 'memory_usage'),
            ('test_llm_performance.py', 'llm_performance'),
        ]

        overall_start = time.time()

        for test_file, suite_name in test_suites:
            try:
                self.run_test_suite(test_file, suite_name)
            except Exception as e:
                print(f"\nError running {suite_name}: {e}")
                self.results['test_suites'].append({
                    'name': suite_name,
                    'file': test_file,
                    'error': str(e),
                    'passed': False
                })

        self.results['summary']['duration_seconds'] = time.time() - overall_start
        self.results['end_time'] = datetime.now().isoformat()

        # Calculate summary
        self.results['summary']['total_suites'] = len(self.results['test_suites'])
        self.results['summary']['passed_suites'] = sum(
            1 for s in self.results['test_suites'] if s.get('passed', False)
        )
        self.results['summary']['failed_suites'] = (
            self.results['summary']['total_suites'] -
            self.results['summary']['passed_suites']
        )

    def generate_html_report(self):
        """Generate HTML report with charts."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DocAssist EMR - Load Test Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .passed {{
            color: #27ae60;
        }}
        .failed {{
            color: #e74c3c;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #34495e;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .status-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        .badge-passed {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>DocAssist EMR - Load Test Report</h1>

        <div class="timestamp">
            Generated: {self.results['end_time']}<br>
            Duration: {self.results['summary']['duration_seconds']:.2f} seconds
        </div>

        <h2>Summary</h2>
        <div class="summary">
            <div class="metric">
                <div class="metric-value">{self.results['summary']['total_suites']}</div>
                <div class="metric-label">Total Test Suites</div>
            </div>
            <div class="metric">
                <div class="metric-value passed">{self.results['summary']['passed_suites']}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value failed">{self.results['summary']['failed_suites']}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{self.results['summary']['duration_seconds']:.1f}s</div>
                <div class="metric-label">Total Duration</div>
            </div>
        </div>

        <h2>Test Suite Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Suite</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>File</th>
                </tr>
            </thead>
            <tbody>
"""

        for suite in self.results['test_suites']:
            status = "PASSED" if suite.get('passed', False) else "FAILED"
            status_class = "badge-passed" if suite.get('passed', False) else "badge-failed"
            duration = suite.get('duration_seconds', 0)

            html += f"""
                <tr>
                    <td><strong>{suite['name']}</strong></td>
                    <td><span class="status-badge {status_class}">{status}</span></td>
                    <td>{duration:.2f}s</td>
                    <td><code>{suite['file']}</code></td>
                </tr>
"""

        html += """
            </tbody>
        </table>

        <h2>Performance Benchmarks</h2>
        <p>For detailed performance metrics and benchmark comparisons, please review the individual test outputs.</p>

        <h2>Test Coverage</h2>
        <ul>
            <li><strong>Database Performance:</strong> Patient search, pagination, bulk operations</li>
            <li><strong>Search Performance:</strong> Phonetic, fuzzy, natural language search</li>
            <li><strong>Report Generation:</strong> Daily summaries, analytics, audit trails</li>
            <li><strong>Concurrent Users:</strong> Multi-user scenarios, burst loads</li>
            <li><strong>Memory Usage:</strong> Memory profiling, leak detection</li>
            <li><strong>LLM Performance:</strong> Queue handling, timeout management</li>
        </ul>

        <div class="footer">
            <p>DocAssist EMR - Load Testing Suite</p>
            <p>Generated by run_load_tests.py</p>
        </div>
    </div>
</body>
</html>
"""

        report_path = self.output_dir / 'load_test_report.html'
        with open(report_path, 'w') as f:
            f.write(html)

        print(f"\n{'='*70}")
        print(f"HTML Report generated: {report_path}")
        print(f"{'='*70}\n")

        return report_path

    def save_json_report(self):
        """Save results as JSON."""
        json_path = self.output_dir / 'load_test_results.json'
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"JSON Report saved: {json_path}\n")
        return json_path

    def print_summary(self):
        """Print summary to console."""
        print("\n" + "="*70)
        print("LOAD TEST SUMMARY")
        print("="*70)

        print(f"\nTotal Test Suites: {self.results['summary']['total_suites']}")
        print(f"Passed: {self.results['summary']['passed_suites']}")
        print(f"Failed: {self.results['summary']['failed_suites']}")
        print(f"Duration: {self.results['summary']['duration_seconds']:.2f} seconds")

        print("\nTest Suite Results:")
        for suite in self.results['test_suites']:
            status = "✓ PASSED" if suite.get('passed', False) else "✗ FAILED"
            duration = suite.get('duration_seconds', 0)
            print(f"  {status} - {suite['name']} ({duration:.2f}s)")

        print("\n" + "="*70 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Run DocAssist EMR load tests')
    parser.add_argument(
        '--output-dir',
        default='test_results/load',
        help='Output directory for test results'
    )
    parser.add_argument(
        '--suite',
        help='Run specific test suite (e.g., database_performance)'
    )

    args = parser.parse_args()

    runner = LoadTestRunner(output_dir=args.output_dir)

    if args.suite:
        # Run specific suite
        suite_files = {
            'database_performance': 'test_database_performance.py',
            'search_performance': 'test_search_performance.py',
            'report_generation': 'test_report_generation.py',
            'concurrent_users': 'test_concurrent_users.py',
            'memory_usage': 'test_memory_usage.py',
            'llm_performance': 'test_llm_performance.py',
        }

        if args.suite in suite_files:
            runner.run_test_suite(suite_files[args.suite], args.suite)
        else:
            print(f"Unknown test suite: {args.suite}")
            print(f"Available suites: {', '.join(suite_files.keys())}")
            sys.exit(1)
    else:
        # Run all tests
        runner.run_all_tests()

    # Generate reports
    runner.save_json_report()
    runner.generate_html_report()
    runner.print_summary()

    # Exit with error if any tests failed
    if runner.results['summary']['failed_suites'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
