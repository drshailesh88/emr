# DocAssist EMR Test Runner

Comprehensive test execution and reporting system for DocAssist EMR.

## Quick Start

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
python run_tests.py

# Run specific test suites
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --smoke

# Run with coverage
python run_tests.py --coverage

# CI mode (strict, all reports)
python run_tests.py --ci
```

## Test Categories

### Unit Tests (`--unit`)
- Fast, isolated tests
- No external dependencies
- Run in parallel
- Located in: `tests/unit/`, `tests/models/`, `tests/services/`

### Integration Tests (`--integration`)
- Tests with database
- Run sequentially (shared state)
- Located in: `tests/integration/`

### Smoke Tests (`--smoke`)
- Quick sanity checks
- Verify basic functionality
- Run first in CI
- Located in: `tests/smoke/`

### Security Tests (`--security`)
- SQL injection prevention
- Secrets detection
- Encryption validation
- Located in: `tests/security/`

### Load Tests (`--load`)
- Performance tests
- Stress tests
- Located in: `tests/load/`

### Clinical Tests (`--clinical`)
- Clinical workflow tests
- Drug safety tests
- Diagnosis engine tests

## Usage Examples

### Development Workflow

```bash
# Quick feedback loop - fast tests only
python run_tests.py --quick

# Re-run only failed tests
python run_tests.py --failed

# Watch mode - auto-run on file changes
python run_tests.py --watch

# Run unit tests with coverage
python run_tests.py --unit --coverage
```

### CI/CD Pipeline

```bash
# Complete CI validation
python run_tests.py --ci --parallel

# Smoke tests (fast validation)
python run_tests.py --smoke --quick

# Security scan
python run_tests.py --security

# Performance regression check
python run_tests.py --load
```

### Debugging

```bash
# Verbose output
python run_tests.py --verbose

# Stop on first failure
pytest tests/ --maxfail=1

# Run specific test
pytest tests/unit/test_database.py::test_create_patient -v

# Run with debugger
pytest tests/unit/test_database.py --pdb
```

## Test Markers

Tests can be marked with decorators:

```python
@pytest.mark.unit         # Unit test
@pytest.mark.integration  # Integration test
@pytest.mark.slow         # Slow test (>1s)
@pytest.mark.security     # Security test
@pytest.mark.smoke        # Smoke test
@pytest.mark.load         # Load test
@pytest.mark.clinical     # Clinical workflow
@pytest.mark.safety       # Drug safety
```

### Running by Marker

```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run security and smoke tests
pytest -m "security or smoke"
```

## Test Structure

```
tests/
├── conftest.py              # Global fixtures and configuration
├── test_runner_config.py    # Test runner configuration
├── reporter.py              # Test reporting
├── test_watch.py            # File watcher
│
├── unit/                    # Unit tests
│   ├── test_database.py
│   ├── test_llm.py
│   ├── test_rag.py
│   └── test_pdf.py
│
├── integration/             # Integration tests
│   └── test_full_workflow.py
│
├── smoke/                   # Smoke tests
│   └── test_basic_functionality.py
│
├── security/                # Security tests
│   ├── test_sql_injection.py
│   ├── test_secrets.py
│   └── test_encryption.py
│
├── load/                    # Load tests
│   └── test_performance.py
│
└── validators/              # Pre-test validators
    ├── import_validator.py
    ├── syntax_validator.py
    ├── type_validator.py
    └── security_validator.py
```

## Validators

Validators run before tests to catch issues early:

### Import Validator
- Validates all modules can be imported
- Catches import errors before tests run

### Syntax Validator
- Checks Python syntax in all files
- Uses AST parsing

### Type Validator
- Runs mypy type checking
- Optional in development, required in CI

### Security Validator
- Runs bandit security scanner
- Checks for common vulnerabilities

Enable validators:
```bash
python run_tests.py --validate
```

## Coverage Reports

### Generate Coverage

```bash
# HTML report (interactive)
python run_tests.py --coverage
open htmlcov/index.html

# XML report (for CI tools)
pytest --cov=src --cov-report=xml

# Terminal report
pytest --cov=src --cov-report=term-missing
```

### Coverage Thresholds

- Minimum coverage: 70%
- Goal: 80%+
- Critical paths: 90%+

### Excluded from Coverage

- UI code (`src/ui/`)
- Test files
- `__init__.py` files
- Configuration files

## Tox - Multi-Environment Testing

```bash
# Install tox
pip install tox

