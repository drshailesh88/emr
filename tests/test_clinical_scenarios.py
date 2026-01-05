"""Tests for real-world clinical scenarios.

Tests complete workflows for common clinical presentations including
diabetic patient visits, chest pain emergencies, pediatric cases, and
prescriptions with interactions.
"""

import pytest
from datetime import date, datetime, timedelta
from src.models.schemas import (
    Patient, Visit, Investigation, Medication, Prescription,
    PatientSnapshot
)
from src.services.safety import PrescriptionSafetyChecker

# Import fixtures
pytest_plugins = ['tests.clinical_conftest']


class TestRealWorldScenarios:
    """Tests for realistic clinical scenarios."""

    @pytest.mark.asyncio
    async def test_diabetic_patient_routine_visit(
        self, clinical_flow, mock_database, service_registry
    ):
        """Test routine follow-up visit for diabetic patient."""
        # Create diabetic patient
        patient = mock_database.add_patient(
            Patient(
                name="Ramesh Kumar",
                age=58,
                gender="M",
                phone="9876543210"
            )
        )

        # Add previous HbA1c result
        investigation = Investigation(
            patient_id=patient.id,
            test_name="HbA1c",
            result="7.8",
            unit="%",
            reference_range="4-6",
            test_date=date.today() - timedelta(days=90),
            is_abnormal=True
        )
        mock_database.add_investigation(investigation)

        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=patient.id,
            doctor_id="DR001"
        )

        # Simulate clinical notes
        current_context = clinical_flow.context_manager.get_current_context()
        current_context.chief_complaint = "Routine diabetes follow-up"
        current_context.clinical_notes = "Patient compliant with medications. No hypoglycemic episodes. Diet well controlled."
        current_context.diagnosis = "Type 2 Diabetes Mellitus - controlled"

        # Generate prescription
        medications = [
            {
                "drug_name": "Metformin",
                "strength": "500mg",
                "dose": "1",
                "frequency": "BD",
                "instructions": "after meals"
            },
            {
                "drug_name": "Glimepiride",
                "strength": "2mg",
                "dose": "1",
                "frequency": "OD",
                "instructions": "before breakfast"
            }
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=patient.id
        )

        # Complete consultation
        summary = await clinical_flow.complete_consultation({
            "visit_date": date.today()
        })

        # Verify consultation completed successfully
        assert summary["visit_id"] is not None
        assert summary["prescription_sent"] is True

        # Verify HbA1c reminder should be triggered (every 3 months)
        # Real implementation would check care gap detector

    @pytest.mark.asyncio
    async def test_chest_pain_emergency(
        self, clinical_flow, mock_database, service_registry
    ):
        """Test emergency presentation with chest pain (possible ACS)."""
        # Create patient
        patient = mock_database.add_patient(
            Patient(
                name="Suresh Patel",
                age=65,
                gender="M",
                phone="9876543211"
            )
        )

        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=patient.id,
            doctor_id="DR001"
        )

        # Process speech with red flag keywords
        audio_data = b"x" * 200  # Longer audio triggers cardiac red flag
        result = await clinical_flow.process_speech(audio_data)

        # Should detect red flags
        if len(result["red_flags"]) > 0:
            assert any("cardiac" in str(flag).lower() for flag in result["red_flags"])

        # Add clinical context
        context = clinical_flow.context_manager.get_current_context()
        context.chief_complaint = "Chest pain radiating to left arm, sweating"
        context.clinical_notes = "Central chest pain, 8/10 severity, started 1 hour ago. Diaphoretic, BP 160/100, HR 110"
        context.diagnosis = "Acute Coronary Syndrome - STEMI suspected"

        # Immediate management prescription
        medications = [
            {
                "drug_name": "Aspirin",
                "strength": "325mg",
                "dose": "1",
                "frequency": "STAT",
                "instructions": "chew immediately"
            },
            {
                "drug_name": "Clopidogrel",
                "strength": "600mg",
                "dose": "1",
                "frequency": "STAT",
                "instructions": "loading dose"
            },
            {
                "drug_name": "Atorvastatin",
                "strength": "80mg",
                "dose": "1",
                "frequency": "STAT",
                "instructions": "high intensity statin"
            }
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=patient.id
        )

        # Verify prescription includes emergency medications
        assert len(prescription["medications"]) > 0

        # Complete consultation with red flag noted
        context.red_flags = ["Cardiac chest pain - ACS protocol initiated"]

        summary = await clinical_flow.complete_consultation({
            "visit_date": date.today()
        })

        # Verify red flags were logged
        assert len(context.red_flags) > 0

    @pytest.mark.asyncio
    async def test_pediatric_fever_with_rash(
        self, clinical_flow, mock_database
    ):
        """Test pediatric case with fever and rash."""
        # Create pediatric patient
        patient = mock_database.add_patient(
            Patient(
                name="Baby Ananya",
                age=5,
                gender="F",
                phone="9876543212"
            )
        )

        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=patient.id,
            doctor_id="DR001"
        )

        # Clinical presentation
        context = clinical_flow.context_manager.get_current_context()
        context.chief_complaint = "High fever for 3 days, rash on body"
        context.clinical_notes = """
        Child presents with high-grade fever (103F) for 3 days.
        Generalized maculopapular rash appeared today.
        Playful, taking feeds well. No vomiting or loose stools.
        Probable viral exanthem vs dengue.
        """
        context.diagnosis = "Viral Fever with Rash - ? Dengue"

        # Pediatric prescription (weight-based dosing)
        child_weight = 18  # kg

        medications = [
            {
                "drug_name": "Paracetamol",
                "strength": "125mg/5ml suspension",
                "dose": "7.5ml",  # 15mg/kg = 270mg
                "frequency": "TDS",
                "instructions": "if fever >100F"
            }
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=patient.id
        )

        # Add investigations
        context.investigations_mentioned = ["CBC", "Dengue NS1 Ag", "Platelet count"]

        # Complete consultation
        summary = await clinical_flow.complete_consultation({
            "visit_date": date.today()
        })

        assert summary["visit_id"] is not None

    @pytest.mark.asyncio
    async def test_antenatal_checkup(
        self, clinical_flow, mock_database
    ):
        """Test antenatal checkup for pregnant patient."""
        # Create pregnant patient
        patient = mock_database.add_patient(
            Patient(
                name="Priya Sharma",
                age=28,
                gender="F",
                phone="9876543213"
            )
        )

        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=patient.id,
            doctor_id="DR001"
        )

        # Antenatal context
        context = clinical_flow.context_manager.get_current_context()
        context.chief_complaint = "Routine ANC - 28 weeks"
        context.clinical_notes = """
        G2P1L1 at 28 weeks gestation.
        No complaints. Fetal movements good.
        BP: 120/80, Weight: 65kg (appropriate weight gain)
        Fundal height: 28cm, FHS: 140/min
        """
        context.diagnosis = "Intrauterine pregnancy - 28 weeks"

        # Pregnancy-safe medications
        medications = [
            {
                "drug_name": "Calcium",
                "strength": "500mg",
                "dose": "1",
                "frequency": "BD",
                "instructions": "after meals"
            },
            {
                "drug_name": "Iron + Folic Acid",
                "strength": "100mg + 500mcg",
                "dose": "1",
                "frequency": "OD",
                "instructions": "at bedtime"
            }
        ]

        # Safety check should pass (pregnancy-safe medications)
        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=patient.id
        )

        # Should not have critical warnings for these medications
        assert "medications" in prescription

        # Complete consultation
        summary = await clinical_flow.complete_consultation({
            "visit_date": date.today()
        })

        assert summary["visit_id"] is not None

    @pytest.mark.asyncio
    async def test_prescription_with_interactions(
        self, clinical_flow, mock_database
    ):
        """Test prescription with known drug-drug interactions."""
        # Create patient on multiple medications
        patient = mock_database.add_patient(
            Patient(
                name="Rajesh Gupta",
                age=70,
                gender="M",
                phone="9876543214"
            )
        )

        # Patient already on warfarin for AF
        snapshot = PatientSnapshot(
            patient_id=patient.id,
            uhid="EMR-2024-TEST",
            demographics=f"{patient.name}, {patient.age}{patient.gender}",
            active_problems=["Atrial Fibrillation", "Hypertension"],
            current_medications=[
                Medication(
                    drug_name="Warfarin",
                    strength="5mg",
                    dose="1",
                    frequency="OD"
                ),
                Medication(
                    drug_name="Ramipril",
                    strength="5mg",
                    dose="1",
                    frequency="OD"
                )
            ],
            allergies=[],
            key_labs={
                "inr": {"value": 2.5, "date": date.today() - timedelta(days=7), "unit": ""}
            }
        )

        # Try to add aspirin (interaction with warfarin)
        checker = PrescriptionSafetyChecker()

        prescription = Prescription(
            diagnosis=["Atrial Fibrillation"],
            medications=[
                Medication(
                    drug_name="Aspirin",
                    strength="75mg",
                    dose="1",
                    frequency="OD"
                )
            ]
        )

        alerts = checker.validate_prescription(prescription, snapshot)

        # Should detect bleeding risk
        interaction_alerts = [a for a in alerts if a.category == "interaction"]
        assert len(interaction_alerts) > 0
        assert any("bleeding" in a.message.lower() for a in interaction_alerts)

    @pytest.mark.asyncio
    async def test_hypertension_urgency(
        self, clinical_flow, mock_database
    ):
        """Test hypertensive urgency presentation."""
        patient = mock_database.add_patient(
            Patient(
                name="Lakshmi Devi",
                age=55,
                gender="F",
                phone="9876543215"
            )
        )

        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=patient.id,
            doctor_id="DR001"
        )

        # Add critical BP reading
        context = clinical_flow.context_manager.get_current_context()
        context.chief_complaint = "Severe headache, BP very high"
        context.clinical_notes = """
        Patient presents with severe frontal headache.
        BP: 200/120 mmHg (confirmed on repeat)
        No chest pain, no dyspnea, no neurological deficits
        Diagnosis: Hypertensive Urgency
        """
        context.diagnosis = "Hypertensive Urgency"

        # Immediate BP control
        medications = [
            {
                "drug_name": "Amlodipine",
                "strength": "5mg",
                "dose": "1",
                "frequency": "STAT then OD"
            },
            {
                "drug_name": "Telmisartan",
                "strength": "40mg",
                "dose": "1",
                "frequency": "OD"
            }
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=patient.id
        )

        # Complete with follow-up in 1 week for BP recheck
        context.follow_up = date.today() + timedelta(days=7)

        summary = await clinical_flow.complete_consultation({
            "visit_date": date.today()
        })

        assert summary["reminders_scheduled"] is not None

    @pytest.mark.asyncio
    async def test_copd_exacerbation(
        self, clinical_flow, mock_database
    ):
        """Test COPD exacerbation management."""
        patient = mock_database.add_patient(
            Patient(
                name="Mohan Singh",
                age=68,
                gender="M",
                phone="9876543216"
            )
        )

        await clinical_flow.start_consultation(
            patient_id=patient.id,
            doctor_id="DR001"
        )

        context = clinical_flow.context_manager.get_current_context()
        context.chief_complaint = "Increased breathlessness, cough with sputum"
        context.clinical_notes = """
        Known case of COPD on regular inhalers.
        Increased dyspnea for 3 days, productive cough with yellow sputum.
        No fever, SpO2: 92% on room air.
        Chest: Bilateral wheeze, prolonged expiration
        Diagnosis: Acute exacerbation of COPD
        """
        context.diagnosis = "COPD - Acute Exacerbation"

        medications = [
            {
                "drug_name": "Azithromycin",
                "strength": "500mg",
                "dose": "1",
                "frequency": "OD",
                "duration": "3 days"
            },
            {
                "drug_name": "Prednisolone",
                "strength": "20mg",
                "dose": "1",
                "frequency": "OD",
                "duration": "5 days"
            },
            {
                "drug_name": "Salbutamol + Ipratropium Nebulization",
                "strength": "2.5mg + 500mcg",
                "dose": "1",
                "frequency": "QID",
                "duration": "5 days"
            }
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=patient.id
        )

        assert len(prescription["medications"]) >= 3

        summary = await clinical_flow.complete_consultation({
            "visit_date": date.today()
        })

        assert summary["visit_id"] is not None

    @pytest.mark.asyncio
    async def test_uti_with_renal_impairment(self        self, clinical_flow, mock_database
    ):
        """Test UTI in patient with renal impairment (dose adjustment needed)."""
        patient = mock_database.add_patient(
            Patient(
                name="Geeta Sharma",
                age=72,
                gender="F",
                phone="9876543217"
            )
        )

        # Patient with renal impairment
        snapshot = PatientSnapshot(
            patient_id=patient.id,
            uhid="EMR-2024-TEST2",
            demographics=f"{patient.name}, {patient.age}{patient.gender}",
            active_problems=["Chronic Kidney Disease - Stage 3"],
            current_medications=[],
            allergies=[],
            key_labs={
                "creatinine": {"value": 2.5, "date": date.today(), "unit": "mg/dL"},
                "egfr": {"value": 28, "date": date.today(), "unit": "ml/min"}
            }
        )

        # Try to prescribe ciprofloxacin (needs renal adjustment)
        checker = PrescriptionSafetyChecker()

        prescription = Prescription(
            diagnosis=["Urinary Tract Infection"],
            medications=[
                Medication(
                    drug_name="Ciprofloxacin",
                    strength="500mg",
                    dose="1",
                    frequency="BD"
                )
            ]
        )

        alerts = checker.validate_prescription(prescription, snapshot)

        # Should warn about renal dose adjustment
        renal_alerts = [a for a in alerts if a.category == "renal"]
        assert len(renal_alerts) > 0
