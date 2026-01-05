"""
Test Reporter for DocAssist EMR

Generates comprehensive test reports in multiple formats:
- Terminal summary
- HTML report with charts
- JUnit XML for CI
- JSON for programmatic access
- Coverage badges
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET


@dataclass
class TestResult:
    """Single test result"""
    name: str
    status: str  # passed, failed, skipped, error
    duration: float
    message: Optional[str] = None
    traceback: Optional[str] = None
    markers: List[str] = None


@dataclass
class TestSuite:
    """Test suite results"""
    name: str
    tests: List[TestResult]
    total: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float


@dataclass
class TestResults:
    """Complete test run results"""
    timestamp: str
    duration: float
    total: int
    passed: int
    failed: int
    skipped: int
    errors: int
    coverage: Optional[float] = None
    suites: List[TestSuite] = None


class TestReporter:
    """Generate comprehensive test reports"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results_dir = self.project_root / 'test_results'
        self.results_dir.mkdir(exist_ok=True)

    def generate_summary_report(self) -> str:
        """Generate terminal summary from JUnit XML"""
        junit_path = self.results_dir / 'junit.xml'

        if not junit_path.exists():
            return "No test results found. Run tests with --ci flag to generate reports."

        try:
            results = self._parse_junit_xml(junit_path)
            return self._format_terminal_summary(results)
        except Exception as e:
            return f"Error generating summary: {e}"

    def _parse_junit_xml(self, xml_path: Path) -> TestResults:
        """Parse JUnit XML file"""
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Parse testsuites
        suites = []
        total = passed = failed = skipped = errors = 0
        total_duration = 0.0

        for testsuite in root.findall('.//testsuite'):
            suite_name = testsuite.get('name', 'unknown')
            suite_tests = []

            for testcase in testsuite.findall('testcase'):
                test_name = testcase.get('name', 'unknown')
                test_duration = float(testcase.get('time', 0))

                # Determine status
                failure = testcase.find('failure')
                error = testcase.find('error')
                skipped_elem = testcase.find('skipped')

                if failure is not None:
                    status = 'failed'
                    message = failure.get('message', '')
                    traceback = failure.text
                    failed += 1
                elif error is not None:
                    status = 'error'
                    message = error.get('message', '')
                    traceback = error.text
                    errors += 1
                elif skipped_elem is not None:
                    status = 'skipped'
                    message = skipped_elem.get('message', '')
                    traceback = None
                    skipped += 1
                else:
                    status = 'passed'
                    message = None
                    traceback = None
                    passed += 1

                total += 1

                suite_tests.append(TestResult(
                    name=test_name,
                    status=status,
                    duration=test_duration,
                    message=message,
                    traceback=traceback
                ))

            suite_duration = float(testsuite.get('time', 0))
            total_duration += suite_duration

            suites.append(TestSuite(
                name=suite_name,
                tests=suite_tests,
                total=len(suite_tests),
                passed=len([t for t in suite_tests if t.status == 'passed']),
                failed=len([t for t in suite_tests if t.status == 'failed']),
                skipped=len([t for t in suite_tests if t.status == 'skipped']),
                errors=len([t for t in suite_tests if t.status == 'error']),
                duration=suite_duration
            ))

        return TestResults(
            timestamp=datetime.now().isoformat(),
            duration=total_duration,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            suites=suites
        )

    def _format_terminal_summary(self, results: TestResults) -> str:
        """Format results as terminal summary"""
        lines = []
        lines.append("=" * 70)
        lines.append("TEST RESULTS SUMMARY")
        lines.append("=" * 70)
        lines.append("")

        # Overall stats
        lines.append(f"Total Tests:    {results.total}")
        lines.append(f"✓ Passed:       {results.passed}")
        lines.append(f"✗ Failed:       {results.failed}")
        lines.append(f"⊘ Skipped:      {results.skipped}")
        lines.append(f"⚠ Errors:       {results.errors}")
        lines.append(f"Duration:       {results.duration:.2f}s")
        lines.append("")

        # Pass rate
        if results.total > 0:
            pass_rate = (results.passed / results.total) * 100
            lines.append(f"Pass Rate:      {pass_rate:.1f}%")
            lines.append("")

        # Failed tests detail
        if results.failed > 0 or results.errors > 0:
            lines.append("=" * 70)
            lines.append("FAILED TESTS")
            lines.append("=" * 70)
            lines.append("")

            for suite in results.suites:
                failed_tests = [t for t in suite.tests if t.status in ['failed', 'error']]
                if failed_tests:
                    lines.append(f"{suite.name}:")
                    for test in failed_tests:
                        lines.append(f"  ✗ {test.name}")
                        if test.message:
                            lines.append(f"    {test.message}")
                    lines.append("")

        # Coverage
        if results.coverage:
            lines.append("=" * 70)
            lines.append(f"Coverage:       {results.coverage:.1f}%")
            lines.append("=" * 70)

        return "\n".join(lines)

    def generate_html_report(self, results: TestResults) -> str:
        """Generate HTML report with charts"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocAssist EMR Test Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin-bottom: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .stat-card {{ padding: 20px; border-radius: 8px; background: #f8f9fa; }}
        .stat-card h3 {{ font-size: 14px; color: #666; margin-bottom: 8px; }}
        .stat-card .value {{ font-size: 32px; font-weight: bold; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #ffc107; }}
        .errors {{ color: #fd7e14; }}
        .suite {{ margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        .suite h2 {{ font-size: 18px; margin-bottom: 15px; }}
        .test-item {{ padding: 10px; margin: 5px 0; border-left: 3px solid #ddd; padding-left: 15px; }}
        .test-item.passed {{ border-left-color: #28a745; background: #d4edda; }}
        .test-item.failed {{ border-left-color: #dc3545; background: #f8d7da; }}
        .test-item.skipped {{ border-left-color: #ffc107; background: #fff3cd; }}
        .test-name {{ font-weight: 500; }}
        .test-duration {{ color: #666; font-size: 12px; }}
        .test-message {{ margin-top: 8px; color: #dc3545; font-size: 14px; }}
        .progress-bar {{ width: 100%; height: 30px; background: #e9ecef; border-radius: 15px; overflow: hidden; margin: 20px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>DocAssist EMR Test Report</h1>
        <p style="color: #666; margin-bottom: 30px;">Generated: {results.timestamp}</p>

        <div class="stats">
            <div class="stat-card">
                <h3>Total Tests</h3>
                <div class="value">{results.total}</div>
            </div>
            <div class="stat-card">
                <h3>Passed</h3>
                <div class="value passed">{results.passed}</div>
            </div>
            <div class="stat-card">
                <h3>Failed</h3>
                <div class="value failed">{results.failed}</div>
            </div>
            <div class="stat-card">
                <h3>Skipped</h3>
                <div class="value skipped">{results.skipped}</div>
            </div>
            <div class="stat-card">
                <h3>Duration</h3>
                <div class="value">{results.duration:.1f}s</div>
            </div>
        </div>

        <div class="progress-bar">
            <div class="progress-fill" style="width: {(results.passed/results.total*100) if results.total > 0 else 0:.1f}%"></div>
        </div>

        <h2 style="margin: 30px 0 20px 0;">Test Suites</h2>
"""

        # Add test suites
        for suite in results.suites or []:
            html += f"""
        <div class="suite">
            <h2>{suite.name}</h2>
            <p style="color: #666; margin-bottom: 15px;">
                {suite.total} tests • {suite.passed} passed • {suite.failed} failed • {suite.duration:.2f}s
            </p>
"""
            for test in suite.tests:
                html += f"""
            <div class="test-item {test.status}">
                <div class="test-name">{test.name}</div>
                <div class="test-duration">{test.duration:.3f}s</div>
"""
                if test.message:
                    html += f'                <div class="test-message">{test.message}</div>\n'

                html += '            </div>\n'

            html += '        </div>\n'

        html += """
    </div>
</body>
</html>
"""
        return html

    def generate_junit_xml(self, results: TestResults) -> str:
        """Generate JUnit XML for CI"""
        root = ET.Element('testsuites')
        root.set('tests', str(results.total))
        root.set('failures', str(results.failed))
        root.set('errors', str(results.errors))
        root.set('skipped', str(results.skipped))
        root.set('time', str(results.duration))

        for suite in results.suites or []:
            testsuite = ET.SubElement(root, 'testsuite')
            testsuite.set('name', suite.name)
            testsuite.set('tests', str(suite.total))
            testsuite.set('failures', str(suite.failed))
            testsuite.set('errors', str(suite.errors))
            testsuite.set('skipped', str(suite.skipped))
            testsuite.set('time', str(suite.duration))

            for test in suite.tests:
                testcase = ET.SubElement(testsuite, 'testcase')
                testcase.set('name', test.name)
                testcase.set('time', str(test.duration))

                if test.status == 'failed':
                    failure = ET.SubElement(testcase, 'failure')
                    failure.set('message', test.message or 'Test failed')
                    if test.traceback:
                        failure.text = test.traceback
                elif test.status == 'error':
                    error = ET.SubElement(testcase, 'error')
                    error.set('message', test.message or 'Test error')
                    if test.traceback:
                        error.text = test.traceback
                elif test.status == 'skipped':
                    skipped = ET.SubElement(testcase, 'skipped')
                    skipped.set('message', test.message or 'Test skipped')

        return ET.tostring(root, encoding='unicode')

    def generate_coverage_badge(self, coverage: float) -> str:
        """Generate coverage badge SVG"""
        # Determine color based on coverage
        if coverage >= 90:
            color = '#4c1'
        elif coverage >= 75:
            color = '#97ca00'
        elif coverage >= 60:
            color = '#dfb317'
        else:
            color = '#e05d44'

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="20">
    <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <mask id="a">
        <rect width="120" height="20" rx="3" fill="#fff"/>
    </mask>
    <g mask="url(#a)">
        <path fill="#555" d="M0 0h63v20H0z"/>
        <path fill="{color}" d="M63 0h57v20H63z"/>
        <path fill="url(#b)" d="M0 0h120v20H0z"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
        <text x="31.5" y="15" fill="#010101" fill-opacity=".3">coverage</text>
        <text x="31.5" y="14">coverage</text>
        <text x="90.5" y="15" fill="#010101" fill-opacity=".3">{coverage:.0f}%</text>
        <text x="90.5" y="14">{coverage:.0f}%</text>
    </g>
</svg>"""
        return svg

    def save_json_report(self, results: TestResults, filename: str = 'test_results.json'):
        """Save results as JSON"""
        output_path = self.results_dir / filename
        with open(output_path, 'w') as f:
            json.dump(asdict(results), f, indent=2, default=str)

    def compare_to_baseline(self, results: TestResults, baseline_path: Optional[Path] = None):
        """Compare results to baseline and flag regressions"""
        if baseline_path is None:
            baseline_path = self.results_dir / 'baseline.json'

        if not baseline_path.exists():
            # No baseline - save current as baseline
            self.save_json_report(results, 'baseline.json')
            return None

        with open(baseline_path) as f:
            baseline = json.load(f)

        comparison = {
            'total_diff': results.total - baseline.get('total', 0),
            'passed_diff': results.passed - baseline.get('passed', 0),
            'failed_diff': results.failed - baseline.get('failed', 0),
            'duration_diff': results.duration - baseline.get('duration', 0),
            'regression': results.failed > baseline.get('failed', 0),
        }

        return comparison
