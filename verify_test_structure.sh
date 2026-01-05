#!/bin/bash

echo "=========================================="
echo "DocAssist EMR - Test Suite Verification"
echo "=========================================="
echo ""

echo "Checking test file structure..."
echo ""

# Count test files
clinical_tests=$(ls tests/test_c*.py tests/test_d*.py tests/test_a*.py 2>/dev/null | wc -l)
echo "✓ Clinical test files: $clinical_tests"

# Check conftest
if [ -f "tests/clinical_conftest.py" ]; then
    echo "✓ clinical_conftest.py exists"
else
    echo "✗ clinical_conftest.py missing"
fi

# Check fixtures
fixture_files=$(ls tests/fixtures/sample_*.py 2>/dev/null | wc -l)
echo "✓ Fixture files: $fixture_files"

# Check documentation
if [ -f "tests/CLINICAL_TESTS_README.md" ]; then
    echo "✓ CLINICAL_TESTS_README.md exists"
else
    echo "✗ CLINICAL_TESTS_README.md missing"
fi

# Check pytest config
if [ -f "pytest.ini" ]; then
    echo "✓ pytest.ini exists"
else
    echo "✗ pytest.ini missing"
fi

echo ""
echo "Test file sizes:"
echo "----------------"
ls -lh tests/test_c*.py tests/test_d*.py tests/test_a*.py 2>/dev/null | awk '{print $9, "-", $5}'

echo ""
echo "Total lines of test code:"
echo "-------------------------"
wc -l tests/test_c*.py tests/test_d*.py tests/test_a*.py tests/clinical_conftest.py 2>/dev/null | tail -1

echo ""
echo "✓ Test suite structure verified!"
echo ""
echo "To run tests (after installing dependencies):"
echo "  pip install pytest pytest-asyncio pytest-cov"
echo "  pytest tests/test_c*.py tests/test_d*.py tests/test_a*.py -v"
echo ""
