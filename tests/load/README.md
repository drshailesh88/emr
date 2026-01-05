# Load Testing Suite - DocAssist EMR

Comprehensive load and performance testing suite for DocAssist EMR.

## Overview

This suite tests the application's performance under realistic load conditions with:
- 10,000 patient database
- Concurrent user scenarios
- Memory profiling
- Performance benchmarking

## Test Suites

### 1. Database Performance (`test_database_performance.py`)
Tests database operations with 10K patients:
- Patient search (target: <100ms)
- Pagination (target: <50ms)
- Visit history loading (target: <200ms)
- Concurrent writes
- Bulk imports

### 2. Search Performance (`test_search_performance.py`)
Tests various search operations:
- Phonetic search (target: <200ms)
- Fuzzy search with typos (target: <300ms)
- Natural language search (target: <500ms)
- Filtered search (target: <200ms)

### 3. Report Generation (`test_report_generation.py`)
Tests report generation:
- Daily summary (target: <1s)
- Monthly analytics (target: <5s)
- Audit trail export (target: <10s)
- PDF prescription generation (target: <1s)

### 4. Concurrent Users (`test_concurrent_users.py`)
Simulates realistic multi-user scenarios:
- 5 doctors consulting simultaneously
- 10 concurrent searches
- Mixed workload (doctors + staff + admin)
- Burst load (50 requests in 1 second)

### 5. Memory Usage (`test_memory_usage.py`)
Memory profiling and leak detection:
- App baseline (target: <100MB)
- With 10K patients (target: <500MB)
- Memory leak detection
- Large patient timeline

### 6. LLM Performance (`test_llm_performance.py`)
LLM operation performance (mocked):
- SOAP extraction (target: <3s)
- Differential diagnosis (target: <2s)
- Queue handling
- Timeout and retry logic

## Running Tests

### Run All Load Tests
```bash
# From project root
python tests/load/run_load_tests.py

# Or using the script directly
./tests/load/run_load_tests.py
```

### Run Specific Test Suite
```bash
# Run only database performance tests
pytest tests/load/test_database_performance.py -v -s

# Run only memory tests
pytest tests/load/test_memory_usage.py -v -s

# Using the runner
./tests/load/run_load_tests.py --suite database_performance
```

### Run With Custom Output Directory
```bash
./tests/load/run_load_tests.py --output-dir ./my_results
```

## Test Fixtures

### Database Fixtures
- `temp_db`: Empty temporary database
- `small_db`: 100 patients, 5-10 visits each
- `medium_db`: 1,000 patients with realistic distribution
- `large_db`: 10,000 patients (session-scoped, created once)
- `heavy_patient_db`: 20 patients with 50-100 visits each

### Utility Fixtures
- `timer`: Performance timing context manager
- `memory_profiler`: Memory usage profiling
- `benchmark_result`: Store benchmark results

## Data Generators

### Patient Generator (`generators/patient_generator.py`)
Generates realistic Indian patient data:
```python
from tests.load.generators.patient_generator import generate_patients

# Generate 100 patients
patients = generate_patients(100)

# Generate with age distribution
patients = generate_patients(
    count=1000,
    age_distribution={
        (0, 18): 0.2,
        (19, 45): 0.4,
        (46, 90): 0.4
    },
    gender_ratio=0.5  # 50% male
)
```

### Visit Generator (`generators/visit_generator.py`)
Generates realistic visit data:
```python
from tests.load.generators.visit_generator import generate_patient_visits

# Generate 10 visits for a patient
visits = generate_patient_visits(patient_id=1, visit_count=10)

# Generate for chronic patient
visits = generate_patient_visits(
    patient_id=1,
    visit_count=20,
    chronic_condition='Type 2 Diabetes Mellitus'
)
```

### Prescription Generator (`generators/prescription_generator.py`)
Generates realistic prescriptions:
```python
from tests.load.generators.prescription_generator import generate_prescription_json

# Generate prescription
rx_json = generate_prescription_json(
    diagnosis='Type 2 Diabetes Mellitus',
    medication_count=4
)

# Generate chronic prescription
rx = generate_chronic_prescription('Hypertension')
```

## Benchmarks

Performance benchmarks are defined in `benchmarks.py`:

| Operation | Target | Max | Description |
|-----------|--------|-----|-------------|
| patient_search | 100ms | 500ms | Search 10K patients |
| visit_save | 50ms | 200ms | Save single visit |
| daily_summary | 1s | 3s | Calculate daily summary |
| soap_extraction | 2s | 5s | LLM SOAP extraction |
| app_startup | 2s | 5s | Application startup |

Memory benchmarks:
- Baseline: 100MB (max 200MB)
- With 10K patients: 500MB (max 1GB)
- Memory leak threshold: 50MB (max 100MB)

## Reports

### HTML Report
After running tests, an HTML report is generated at:
```
test_results/load/load_test_report.html
```

The report includes:
- Summary of all test suites
- Pass/fail status
- Duration metrics
- Performance benchmarks

### JSON Report
Machine-readable results are saved to:
```
test_results/load/load_test_results.json
```

## Performance Tips

### Optimize Database Tests
- The `large_db` fixture is session-scoped and created once
- This saves ~5 minutes per test run
- To regenerate, delete the temporary database

### Parallel Execution
You can run test suites in parallel using pytest-xdist:
```bash
pytest tests/load/ -n auto
```

Note: The `large_db` fixture handles parallel access safely.

### Skip Slow Tests
Mark slow tests to skip during development:
```bash
pytest tests/load/ -m "not slow"
```

## Interpreting Results

### Green (Excellent)
Performance is at or better than target:
```
✓ EXCELLENT: patient_search: 85.23ms (target: 100ms, max: 500ms)
```

### Yellow (Acceptable)
Performance is between target and max:
```
⚠ ACCEPTABLE: patient_search: 320.45ms (target: 100ms, max: 500ms)
```

### Red (Failed)
Performance exceeds maximum threshold:
```
✗ FAILED: patient_search: 650.12ms (target: 100ms, max: 500ms)
```

## Continuous Integration

Add to CI pipeline:
```yaml
# .github/workflows/load-tests.yml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-benchmark
      - name: Run load tests
        run: ./tests/load/run_load_tests.py
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: load-test-report
          path: test_results/load/
```

## Troubleshooting

### Tests Are Too Slow
- Check if running on slow hardware
- Reduce test data size in conftest.py
- Run specific suites instead of all

### Memory Tests Failing
- Garbage collection may not run immediately
- Results can vary between Python versions
- Consider increasing thresholds slightly

### Database Locked Errors
- Ensure proper connection cleanup
- Check concurrent test isolation
- May need to adjust SQLite timeout settings

## Adding New Tests

1. Create test file in `tests/load/`
2. Use existing fixtures from `conftest.py`
3. Add benchmarks to `benchmarks.py`
4. Update `run_load_tests.py` to include new suite

Example:
```python
# test_my_feature.py
import pytest
from tests.load.benchmarks import BENCHMARKS

class TestMyFeature:
    def test_my_operation(self, large_db, timer):
        with timer("My operation") as t:
            # Your test code
            pass

        assert t.elapsed_ms <= 1000
```

## License

Part of DocAssist EMR project.
