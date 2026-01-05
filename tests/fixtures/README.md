# DocAssist EMR Test Fixtures

Comprehensive test data fixtures for DocAssist EMR covering all clinical scenarios.

## Overview

This directory contains realistic test data for:
- **Patients**: Various demographics, conditions, and medical histories
- **Visits**: Routine checkups, emergencies, follow-ups
- **Prescriptions**: Standard treatments, complex polypharmacy cases
- **Lab Results**: Normal and abnormal test results with trends
- **Transcripts**: Hindi, English, and Hinglish voice notes
- **Drug Interactions**: Safety scenarios and contraindications
- **Red Flags**: Medical emergencies requiring immediate attention
- **Scenarios**: Complete clinic day simulations

## Quick Start

```python
from tests.fixtures import (
    PATIENTS, generate_patients,
    VISITS, create_routine_visit,
    LAB_RESULTS, generate_lab_history,
    create_clinic_data,
    generate_clinic_day
)

# Get a predefined patient
patient = PATIENTS['diabetic_elderly']

# Generate random patients
patients = generate_patients(n=10, seed=42)

# Create a clinic day scenario
clinic_day = generate_clinic_day('busy_monday_morning', seed=42)
# Access: clinic_day.patients, clinic_day.visits, clinic_day.statistics
```

## Patient Fixtures

### Predefined Patients (`patients.py`)

```python
PATIENTS = {
    'diabetic_elderly': ...,      # 65M with Type 2 DM
    'diabetic_young': ...,         # 42M with early diabetes
    'cardiac_af': ...,             # 72M with atrial fibrillation
    'post_mi': ...,                # 60M post-MI on anticoagulation
    'ckd_stage_3': ...,           # 68F with CKD
    'pediatric_asthma': ...,      # 8M with asthma
    'pregnant_normal': ...,        # 28F pregnant at 28 weeks
    'elderly_polypharmacy': ...,  # 78F on 10+ medications
    # ... 25 total patient templates
}
```

### Generate Random Patients

```python
# Generate n patients with realistic Indian demographics
patients = generate_patients(n=100, seed=42)

# Generate patient with specific condition
from tests.fixtures import generate_patient_with_condition
diabetic = generate_patient_with_condition("diabetes")
cardiac = generate_patient_with_condition("cardiac")
pediatric = generate_patient_with_condition("pediatric")
```

### Get Patient with Full Snapshot

```python
from tests.fixtures import get_patient_by_condition

patient, snapshot = get_patient_by_condition('diabetic_elderly')

# Access clinical data
print(snapshot.active_problems)        # Current diagnoses
print(snapshot.current_medications)    # Current meds
print(snapshot.allergies)              # Known allergies
print(snapshot.key_labs)               # Latest lab values
print(snapshot.on_anticoagulation)     # Safety flag
```

## Visit Fixtures

### Predefined Visits (`visits.py`)

```python
VISITS = {
    'routine_diabetes_checkup': ...,
    'acute_chest_pain': ...,           # Emergency
    'fever_child': ...,                # Pediatric
    'antenatal_checkup': ...,         # Pregnancy
    'follow_up_hypertension': ...,
    'copd_exacerbation': ...,         # Respiratory emergency
}
```

### Generate Visit History

```python
from tests.fixtures import generate_visit_history

# Generate 12 months of visits
visits = generate_visit_history(
    patient_id=1,
    n_visits=12,
    visit_interval_days=30
)
```

### Create Custom Visits

```python
from tests.fixtures import create_routine_visit, create_emergency_visit

# Routine visit
visit = create_routine_visit(patient_id=1, visit_type="diabetes")

# Emergency visit
emergency = create_emergency_visit(patient_id=1, emergency_type="chest_pain")
```

## Lab Result Fixtures

### Predefined Lab Results (`lab_results.py`)

```python
LAB_RESULTS = {
    'normal_cbc': [...],               # Normal CBC panel
    'anemia': [...],                   # Microcytic anemia
    'diabetic_hba1c_high': ...,       # HbA1c 9.5%
    'renal_impairment': [...],        # CKD labs
    'critical_potassium_high': ...,   # K+ 6.8 (critical)
    'dyslipidemia': [...],            # Abnormal lipids
    # ... 20 total lab scenarios
}
```

### Generate Lab History with Trends

```python
from tests.fixtures import generate_lab_history

# Generate HbA1c trend (improving over 6 months)
hba1c_history = generate_lab_history(
    patient_id=1,
    test_name="HbA1c",
    months=6,
    trend="improving"  # "improving", "worsening", "stable", "fluctuating"
)

# Generate other test trends
creatinine = generate_lab_history(patient_id=1, test_name="Creatinine", months=12, trend="worsening")
fbs = generate_lab_history(patient_id=1, test_name="Fasting Blood Sugar", months=6, trend="stable")
```

### Diabetes Monitoring Labs

```python
from tests.fixtures import generate_diabetes_monitoring_labs

# 12 months of diabetes monitoring
labs = generate_diabetes_monitoring_labs(patient_id=1, months=12)
# Includes HbA1c every 3 months, FBS monthly
```

