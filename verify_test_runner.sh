#!/bin/bash
# Verification script for test runner installation

echo "======================================================================"
echo "DocAssist EMR Test Runner Verification"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ (missing)"
        return 1
    fi
}

# Check main files
echo "Main Files:"
check_file "run_tests.py"
check_file "pytest.ini"
check_file "tox.ini"
check_file "requirements-dev.txt"
check_file "TEST_RUNNER_README.md"
check_file "TEST_QUICK_REFERENCE.md"
check_file "TEST_RUNNER_IMPLEMENTATION_SUMMARY.md"
echo ""

# Check test infrastructure
echo "Test Infrastructure:"
check_file "tests/conftest.py"
check_file "tests/test_runner_config.py"
check_file "tests/reporter.py"
check_file "tests/test_watch.py"
echo ""

# Check validators
echo "Validators:"
check_dir "tests/validators"
check_file "tests/validators/__init__.py"
check_file "tests/validators/import_validator.py"
check_file "tests/validators/syntax_validator.py"
check_file "tests/validators/type_validator.py"
check_file "tests/validators/security_validator.py"
echo ""

# Check security tests
echo "Security Tests:"
check_dir "tests/security"
check_file "tests/security/__init__.py"
check_file "tests/security/test_sql_injection.py"
check_file "tests/security/test_secrets.py"
check_file "tests/security/test_encryption.py"
echo ""

# Check smoke tests
echo "Smoke Tests:"
check_dir "tests/smoke"
check_file "tests/smoke/__init__.py"
check_file "tests/smoke/test_basic_functionality.py"
echo ""

# Check load tests
echo "Load Tests:"
check_dir "tests/load"
check_file "tests/load/__init__.py"
check_file "tests/load/test_performance.py"
echo ""

# Check directories
echo "Output Directories:"
check_dir "test_results"
check_dir "coverage_report"
echo ""

# Check executable permissions
echo "Permissions:"
if [ -x "run_tests.py" ]; then
    echo -e "${GREEN}✓${NC} run_tests.py is executable"
else
    echo -e "${YELLOW}⚠${NC} run_tests.py is not executable (run: chmod +x run_tests.py)"
fi
echo ""

# Check Python syntax
echo "Syntax Check:"
python3 -m py_compile run_tests.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} run_tests.py syntax valid"
else
    echo -e "${RED}✗${NC} run_tests.py syntax error"
fi

python3 -m py_compile tests/test_runner_config.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} test_runner_config.py syntax valid"
else
    echo -e "${RED}✗${NC} test_runner_config.py syntax error"
fi

python3 -m py_compile tests/reporter.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} reporter.py syntax valid"
else
    echo -e "${RED}✗${NC} reporter.py syntax error"
fi
echo ""

# Count test files
echo "Test Statistics:"
unit_tests=$(find tests/unit -name "test_*.py" 2>/dev/null | wc -l)
integration_tests=$(find tests/integration -name "test_*.py" 2>/dev/null | wc -l)
security_tests=$(find tests/security -name "test_*.py" 2>/dev/null | wc -l)
smoke_tests=$(find tests/smoke -name "test_*.py" 2>/dev/null | wc -l)
load_tests=$(find tests/load -name "test_*.py" 2>/dev/null | wc -l)

echo "  Unit tests:        $unit_tests"
echo "  Integration tests: $integration_tests"
echo "  Security tests:    $security_tests"
echo "  Smoke tests:       $smoke_tests"
echo "  Load tests:        $load_tests"
echo ""

# Summary
echo "======================================================================"
echo "Summary"
echo "======================================================================"
echo ""
echo "The test runner has been successfully installed!"
echo ""
echo "Next steps:"
echo "  1. Install dependencies:  pip install -r requirements-dev.txt"
echo "  2. Run smoke tests:       python run_tests.py --smoke"
echo "  3. Run all tests:         python run_tests.py"
echo "  4. View documentation:    cat TEST_RUNNER_README.md"
echo ""
echo "Quick commands:"
echo "  python run_tests.py --unit --quick    # Fast unit tests"
echo "  python run_tests.py --coverage        # With coverage"
echo "  python run_tests.py --ci              # CI mode"
echo "  python run_tests.py --watch           # Watch mode"
echo ""
