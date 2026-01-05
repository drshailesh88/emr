"""Integration tests for DocAssist EMR - complete workflow testing."""

import pytest
import json
import os
from pathlib import Path
from datetime import date, datetime
from unittest.mock import Mock, patch

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.schemas import Patient, Visit, Investigation, Procedure, Medication, Prescription
from src.services.database import DatabaseService
from src.services.rag import RAGService
from src.services.pdf import PDFService
from src.services.llm import LLMService


@pytest.mark.integration
class TestPatientWorkflow:
    """Test complete patient workflow from creation to RAG queries."""

    def test_complete_patient_workflow(self, db_service, rag_service):
        """Test: Create patient -> Index in RAG -> Search -> Add records -> Re-index -> Query."""

        # Step 1: Create patient via DatabaseService
        patient = Patient(
            name="Ram Lal",
            age=65,
            gender="M",
            phone="9876543210",
            address="123 MG Road, Delhi"
        )
        created_patient = db_service.add_patient(patient)
        assert created_patient.id is not None
        assert created_patient.uhid is not None
        assert created_patient.uhid.startswith("EMR-")

        # Step 2: Index patient in RAGService
        summary = db_service.get_patient_summary(created_patient.id)
        assert "Ram Lal" in summary
        assert created_patient.uhid in summary

        rag_service.index_patient_summary(created_patient.id, summary)

        # Step 3: Search for patient via RAG
        search_results = rag_service.search_patients("Ram Lal", n_results=5)
        assert len(search_results) > 0
        assert search_results[0][0] == created_patient.id  # patient_id matches
        assert "Ram Lal" in search_results[0][2]  # summary contains name

        # Step 4: Add visit, investigation, procedure
        visit = Visit(
            patient_id=created_patient.id,
            visit_date=date.today(),
            chief_complaint="Chest pain for 2 days",
            clinical_notes="Patient presents with chest pain, BP 150/90",
            diagnosis="Unstable Angina"
        )
        created_visit = db_service.add_visit(visit)
        assert created_visit.id is not None

        investigation = Investigation(
            patient_id=created_patient.id,
            test_name="Troponin",
            result="0.8",
            unit="ng/mL",
            reference_range="< 0.04",
            test_date=date.today(),
            is_abnormal=True
        )
        created_inv = db_service.add_investigation(investigation)
        assert created_inv.id is not None

        procedure = Procedure(
            patient_id=created_patient.id,
            procedure_name="PCI to LAD",
            details="Drug-eluting stent placed in LAD",
            procedure_date=date.today(),
            notes="Successful procedure, no complications"
        )
        created_proc = db_service.add_procedure(procedure)
        assert created_proc.id is not None

        # Step 5: Re-index documents
        documents = db_service.get_patient_documents_for_rag(created_patient.id)
        assert len(documents) == 3  # 1 visit + 1 investigation + 1 procedure

        rag_service.index_patient_documents(created_patient.id, documents)

        # Verify documents were indexed
        doc_count = rag_service.get_patient_document_count(created_patient.id)
        assert doc_count == 3

        # Step 6: Query patient context
        context = rag_service.query_patient_context(
            created_patient.id,
            "What was the troponin level?",
            n_results=5
        )
        assert "Troponin" in context
        assert "0.8" in context

        # Query about procedure
        context = rag_service.query_patient_context(
            created_patient.id,
            "What procedures were done?",
            n_results=5
        )
        assert "PCI" in context or "LAD" in context

    def test_patient_reindexing_after_updates(self, db_service, rag_service):
        """Test that patient data updates are reflected in RAG after reindexing."""

        # Create patient
        patient = db_service.add_patient(Patient(
            name="Priya Sharma",
            age=45,
            gender="F"
        ))

        # Initial indexing with no records
        summary = db_service.get_patient_summary(patient.id)
        rag_service.index_patient_summary(patient.id, summary)

        initial_docs = db_service.get_patient_documents_for_rag(patient.id)
        assert len(initial_docs) == 0

        # Add a visit
        db_service.add_visit(Visit(
            patient_id=patient.id,
            visit_date=date.today(),
            chief_complaint="Fever",
            diagnosis="Viral fever"
        ))

        # Re-index
        updated_docs = db_service.get_patient_documents_for_rag(patient.id)
        assert len(updated_docs) == 1

        rag_service.index_patient_documents(patient.id, updated_docs)

        # Query should now find the visit
        context = rag_service.query_patient_context(patient.id, "What was the complaint?")
        assert "Fever" in context or "fever" in context


