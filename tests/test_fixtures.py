"""Test that all fixtures can be imported and used correctly."""

import pytest
from datetime import date


def test_patient_fixtures_import():
    """Test that patient fixtures can be imported."""
    from tests.fixtures import PATIENTS, generate_patients, get_patient_by_condition

    # Test patient dictionary
    assert 'diabetic_elderly' in PATIENTS
    assert PATIENTS['diabetic_elderly'].name == 'Ramesh Kumar'
    assert PATIENTS['diabetic_elderly'].age == 65

    # Test patient generator
    patients = generate_patients(n=5, seed=42)
    assert len(patients) == 5
    assert all(p.name for p in patients)
    assert all(p.phone for p in patients)

    # Test get patient by condition
    result = get_patient_by_condition('diabetic_elderly')
    assert result is not None
    patient, snapshot = result
    assert patient.name == 'Ramesh Kumar'
    assert snapshot.uhid == "EMR-2024-00001"


def test_visit_fixtures_import():
    """Test that visit fixtures can be imported."""
    from tests.fixtures import VISITS, generate_visit_history, create_routine_visit

    # Test visit dictionary
    assert 'routine_diabetes_checkup' in VISITS
    assert VISITS['routine_diabetes_checkup'].chief_complaint == 'Routine diabetes checkup'

    # Test visit generator
    visits = generate_visit_history(patient_id=1, n_visits=5)
    assert len(visits) == 5
    assert all(v.patient_id == 1 for v in visits)

    # Test create routine visit
    visit = create_routine_visit(patient_id=1, visit_type="diabetes")
    assert visit.patient_id == 1
    assert "diabetes" in visit.chief_complaint.lower()


def test_lab_results_fixtures_import():
    """Test that lab result fixtures can be imported."""
    from tests.fixtures import LAB_RESULTS, generate_lab_history, create_lab_result

    # Test lab results dictionary
    assert 'normal_cbc' in LAB_RESULTS
    assert 'diabetic_hba1c_high' in LAB_RESULTS

    # Test lab history generator
    history = generate_lab_history(patient_id=1, test_name="HbA1c", months=6, trend="improving")
    assert len(history) == 6
    assert all(h.test_name == "HbA1c" for h in history)

    # Test create lab result
    lab = create_lab_result(
        patient_id=1,
        test_name="Hemoglobin",
        result="14.5",
        unit="g/dL",
        reference_range="13-17"
    )
    assert lab.test_name == "Hemoglobin"
    assert lab.result == "14.5"


def test_prescription_fixtures_import():
    """Test that prescription fixtures can be imported."""
    from tests.fixtures import get_prescription_by_scenario, get_all_sample_prescriptions

    # Test get prescription by scenario
    prescription = get_prescription_by_scenario("diabetes")
    assert prescription is not None
    assert "Diabetes" in prescription.diagnosis[0]

    # Test get all prescriptions
    all_prescriptions = get_all_sample_prescriptions()
    assert len(all_prescriptions) > 0


def test_transcript_fixtures_import():
    """Test that transcript fixtures can be imported."""
    from tests.fixtures import get_transcript_by_language, get_all_transcripts

    # Test get transcript by language
    transcript = get_transcript_by_language("fever", "english")
    assert transcript
    assert "fever" in transcript.lower()

    # Test get all transcripts
    all_transcripts = get_all_transcripts()
    assert 'english' in all_transcripts
    assert 'hindi' in all_transcripts
    assert 'hinglish' in all_transcripts


def test_interaction_fixtures_import():
    """Test that drug interaction fixtures can be imported."""
    from tests.fixtures import INTERACTION_SCENARIOS, get_critical_interactions

    # Test interaction scenarios
    assert 'warfarin_aspirin' in INTERACTION_SCENARIOS
    assert INTERACTION_SCENARIOS['warfarin_aspirin']['expected_severity'] == 'CRITICAL'

    # Test get critical interactions
    critical = get_critical_interactions()
    assert len(critical) > 0
    assert all(s['expected_severity'] == 'CRITICAL' for s in critical.values())


