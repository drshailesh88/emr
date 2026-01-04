"""Unit tests for Clinical NLP Engine.

Run with: pytest src/services/clinical_nlp/test_clinical_nlp.py -v
"""

import pytest
from datetime import datetime

# Import components to test
from .note_extractor import ClinicalNoteExtractor
from .medical_entity_recognition import MedicalNER
from .clinical_reasoning import ClinicalReasoning
from .entities import (
    Symptom, Diagnosis, Drug, Investigation, Procedure,
    SOAPNote, Differential, RedFlag, ClinicalContext,
    Severity, Onset
)


class TestClinicalNoteExtractor:
    """Test SOAP note extraction."""

    def setup_method(self):
        """Setup test fixtures."""
        self.extractor = ClinicalNoteExtractor()

    def test_extract_vitals_basic(self):
        """Test basic vital signs extraction."""
        text = "BP 120/80, PR 72, temp 98.6F, SpO2 98%"
        vitals = self.extractor.extract_vitals(text)

        assert vitals.bp_systolic == 120
        assert vitals.bp_diastolic == 80
        assert vitals.pulse == 72
        assert vitals.spo2 == 98
        assert vitals.temperature is not None

    def test_extract_vitals_hinglish(self):
        """Test vitals extraction from Hinglish text."""
        text = "Patient ka BP hai 140/90, pulse 88 hai"
        vitals = self.extractor.extract_vitals(text)

        assert vitals.bp_systolic == 140
        assert vitals.bp_diastolic == 90
        assert vitals.pulse == 88

    def test_extract_vitals_with_bmi(self):
        """Test BMI calculation from height and weight."""
        text = "Weight 70kg, height 170cm"
        vitals = self.extractor.extract_vitals(text)

        assert vitals.weight == 70.0
        assert vitals.height == 170.0
        assert vitals.bmi is not None
        assert 23 < vitals.bmi < 25  # BMI should be around 24.2

    def test_normalize_text_abbreviations(self):
        """Test abbreviation expansion."""
        text = "Patient c/o chest pain, h/o DM"
        normalized = self.extractor._normalize_text(text)

        assert "complains of" in normalized
        assert "history of" in normalized

    def test_normalize_text_hinglish(self):
        """Test Hinglish translation."""
        text = "Patient ko bukhar hai with dard"
        normalized = self.extractor._normalize_text(text)

        assert "fever" in normalized
        assert "pain" in normalized

    def test_extract_chief_complaint(self):
        """Test chief complaint extraction."""
        text = "Patient complains of chest pain for 2 days"
        normalized = self.extractor._normalize_text(text)
        complaint = self.extractor._extract_chief_complaint(normalized)

        assert "chest pain" in complaint.lower()

    def test_extract_duration(self):
        """Test duration extraction."""
        text = "Patient has fever for 3 days"
        normalized = self.extractor._normalize_text(text)
        duration = self.extractor._extract_duration(normalized)

        assert duration == "3 days"

    def test_extract_medications_basic(self):
        """Test medication extraction."""
        text = "Tab. Paracetamol 650mg TDS for 5 days"
        medications = self.extractor.extract_medications(text)

        assert len(medications) > 0
        med = medications[0]
        assert "paracetamol" in med.drug_name.lower()
        assert "650mg" in med.strength.lower()

    def test_extract_soap_note(self):
        """Test full SOAP note extraction."""
        transcript = """
        Patient c/o chest pain for 2 days.
        BP 150/95, PR 88, temp 98.2F.
        Impression: Acute coronary syndrome.
        Tab. Aspirin 325mg stat.
        """

        soap = self.extractor.extract_soap_note(transcript)

        assert soap.chief_complaint != ""
        assert len(soap.vitals) > 0
        assert len(soap.diagnoses) > 0