# Run all environments
tox

# Run specific environment
tox -e py311      # Python 3.11
tox -e lint       # Linting
tox -e type       # Type checking
tox -e security   # Security checks
tox -e coverage   # Coverage report

# Recreate environments
tox -r
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt

      - name: Run validators
        run: python run_tests.py --validate

      - name: Run smoke tests
        run: python run_tests.py --smoke

      - name: Run all tests with coverage
        run: python run_tests.py --ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Performance Benchmarks

### Benchmark Tests

```python
@pytest.mark.benchmark
def test_database_insert(benchmark):
    result = benchmark(insert_patient, patient_data)
    assert result is not None
```

### Run Benchmarks

```bash
pytest tests/ --benchmark-only
```

## Test Data Generation

### Using Faker

```python
from faker import Faker

fake = Faker('en_IN')  # Indian locale

def test_patient_creation():
    patient = {
        'name': fake.name(),
        'phone': fake.phone_number(),
        'address': fake.address(),
    }
    # Test with realistic data
```

### Using Hypothesis (Property-Based Testing)

```python
from hypothesis import given
from hypothesis import strategies as st

@given(st.text(min_size=1, max_size=100))
def test_patient_name_validation(name):
    # Test with many random inputs
    assert validate_patient_name(name)
```

## Watch Mode

Automatically run tests when files change:

```bash
# Start watcher
python run_tests.py --watch

# Or use pytest-watch
ptw tests/
```

File change mapping:
- `src/services/database.py` → `tests/unit/test_database.py`
- `src/services/drugs/` → `tests/test_drug_*.py`
- `src/ui/` → `tests/smoke/`

## Troubleshooting

### Tests Hanging

```bash
# Add timeout
pytest tests/ --timeout=30
```

### Out of Memory

```bash
# Run sequentially
pytest tests/ -n0

# Run only unit tests
python run_tests.py --unit
```

### Import Errors

```bash
# Check imports first
python run_tests.py --validate

# Run syntax validator
pytest tests/validators/test_import_validator.py
```

### Flaky Tests

Flaky tests are automatically retried up to 3 times. Check logs for:
```
⚠️ Flaky test detected: test_name failed 2 times
```

## Best Practices

### Writing Tests

1. **Use fixtures** for common setup
2. **Mark tests appropriately** (`@pytest.mark.unit`, etc.)
3. **Keep tests fast** - unit tests should be < 1s
4. **Use descriptive names** - `test_patient_creation_with_valid_data`
5. **One assertion per test** when possible
6. **Mock external dependencies** (LLM, network, etc.)

### Test Organization

1. **Unit tests** - Test single function/class
2. **Integration tests** - Test multiple components
3. **Smoke tests** - Test critical paths
4. **Security tests** - Test security measures
5. **Load tests** - Test performance

### Running Tests Efficiently

1. **During development**: `--quick --failed`
2. **Before commit**: `--unit --integration`
3. **Before push**: `--coverage`
4. **In CI**: `--ci --parallel`

## Reports

### Generated Reports

After running with `--ci` or `--coverage`:

- `htmlcov/index.html` - HTML coverage report
- `test_results/junit.xml` - JUnit XML for CI
- `test_results/summary.txt` - Text summary
- `coverage.xml` - XML coverage for tools
- `test_results/pytest.log` - Detailed logs

### Viewing Reports

```bash
# Coverage report
open htmlcov/index.html

# Summary
cat test_results/summary.txt
```

## Configuration Files

- `pytest.ini` - Pytest configuration
- `tox.ini` - Tox configuration
- `tests/test_runner_config.py` - Test runner settings
- `tests/conftest.py` - Shared fixtures

## Environment Variables

```bash
# Skip validators
SKIP_VALIDATORS=1 python run_tests.py

# Custom coverage threshold
MIN_COVERAGE=80 python run_tests.py --coverage

# Verbose logging
LOG_LEVEL=DEBUG pytest tests/
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Tox Documentation](https://tox.wiki/)
- [Hypothesis Guide](https://hypothesis.readthedocs.io/)

## Support

For issues or questions:
1. Check test logs: `test_results/pytest.log`
2. Run with `--verbose` for detailed output
3. Isolate failing test: `pytest path/to/test.py::test_name -v`