@pytest.mark.integration
class TestPrescriptionWorkflow:
    """Test complete prescription workflow with mocked LLM."""

    def test_prescription_workflow_with_mocked_llm(
        self, db_service, pdf_service, temp_pdf_dir
    ):
        """Test: Create patient -> Mock LLM -> Generate prescription -> Save visit -> Generate PDF."""

        # Step 1: Create patient
        patient = db_service.add_patient(Patient(
            name="Amit Kumar",
            age=55,
            gender="M",
            phone="9123456789"
        ))

        # Step 2: Mock LLM to return valid prescription JSON
        mock_prescription_data = {
            "diagnosis": ["Type 2 Diabetes Mellitus", "Essential Hypertension"],
            "medications": [
                {
                    "drug_name": "Metformin",
                    "strength": "500mg",
                    "form": "tablet",
                    "dose": "1",
                    "frequency": "BD",
                    "duration": "30 days",
                    "instructions": "after meals"
                },
                {
                    "drug_name": "Amlodipine",
                    "strength": "5mg",
                    "form": "tablet",
                    "dose": "1",
                    "frequency": "OD",
                    "duration": "30 days",
                    "instructions": "morning"
                }
            ],
            "investigations": ["HbA1c", "Fasting Blood Sugar", "Lipid Profile"],
            "advice": ["Low salt diet", "Regular exercise 30 min daily", "Monitor BP"],
            "follow_up": "1 month",
            "red_flags": ["Hypoglycemia symptoms", "Chest pain", "Severe headache"]
        }

        clinical_notes = "Patient with uncontrolled diabetes and hypertension. BP 160/95, FBS 185."

        # Mock the LLM service
        with patch.object(LLMService, 'generate') as mock_generate:
            mock_generate.return_value = (True, json.dumps(mock_prescription_data))

            llm_service = LLMService.for_testing()

            # Step 3: Generate prescription
            success, prescription, raw_json = llm_service.generate_prescription(clinical_notes)

            assert success is True
            assert prescription is not None
            assert isinstance(prescription, Prescription)
            assert len(prescription.medications) == 2
            assert prescription.medications[0].drug_name == "Metformin"
            assert "Type 2 Diabetes Mellitus" in prescription.diagnosis

        # Step 4: Save visit with prescription
        prescription_json = json.dumps(mock_prescription_data)
        visit = Visit(
            patient_id=patient.id,
            visit_date=date.today(),
            chief_complaint="Follow-up for diabetes and hypertension",
            clinical_notes=clinical_notes,
            diagnosis="Type 2 Diabetes Mellitus, Essential Hypertension",
            prescription_json=prescription_json
        )
        saved_visit = db_service.add_visit(visit)
        assert saved_visit.id is not None

        # Step 5: Generate PDF
        pdf_path = pdf_service.generate_prescription_pdf(
            patient=patient,
            prescription=prescription,
            chief_complaint=visit.chief_complaint,
            doctor_name="Dr. Test Doctor",
            clinic_name="Test Clinic",
            clinic_address="123 Test Street, Test City"
        )

        # Step 6: Verify PDF exists
        assert pdf_path is not None
        assert os.path.exists(pdf_path)
        assert pdf_path.endswith(".pdf")

        # Verify PDF is in the correct directory
        assert temp_pdf_dir in pdf_path

        # Verify visit can be retrieved with prescription
        retrieved_visits = db_service.get_patient_visits(patient.id)
        assert len(retrieved_visits) == 1
        assert retrieved_visits[0].prescription_json is not None

        # Parse and validate stored prescription
        stored_prescription_data = json.loads(retrieved_visits[0].prescription_json)
        assert len(stored_prescription_data["medications"]) == 2
        assert stored_prescription_data["follow_up"] == "1 month"

    def test_prescription_validation_with_invalid_json(self):
        """Test that invalid LLM output is properly handled."""

        invalid_json = "This is not valid JSON"

        with patch.object(LLMService, 'generate') as mock_generate:
            mock_generate.return_value = (True, invalid_json)

            llm_service = LLMService.for_testing()
            success, prescription, error = llm_service.generate_prescription("test notes")

            assert success is False
            assert prescription is None
            assert "Invalid JSON" in error or "JSONDecodeError" in error

    def test_prescription_pdf_generation_without_llm(self, db_service, pdf_service):
        """Test PDF generation with manually created prescription (no LLM)."""

        patient = db_service.add_patient(Patient(
            name="Test Patient",
            age=40,
            gender="F"
        ))

        # Create prescription manually
        prescription = Prescription(
            diagnosis=["Common Cold"],
            medications=[
                Medication(
                    drug_name="Paracetamol",
                    strength="500mg",
                    form="tablet",
                    dose="1",
                    frequency="TDS",
                    duration="3 days",
                    instructions="after meals"
                )
            ],
            investigations=["None"],
            advice=["Rest", "Plenty of fluids"],
            follow_up="If symptoms persist after 3 days",
            red_flags=["High fever > 102F", "Difficulty breathing"]
        )

        pdf_path = pdf_service.generate_prescription_pdf(
            patient=patient,
            prescription=prescription,
            chief_complaint="Fever and body ache"
        )

        assert pdf_path is not None
        assert os.path.exists(pdf_path)


