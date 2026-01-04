# DocAssist EMR Test Suite

Comprehensive test suite for DocAssist EMR with 80%+ coverage on services layer.

## Quick Start

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=src --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures (temp DB, mock Ollama, sample data)
├── unit/                    # Unit tests for individual components
│   ├── test_database.py     # Database service tests (CRUD operations)
│   ├── test_llm.py          # LLM service tests (all mocked, no real Ollama needed)
│   ├── test_rag.py          # RAG service tests (ChromaDB operations)
│   ├── test_pdf.py          # PDF generation tests
│   └── test_schemas.py      # Pydantic model validation tests
├── integration/             # Integration tests for complete workflows
│   └── test_workflows.py    # End-to-end workflows (patient → visit → Rx → PDF)
└── fixtures/                # Test data
    ├── sample_patients.json
    ├── sample_visits.json
    └── mock_llm_responses.json
```

## Running Specific Tests

### By Category

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Database tests only
pytest tests/unit/test_database.py

# LLM tests only
pytest tests/unit/test_llm.py
```

### By Marker

```bash
# All database tests
pytest -m database

# All RAG tests
pytest -m rag

# All LLM tests
pytest -m llm
```

### By Name Pattern

```bash
# All patient-related tests
pytest -k patient

# All prescription tests
pytest -k prescription
```

## Test Fixtures

### Temporary Resources

- `temp_dir` - Temporary directory (auto-cleaned)
- `temp_db` - Fresh SQLite database for each test
- `temp_rag` - Fresh ChromaDB instance for each test
- `temp_pdf` - PDF service with temp output directory

### Mock Services

- `mock_ollama_available` - Mock Ollama as running
- `mock_ollama_generate` - Mock Ollama generate endpoint
- `mock_llm_service` - Complete mocked LLM service

### Sample Data

- `sample_patient` - Sample Patient object
- `sample_patient_data` - Sample patient in database
- `sample_visit` - Sample Visit object
- `sample_visit_data` - Sample visit in database
- `sample_investigation` - Sample Investigation object
- `sample_procedure` - Sample Procedure object
- `sample_prescription` - Sample Prescription object

## Coverage Goals

- **Services Layer**: 80%+ coverage ✅
- **Models/Schemas**: 60%+ coverage ✅
- **UI Layer**: Not tested (too complex for MVP)

## Important Notes

### No Real Ollama Required

All LLM tests use mocks - you don't need Ollama running to run tests.

```python
# Example: Mocking LLM response
with patch('requests.post') as mock_post:
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"response": json.dumps(prescription_data)}
    )
    llm = LLMService()
    success, prescription, _ = llm.generate_prescription("notes")
```

### Tests Are Isolated

Each test gets fresh instances:
- New database file
- New ChromaDB directory
- No shared state between tests

### Temp Files Are Cleaned

All temporary files/directories are automatically cleaned up after each test.

## Writing New Tests

### Unit Test Template

```python
class TestMyFeature:
    """Tests for my feature."""

    def test_basic_functionality(self, temp_db):
        """Test basic functionality."""
        # Arrange
        patient = Patient(name="Test")

        # Act
        result = temp_db.add_patient(patient)

        # Assert
        assert result.id is not None
```

### Integration Test Template

```python
def test_complete_workflow(self, temp_db, temp_rag, temp_pdf):
    """Test complete workflow."""
    # 1. Create patient
    patient = temp_db.add_patient(Patient(name="Test"))

    # 2. Add visit
    visit = temp_db.add_visit(Visit(patient_id=patient.id))

    # 3. Index for RAG
    docs = temp_db.get_patient_documents_for_rag(patient.id)
    temp_rag.index_patient_documents(patient.id, docs)

    # 4. Verify
    assert temp_rag.get_patient_document_count(patient.id) > 0
```

## Continuous Integration

Tests are designed to run in CI environments:
- No GUI required
- No external dependencies (Ollama is mocked)
- Fast execution (< 60 seconds for full suite)
- Deterministic results

### GitHub Actions Example

```yaml
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### ChromaDB Import Errors

If you see ChromaDB-related errors:
```bash
pip install --upgrade chromadb
```

### Tests Are Slow

Run tests in parallel:
```bash
pytest -n auto  # Uses all CPU cores
```

### Coverage Too Low

See which files need more tests:
```bash
pytest --cov=src --cov-report=term-missing
```

## Performance

- **Full suite**: ~30-45 seconds
- **Unit tests**: ~15-20 seconds
- **Integration tests**: ~15-20 seconds

Tests are optimized for speed:
- In-memory operations where possible
- Minimal data creation
- Parallel execution support
