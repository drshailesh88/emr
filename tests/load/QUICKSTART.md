# Load Testing - Quick Start Guide

## Installation

1. **Ensure pytest is installed**:
   ```bash
   pip install pytest pytest-benchmark tracemalloc
   ```

2. **Verify installation**:
   ```bash
   cd /home/user/emr
   python -c "import pytest; print(f'pytest {pytest.__version__} installed')"
   ```

## Running Tests

### Option 1: Run All Load Tests (Recommended)
```bash
# From project root
./tests/load/run_load_tests.py

# This will:
# - Run all 6 test suites (66 tests total)
# - Generate HTML report at test_results/load/load_test_report.html
# - Generate JSON report at test_results/load/load_test_results.json
# - Display summary in terminal
```

**Expected Duration**: 10-15 minutes (first run creates 10K patient database)

### Option 2: Run Specific Test Suite
```bash
# Database performance tests
pytest tests/load/test_database_performance.py -v -s

# Search performance tests
pytest tests/load/test_search_performance.py -v -s

# Concurrent users tests
pytest tests/load/test_concurrent_users.py -v -s

# Memory usage tests
pytest tests/load/test_memory_usage.py -v -s

# Report generation tests
pytest tests/load/test_report_generation.py -v -s

# LLM performance tests (mocked)
pytest tests/load/test_llm_performance.py -v -s
```

### Option 3: Run Single Test
```bash
# Run one specific test
pytest tests/load/test_database_performance.py::TestDatabasePerformance::test_patient_search_10k_patients -v -s
```

## Understanding Results

### Console Output
Tests display performance metrics in real-time:

```
✓ EXCELLENT: patient_search: 85.23ms (target: 100ms, max: 500ms)
⚠ ACCEPTABLE: visit_history_load: 320.45ms (target: 200ms, max: 1000ms)
✗ FAILED: bulk_import: 35000.00ms (target: 10000ms, max: 30000ms)
```

- **Green (EXCELLENT)**: Performance meets target
- **Yellow (ACCEPTABLE)**: Performance between target and max
- **Red (FAILED)**: Performance exceeds max threshold

### HTML Report
After running `run_load_tests.py`, open the HTML report:
```bash
# Linux/Mac
xdg-open test_results/load/load_test_report.html

# Or manually open in browser
firefox test_results/load/load_test_report.html
```

## Test Data

### Automatic Generation
The test suite automatically generates realistic test data:

- **Small database**: 100 patients, ~750 visits (5 seconds)
- **Medium database**: 1,000 patients, ~10,000 visits (30 seconds)
- **Large database**: 10,000 patients, ~120,000 visits (5 minutes, created once per session)

### Manual Generation
Generate test data manually:

```python
from tests.load.generators.patient_generator import generate_patients
from tests.load.generators.visit_generator import generate_patient_visits
from tests.load.generators.prescription_generator import generate_prescription_json

# Generate 10 patients
patients = generate_patients(10)
print(f"Generated {len(patients)} patients")
for p in patients[:3]:
    print(f"  - {p['name']} ({p['gender']}, {p['age']}y)")

# Generate visits for a patient
visits = generate_patient_visits(patient_id=1, visit_count=5)
print(f"\nGenerated {len(visits)} visits")

# Generate prescription
rx_json = generate_prescription_json('Type 2 Diabetes Mellitus')
print(f"\nGenerated prescription: {rx_json[:100]}...")
```

## Interpreting Benchmarks

### Database Operations
| Operation | Target | Max | What It Tests |
|-----------|--------|-----|---------------|
| Patient search | 100ms | 500ms | Search 10K patients by name/UHID |
| Visit save | 50ms | 200ms | Insert single visit record |
| Visit history | 200ms | 1000ms | Load all visits for heavy patient |
| Bulk import | 10s | 30s | Import 1000 patients with data |

### Memory Usage
| Metric | Target | Max | What It Tests |
|--------|--------|-----|---------------|
| Baseline | 100MB | 200MB | Empty app memory |
| With 10K patients | 500MB | 1GB | Memory with full database |
| Memory leak | 50MB | 100MB | Growth after 1000 operations |

## Common Issues

### Tests Taking Too Long
**Solution**: Use specific test suites instead of running all:
```bash
# Instead of running all tests
./tests/load/run_load_tests.py

# Run just database tests
pytest tests/load/test_database_performance.py -v
```

### Memory Tests Failing
**Issue**: Memory thresholds are environment-dependent

**Solution**: Memory tests use Python's tracemalloc which can vary. If consistently failing:
1. Check if other processes are using memory
2. Run tests individually: `pytest tests/load/test_memory_usage.py::TestMemoryUsage::test_memory_baseline -v`

### Database Locked Errors
**Issue**: SQLite doesn't handle concurrent writes well

**Solution**: This is expected and tested! The concurrent tests verify proper handling.

## Continuous Monitoring

### Daily Automated Tests
Set up cron job for daily load testing:

```bash
# Add to crontab
0 2 * * * cd /home/user/emr && ./tests/load/run_load_tests.py >> /var/log/emr_load_tests.log 2>&1
```

### Performance Regression Detection
Compare results over time:

```bash
# Run tests and save results
./tests/load/run_load_tests.py

# Results saved with timestamp
ls -la test_results/load/load_test_results.json
```

## Next Steps

1. **Run Initial Baseline**:
   ```bash
   ./tests/load/run_load_tests.py
   ```

2. **Review HTML Report**: Check test_results/load/load_test_report.html

3. **Identify Bottlenecks**: Look for yellow/red results

4. **Optimize**: Focus on failed benchmarks

5. **Re-test**: Verify improvements

6. **Set Up Monitoring**: Add to CI/CD pipeline

## Getting Help

- **Documentation**: See `/home/user/emr/tests/load/README.md`
- **Implementation Details**: See `/home/user/emr/tests/load/LOAD_TEST_SUITE_SUMMARY.md`
- **Benchmarks**: See `/home/user/emr/tests/load/benchmarks.py`

## Example Session

```bash
# 1. Navigate to project
cd /home/user/emr

# 2. Run quick test to verify setup
pytest tests/load/test_database_performance.py::TestDatabasePerformance::test_patient_list_pagination -v

# 3. Run full database performance suite
pytest tests/load/test_database_performance.py -v -s

# 4. Run all load tests with report generation
./tests/load/run_load_tests.py

# 5. Open HTML report
firefox test_results/load/load_test_report.html
```

## Performance Optimization Tips

After running tests, if you see failures:

1. **Database Performance**:
   - Add indexes for frequently searched fields
   - Use connection pooling
   - Optimize complex queries

2. **Memory Usage**:
   - Implement pagination for large result sets
   - Clear unused references
   - Use generators for bulk operations

3. **Concurrency**:
   - Use WAL mode for SQLite
   - Implement request queuing
   - Add connection limits

4. **Search Performance**:
   - Add full-text search indexes
   - Implement search result caching
   - Use database triggers for derived data

## Success Criteria

Your load test run is successful if:
- ✓ All test suites pass (green)
- ✓ No red (FAILED) benchmarks
- ✓ Memory leak tests pass
- ✓ Concurrent operations complete without deadlocks
- ✓ HTML report generates successfully

Happy testing! 🚀
