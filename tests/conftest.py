"""Pytest configuration and fixtures for DocAssist tests.

This module configures imports to allow testing of individual services
without loading heavy dependencies (chromadb, sentence-transformers, etc.)
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock
from typing import Dict
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mock heavy dependencies before they're imported
# This allows testing backup/crypto/sync without chromadb, sentence-transformers, etc.
MOCK_MODULES = [
    'chromadb',
    'chromadb.config',
    'chromadb.api',
    'sentence_transformers',
    'flet',
    'fpdf',
    'fpdf2',
]

for mod_name in MOCK_MODULES:
    if mod_name not in sys.modules:
        mock = MagicMock()
        # Make FPDF class available
        if mod_name == 'fpdf':
            mock.FPDF = MagicMock()
        sys.modules[mod_name] = mock


# Global test timing tracking
test_timings: Dict[str, float] = {}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Track test execution time"""
    start_time = time.time()
    yield
    duration = time.time() - start_time

    test_timings[item.nodeid] = duration

    # Warn about slow tests (> 1s for unit tests)
    if 'unit' in item.nodeid and duration > 1.0:
        print(f"\n⚠️  Slow test detected: {item.nodeid} took {duration:.2f}s")


@pytest.hookimpl()
def pytest_sessionfinish(session, exitstatus):
    """Print timing summary at end of test session"""
    if test_timings:
        print("\n" + "="*70)
        print("Slowest Tests:")
        print("="*70)

        sorted_tests = sorted(test_timings.items(), key=lambda x: x[1], reverse=True)
        for test_name, duration in sorted_tests[:10]:
            print(f"  {duration:6.2f}s - {test_name}")


@pytest.fixture
def temp_db():
    """Provide a temporary database for testing"""
    import tempfile
    import sqlite3

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)

    yield conn

    conn.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_patient():
    """Provide sample patient data"""
    return {
        'uhid': 'EMR-2024-0001',
        'name': 'John Doe',
        'age': 45,
        'gender': 'M',
        'phone': '9876543210',
        'address': 'Test Address, City',
    }


@pytest.fixture
def sample_visit():
    """Provide sample visit data"""
    return {
        'patient_id': 1,
        'visit_date': '2024-01-15',
        'chief_complaint': 'Chest pain',
        'clinical_notes': 'Patient presents with chest pain radiating to left arm',
        'diagnosis': 'Unstable angina',
    }


@pytest.fixture
def sample_prescription():
    """Provide sample prescription data"""
    return {
        'diagnosis': ['Hypertension', 'Diabetes Type 2'],
        'medications': [
            {
                'drug_name': 'Metformin',
                'strength': '500mg',
                'form': 'tablet',
                'dose': '1',
                'frequency': 'BD',
                'duration': '30 days',
                'instructions': 'after meals',
            },
            {
                'drug_name': 'Amlodipine',
                'strength': '5mg',
                'form': 'tablet',
                'dose': '1',
                'frequency': 'OD',
                'duration': '30 days',
                'instructions': 'morning',
            },
        ],
        'investigations': ['HbA1c', 'Lipid Profile'],
        'advice': ['Low salt diet', 'Regular exercise'],
        'follow_up': '2 weeks',
    }


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test"""
    yield
    # Cleanup logic runs after test
    # Could delete temp files, reset database, etc.


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, uses database)"
    )
    config.addinivalue_line(
        "markers", "load: Load and performance tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )
    config.addinivalue_line(
        "markers", "smoke: Quick smoke tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take > 1 second"
    )
    config.addinivalue_line(
        "markers", "clinical: Clinical workflow tests"
    )
    config.addinivalue_line(
        "markers", "safety: Drug safety tests"
    )
    config.addinivalue_line(
        "markers", "nlp: Clinical NLP tests"
    )