## Prescription Fixtures

### Get Prescriptions by Scenario

```python
from tests.fixtures import get_prescription_by_scenario

# Standard prescriptions
diabetes_rx = get_prescription_by_scenario("diabetes")
hypertension_rx = get_prescription_by_scenario("hypertension")
viral_fever_rx = get_prescription_by_scenario("viral_fever")

# Special cases
allergy_safe_rx = get_prescription_by_scenario("penicillin_allergy")
renal_adjusted_rx = get_prescription_by_scenario("renal_adjustment")

# Emergencies
acs_rx = get_prescription_by_scenario("acs")
```

## Drug Interaction Fixtures

### Interaction Scenarios (`interactions.py`)

```python
from tests.fixtures import (
    INTERACTION_SCENARIOS,
    get_critical_interactions,
    get_pregnancy_contraindications
)

# Get specific interaction
warfarin_aspirin = INTERACTION_SCENARIOS['warfarin_aspirin']
print(warfarin_aspirin['expected_severity'])    # 'CRITICAL'
print(warfarin_aspirin['expected_message'])     # Bleeding risk warning
print(warfarin_aspirin['alternatives'])         # Alternative drugs

# Get all critical interactions
critical = get_critical_interactions()

# Get pregnancy contraindications
pregnancy_risks = get_pregnancy_contraindications()

# Get renal contraindications
from tests.fixtures import get_renal_contraindications
renal_risks = get_renal_contraindications()
```

### Available Interaction Categories

- **Major bleeding risks**: warfarin+aspirin, warfarin+NSAID
- **Serotonin syndrome**: SSRI+MAOI (contraindicated)
- **Hyperkalemia**: ACE-I+potassium
- **Pregnancy contraindications**: ACE-I, warfarin, methotrexate
- **Renal contraindications**: metformin in CKD, NSAIDs in CKD
- **Pediatric contraindications**: aspirin in viral illness, tetracyclines

## Red Flag Fixtures

### Emergency Scenarios (`red_flags.py`)

```python
from tests.fixtures import (
    RED_FLAG_SCENARIOS,
    get_red_flags_by_urgency,
    get_cardiac_emergencies
)

# Get specific emergency
acute_mi = RED_FLAG_SCENARIOS['acute_mi']
print(acute_mi['symptoms'])               # List of symptoms
print(acute_mi['vitals'])                 # Abnormal vitals
print(acute_mi['immediate_management'])   # Emergency protocol
print(acute_mi['time_sensitive'])         # "Door to balloon <90 min"

# Get all emergencies by urgency
emergencies = get_red_flags_by_urgency('EMERGENCY')

# Get by category
cardiac = get_cardiac_emergencies()
neuro = get_neurological_emergencies()
respiratory = get_respiratory_emergencies()
```

### Available Emergency Scenarios

- **Cardiac**: Acute MI, acute heart failure
- **Neurological**: Stroke, meningitis, subarachnoid hemorrhage
- **Respiratory**: Severe asthma, pulmonary embolism
- **Abdominal**: Ectopic pregnancy, acute appendicitis
- **Systemic**: Septic shock, anaphylaxis, DKA

## Transcript Fixtures

### Voice Transcripts (`sample_transcripts.py`)

```python
from tests.fixtures import get_transcript_by_language, get_all_transcripts

# Get transcript by language
hindi_fever = get_transcript_by_language("fever", "hindi")
english_chest_pain = get_transcript_by_language("chest_pain", "english")
hinglish_diabetes = get_transcript_by_language("diabetes", "hinglish")

# Get all transcripts organized by language
all_transcripts = get_all_transcripts()
# Returns: {'english': {...}, 'hindi': {...}, 'hinglish': {...}, 'red_flags': {...}}
```

## Factory Functions

### Create Individual Objects

```python
from tests.fixtures import (
    create_patient, create_visit, create_prescription,
    create_medication, create_investigation, create_vitals
)

# Create patient with defaults
patient = create_patient()  # Random Indian name, age, etc.

# Override specific fields
patient = create_patient(
    name="Ramesh Kumar",
    age=58,
    gender="M",
    phone="9876543210"
)

# Create visit
visit = create_visit(
    patient_id=1,
    chief_complaint="Diabetes checkup",
    diagnosis="Type 2 DM - controlled"
)

# Create medication
medication = create_medication(
    drug_name="Metformin",
    strength="500mg",
    frequency="BD",
    instructions="after meals"
)

# Create investigation
lab = create_investigation(
    patient_id=1,
    test_name="HbA1c",
    result="7.2",
    unit="%",
    reference_range="<5.7",
    is_abnormal=True
)
```

### Generate Complete Clinic Data

```python
from tests.fixtures import create_clinic_data

# Generate full clinic with patients, visits, labs
clinic_data = create_clinic_data(
    n_patients=50,
    n_visits_per_patient=5,
    seed=42  # For reproducibility
)

# Access generated data
print(f"Patients: {len(clinic_data.patients)}")
print(f"Visits: {len(clinic_data.visits)}")
print(f"Investigations: {len(clinic_data.investigations)}")
print(f"Procedures: {len(clinic_data.procedures)}")
print(f"Vitals: {len(clinic_data.vitals)}")
```