@pytest.mark.integration
class TestRAGSearch:
    """Test RAG search across multiple patients."""

    def test_rag_search_multiple_patients_by_diagnosis(self, db_service, rag_service):
        """Test: Create multiple patients with different diagnoses -> Index all -> Search by diagnosis."""

        # Create patient 1: Diabetic
        patient1 = db_service.add_patient(Patient(
            name="Rajesh Diabetic",
            age=60,
            gender="M"
        ))
        db_service.add_visit(Visit(
            patient_id=patient1.id,
            diagnosis="Type 2 Diabetes Mellitus",
            clinical_notes="Patient on metformin, good control"
        ))

        # Create patient 2: Hypertensive
        patient2 = db_service.add_patient(Patient(
            name="Sunita HTN",
            age=55,
            gender="F"
        ))
        db_service.add_visit(Visit(
            patient_id=patient2.id,
            diagnosis="Essential Hypertension",
            clinical_notes="Patient on amlodipine"
        ))

        # Create patient 3: Both diabetes and hypertension
        patient3 = db_service.add_patient(Patient(
            name="Kumar Both",
            age=65,
            gender="M"
        ))
        db_service.add_visit(Visit(
            patient_id=patient3.id,
            diagnosis="Type 2 Diabetes Mellitus",
            clinical_notes="Patient with diabetes and hypertension"
        ))
        db_service.add_visit(Visit(
            patient_id=patient3.id,
            diagnosis="Essential Hypertension",
            clinical_notes="BP control needed"
        ))

        # Create patient 4: Cardiac patient
        patient4 = db_service.add_patient(Patient(
            name="Sharma Heart",
            age=70,
            gender="M"
        ))
        db_service.add_procedure(Procedure(
            patient_id=patient4.id,
            procedure_name="CABG",
            details="Triple vessel disease, underwent CABG",
            procedure_date=date.today()
        ))

        # Index all patients
        for patient in [patient1, patient2, patient3, patient4]:
            summary = db_service.get_patient_summary(patient.id)
            rag_service.index_patient_summary(patient.id, summary)

        # Search for diabetic patients
        diabetes_results = rag_service.search_patients("diabetic patients", n_results=10)
        diabetes_patient_ids = [result[0] for result in diabetes_results]

        # Should find patient1 and patient3 (both have diabetes)
        assert patient1.id in diabetes_patient_ids or patient3.id in diabetes_patient_ids

        # Search for hypertension
        htn_results = rag_service.search_patients("patients with high blood pressure", n_results=10)
        htn_patient_ids = [result[0] for result in htn_results]

        # Should find patient2 and patient3 (both have hypertension)
        assert patient2.id in htn_patient_ids or patient3.id in htn_patient_ids

        # Search for cardiac surgery
        cardiac_results = rag_service.search_patients("CABG surgery patients", n_results=10)
        cardiac_patient_ids = [result[0] for result in cardiac_results]

        # Should find patient4
        assert patient4.id in cardiac_patient_ids

    def test_rag_search_by_patient_name(self, db_service, rag_service):
        """Test searching patients by name using RAG."""

        patients = [
            Patient(name="Aarav Patel", age=30, gender="M"),
            Patient(name="Priya Sharma", age=25, gender="F"),
            Patient(name="Rahul Kumar", age=45, gender="M"),
        ]

        created_patients = []
        for patient in patients:
            created = db_service.add_patient(patient)
            created_patients.append(created)
            summary = db_service.get_patient_summary(created.id)
            rag_service.index_patient_summary(created.id, summary)

        # Search by first name
        results = rag_service.search_patients("Priya", n_results=5)
        assert len(results) > 0

        # The top result should be Priya Sharma
        top_patient_id = results[0][0]
        matching_patient = next(p for p in created_patients if p.id == top_patient_id)
        assert "Priya" in matching_patient.name

    def test_rag_search_with_procedure_history(self, db_service, rag_service):
        """Test searching patients by procedure history."""

        # Patient with PCI
        patient1 = db_service.add_patient(Patient(name="PCI Patient", age=65, gender="M"))
        db_service.add_procedure(Procedure(
            patient_id=patient1.id,
            procedure_name="PCI to LAD",
            details="Drug-eluting stent"
        ))

        # Patient with CABG
        patient2 = db_service.add_patient(Patient(name="CABG Patient", age=70, gender="M"))
        db_service.add_procedure(Procedure(
            patient_id=patient2.id,
            procedure_name="CABG",
            details="Triple vessel disease"
        ))

        # Index patients
        for patient in [patient1, patient2]:
            summary = db_service.get_patient_summary(patient.id)
            rag_service.index_patient_summary(patient.id, summary)

        # Search for PCI patients
        pci_results = rag_service.search_patients("patients who had PCI stent", n_results=5)
        pci_ids = [r[0] for r in pci_results]
        assert patient1.id in pci_ids

        # Search for CABG patients
        cabg_results = rag_service.search_patients("bypass surgery patients", n_results=5)
        cabg_ids = [r[0] for r in cabg_results]
        assert patient2.id in cabg_ids


