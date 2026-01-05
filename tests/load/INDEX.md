# Load Testing Suite - Complete Index

## 📁 Directory Structure

```
tests/load/
├── 📄 INDEX.md                          (This file - Start here!)
├── 📄 QUICKSTART.md                     (Quick start guide)
├── 📄 README.md                         (Detailed documentation)
├── 📄 LOAD_TEST_SUITE_SUMMARY.md        (Implementation summary)
│
├── 🔧 Core Infrastructure
│   ├── __init__.py                      (Package initialization)
│   ├── benchmarks.py                    (Performance benchmarks)
│   ├── conftest.py                      (Pytest fixtures)
│   └── run_load_tests.py                (Test runner with HTML reports)
│
├── 🏭 Data Generators
│   └── generators/
│       ├── __init__.py
│       ├── patient_generator.py         (Realistic patient data)
│       ├── visit_generator.py           (Visit and clinical notes)
│       └── prescription_generator.py    (Medications and prescriptions)
│
└── 🧪 Test Suites
    ├── test_database_performance.py     (15 tests - Database ops)
    ├── test_search_performance.py       (12 tests - Search functionality)
    ├── test_report_generation.py        (10 tests - Report generation)
    ├── test_concurrent_users.py         (8 tests - Multi-user scenarios)
    ├── test_memory_usage.py             (10 tests - Memory profiling)
    └── test_llm_performance.py          (11 tests - LLM operations)
```

## 🚀 Quick Start

### First Time Setup
```bash
# 1. Install dependencies
pip install pytest pytest-benchmark

# 2. Navigate to project
cd /home/user/emr

# 3. Run a quick test
pytest tests/load/test_database_performance.py::TestDatabasePerformance::test_visit_save_performance -v -s
```

### Run Full Load Test Suite
```bash
./tests/load/run_load_tests.py
```

This will:
- ✓ Run all 66 load tests
- ✓ Generate 10,000 patient test database
- ✓ Create HTML report at `test_results/load/load_test_report.html`
- ✓ Create JSON report at `test_results/load/load_test_results.json`
- ⏱️ Takes about 10-15 minutes (first run)

## 📚 Documentation Guide

| Document | Purpose | Read Time | Audience |
|----------|---------|-----------|----------|
| **INDEX.md** | Overview and navigation | 2 min | Everyone |
| **QUICKSTART.md** | Get started immediately | 5 min | Developers |
| **README.md** | Complete usage guide | 15 min | Test engineers |
| **LOAD_TEST_SUITE_SUMMARY.md** | Implementation details | 10 min | Contributors |

## 🎯 Test Suites Overview

### 1. Database Performance (`test_database_performance.py`)
**Purpose**: Test database operations with realistic load

**Key Tests**:
- Patient search in 10K database (target: <100ms)
- Visit history for heavy patients (target: <200ms)
- Concurrent writes without deadlocks
- Bulk patient import (1000 patients)

**Run**:
```bash
pytest tests/load/test_database_performance.py -v -s
```

### 2. Search Performance (`test_search_performance.py`)
**Purpose**: Test search functionality under load

**Key Tests**:
- Phonetic search (Sharma, Shrama) - target: <200ms
- Fuzzy search with typos - target: <300ms
- Natural language search - target: <500ms
- Multi-criteria filtered search

**Run**:
```bash
pytest tests/load/test_search_performance.py -v -s
```

### 3. Report Generation (`test_report_generation.py`)
**Purpose**: Test report generation performance

**Key Tests**:
- Daily summary calculation - target: <1s
- Monthly analytics - target: <5s
- Audit trail export (1 year) - target: <10s
- Bulk PDF generation (100 prescriptions)

**Run**:
```bash
pytest tests/load/test_report_generation.py -v -s
```

### 4. Concurrent Users (`test_concurrent_users.py`)
**Purpose**: Simulate realistic multi-user scenarios

**Key Tests**:
- 5 doctors consulting simultaneously
- 10 concurrent patient searches
- Mixed workload (doctors + staff + admin)
- Burst load (50 requests in 1 second)

**Run**:
```bash
pytest tests/load/test_concurrent_users.py -v -s
```

### 5. Memory Usage (`test_memory_usage.py`)
**Purpose**: Profile memory usage and detect leaks

**Key Tests**:
- App baseline memory (target: <100MB)
- Memory with 10K patients (target: <500MB)
- Memory leak detection (1000 operations)
- Large patient timeline (500 visits)

