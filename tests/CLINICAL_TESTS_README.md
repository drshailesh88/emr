# DocAssist EMR - Clinical Workflow Test Suite

Comprehensive end-to-end test suite for the DocAssist EMR clinical consultation workflow.

## Overview

This test suite validates the complete clinical consultation workflow from patient selection to prescription delivery, including:

- **Consultation Flow**: Start, speech processing, prescription generation, completion
- **Clinical NLP**: Entity extraction from Hindi, English, and Hinglish speech
- **Diagnosis Engine**: Differential diagnosis, red flag detection, protocol adherence
- **Drug Safety**: Interaction checking, allergy detection, dose validation
- **Communication**: WhatsApp/SMS delivery, reminders, notifications
- **Audit Trail**: Comprehensive logging, chain integrity, compliance reporting
- **Integration**: Complete end-to-end workflows with all services
- **Scenarios**: Real-world clinical presentations

## Test Coverage

### Target: **80% Code Coverage**

```
tests/
├── clinical_conftest.py              # Enhanced pytest fixtures
├── test_consultation_workflow.py     # E2E consultation tests (11 tests)
├── test_clinical_nlp.py              # NLP extraction tests (20 tests)
├── test_diagnosis_engine.py          # Diagnosis & CDS tests (24 tests)
├── test_drug_safety.py               # Drug safety tests (22 tests)
├── test_communication_services.py    # Communication tests (18 tests)
├── test_audit_trail.py               # Audit compliance tests (15 tests)
├── test_clinical_integration.py      # Integration tests (12 tests)
├── test_clinical_scenarios.py        # Real-world scenarios (8 tests)
└── fixtures/
    ├── sample_transcripts.py         # Hindi/English/Hinglish samples
    ├── sample_patients_extended.py   # Patient profiles
    └── sample_prescriptions_extended.py  # Prescription samples
```

**Total: 130+ tests**

## Installation

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Or using requirements-dev.txt
pip install -r requirements-dev.txt
```

## Running Tests

### Run All Clinical Tests

```bash
# From project root
pytest tests/test_consultation_workflow.py \
       tests/test_clinical_nlp.py \
       tests/test_diagnosis_engine.py \
       tests/test_drug_safety.py \
       tests/test_communication_services.py \
       tests/test_audit_trail.py \
       tests/test_clinical_integration.py \
       tests/test_clinical_scenarios.py \
       -v
```

### Run Specific Test Files

```bash
# Consultation workflow only
pytest tests/test_consultation_workflow.py -v

# Drug safety tests only
pytest tests/test_drug_safety.py -v

# Real-world scenarios
pytest tests/test_clinical_scenarios.py -v
```

### Run with Coverage

```bash
# Generate coverage report
pytest tests/test_*.py --cov=src/services --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Run single test
pytest tests/test_consultation_workflow.py::TestConsultationWorkflow::test_start_consultation_loads_patient_data -v

# Run all tests matching pattern
pytest -k "interaction" -v
```

### Run with Markers

```bash
# Run only async tests
pytest -m asyncio -v

# Run integration tests only
pytest tests/test_clinical_integration.py -v
```

## Test Files Description

### 1. `test_consultation_workflow.py`

Tests the complete consultation lifecycle.

**Key Tests:**
- ✅ Starting consultation loads patient data
- ✅ Speech processing extracts SOAP notes
- ✅ Prescription checks for drug interactions
- ✅ Completing consultation saves visit
- ✅ WhatsApp sent after consultation
- ✅ Complete audit trail maintained
- ✅ Workflow state transitions correctly
- ✅ Error recovery mechanisms

**Example:**
```python
@pytest.mark.asyncio
async def test_start_consultation_loads_patient_data(clinical_flow, sample_patient):
    context = await clinical_flow.start_consultation(
        patient_id=sample_patient.id,
        doctor_id="DR001"
    )
    assert context.patient_timeline is not None
    assert len(context.care_gaps) > 0
```

### 2. `test_clinical_nlp.py`

Tests clinical entity extraction from text.

**Key Tests:**
- ✅ Extract vitals from speech
- ✅ Extract medications (Hindi, English, Hinglish)
- ✅ Extract symptoms with duration
- ✅ Extract diagnoses
- ✅ SOAP note structure parsing
- ✅ Negation handling
- ✅ Family history extraction
- ✅ Temporal expressions
- ✅ Medical abbreviation expansion

**Example:**
```python
@pytest.mark.asyncio
async def test_extract_medications_hinglish(mock_clinical_nlp):
    text = "Patient ko paracetamol 500 mg dena hai twice daily"
    entities = await mock_clinical_nlp.extract_entities(text)
    assert "medications" in entities