@pytest.mark.integration
class TestDataPersistence:
    """Test data persistence across service instances."""

    def test_database_persistence_across_instances(self, temp_db_path):
        """Test: Create patient -> New DB instance -> Verify data persists."""

        # Create first database service instance
        db1 = DatabaseService(db_path=temp_db_path)

        # Add patient and records
        patient = db1.add_patient(Patient(
            name="Persistence Test",
            age=50,
            gender="M",
            phone="9999999999"
        ))
        original_patient_id = patient.id
        original_uhid = patient.uhid

        visit = db1.add_visit(Visit(
            patient_id=patient.id,
            chief_complaint="Test complaint",
            diagnosis="Test diagnosis"
        ))
        original_visit_id = visit.id

        investigation = db1.add_investigation(Investigation(
            patient_id=patient.id,
            test_name="HbA1c",
            result="7.5",
            unit="%"
        ))
        original_inv_id = investigation.id

        # Create second database service instance (simulates app restart)
        db2 = DatabaseService(db_path=temp_db_path)

        # Verify patient persists
        retrieved_patient = db2.get_patient(original_patient_id)
        assert retrieved_patient is not None
        assert retrieved_patient.name == "Persistence Test"
        assert retrieved_patient.uhid == original_uhid
        assert retrieved_patient.phone == "9999999999"

        # Verify visit persists
        visits = db2.get_patient_visits(original_patient_id)
        assert len(visits) == 1
        assert visits[0].id == original_visit_id
        assert visits[0].chief_complaint == "Test complaint"

        # Verify investigation persists
        investigations = db2.get_patient_investigations(original_patient_id)
        assert len(investigations) == 1
        assert investigations[0].id == original_inv_id
        assert investigations[0].test_name == "HbA1c"
        assert investigations[0].result == "7.5"

        # Verify we can add more data with second instance
        new_visit = db2.add_visit(Visit(
            patient_id=original_patient_id,
            chief_complaint="Follow-up"
        ))
        assert new_visit.id is not None

        # Create third instance to verify second instance's changes
        db3 = DatabaseService(db_path=temp_db_path)
        all_visits = db3.get_patient_visits(original_patient_id)
        assert len(all_visits) == 2

    def test_rag_persistence_across_instances(self, temp_chroma_dir):
        """Test: Index documents -> New RAG instance -> Verify index persists."""

        # Create first RAG service instance
        rag1 = RAGService(persist_directory=temp_chroma_dir)

        # Index patient summaries
        rag1.index_patient_summary(1, "Patient: John Doe. Age: 50. Diagnosis: Diabetes")
        rag1.index_patient_summary(2, "Patient: Jane Smith. Age: 45. Diagnosis: Hypertension")

        # Index patient documents
        documents = [
            ("visit_1", "Visit on 2024-01-01: Patient with diabetes", {"type": "visit", "patient_id": 1}),
            ("inv_1", "HbA1c = 7.5%", {"type": "investigation", "patient_id": 1})
        ]
        rag1.index_patient_documents(1, documents)

        # Create second RAG service instance (simulates app restart)
        rag2 = RAGService(persist_directory=temp_chroma_dir)

        # Verify patient summaries persist
        search_results = rag2.search_patients("diabetes", n_results=5)
        assert len(search_results) > 0
        patient_ids = [r[0] for r in search_results]
        assert 1 in patient_ids

        # Verify patient documents persist
        doc_count = rag2.get_patient_document_count(1)
        assert doc_count == 2

        # Verify we can query the documents
        context = rag2.query_patient_context(1, "What is the HbA1c?")
        assert "HbA1c" in context or "7.5" in context

        # Verify we can add more data with second instance
        rag2.index_patient_summary(3, "Patient: Bob Wilson. Age: 60. Diagnosis: Heart Disease")

        # Create third instance to verify persistence
        rag3 = RAGService(persist_directory=temp_chroma_dir)
        all_patient_ids = rag3.get_all_patient_ids()
        assert len(all_patient_ids) == 3
        assert 1 in all_patient_ids
        assert 2 in all_patient_ids
        assert 3 in all_patient_ids

    def test_full_system_persistence(self, temp_db_path, temp_chroma_dir):
        """Test persistence of complete system: DB + RAG."""

        # Session 1: Create and index data
        db1 = DatabaseService(db_path=temp_db_path)
        rag1 = RAGService(persist_directory=temp_chroma_dir)

        patient = db1.add_patient(Patient(name="Full System Test", age=55, gender="M"))
        db1.add_visit(Visit(
            patient_id=patient.id,
            diagnosis="Type 2 Diabetes",
            clinical_notes="Patient needs insulin"
        ))

        summary = db1.get_patient_summary(patient.id)
        documents = db1.get_patient_documents_for_rag(patient.id)
        rag1.index_patient_summary(patient.id, summary)
        rag1.index_patient_documents(patient.id, documents)

        patient_id = patient.id

        # Session 2: Restart system (new instances)
        db2 = DatabaseService(db_path=temp_db_path)
        rag2 = RAGService(persist_directory=temp_chroma_dir)

        # Verify patient can be retrieved from DB
        retrieved_patient = db2.get_patient(patient_id)
        assert retrieved_patient is not None
        assert retrieved_patient.name == "Full System Test"

        # Verify patient can be found via RAG
        search_results = rag2.search_patients("Full System Test", n_results=5)
        assert len(search_results) > 0
        found_ids = [r[0] for r in search_results]
        assert patient_id in found_ids

        # Verify patient documents are queryable
        context = rag2.query_patient_context(patient_id, "What is the diagnosis?")
        assert "Diabetes" in context or "diabetes" in context


