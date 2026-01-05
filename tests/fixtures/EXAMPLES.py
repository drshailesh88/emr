"""Practical examples of using DocAssist EMR test fixtures."""

from datetime import date


# ============== EXAMPLE 1: Generate Test Patients ==============

def example_generate_test_patients():
    """Generate a batch of test patients for testing."""
    from tests.fixtures import generate_patients

    # Generate 100 random patients with realistic Indian demographics
    patients = generate_patients(n=100, seed=42)

    print(f"Generated {len(patients)} patients")
    print("\nFirst 5 patients:")
    for i, p in enumerate(patients[:5], 1):
        print(f"  {i}. {p.name}, {p.age}y {p.gender}, {p.phone}")


# ============== EXAMPLE 2: Get Patient with Medical History ==============

def example_diabetic_patient():
    """Get a complete diabetic patient with medical history."""
    from tests.fixtures import get_patient_by_condition

    patient, snapshot = get_patient_by_condition('diabetic_elderly')

    print(f"\nPatient: {patient.name} ({snapshot.demographics})")
    print(f"UHID: {snapshot.uhid}")
    print(f"\nActive Problems:")
    for problem in snapshot.active_problems:
        print(f"  - {problem}")

    print(f"\nCurrent Medications:")
    for med in snapshot.current_medications:
        print(f"  - {med.drug_name} {med.strength} {med.frequency}")

    print(f"\nKey Labs:")
    for test, result in snapshot.key_labs.items():
        print(f"  - {test}: {result['value']} {result.get('unit', '')}")


# ============== EXAMPLE 3: Simulate a Clinic Day ==============

def example_busy_clinic_day():
    """Simulate a busy Monday morning clinic."""
    from tests.fixtures import generate_clinic_day

    clinic = generate_clinic_day('busy_monday_morning', seed=42)

    print(f"\nClinic Day: {clinic.scenario_name}")
    print(f"Date: {clinic.date}")
    print(f"\nStatistics:")
    for key, value in clinic.statistics.items():
        print(f"  {key}: {value}")

    print(f"\nFirst 5 patients of the day:")
    for i, (patient, visit) in enumerate(zip(clinic.patients[:5], clinic.visits[:5]), 1):
        print(f"  {i}. {patient.name} - {visit.chief_complaint}")


# ============== EXAMPLE 4: Test Drug Interactions ==============

def example_drug_interaction_check():
    """Test drug interaction detection."""
    from tests.fixtures import INTERACTION_SCENARIOS, get_critical_interactions

    print("\n=== Critical Drug Interactions ===")

    # Check warfarin + aspirin interaction
    warfarin_aspirin = INTERACTION_SCENARIOS['warfarin_aspirin']
    print(f"\nScenario: Warfarin + Aspirin")
    print(f"Current: {warfarin_aspirin['current']}")
    print(f"New: {warfarin_aspirin['new']}")
    print(f"Severity: {warfarin_aspirin['expected_severity']}")
    print(f"Warning: {warfarin_aspirin['expected_message']}")
    print(f"Clinical Note: {warfarin_aspirin['clinical_notes']}")

    # Get all critical interactions
    critical = get_critical_interactions()
    print(f"\nTotal critical interactions: {len(critical)}")


# ============== EXAMPLE 5: Test Red Flag Detection ==============

def example_emergency_red_flags():
    """Test emergency red flag detection."""
    from tests.fixtures import RED_FLAG_SCENARIOS, get_cardiac_emergencies

    print("\n=== Emergency Red Flags ===")

    # Acute MI scenario
    acute_mi = RED_FLAG_SCENARIOS['acute_mi']
    print(f"\nScenario: Acute Myocardial Infarction")
    print(f"Urgency: {acute_mi['expected_urgency']}")
    print(f"\nSymptoms:")
    for symptom in acute_mi['symptoms']:
        print(f"  - {symptom}")

    print(f"\nVitals:")
    for vital, value in acute_mi['vitals'].items():
        print(f"  {vital}: {value}")

    print(f"\nImmediate Management:")
    for step in acute_mi['immediate_management'][:3]:
        print(f"  - {step}")

    print(f"\nTime-Sensitive: {acute_mi['time_sensitive']}")


# ============== EXAMPLE 6: Generate Lab History with Trends ==============

