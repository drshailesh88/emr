# DocAssist EMR - Load Testing Suite

Comprehensive load testing suite for DocAssist EMR, covering database performance, concurrency, memory usage, and scalability from 100 to 50,000+ patients.

## Overview

The load testing suite validates that DocAssist EMR can:

- **Handle scale:** Support databases with 10K+ patients and 100K+ visits
- **Maintain performance:** Search and retrieval operations remain fast at scale
- **Support concurrency:** Multiple doctors using the system simultaneously
- **Manage memory:** No memory leaks during extended use
- **Start quickly:** Application startup under 5 seconds even with large databases

### Quick Start

```bash
# Run all tests (fast - skips 50K tests)
python tests/load/run_benchmarks.py

# Run with regression detection
python tests/load/run_benchmarks.py --save-baseline

# Run specific test suite
python tests/load/run_benchmarks.py --suite startup
```

## Test Suites

### 1. Startup Time (`test_startup_time.py`) **NEW**
Tests application startup performance at different scales:
- Cold start with empty database (<2s)
- Startup with 100 patients (<2s)
- Startup with 1,000 patients (<3s)
- Startup with 10,000 patients (<5s)
- Index creation time
- Connection pool overhead

### 2. Database Scale (`test_database_scale.py`) **NEW**
Comprehensive scale testing at 1K, 10K, and 50K patient levels:
- Patient search at each scale
- Visit retrieval at each scale
- Complex analytical queries
- Pagination performance
- Scale comparison (degradation analysis)
- Write performance on large databases

### 3. Database Performance (`test_database_performance.py`)
Tests database operations with 10K patients:
- Patient search (target: <100ms)
- Pagination (target: <50ms)
- Visit history loading (target: <200ms)
- Concurrent writes
- Bulk imports

### 4. Search Performance (`test_search_performance.py`)
Tests various search operations:
- Phonetic search (target: <200ms)
- Fuzzy search with typos (target: <300ms)
- Natural language search (target: <500ms)
- Filtered search (target: <200ms)

### 5. Report Generation (`test_report_generation.py`)
Tests report generation:
- Daily summary (target: <1s)
- Monthly analytics (target: <5s)
- Audit trail export (target: <10s)
- PDF prescription generation (target: <1s)

### 6. Concurrent Users (`test_concurrent_users.py`)
Simulates realistic multi-user scenarios:
- 5 doctors consulting simultaneously
- 10 concurrent searches
- Mixed workload (doctors + staff + admin)
- Burst load (50 requests in 1 second)

### 7. Memory Usage (`test_memory_usage.py`)
Memory profiling and leak detection:
- App baseline (target: <100MB)
- With 10K patients (target: <500MB)
- Memory leak detection
- Large patient timeline

### 8. LLM Performance (`test_llm_performance.py`)
LLM operation performance (mocked):
- SOAP extraction (target: <3s)
- Differential diagnosis (target: <2s)
- Queue handling
- Timeout and retry logic

## Running Tests

### Using run_benchmarks.py (Recommended - NEW)

```bash
# Run all tests (skips slow 50K tests)
python tests/load/run_benchmarks.py

# Run with regression detection
python tests/load/run_benchmarks.py --save-baseline

# Include slow tests (50K+ patients)
python tests/load/run_benchmarks.py --include-slow

# Run specific suite
python tests/load/run_benchmarks.py --suite startup
python tests/load/run_benchmarks.py --suite scale
python tests/load/run_benchmarks.py --suite memory

# Custom output directory
python tests/load/run_benchmarks.py --output-dir my_results/
```

**Features:**
- Baseline comparison and regression detection
- Comprehensive markdown and JSON reports
- Performance degradation analysis
- Automatic pass/fail with ±20% thresholds

### Using run_load_tests.py (Original)

```bash
# From project root
python tests/load/run_load_tests.py

# Run specific suite
./tests/load/run_load_tests.py --suite database_performance

# Custom output directory
./tests/load/run_load_tests.py --output-dir ./my_results
```

### Using pytest Directly

```bash
# Run single test file
pytest tests/load/test_startup_time.py -v -s

# Run specific test
pytest tests/load/test_startup_time.py::TestStartupTime::test_cold_start_empty_db -v -s

# Skip slow tests
pytest tests/load/test_database_scale.py -v -s -m "not slow"
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

### Unified Data Generator (`data_generator.py`) **NEW**
Convenient interface to all generators with database integration:

```python
from tests.load.data_generator import DataGenerator, quick_populate

# Quick database population
db = DatabaseService('test.db')
generator = DataGenerator(db)

# Presets for different scales
generator.populate_small_database()      # 100 patients
generator.populate_medium_database()     # 1,000 patients
generator.populate_large_database()      # 10,000 patients
generator.populate_heavy_patient_database()  # 20 patients with 50-100 visits each

# Custom generation
generator.generate_and_save_patients(
    count=500,
    with_visits=True,
    visits_per_patient=(5, 15)
)

# Generate chronic disease cohort
generator.generate_chronic_disease_cohort(
    condition='Type 2 Diabetes Mellitus',
    patient_count=50
)

# Quick populate shortcut
quick_populate(db, scale='medium')  # 1,000 patients
```

**Features:**
- One-line database population
- Realistic Indian patient data
- Chronic disease cohorts
- Recent activity generation
- Automatic visit and prescription generation

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