```

### 3. `test_diagnosis_engine.py`

Tests diagnosis generation and clinical decision support.

**Key Tests:**
- ✅ Differential diagnosis for chest pain
- ✅ Differential diagnosis for fever
- ✅ Cardiac red flag detection
- ✅ Neurological red flag detection
- ✅ Diabetes protocol adherence
- ✅ Hypertension protocol adherence
- ✅ Critical value detection (potassium, glucose, creatinine, INR)
- ✅ Normal range handling
- ✅ Age-specific protocols
- ✅ Pregnancy category checking

**Example:**
```python
def test_critical_value_potassium_high():
    alert = check_critical_value("Potassium", 6.5)
    assert alert is not None
    assert alert["severity"] == "critical"
    assert "arrhythmia" in alert["message"].lower()
```

### 4. `test_drug_safety.py`

Tests prescription safety validation.

**Key Tests:**
- ✅ Major interaction: Warfarin + Aspirin
- ✅ Allergy detection and blocking
- ✅ Cross-reactivity checking
- ✅ Renal dose adjustment warnings
- ✅ Hepatic caution alerts
- ✅ Pediatric dose calculation
- ✅ Duplicate therapy detection
- ✅ Same class drug detection
- ✅ Maximum daily dose validation
- ✅ Contraindicated conditions

**Example:**
```python
def test_allergy_detection(sample_patient_snapshot):
    checker = PrescriptionSafetyChecker()
    snapshot.allergies = ["Penicillin"]

    prescription = Prescription(
        medications=[Medication(drug_name="Amoxicillin", ...)]
    )

    alerts = checker.validate_prescription(prescription, snapshot)
    blocking_alerts = [a for a in alerts if a.action == "BLOCK"]
    assert len(blocking_alerts) > 0
```

### 5. `test_communication_services.py`

Tests WhatsApp/SMS delivery and reminders.

**Key Tests:**
- ✅ Appointment reminder scheduling
- ✅ Follow-up reminder creation
- ✅ Medication reminders
- ✅ Broadcast to patient segments
- ✅ Template rendering (English, Hindi)
- ✅ Notification queue priority
- ✅ Retry on failure
- ✅ Rate limiting
- ✅ Opt-out handling
- ✅ Birthday greetings
- ✅ Critical lab alerts

**Example:**
```python
@pytest.mark.asyncio
async def test_appointment_reminder_scheduling(mock_whatsapp_client):
    await mock_whatsapp_client.send_prescription(
        phone="9876543210",
        prescription={"message": "Appointment tomorrow"},
        patient_name="Ram Lal"
    )
    assert len(mock_whatsapp_client.sent_messages) == 1
```

### 6. `test_audit_trail.py`

Tests audit logging and compliance.

**Key Tests:**
- ✅ Consultation start/end logged
- ✅ Prescription logged with warnings
- ✅ Safety alert overrides logged
- ✅ Patient view access logged
- ✅ Chain integrity (blockchain-like)
- ✅ Legal export format
- ✅ Unauthorized access attempts
- ✅ Bulk export logging
- ✅ Record modifications logged
- ✅ Deletions logged with reason
- ✅ User login/logout tracking
- ✅ Compliance report generation

**Example:**
```python
@pytest.mark.asyncio
async def test_chain_integrity():
    audit_chain = []
    previous_hash = "0" * 64

    for entry in entries:
        entry["previous_hash"] = previous_hash
        current_hash = calculate_hash(entry)
        entry["hash"] = current_hash
        audit_chain.append(entry)
        previous_hash = current_hash

    # Verify integrity
    for i in range(1, len(audit_chain)):
        assert audit_chain[i-1]["hash"] == audit_chain[i]["previous_hash"]
```

### 7. `test_clinical_integration.py`

Tests complete end-to-end workflows.

**Key Tests:**
- ✅ Full consultation flow (start to finish)
- ✅ Voice to prescription flow
- ✅ Patient timeline updated
- ✅ Analytics recorded
- ✅ Event bus propagation
- ✅ Concurrent consultations
- ✅ Critical lab alert workflow
- ✅ Prescription with allergy block
- ✅ Follow-up reminder integration
- ✅ Multi-medication safety check
- ✅ Error handling (DB failure)
- ✅ State recovery after error

**Example:**
```python
@pytest.mark.asyncio
async def test_full_consultation_flow(clinical_flow, sample_patient):
    # 1. Start consultation
    context = await clinical_flow.start_consultation(...)

    # 2. Process speech
    speech_result = await clinical_flow.process_speech(audio_data)

    # 3. Generate prescription
    prescription = await clinical_flow.generate_prescription(medications, ...)

    # 4. Complete consultation
    summary = await clinical_flow.complete_consultation(visit_data)

    assert summary["visit_id"] is not None
    assert summary["prescription_sent"] is True