def example_lab_trend_analysis():
    """Generate and analyze lab trends."""
    from tests.fixtures import generate_lab_history

    print("\n=== HbA1c Trend Analysis ===")

    # Generate improving HbA1c trend over 6 months
    improving = generate_lab_history(
        patient_id=1,
        test_name="HbA1c",
        months=6,
        trend="improving"
    )

    print("\nImproving trend (good diabetes control):")
    for lab in improving:
        print(f"  {lab.test_date}: {lab.result}% {'(abnormal)' if lab.is_abnormal else ''}")

    # Generate worsening trend
    worsening = generate_lab_history(
        patient_id=2,
        test_name="Creatinine",
        months=6,
        trend="worsening"
    )

    print("\nWorsening trend (declining renal function):")
    for lab in worsening:
        print(f"  {lab.test_date}: {lab.result} mg/dL {'(abnormal)' if lab.is_abnormal else ''}")


# ============== EXAMPLE 7: Create Emergency Case ==============

def example_emergency_case():
    """Create a complete emergency case."""
    from tests.fixtures import create_emergency_case

    print("\n=== Emergency Case: Chest Pain ===")

    case = create_emergency_case(emergency_type="chest_pain")

    patient = case['patient']
    visit = case['visit']
    vitals = case['vitals']

    print(f"\nPatient: {patient.name}, {patient.age}y {patient.gender}")
    print(f"Chief Complaint: {visit.chief_complaint}")
    print(f"Diagnosis: {visit.diagnosis}")
    print(f"\nVitals:")
    print(f"  BP: {vitals.bp_systolic}/{vitals.bp_diastolic} mmHg")
    print(f"  Pulse: {vitals.pulse}/min")
    print(f"  SpO2: {vitals.spo2}%")


# ============== EXAMPLE 8: Generate Complete Clinic Data ==============

def example_complete_clinic():
    """Generate complete clinic with all data."""
    from tests.fixtures import create_clinic_data

    print("\n=== Complete Clinic Data ===")

    clinic = create_clinic_data(
        n_patients=20,
        n_visits_per_patient=5,
        seed=42
    )

    print(f"\nGenerated clinic data:")
    print(f"  Patients: {len(clinic.patients)}")
    print(f"  Visits: {len(clinic.visits)}")
    print(f"  Investigations: {len(clinic.investigations)}")
    print(f"  Procedures: {len(clinic.procedures)}")
    print(f"  Vitals: {len(clinic.vitals)}")

    # Show a sample patient with their data
    sample_patient = clinic.patients[0]
    patient_visits = [v for v in clinic.visits if v.patient_id == sample_patient.id]
    patient_labs = [l for l in clinic.investigations if l.patient_id == sample_patient.id]

    print(f"\nSample patient: {sample_patient.name}")
    print(f"  Visits: {len(patient_visits)}")
    print(f"  Lab tests: {len(patient_labs)}")


# ============== EXAMPLE 9: Test Transcripts ==============

def example_multilingual_transcripts():
    """Test multilingual voice transcripts."""
    from tests.fixtures import get_transcript_by_language, get_all_transcripts

    print("\n=== Multilingual Transcripts ===")

    # Get Hindi transcript
    hindi = get_transcript_by_language("fever", "hindi")
    print("\nHindi (Fever case):")
    print(hindi[:100] + "...")

    # Get Hinglish transcript
    hinglish = get_transcript_by_language("diabetes", "hinglish")
    print("\nHinglish (Diabetes case):")
    print(hinglish[:100] + "...")

    # Count all available transcripts
    all_transcripts = get_all_transcripts()
    total = sum(len(cases) for cases in all_transcripts.values())
    print(f"\nTotal transcripts available: {total}")


# ============== EXAMPLE 10: Weekly Schedule ==============

def example_weekly_schedule():
    """Generate a complete weekly clinic schedule."""
    from tests.fixtures import generate_weekly_schedule

    print("\n=== Weekly Clinic Schedule ===")

    schedule = generate_weekly_schedule(seed=42)

    print(f"\nWeek starting: {list(schedule.values())[0].date}")

    for day_name, clinic_day in schedule.items():
        stats = clinic_day.statistics
        print(f"\n{day_name}:")
        print(f"  Scenario: {clinic_day.scenario_name}")
        print(f"  Total patients: {stats['total_patients']}")
        print(f"  - Routine: {stats['routine_followup']}")
        print(f"  - New: {stats['new_patients']}")
        print(f"  - Acute: {stats['acute_illness']}")
        print(f"  - Emergency: {stats['emergencies']}")


# ============== RUN ALL EXAMPLES ==============

if __name__ == "__main__":
    print("=" * 80)
    print("DocAssist EMR Test Fixtures - Practical Examples")
    print("=" * 80)

    example_generate_test_patients()
    example_diabetic_patient()
    example_busy_clinic_day()
    example_drug_interaction_check()
    example_emergency_red_flags()
    example_lab_trend_analysis()
    example_emergency_case()
    example_complete_clinic()
    example_multilingual_transcripts()
    example_weekly_schedule()

    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)