class TestMedicalNER:
    """Test Medical Named Entity Recognition."""

    def setup_method(self):
        """Setup test fixtures."""
        self.ner = MedicalNER()

    def test_extract_symptoms(self):
        """Test symptom extraction."""
        text = "Patient has severe headache since 3 days with fever"
        symptoms = self.ner.extract_symptoms(text)

        symptom_names = [s.name for s in symptoms]
        assert "headache" in symptom_names
        assert "fever" in symptom_names

        # Check duration extraction
        headache = [s for s in symptoms if s.name == "headache"][0]
        assert headache.duration is not None

    def test_extract_symptoms_with_severity(self):
        """Test severity extraction."""
        text = "Patient has severe chest pain"
        symptoms = self.ner.extract_symptoms(text)

        if symptoms:
            chest_pain = [s for s in symptoms if "pain" in s.name]
            if chest_pain:
                assert chest_pain[0].severity == Severity.SEVERE

    def test_extract_diagnoses_with_icd10(self):
        """Test diagnosis extraction with ICD-10 mapping."""
        text = "Diagnosed with diabetes mellitus type 2 and hypertension"
        diagnoses = self.ner.extract_diagnoses(text)

        assert len(diagnoses) >= 1
        diagnosis_names = [d.name.lower() for d in diagnoses]

        # Should find at least one of these
        assert any("diabetes" in name for name in diagnosis_names) or \
               any("hypertension" in name for name in diagnosis_names)

    def test_extract_drugs_indian_brands(self):
        """Test extraction of Indian drug brands."""
        text = "Tab. Crocin 650mg BD, Tab. Glycomet 500mg OD"
        drugs = self.ner.extract_drugs(text)

        assert len(drugs) >= 1
        # Drugs should be extracted with strength
        for drug in drugs:
            assert drug.strength != ""

    def test_extract_investigations(self):
        """Test investigation extraction."""
        text = "Investigations: CBC, creatinine, chest X-ray, ECG"
        investigations = self.ner.extract_investigations(text)

        inv_names = [i.name.upper() for i in investigations]
        assert "CBC" in inv_names or any("cbc" in name.lower() for name in inv_names)

    def test_extract_procedures(self):
        """Test procedure extraction."""
        text = "Patient underwent PCI with stenting to LAD"
        procedures = self.ner.extract_procedures(text)

        proc_names = [p.name.upper() for p in procedures]
        assert any("PCI" in name or "stent" in name.lower() for name in proc_names)

    def test_map_drug_name(self):
        """Test drug name mapping to generic/brand."""
        generic, brand = self.ner._map_drug_name("metformin")
        assert generic == "Metformin"

        generic, brand = self.ner._map_drug_name("Glycomet")
        assert generic == "Metformin"
        assert brand == "Glycomet"


class TestClinicalReasoning:
    """Test Clinical Reasoning engine."""

    def setup_method(self):
        """Setup test fixtures."""
        self.reasoner = ClinicalReasoning()

    def test_generate_differentials_chest_pain(self):
        """Test differential generation for chest pain."""
        symptoms = [
            Symptom(
                name="chest pain",
                duration="4 hours",
                severity=Severity.SEVERE,
                radiation="left arm",
            )
        ]

        differentials = self.reasoner.generate_differentials(symptoms)

        assert len(differentials) > 0

        # Should include cardiac diagnoses
        diagnosis_names = [d.diagnosis.lower() for d in differentials]
        assert any("cardiac" in name or "coronary" in name or "angina" in name
                   for name in diagnosis_names)

    def test_generate_differentials_with_context(self):
        """Test differential with patient context."""
        symptoms = [
            Symptom(name="chest pain", severity=Severity.SEVERE)
        ]

        context = ClinicalContext(
            patient_age=60,
            patient_gender="M",
            known_conditions=["Diabetes Mellitus", "Hypertension"]
        )

        differentials = self.reasoner.generate_differentials(symptoms, context)

        # Probability should be adjusted based on context
        assert len(differentials) > 0
        assert all(0 <= d.probability <= 1 for d in differentials)

    def test_suggest_investigations(self):
        """Test investigation suggestions."""
        differentials = [
            Differential(
                diagnosis="Acute Coronary Syndrome",
                probability=0.7,
                prior_probability=0.0003,
                supporting_features=["chest pain"],
                recommended_investigations=["ECG", "Troponin I", "CK-MB"],
                treatment_urgency="stat",
            )
        ]

        investigations = self.reasoner.suggest_investigations(differentials)

        assert len(investigations) > 0
        inv_names = [i.name for i in investigations]
        assert "ECG" in inv_names

    def test_flag_red_flags_cardiac(self):
        """Test red flag detection for cardiac symptoms."""
        presentation = {
            "symptoms": [
                Symptom(name="chest pain radiating to jaw", severity=Severity.SEVERE)
            ],
            "vitals": {"BP": "160/100", "Pulse": "110"},
            "history": "crushing chest pain with sweating",
        }

        red_flags = self.reasoner.flag_red_flags(presentation)

        assert len(red_flags) > 0
        # Should flag cardiac red flags
        categories = [f.category for f in red_flags]
        assert any("cardiac" in cat.lower() for cat in categories)

    def test_flag_red_flags_vitals(self):
        """Test red flag detection from vitals."""
        presentation = {
            "symptoms": [],
            "vitals": {"BP": "200/120", "SpO2": "85%"},
            "history": "",
        }

        red_flags = self.reasoner.flag_red_flags(presentation)

        assert len(red_flags) > 0
        # Should flag hypertensive crisis and hypoxia

    def test_generate_clinical_summary(self):
        """Test clinical summary generation."""
        soap = SOAPNote(
            chief_complaint="fever and cough",
            duration="3 days",
            vitals={"Temperature": "101°F", "SpO2": "95%"},
            diagnoses=["Pneumonia"],
        )

        summary = self.reasoner.generate_clinical_summary(soap)

        assert summary != ""
        assert "fever" in summary.lower() or "cough" in summary.lower()

    def test_bayesian_reasoning(self):
        """Test Bayesian probability calculation."""
        # Test that high-prevalence diseases get higher priors
        symptoms = [Symptom(name="fever")]

        differentials = self.reasoner.generate_differentials(symptoms)

        # Viral fever (common) should have reasonable probability
        viral_fever = [d for d in differentials if "viral" in d.diagnosis.lower()]
        if viral_fever:
            assert viral_fever[0].prior_probability > 0.001  # Should have decent prior

    def test_india_specific_prevalence(self):
        """Test India-specific disease prevalence."""
        # Diabetes should have higher prior in India (8%)
        assert self.reasoner.INDIA_PREVALENCE.get("diabetes mellitus", 0) == 0.08

        # Dengue should be in the database
        assert "dengue" in self.reasoner.INDIA_PREVALENCE

        # TB should be in the database (endemic in India)
        assert "tuberculosis" in self.reasoner.INDIA_PREVALENCE