@pytest.mark.integration
class TestCompleteWorkflowIntegration:
    """Test complete end-to-end workflows combining all services."""

    def test_new_patient_complete_flow(self, db_service, rag_service, pdf_service):
        """Test complete flow: New patient -> Visit -> Index -> Generate PDF -> Query."""

        # Step 1: Register new patient
        patient = db_service.add_patient(Patient(
            name="Complete Flow Patient",
            age=42,
            gender="F",
            phone="9876543210",
            address="New Delhi"
        ))
        assert patient.id is not None

        # Step 2: First visit with prescription
        prescription_data = {
            "diagnosis": ["Migraine"],
            "medications": [
                {
                    "drug_name": "Sumatriptan",
                    "strength": "50mg",
                    "form": "tablet",
                    "dose": "1",
                    "frequency": "SOS",
                    "duration": "as needed",
                    "instructions": "at onset of headache"
                }
            ],
            "investigations": ["MRI Brain if symptoms persist"],
            "advice": ["Avoid triggers", "Adequate sleep", "Stress management"],
            "follow_up": "2 weeks",
            "red_flags": ["Severe headache with vomiting", "Visual disturbances", "Fever"]
        }

        visit = db_service.add_visit(Visit(
            patient_id=patient.id,
            visit_date=date.today(),
            chief_complaint="Severe headache for 1 day",
            clinical_notes="Unilateral throbbing headache with photophobia",
            diagnosis="Migraine",
            prescription_json=json.dumps(prescription_data)
        ))

        # Step 3: Add investigation
        db_service.add_investigation(Investigation(
            patient_id=patient.id,
            test_name="BP",
            result="120/80",
            unit="mmHg",
            test_date=date.today(),
            is_abnormal=False
        ))

        # Step 4: Index in RAG
        summary = db_service.get_patient_summary(patient.id)
        documents = db_service.get_patient_documents_for_rag(patient.id)

        rag_service.index_patient_summary(patient.id, summary)
        rag_service.index_patient_documents(patient.id, documents)

        # Step 5: Generate PDF
        prescription = Prescription(**prescription_data)
        pdf_path = pdf_service.generate_prescription_pdf(
            patient=patient,
            prescription=prescription,
            chief_complaint=visit.chief_complaint
        )
        assert pdf_path is not None
        assert os.path.exists(pdf_path)

        # Step 6: Verify RAG queries work
        context = rag_service.query_patient_context(patient.id, "What was the BP?")
        assert "120/80" in context or "BP" in context

        context = rag_service.query_patient_context(patient.id, "What medication was prescribed?")
        assert "Sumatriptan" in context or "medication" in context.lower()

        # Step 7: Verify patient searchable
        search_results = rag_service.search_patients("migraine patient", n_results=5)
        patient_ids = [r[0] for r in search_results]
        assert patient.id in patient_ids

    def test_follow_up_visit_workflow(self, db_service, rag_service):
        """Test follow-up visit workflow with re-indexing."""

        # Initial visit
        patient = db_service.add_patient(Patient(name="Follow Up Patient", age=50, gender="M"))

        first_visit = db_service.add_visit(Visit(
            patient_id=patient.id,
            chief_complaint="Fever",
            diagnosis="Viral Fever",
            clinical_notes="Patient with fever 101F"
        ))

        # Index after first visit
        summary = db_service.get_patient_summary(patient.id)
        documents = db_service.get_patient_documents_for_rag(patient.id)
        rag_service.reindex_patient(patient.id, summary, documents)

        # Follow-up visit
        second_visit = db_service.add_visit(Visit(
            patient_id=patient.id,
            chief_complaint="Follow-up",
            diagnosis="Recovered",
            clinical_notes="Patient feeling better, fever subsided"
        ))

        # Re-index after follow-up
        updated_summary = db_service.get_patient_summary(patient.id)
        updated_documents = db_service.get_patient_documents_for_rag(patient.id)
        rag_service.reindex_patient(patient.id, updated_summary, updated_documents)

        # Verify both visits are indexed
        doc_count = rag_service.get_patient_document_count(patient.id)
        assert doc_count == 2

        # Query should find both visits
        context = rag_service.query_patient_context(patient.id, "What was the patient history?")
        assert "Fever" in context or "fever" in context
        assert "Recovered" in context or "better" in context