```

### 8. `test_clinical_scenarios.py`

Tests real-world clinical presentations.

**Key Tests:**
- ✅ Diabetic patient routine visit
- ✅ Chest pain emergency (ACS)
- ✅ Pediatric fever with rash
- ✅ Antenatal checkup
- ✅ Prescription with interactions
- ✅ Hypertensive urgency
- ✅ COPD exacerbation
- ✅ UTI with renal impairment

**Example:**
```python
@pytest.mark.asyncio
async def test_diabetic_patient_routine_visit(clinical_flow, mock_database):
    # Create diabetic patient with previous HbA1c
    patient = mock_database.add_patient(Patient(...))

    # Add HbA1c result
    investigation = Investigation(test_name="HbA1c", result="7.8", ...)

    # Complete consultation
    context = await clinical_flow.start_consultation(...)
    prescription = await clinical_flow.generate_prescription(...)
    summary = await clinical_flow.complete_consultation(...)

    assert summary["visit_id"] is not None
```

## Fixtures

### Patient Fixtures

Located in `tests/fixtures/sample_patients_extended.py`:

- **Diabetic patients**: Controlled and uncontrolled
- **Cardiac patients**: AF on warfarin, post-MI
- **CKD patient**: Stage 3 with renal impairment
- **Pediatric patient**: Asthma
- **Pregnant patient**: Antenatal care
- **Allergy patient**: Multiple allergies

### Prescription Fixtures

Located in `tests/fixtures/sample_prescriptions_extended.py`:

- Simple prescriptions (viral fever, URTI)
- Chronic disease management (diabetes, hypertension)
- Prescriptions with interactions
- Emergency prescriptions (ACS, anaphylaxis)
- Pediatric prescriptions
- Dose adjustment scenarios

### Transcript Fixtures

Located in `tests/fixtures/sample_transcripts.py`:

- **English transcripts**: Fever, chest pain, diabetes
- **Hindi transcripts**: बुखार, पेट दर्द, BP
- **Hinglish transcripts**: Mixed clinical notes
- **Red flag scenarios**: Cardiac, neuro, sepsis

## Test Data

All test data is self-contained and uses:

- **In-memory SQLite database** - No persistent data
- **Mock services** - LLM, WhatsApp, Speech-to-Text
- **Sample patients** - Realistic clinical profiles
- **Sample prescriptions** - Common and edge cases

## Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| Clinical Flow | 90% | - |
| Safety Checker | 95% | - |
| Clinical Rules | 100% | - |
| Communication | 80% | - |
| Audit Logger | 90% | - |
| **Overall** | **80%** | **-** |

## Continuous Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Clinical Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run clinical tests
        run: |
          pytest tests/test_*.py --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Best Practices

1. **Use fixtures** - Don't create test data in tests
2. **Test one thing** - Each test should validate one behavior
3. **Clear assertions** - Use descriptive assertion messages
4. **Mock external services** - Don't make real API calls
5. **Test edge cases** - Include boundary conditions
6. **Test error paths** - Validate error handling
7. **Keep tests fast** - Use in-memory databases
8. **Descriptive names** - Test names should describe what's tested

## Troubleshooting

### Tests failing due to missing fixtures

```bash
# Ensure clinical_conftest.py is being loaded
pytest --fixtures | grep clinical
```

### Async tests not running

```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Check test is marked
@pytest.mark.asyncio
async def test_something():
    ...
```

### Import errors

```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/emr"
pytest tests/
```

## Contributing

When adding new tests:

1. Add test to appropriate file
2. Use existing fixtures where possible
3. Add new fixtures to `clinical_conftest.py`
4. Update this README if adding new test file
5. Ensure tests pass: `pytest tests/ -v`
6. Check coverage: `pytest tests/ --cov=src`

## License

Same as DocAssist EMR project.

## Support

For questions about tests:
- Check this README
- Review existing test files for examples
- Check `clinical_conftest.py` for available fixtures