**Run**:
```bash
pytest tests/load/test_memory_usage.py -v -s
```

### 6. LLM Performance (`test_llm_performance.py`)
**Purpose**: Test LLM operations (mocked for speed)

**Key Tests**:
- SOAP extraction latency
- Differential diagnosis generation
- LLM request queue handling
- Timeout and retry logic

**Run**:
```bash
pytest tests/load/test_llm_performance.py -v -s
```

## 🔧 Data Generators

### Patient Generator
Generates realistic Indian patient data:
```python
from tests.load.generators.patient_generator import generate_patients

# Generate 100 patients with realistic distribution
patients = generate_patients(100)

# Custom age distribution
patients = generate_patients(
    count=1000,
    age_distribution={
        (0, 18): 0.15,    # 15% children
        (19, 45): 0.40,   # 40% adults
        (46, 65): 0.30,   # 30% middle-age
        (66, 90): 0.15    # 15% elderly
    },
    gender_ratio=0.52  # 52% male, 48% female
)
```

**Features**:
- 47 male names, 45 female names
- 50 Indian surnames
- 24 Indian cities
- Realistic phone numbers (+91)
- Chronic condition simulation

### Visit Generator
Generates realistic visit data:
```python
from tests.load.generators.visit_generator import generate_patient_visits

# Generate 10 visits
visits = generate_patient_visits(patient_id=1, visit_count=10)

# Chronic patient with regular follow-ups
visits = generate_patient_visits(
    patient_id=1,
    visit_count=20,
    chronic_condition='Type 2 Diabetes Mellitus'
)

# Heavy patient for stress testing
from tests.load.generators.visit_generator import generate_heavy_patient_visits
visits = generate_heavy_patient_visits(patient_id=1)  # 50-100 visits
```

**Features**:
- 50+ chief complaints categorized by system
- Realistic clinical notes
- 30+ common diagnoses
- Visit progression tracking

### Prescription Generator
Generates realistic prescriptions:
```python
from tests.load.generators.prescription_generator import (
    generate_prescription_json,
    generate_chronic_prescription
)

# Acute prescription
rx_json = generate_prescription_json(
    diagnosis='Viral Fever',
    medication_count=3
)

# Chronic prescription
rx = generate_chronic_prescription('Type 2 Diabetes Mellitus, Hypertension')
# Returns prescription with 3-6 medications, proper durations
```

**Features**:
- 40+ common Indian medications
- Realistic frequencies (OD, BD, TDS, etc.)
- Appropriate durations
- Category-based drug selection
- Chronic vs acute prescriptions

## 📊 Performance Benchmarks

### Time Benchmarks

| Category | Operation | Target | Max | Description |
|----------|-----------|--------|-----|-------------|
| **Database** | Patient search | 100ms | 500ms | Search 10K patients |
| | Visit save | 50ms | 200ms | Save single visit |
| | Bulk import | 10s | 30s | Import 1000 patients |
| **Search** | Phonetic | 200ms | 500ms | Sound-alike search |
| | Fuzzy | 300ms | 800ms | Typo-tolerant |
| | Natural language | 500ms | 2s | Semantic search |
| **Reports** | Daily summary | 1s | 3s | Calculate daily stats |
| | Monthly analytics | 5s | 15s | Full month analysis |
| | Audit export | 10s | 30s | 1 year audit trail |
| **Concurrency** | 5 concurrent writes | 500ms | 2s | Simultaneous saves |
| | Burst load | 2s | 5s | 50 requests/second |

### Memory Benchmarks

| Metric | Target | Max | Description |
|--------|--------|-----|-------------|
| Baseline | 100MB | 200MB | Empty app memory |
| With 10K patients | 500MB | 1GB | Full database loaded |
| Memory leak threshold | 50MB | 100MB | After 1000 operations |

## 🔍 Understanding Test Results

### Console Output Format
```
✓ EXCELLENT: patient_search: 85.23ms (target: 100ms, max: 500ms)
⚠ ACCEPTABLE: visit_history: 320.45ms (target: 200ms, max: 1000ms)
✗ FAILED: bulk_import: 35000.00ms (target: 10s, max: 30s)
```

### Status Indicators
- ✓ **EXCELLENT** (Green): Performance meets target
- ⚠ **ACCEPTABLE** (Yellow): Between target and max
- ✗ **FAILED** (Red): Exceeds maximum threshold