### Generate Specialized Patient Cases

```python
from tests.fixtures import create_diabetic_patient_with_history

# Complete diabetic patient with 1 year history
data = create_diabetic_patient_with_history(patient_id=1)

patient = data['patient']
visits = data['visits']             # 4 quarterly visits
investigations = data['investigations']  # HbA1c trends
medications = data['medications']   # Current medications
```

## Clinic Scenario Fixtures

### Available Scenarios (`scenarios.py`)

```python
SCENARIOS = {
    'busy_monday_morning': {...},      # 25 patients, 48% routine
    'quiet_sunday': {...},             # 8 patients, emergency coverage
    'flu_season': {...},               # 30 patients, respiratory focus
    'monsoon_clinic': {...},           # 28 patients, dengue/malaria
    'diabetes_screening_camp': {...},  # 50 patients, screening
    'post_holiday_rush': {...},        # 35 patients, injuries
    'pediatric_vaccination_day': {...},
    'senior_citizen_clinic': {...},
    'night_emergency_shift': {...},
    'antenatal_clinic': {...},
}
```

### Generate Complete Clinic Day

```python
from tests.fixtures import generate_clinic_day

clinic_day = generate_clinic_day(
    scenario_name='busy_monday_morning',
    clinic_date=date.today(),
    seed=42
)

# Access generated data
patients = clinic_day.patients
visits = clinic_day.visits
investigations = clinic_day.investigations
vitals = clinic_day.vitals

# View statistics
stats = clinic_day.statistics
print(f"Total patients: {stats['total_patients']}")
print(f"Emergencies: {stats['emergencies']}")
print(f"Expected duration: {stats['expected_duration_minutes']} minutes")
```

### Generate Weekly Schedule

```python
from tests.fixtures import generate_weekly_schedule

schedule = generate_weekly_schedule(seed=42)

# Returns dict mapping day names to ClinicDay objects
monday_clinic = schedule['Monday']
sunday_clinic = schedule['Sunday']
```

## Testing Patterns

### Test Patient Search

```python
from tests.fixtures import generate_patients

def test_patient_search():
    patients = generate_patients(n=100, seed=42)
    # Test search functionality with realistic data
```

### Test Drug Safety

```python
from tests.fixtures import INTERACTION_SCENARIOS

def test_warfarin_aspirin_interaction():
    scenario = INTERACTION_SCENARIOS['warfarin_aspirin']

    # Test detection
    assert detect_interaction(scenario['current'], scenario['new']) is not None

    # Test severity
    alert = detect_interaction(scenario['current'], scenario['new'])
    assert alert.severity == scenario['expected_severity']
```

### Test Red Flag Detection

```python
from tests.fixtures import RED_FLAG_SCENARIOS

def test_acute_mi_detection():
    mi_case = RED_FLAG_SCENARIOS['acute_mi']

    # Test vitals trigger alerts
    vitals = parse_vitals(mi_case['vitals'])
    assert check_red_flags(vitals, mi_case['symptoms']) == 'EMERGENCY'
```

### Test Clinic Load

```python
from tests.fixtures import generate_clinic_day

def test_busy_clinic_performance():
    clinic = generate_clinic_day('busy_monday_morning', seed=42)

    # Test system can handle 25 patients
    assert len(clinic.patients) == 25

    # Test all have visits
    assert len(clinic.visits) == 25
```

## Data Characteristics

### Indian Context
- **Names**: Regional variety (North, South, East, West India)
- **Phone**: Valid Indian mobile format (10 digits, starts with 9/8/7)
- **Addresses**: Real localities from major Indian cities
- **Languages**: Hindi, English, Hinglish support
- **Diseases**: Prevalence matching Indian demographics

### Medical Realism
- **Age distribution**: Matches Indian population pyramid
- **Vital signs**: Realistic normal and abnormal ranges
- **Lab values**: Standard reference ranges used in India
- **Drug names**: Generic names as per Indian practice
- **Dosing**: Standard Indian formulations

### Test Coverage
- **Routine cases**: 48% of clinic volume
- **Acute illness**: 24% of volume
- **New patients**: 20% of volume
- **Emergencies**: 8% of volume
- **Seasonal variations**: Flu season, monsoon patterns

## Files

- `__init__.py` - Central export of all fixtures
- `patients.py` - Patient templates and generators
- `visits.py` - Visit scenarios and generators
- `lab_results.py` - Lab results with trends
- `sample_prescriptions_extended.py` - Prescription templates
- `sample_transcripts.py` - Voice note transcripts
- `interactions.py` - Drug interaction scenarios
- `red_flags.py` - Medical emergency scenarios
- `factories.py` - Factory functions for test data
- `scenarios.py` - Complete clinic simulations

## Contributing

When adding new fixtures:
1. Use realistic Indian names, addresses, phone numbers
2. Follow standard medical terminology
3. Include appropriate reference ranges
4. Add helper functions for common use cases
5. Document in this README
6. Add tests in `test_fixtures.py`

## License

Part of DocAssist EMR project.
