"""
Test Runner Configuration for DocAssist EMR

Defines test categories, timeouts, and execution strategies.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Test configuration for different test types
TEST_CONFIG = {
    'unit': {
        'paths': ['tests/unit/', 'tests/models/', 'tests/services/'],
        'exclude': [],
        'timeout': 10,  # seconds per test
        'parallel': True,
        'markers': ['unit', 'not integration', 'not load', 'not security'],
        'description': 'Fast, isolated unit tests',
    },

    'integration': {
        'paths': ['tests/integration/'],
        'exclude': [],
        'timeout': 60,
        'parallel': False,  # Shared database - run sequentially
        'markers': ['integration'],
        'description': 'Integration tests with database',
    },

    'load': {
        'paths': ['tests/load/'],
        'exclude': [],
        'timeout': 300,  # 5 minutes
        'parallel': False,
        'markers': ['load'],
        'description': 'Performance and load tests',
    },

    'security': {
        'paths': ['tests/security/'],
        'exclude': [],
        'timeout': 30,
        'parallel': True,
        'markers': ['security'],
        'description': 'Security and vulnerability tests',
    },

    'smoke': {
        'paths': ['tests/smoke/'],
        'exclude': [],
        'timeout': 5,
        'parallel': True,
        'markers': ['smoke'],
        'description': 'Quick smoke tests for basic functionality',
    },

    'clinical': {
        'paths': [
            'tests/test_clinical_*.py',
            'tests/test_diagnosis_*.py',
            'tests/test_drug_*.py',
        ],
        'exclude': [],
        'timeout': 30,
        'parallel': True,
        'markers': ['clinical', 'safety', 'nlp'],
        'description': 'Clinical workflow and medical logic tests',
    },
}

# Coverage configuration
COVERAGE_CONFIG = {
    'source': ['src/'],
    'omit': [
        '*/test_*',
        '*/__pycache__/*',
        '*/conftest.py',
        '*/__init__.py',
        '*/ui/*',  # UI tests require special setup
    ],
    'fail_under': 70,  # Minimum coverage percentage
    'report_formats': ['html', 'xml', 'term'],
    'show_missing': True,
    'precision': 2,
}

# Pytest timeout settings (in seconds)
TIMEOUT_CONFIG = {
    'default': 30,
    'unit': 10,
    'integration': 60,
    'load': 300,
    'security': 30,
    'smoke': 5,
}

# Validator configuration
VALIDATOR_CONFIG = {
    'import': {
        'enabled': True,
        'paths': ['src/', 'tests/'],
        'exclude': ['__pycache__', '.pyc', 'htmlcov'],
    },

    'syntax': {
        'enabled': True,
        'paths': ['src/', 'tests/'],
        'python_version': '3.11',
    },

    'type': {
        'enabled': True,
        'paths': ['src/'],
        'strict': False,  # Set to True for stricter type checking
        'exclude': ['src/ui/'],  # Flet has limited type support
    },

    'security': {
        'enabled': True,
        'paths': ['src/'],
        'severity': 'medium',  # low, medium, high
        'exclude_tests': ['B101'],  # assert_used (OK in tests)
    },
}

# Reporter configuration
REPORTER_CONFIG = {
    'formats': ['terminal', 'html', 'junit', 'json'],
    'output_dir': PROJECT_ROOT / 'test_results',
    'coverage_dir': PROJECT_ROOT / 'coverage_report',
    'history_dir': PROJECT_ROOT / 'test_results' / 'history',

    'terminal': {
        'show_passed': True,
        'show_skipped': True,
        'show_errors': True,
        'show_summary': True,
        'colorize': True,
    },

    'html': {
        'template': 'default',
        'include_charts': True,
        'include_history': True,
    },

    'junit': {
        'filename': 'junit.xml',
        'include_properties': True,
    },

    'json': {
        'filename': 'test_results.json',
        'pretty_print': True,
        'include_metadata': True,
    },
}

# CI/CD specific configuration
CI_CONFIG = {
    'strict_mode': True,
    'fail_on_warnings': False,
    'generate_all_reports': True,
    'upload_coverage': True,
    'check_coverage_diff': True,
    'min_coverage_increase': 0,  # Don't allow coverage to decrease
    'max_test_duration': 600,  # 10 minutes total
}

# Test watch mode configuration
WATCH_CONFIG = {
    'enabled': True,
    'watch_dirs': ['src/', 'tests/'],
    'watch_patterns': ['*.py'],
    'ignore_patterns': ['*/__pycache__/*', '*/.pyc', '*/htmlcov/*'],
    'debounce_seconds': 1,  # Wait 1 second after last change before running

    # Map file changes to relevant tests
    'test_mapping': {
        'src/services/database.py': ['tests/unit/test_database.py', 'tests/integration/'],
        'src/services/llm.py': ['tests/unit/test_llm.py'],
        'src/services/rag.py': ['tests/unit/test_rag.py'],
        'src/services/pdf.py': ['tests/unit/test_pdf.py'],
        'src/services/drugs/': ['tests/test_drug_*.py'],
        'src/services/diagnosis/': ['tests/test_diagnosis_*.py'],
        'src/services/clinical/': ['tests/test_clinical_*.py'],
        'src/models/schemas.py': ['tests/models/', 'tests/unit/test_schemas.py'],
        # UI changes run smoke tests
        'src/ui/': ['tests/smoke/'],
    },
}

# Flaky test configuration
FLAKY_CONFIG = {
    'max_retries': 3,
    'retry_delay': 1,  # seconds
    'track_flaky_tests': True,
    'flaky_threshold': 2,  # Number of failures before marking as flaky
}

# Performance baseline configuration
PERFORMANCE_CONFIG = {
    'track_performance': True,
    'baseline_file': PROJECT_ROOT / 'test_results' / 'performance_baseline.json',
    'regression_threshold': 1.5,  # Fail if test is 50% slower than baseline
    'benchmarks': {
        'database_insert': 0.1,  # seconds
        'database_query': 0.05,
        'rag_search': 2.0,
        'llm_generation': 5.0,
        'pdf_generation': 1.0,
    },
}

# Parallel execution configuration
PARALLEL_CONFIG = {
    'enabled': True,
    'auto_detect_cores': True,
    'max_workers': None,  # None = use all cores
    'safe_for_parallel': ['unit', 'security', 'smoke'],
    'sequential_only': ['integration', 'load'],  # Tests that share state
}

def get_test_config(test_type: str) -> dict:
    """Get configuration for a specific test type"""
    return TEST_CONFIG.get(test_type, {})


def get_timeout(test_type: str = 'default') -> int:
    """Get timeout for a specific test type"""
    return TIMEOUT_CONFIG.get(test_type, TIMEOUT_CONFIG['default'])


def is_parallel_safe(test_type: str) -> bool:
    """Check if a test type can be run in parallel"""
    return test_type in PARALLEL_CONFIG['safe_for_parallel']