## 📈 Test Reports

### HTML Report
Generated at: `test_results/load/load_test_report.html`

Includes:
- Executive summary with pass/fail counts
- Detailed results for each test suite
- Duration metrics
- Visual status indicators

### JSON Report
Generated at: `test_results/load/load_test_results.json`

Machine-readable format for:
- CI/CD integration
- Trend analysis
- Custom reporting

## 🎓 Common Use Cases

### Development
```bash
# Quick sanity check
pytest tests/load/test_database_performance.py::TestDatabasePerformance::test_patient_search_10k_patients -v

# Test after optimization
pytest tests/load/test_search_performance.py -v -s
```

### Pre-Release Testing
```bash
# Full load test suite
./tests/load/run_load_tests.py

# Review HTML report
firefox test_results/load/load_test_report.html
```

### Performance Regression
```bash
# Baseline before changes
./tests/load/run_load_tests.py
cp test_results/load/load_test_results.json baseline.json

# After changes
./tests/load/run_load_tests.py

# Compare results
diff baseline.json test_results/load/load_test_results.json
```

### CI/CD Integration
```bash
# Run in CI pipeline
./tests/load/run_load_tests.py --output-dir ./artifacts/load-tests

# Upload reports as artifacts
```

## 🛠️ Troubleshooting

### Tests Too Slow
**Problem**: Full suite takes too long

**Solutions**:
1. Run specific suites: `pytest tests/load/test_database_performance.py`
2. Use smaller databases: Tests use `medium_db` instead of `large_db`
3. Skip slow tests: `pytest -m "not slow"`

### Memory Tests Failing
**Problem**: Memory thresholds exceeded

**Solutions**:
1. Close other applications
2. Run garbage collection: Tests already do this
3. Increase thresholds in `benchmarks.py` if consistently failing

### Database Locked
**Problem**: SQLite database locked errors

**Solutions**:
1. This is tested! Concurrent tests verify proper handling
2. Enable WAL mode in production
3. Use connection pooling

## 📦 Test Fixtures

### Database Fixtures

| Fixture | Patients | Visits | Creation Time | Scope |
|---------|----------|--------|---------------|-------|
| `temp_db` | 0 | 0 | Instant | Function |
| `small_db` | 100 | ~750 | ~5s | Function |
| `medium_db` | 1,000 | ~10,000 | ~30s | Function |
| `large_db` | 10,000 | ~120,000 | ~5min | Session |
| `heavy_patient_db` | 20 | ~1,500 | ~10s | Function |

### Utility Fixtures
- `timer`: Performance timing context manager
- `memory_profiler`: Memory usage profiling
- `benchmark_result`: Store and compare results

## 🎯 Success Metrics

Your load test run is successful when:
- ✅ All 66 tests pass
- ✅ No RED (failed) benchmarks
- ✅ Memory leak tests pass
- ✅ Concurrent operations complete without deadlocks
- ✅ Reports generate successfully

## 🔗 Related Documentation

- **Main Project README**: `/home/user/emr/README.md`
- **Test Suite Overview**: `/home/user/emr/tests/README.md`
- **Database Service**: `/home/user/emr/src/services/database.py`
- **Models**: `/home/user/emr/src/models/schemas.py`

## 💡 Pro Tips

1. **First Run**: The `large_db` fixture takes ~5 minutes to create but is cached for the session
2. **Quick Tests**: Use `medium_db` for faster iteration during development
3. **Benchmarks**: Adjust in `benchmarks.py` as application evolves
4. **Reports**: HTML reports are great for stakeholder demos
5. **CI/CD**: JSON reports perfect for automated monitoring

## 🤝 Contributing

To add new load tests:

1. Create test file: `test_my_feature.py`
2. Use existing fixtures from `conftest.py`
3. Define benchmarks in `benchmarks.py`
4. Add to `run_load_tests.py`
5. Update this INDEX.md

## 📞 Support

- Check `README.md` for detailed usage
- Review `QUICKSTART.md` for common patterns
- See `LOAD_TEST_SUITE_SUMMARY.md` for implementation details
- Review individual test files for examples

---

**Total**: 66 comprehensive load tests | 4,500+ lines of code | Complete documentation

Start with `QUICKSTART.md` → Run `./run_load_tests.py` → Review HTML report 🚀