def test_red_flag_fixtures_import():
    """Test that red flag fixtures can be imported."""
    from tests.fixtures import RED_FLAG_SCENARIOS, get_red_flags_by_urgency

    # Test red flag scenarios
    assert 'acute_mi' in RED_FLAG_SCENARIOS
    assert RED_FLAG_SCENARIOS['acute_mi']['expected_urgency'] == 'EMERGENCY'

    # Test get by urgency
    emergencies = get_red_flags_by_urgency('EMERGENCY')
    assert len(emergencies) > 0


def test_factory_functions():
    """Test factory functions."""
    from tests.fixtures import (
        create_patient, create_visit, create_prescription,
        create_medication, create_investigation, create_clinic_data
    )

    # Test create patient
    patient = create_patient(name="Test Patient", age=45, gender="M")
    assert patient.name == "Test Patient"
    assert patient.age == 45
    assert patient.gender == "M"

    # Test create visit
    visit = create_visit(patient_id=1, chief_complaint="Test complaint")
    assert visit.patient_id == 1
    assert visit.chief_complaint == "Test complaint"

    # Test create prescription
    prescription = create_prescription(
        diagnosis=["Test diagnosis"],
        medications=[create_medication("Test Drug", "10mg")]
    )
    assert "Test diagnosis" in prescription.diagnosis
    assert prescription.medications[0].drug_name == "Test Drug"

    # Test create investigation
    investigation = create_investigation(
        patient_id=1,
        test_name="Test",
        result="Normal"
    )
    assert investigation.test_name == "Test"
    assert investigation.result == "Normal"

    # Test create clinic data
    clinic_data = create_clinic_data(n_patients=5, n_visits_per_patient=3, seed=42)
    assert len(clinic_data.patients) == 5
    assert len(clinic_data.visits) > 0


def test_scenario_fixtures():
    """Test scenario fixtures."""
    from tests.fixtures import SCENARIOS, generate_clinic_day, get_scenario_by_type

    # Test scenarios dictionary
    assert 'busy_monday_morning' in SCENARIOS
    assert SCENARIOS['busy_monday_morning']['total_patients'] == 25

    # Test generate clinic day
    clinic_day = generate_clinic_day('busy_monday_morning', seed=42)
    assert clinic_day.scenario_name == 'busy_monday_morning'
    assert len(clinic_day.patients) == 25
    assert len(clinic_day.visits) == 25

    # Test get scenario by type
    busy_scenarios = get_scenario_by_type('busy')
    assert len(busy_scenarios) > 0


def test_comprehensive_patient_with_history():
    """Test creating comprehensive patient with full history."""
    from tests.fixtures import create_diabetic_patient_with_history

    data = create_diabetic_patient_with_history(patient_id=1)

    assert 'patient' in data
    assert 'visits' in data
    assert 'investigations' in data
    assert 'medications' in data

    patient = data['patient']
    assert patient.name == "Ramesh Kumar"
    assert patient.age == 58

    visits = data['visits']
    assert len(visits) == 4  # Quarterly visits

    investigations = data['investigations']
    assert len(investigations) == 4  # HbA1c every 3 months
    assert all(i.test_name == "HbA1c" for i in investigations)

    medications = data['medications']
    assert len(medications) == 3
    assert any(m.drug_name == "Metformin" for m in medications)


def test_emergency_case_generation():
    """Test emergency case generation."""
    from tests.fixtures import create_emergency_case

    # Test chest pain emergency
    case = create_emergency_case(emergency_type="chest_pain")
    assert 'patient' in case
    assert 'visit' in case
    assert 'vitals' in case
    assert "chest pain" in case['visit'].chief_complaint.lower()

    # Test stroke emergency
    case = create_emergency_case(emergency_type="stroke")
    assert "stroke" in case['visit'].diagnosis.lower()

    # Test asthma emergency
    case = create_emergency_case(emergency_type="asthma")
    assert "asthma" in case['visit'].diagnosis.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
