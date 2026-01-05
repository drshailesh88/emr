# Test Runner Quick Reference

## Common Commands

```bash
# Development
python run_tests.py --unit --quick        # Fast unit tests
python run_tests.py --failed              # Re-run failures
python run_tests.py --watch               # Auto-run on changes

# Before Commit
python run_tests.py --unit --integration --coverage

# CI/CD
python run_tests.py --ci --parallel

# Specific Suites
python run_tests.py --smoke               # Smoke tests
python run_tests.py --security            # Security tests
python run_tests.py --load                # Performance tests

# With Options
python run_tests.py --verbose             # Detailed output
python run_tests.py --validate            # Run validators first
```

## Test Markers

```python
@pytest.mark.unit         # Fast unit test
@pytest.mark.integration  # Integration test
@pytest.mark.slow         # Slow test (>1s)
@pytest.mark.smoke        # Quick sanity check
@pytest.mark.security     # Security test
@pytest.mark.load         # Performance test
@pytest.mark.clinical     # Clinical workflow
```

## Pytest Direct Commands

```bash
# Run specific file
pytest tests/unit/test_database.py -v

# Run specific test
pytest tests/unit/test_database.py::test_create_patient -v

# Run by marker
pytest -m unit -v
pytest -m "not slow" -v

# With debugger
pytest tests/unit/test_database.py --pdb

# Coverage
pytest --cov=src --cov-report=html
```

## Tox Commands

```bash
tox                 # Run all environments
tox -e py311        # Python 3.11 tests
tox -e lint         # Linting only
tox -e type         # Type checking
tox -e security     # Security scan
tox -e coverage     # With coverage
tox -e quick        # Fast tests
```

## File Locations

```
tests/
  unit/           # Unit tests
  integration/    # Integration tests
  smoke/          # Smoke tests
  security/       # Security tests
  load/           # Performance tests
  validators/     # Pre-test validators

test_results/     # Test reports
  junit.xml       # JUnit XML
  summary.txt     # Summary report
  pytest.log      # Detailed logs

htmlcov/          # Coverage HTML
coverage.xml      # Coverage XML
```

## Coverage

```bash
# Generate HTML coverage report
python run_tests.py --coverage
open htmlcov/index.html

# Quick coverage check
pytest --cov=src --cov-report=term

# CI coverage
pytest --cov=src --cov-report=xml --cov-fail-under=70
```

## Validators

```bash
# Run all validators
python run_tests.py --validate

# Individual validators
pytest tests/validators/test_import_validator.py
pytest tests/validators/test_syntax_validator.py
pytest tests/validators/test_type_validator.py
pytest tests/validators/test_security_validator.py
```

## Debugging

```bash
# Verbose output
pytest -vv

# Show print statements
pytest -s

# Last failed tests
pytest --lf

# Step-through failures
pytest --pdb

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

## Environment Variables

```bash
# Pytest options
PYTEST_ADDOPTS="-v --tb=short" pytest

# Coverage threshold
MIN_COVERAGE=80 python run_tests.py --coverage

# Skip validators
SKIP_VALIDATORS=1 python run_tests.py
```

## Exit Codes

- `0` - All tests passed
- `1` - Tests failed
- `2` - Interrupted
- `3` - Internal error
- `4` - Usage error
- `5` - No tests collected
