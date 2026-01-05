# Load Testing - Quick Command Reference

## Essential Commands

### Run All Tests
```bash
./tests/load/run_load_tests.py
```

### Run Specific Suite
```bash
# Database performance
pytest tests/load/test_database_performance.py -v -s

# Search performance
pytest tests/load/test_search_performance.py -v -s

# Report generation
pytest tests/load/test_report_generation.py -v -s

# Concurrent users
pytest tests/load/test_concurrent_users.py -v -s

# Memory usage
pytest tests/load/test_memory_usage.py -v -s

# LLM performance
pytest tests/load/test_llm_performance.py -v -s
```

### Run Single Test
```bash
pytest tests/load/test_database_performance.py::TestDatabasePerformance::test_patient_search_10k_patients -v -s
```

### View Results
```bash
# View HTML report
firefox test_results/load/load_test_report.html

# View JSON report
cat test_results/load/load_test_results.json | jq
```

## Development Workflow

### Quick Sanity Check
```bash
# Run fastest test
pytest tests/load/test_database_performance.py::TestDatabasePerformance::test_visit_save_performance -v -s
```

### Test After Optimization
```bash
# Before optimization
pytest tests/load/test_database_performance.py -v -s > before.txt

# Make changes...

# After optimization
pytest tests/load/test_database_performance.py -v -s > after.txt

# Compare
diff before.txt after.txt
```

### Generate Test Data
```python
# In Python shell
from tests.load.generators.patient_generator import generate_patients
from tests.load.generators.visit_generator import generate_visit
from tests.load.generators.prescription_generator import generate_prescription_json

# Generate data
patients = generate_patients(10)
visit = generate_visit(1)
rx = generate_prescription_json('Diabetes')
```

## Advanced Usage

### Custom Output Directory
```bash
./tests/load/run_load_tests.py --output-dir ./my_results
```

### Verbose Output
```bash
pytest tests/load/ -vv -s
```

### Stop on First Failure
```bash
pytest tests/load/ -x
```

### Parallel Execution (if pytest-xdist installed)
```bash
pytest tests/load/ -n auto
```

### Show Slowest Tests
```bash
pytest tests/load/ --durations=10
```

## Troubleshooting Commands

### Check Dependencies
```bash
pip list | grep pytest
```

### Clear Pytest Cache
```bash
pytest --cache-clear
```

### Debug Failing Test
```bash
pytest tests/load/test_database_performance.py::TestDatabasePerformance::test_patient_search_10k_patients -v -s --pdb
```

### Check Memory Usage
```bash
pytest tests/load/test_memory_usage.py -v -s --tb=short
```

## Reporting Commands

### Generate Reports Only
```bash
# Tests already run, just regenerate reports
python -c "
from tests.load.run_load_tests import LoadTestRunner
runner = LoadTestRunner()
runner.generate_html_report()
"
```

### Convert JSON to CSV
```bash
# Install jq if needed
cat test_results/load/load_test_results.json | jq -r '.test_suites[] | [.name,.passed,.duration_seconds] | @csv' > results.csv
```

## CI/CD Commands

### Run in CI
```bash
# Run with timeout
timeout 30m ./tests/load/run_load_tests.py

# Exit code 0 if all pass, 1 if any fail
echo $?
```

### Upload Artifacts
```bash
# Archive results
tar -czf load-test-results.tar.gz test_results/load/

# Upload to S3 (example)
aws s3 cp load-test-results.tar.gz s3://my-bucket/
```

## One-Liners

```bash
# Quick database test
pytest tests/load/test_database_performance.py -k "search" -v

# Quick memory test
pytest tests/load/test_memory_usage.py -k "baseline" -v

# All concurrent tests
pytest tests/load/test_concurrent_users.py -v

# Count total tests
pytest tests/load/ --collect-only | grep "test_" | wc -l

# List all test names
pytest tests/load/ --collect-only -q
```

## Useful Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
# Load test aliases
alias load-test='cd /home/user/emr && ./tests/load/run_load_tests.py'
alias load-db='pytest tests/load/test_database_performance.py -v -s'
alias load-search='pytest tests/load/test_search_performance.py -v -s'
alias load-report='firefox test_results/load/load_test_report.html'
```

## Performance Profiling

### Time a Specific Operation
```python
from tests.load.conftest import PerformanceTimer

with PerformanceTimer("My operation") as timer:
    # Your code here
    pass

print(f"Took {timer.elapsed_ms}ms")
```

### Profile Memory
```python
from tests.load.conftest import MemoryProfiler

with MemoryProfiler("My operation") as mem:
    # Your code here
    pass

print(f"Peak: {mem.get_peak_mb()}MB")
```

## Quick Reference

| Task | Command |
|------|---------|
| Run all | `./tests/load/run_load_tests.py` |
| Run database tests | `pytest tests/load/test_database_performance.py -v` |
| Run one test | `pytest tests/load/test_*.py::Test*::test_* -v` |
| View report | `firefox test_results/load/load_test_report.html` |
| Generate data | `python -c "from tests.load.generators..."` |
| Check fixtures | `pytest tests/load/ --fixtures` |
| Debug | `pytest tests/load/... --pdb` |

---

**Tip**: Start with `./tests/load/run_load_tests.py` then drill down to specific tests!