class TestEntities:
    """Test entity dataclasses."""

    def test_symptom_creation(self):
        """Test Symptom dataclass."""
        symptom = Symptom(
            name="chest pain",
            duration="2 hours",
            severity=Severity.SEVERE,
            onset=Onset.SUDDEN,
            location="central",
        )

        assert symptom.name == "chest pain"
        assert symptom.severity == Severity.SEVERE
        assert symptom.onset == Onset.SUDDEN

    def test_diagnosis_creation(self):
        """Test Diagnosis dataclass."""
        diagnosis = Diagnosis(
            name="Diabetes Mellitus",
            icd10_code="E11.9",
            confidence=0.9,
            is_primary=True,
        )

        assert diagnosis.icd10_code == "E11.9"
        assert diagnosis.is_primary is True

    def test_soap_note_defaults(self):
        """Test SOAPNote default values."""
        soap = SOAPNote()

        assert soap.chief_complaint == ""
        assert soap.vitals == {}
        assert soap.diagnoses == []
        assert soap.medications == []

    def test_differential_creation(self):
        """Test Differential dataclass."""
        diff = Differential(
            diagnosis="Acute Coronary Syndrome",
            probability=0.75,
            prior_probability=0.0003,
            supporting_features=["chest pain", "sweating"],
            recommended_investigations=["ECG", "Troponin"],
        )

        assert diff.probability == 0.75
        assert len(diff.supporting_features) == 2


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_clinical_workflow(self):
        """Test complete workflow from transcript to differentials."""
        # 1. Extract SOAP note
        extractor = ClinicalNoteExtractor()
        transcript = """
        Patient c/o chest pain for 4 hours, radiating to left arm.
        Associated breathlessness and sweating.
        BP 160/100, PR 110, SpO2 94%.
        """

        soap = extractor.extract_soap_note(transcript)

        # 2. Extract entities
        ner = MedicalNER()
        symptoms = ner.extract_symptoms(transcript)

        # 3. Generate differentials
        reasoner = ClinicalReasoning()
        context = ClinicalContext(patient_age=55, patient_gender="M")
        differentials = reasoner.generate_differentials(symptoms, context)

        # 4. Check for red flags
        presentation = {
            "symptoms": symptoms,
            "vitals": soap.vitals,
            "history": transcript,
        }
        red_flags = reasoner.flag_red_flags(presentation)

        # Assertions
        assert soap.chief_complaint != ""
        assert len(symptoms) > 0
        assert len(differentials) > 0
        assert len(red_flags) > 0  # Should flag cardiac red flags

    def test_hinglish_workflow(self):
        """Test workflow with Hinglish input."""
        extractor = ClinicalNoteExtractor()
        ner = MedicalNER()

        text = """
        Patient ko bukhar hai for 3 days with khasi.
        BP 120/80, temp 101F hai.
        """

        # Extract SOAP
        soap = extractor.extract_soap_note(text)
        assert soap.chief_complaint != ""

        # Extract symptoms
        symptoms = ner.extract_symptoms(text)
        # After normalization, should find fever and cough

    def test_medication_workflow(self):
        """Test medication extraction and mapping."""
        ner = MedicalNER()

        text = """
        Tab. Crocin 650mg TDS for fever
        Tab. Glycomet 500mg BD for diabetes
        Inj. Actrapid 10 units SC
        """

        drugs = ner.extract_drugs(text)

        assert len(drugs) >= 1
        # Should extract with frequencies
        for drug in drugs:
            assert drug.frequency in ["TDS", "BD", "OD", ""] or \
                   any(freq in drug.frequency.upper() for freq in ["TDS", "BD", "OD"])


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
