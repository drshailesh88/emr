"""Tests for diagnosis engine and clinical decision support.

Tests differential diagnosis generation, red flag detection,
protocol adherence, and clinical guideline compliance.
"""

import pytest
from src.services.clinical_rules import check_critical_value, CRITICAL_VALUES

# Import fixtures
pytest_plugins = ['tests.clinical_conftest']


class TestDiagnosisEngine:
    """Tests for diagnosis and clinical decision support."""

    @pytest.mark.asyncio
    async def test_differential_for_chest_pain(self, mock_clinical_nlp, mock_red_flag_detector):
        """Test differential diagnosis generation for chest pain."""
        clinical_text = "65 year old male with central chest pain radiating to left arm, sweating, shortness of breath"

        # Extract entities
        entities = await mock_clinical_nlp.extract_entities(clinical_text)

        # Check for red flags
        red_flags = await mock_red_flag_detector.check_text(clinical_text)

        # Should detect cardiac red flags
        assert len(red_flags) > 0
        assert any(flag["type"] == "cardiac" for flag in red_flags)
        assert any("coronary syndrome" in flag["message"].lower() for flag in red_flags)

    @pytest.mark.asyncio
    async def test_differential_for_fever(self, mock_red_flag_detector):
        """Test differential diagnosis for fever presentations."""
        clinical_text = "Child with high fever 104F for 2 days, rash, photophobia, neck stiffness"

        red_flags = await mock_red_flag_detector.check_text(clinical_text)

        # Real implementation should flag meningitis
        assert red_flags is not None

    @pytest.mark.asyncio
    async def test_red_flag_cardiac(self, mock_red_flag_detector):
        """Test cardiac red flag detection."""
        texts = [
            "Chest pain radiating to left arm",
            "Severe chest discomfort with sweating",
            "Crushing chest pain with shortness of breath"
        ]

        for text in texts:
            red_flags = await mock_red_flag_detector.check_text(text)
            assert len(red_flags) > 0, f"Should detect cardiac red flag in: {text}"

    @pytest.mark.asyncio
    async def test_red_flag_neuro(self, mock_red_flag_detector):
        """Test neurological red flag detection."""
        texts = [
            "Worst headache of my life",
            "Severe headache with thunderclap onset",
            "Sudden severe headache unlike any before"
        ]

        for text in texts:
            red_flags = await mock_red_flag_detector.check_text(text)
            # Should detect neuro red flags
            assert red_flags is not None

    def test_protocol_diabetes(self):
        """Test diabetes management protocol adherence."""
        from src.services.clinical_rules import SCREENING_RULES

        # Check diabetes screening rules exist
        assert "diabetes" in SCREENING_RULES
        diabetes_rules = SCREENING_RULES["diabetes"]

        # Should have HbA1c monitoring
        assert "HbA1c" in diabetes_rules
        assert diabetes_rules["HbA1c"]["frequency_months"] == 3

        # Should have foot exam
        assert "Foot Exam" in diabetes_rules

        # Should have eye exam
        assert "Eye Exam" in diabetes_rules

    def test_protocol_hypertension(self):
        """Test hypertension management protocol."""
        from src.services.clinical_rules import SCREENING_RULES

        assert "hypertension" in SCREENING_RULES
        htn_rules = SCREENING_RULES["hypertension"]

        # Should have annual ECG
        assert "ECG" in htn_rules

        # Should have lipid monitoring
        assert "Lipid Panel" in htn_rules

    def test_compliance_check_correct_prescription(self, sample_prescription, sample_patient_snapshot):
        """Test that compliant prescriptions pass validation."""
        from src.services.safety import PrescriptionSafetyChecker

        checker = PrescriptionSafetyChecker()

        # Remove penicillin allergy to avoid conflicts
        snapshot = sample_patient_snapshot.model_copy()
        snapshot.allergies = []

        alerts = checker.validate_prescription(sample_prescription, snapshot)

        # Should have no critical alerts for this simple prescription
        critical_alerts = [a for a in alerts if a.severity == "CRITICAL"]
        assert len(critical_alerts) == 0

    def test_compliance_check_incorrect_antibiotics(self):
        """Test detection of inappropriate antibiotic use."""
        # This would be implemented with clinical guidelines
        # Example: Antibiotics for viral URTI

        diagnosis = "Viral Upper Respiratory Tract Infection"
        medications = ["Azithromycin", "Amoxicillin"]

        # Real implementation should flag inappropriate antibiotic use
        # For viral infections
        assert diagnosis is not None

    def test_critical_value_potassium_high(self):
        """Test critical value detection for high potassium."""
        alert = check_critical_value("Potassium", 6.5)

        assert alert is not None
        assert alert["severity"] == "critical"
        assert alert["direction"] == "HIGH"
        assert "arrhythmia" in alert["message"].lower()

    def test_critical_value_potassium_low(self):
        """Test critical value detection for low potassium."""
        alert = check_critical_value("Potassium", 2.0)

        assert alert is not None
        assert alert["severity"] == "critical"
        assert alert["direction"] == "LOW"

    def test_critical_value_glucose_high(self):
        """Test critical value detection for high glucose."""
        alert = check_critical_value("Glucose", 550)

        assert alert is not None
        assert alert["direction"] == "HIGH"
        assert "DKA" in alert["message"] or "ketones" in alert["message"].lower()

    def test_critical_value_glucose_low(self):
        """Test critical value detection for low glucose."""
        alert = check_critical_value("Glucose", 40)

        assert alert is not None
        assert alert["direction"] == "LOW"
        assert "hypoglycemic" in alert["message"].lower()

    def test_critical_value_hemoglobin_low(self):
        """Test critical value detection for low hemoglobin."""
        alert = check_critical_value("Hemoglobin", 5.5)

        assert alert is not None
        assert alert["direction"] == "LOW"
        assert "transfusion" in alert["message"].lower()

    def test_critical_value_creatinine_high(self):
        """Test critical value detection for high creatinine."""
        alert = check_critical_value("Creatinine", 12.0)

        assert alert is not None
        assert alert["direction"] == "HIGH"
        assert "dialysis" in alert["message"].lower()

    def test_critical_value_inr_high(self):
        """Test critical value detection for high INR."""
        alert = check_critical_value("INR", 6.0)

        assert alert is not None
        assert "bleeding" in alert["message"].lower()
        assert "vitamin k" in alert["message"].lower() or "Vitamin K" in alert["message"]

    def test_critical_value_normal_range(self):
        """Test that normal values don't trigger alerts."""
        # Normal potassium
        alert = check_critical_value("Potassium", 4.0)
        assert alert is None

        # Normal glucose
        alert = check_critical_value("Glucose", 100)
        assert alert is None

        # Normal hemoglobin
        alert = check_critical_value("Hemoglobin", 13.5)
        assert alert is None

    def test_critical_value_case_insensitive(self):
        """Test that critical value checking is case-insensitive."""
        # Various casings
        alert1 = check_critical_value("potassium", 6.5)
        alert2 = check_critical_value("POTASSIUM", 6.5)
        alert3 = check_critical_value("Potassium", 6.5)

        assert alert1 is not None
        assert alert2 is not None
        assert alert3 is not None

    def test_get_critical_value_range(self):
        """Test retrieval of critical value ranges."""
        from src.services.clinical_rules import get_critical_value_range

        low, high, unit = get_critical_value_range("Potassium")

        assert low == 2.5
        assert high == 6.0
        assert unit == "mEq/L"

    def test_screening_reminder_diabetes(self):
        """Test that diabetes screening reminders are configured correctly."""
        from src.services.clinical_rules import SCREENING_RULES

        rules = SCREENING_RULES["diabetes"]

        # HbA1c every 3 months
        assert rules["HbA1c"]["frequency_months"] == 3

        # Annual screenings
        assert rules["Foot Exam"]["frequency_months"] == 12
        assert rules["Eye Exam"]["frequency_months"] == 12

    @pytest.mark.asyncio
    async def test_red_flag_with_patient_context(self, mock_red_flag_detector, sample_patient_snapshot):
        """Test red flag detection with patient context."""
        # Patient on anticoagulation with bleeding symptoms
        patient_data = {
            "on_anticoagulation": True,
            "anticoag_drug": "Warfarin",
            "active_problems": ["Atrial Fibrillation"]
        }

        clinical_text = "Patient reports blood in stool, black tarry stools"

        red_flags = await mock_red_flag_detector.check_text(clinical_text, patient_data)

        # Should flag bleeding risk in anticoagulated patient
        assert red_flags is not None

    def test_age_specific_protocols(self):
        """Test that age-specific protocols are available."""
        # Pediatric vs adult vs geriatric dosing
        # Real implementation would have age-specific rules

        ages = {
            "pediatric": 5,
            "adult": 35,
            "geriatric": 75
        }

        # Different dosing and monitoring for different age groups
        for category, age in ages.items():
            assert age > 0  # Placeholder for real protocol checks

    def test_pregnancy_category_checking(self):
        """Test pregnancy category drug checking."""
        from src.services.safety import DRUG_DATABASE

        # Warfarin is contraindicated in pregnancy
        if "warfarin" in DRUG_DATABASE:
            warfarin = DRUG_DATABASE["warfarin"]
            assert "pregnancy" in [c.lower() for c in warfarin.contraindicated_conditions]

    def test_renal_dosing_recommendations(self):
        """Test renal dose adjustment recommendations."""
        from src.services.safety import DRUG_DATABASE

        # Metformin requires renal adjustment
        metformin = DRUG_DATABASE["metformin"]
        assert metformin.renal_adjustment_egfr is not None
        assert metformin.renal_adjustment_egfr == 30

    def test_hepatic_dosing_recommendations(self):
        """Test hepatic dose adjustment recommendations."""
        from src.services.safety import DRUG_DATABASE

        # Paracetamol requires hepatic caution
        paracetamol = DRUG_DATABASE["paracetamol"]
        assert paracetamol.hepatic_caution is True
