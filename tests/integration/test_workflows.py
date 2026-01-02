"""Integration tests for complete EMR workflows."""

import pytest
import json
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

from src.services.database import DatabaseService
from src.services.llm import LLMService
from src.services.rag import RAGService
from src.services.pdf import PDFService
from src.models.schemas import Patient, Visit, Investigation, Procedure, Medication


class TestPatientWorkflow:
    """Integration tests for patient management workflow."""

    def test_complete_patient_registration_workflow(self, temp_db, temp_rag):
        """Test complete workflow of adding a new patient."""
        # 1. Create patient
        patient = Patient(
            name="Mohan Singh",
            age=55,
            gender="M",
            phone="9999999999",
            address="Mumbai"
        )

        # 2. Add to database
        added_patient = temp_db.add_patient(patient)
        assert added_patient.id is not None
        assert added_patient.uhid is not None

        # 3. Index patient summary for search
        summary = temp_db.get_patient_summary(added_patient.id)
        temp_rag.index_patient_summary(added_patient.id, summary)

        # 4. Verify patient can be found
        retrieved = temp_db.get_patient(added_patient.id)
        assert retrieved.name == "Mohan Singh"

        # 5. Verify patient can be searched
        search_results = temp_db.search_patients_basic("Mohan")
        assert len(search_results) > 0
        assert any(p.id == added_patient.id for p in search_results)

    def test_patient_update_workflow(self, temp_db, sample_patient_data):
        """Test workflow of updating patient information."""
        # 1. Get current patient
        patient = temp_db.get_patient(sample_patient_data.id)

        # 2. Update details
        patient.phone = "8888888888"
        patient.address = "New Address, Delhi"

        # 3. Save update
        success = temp_db.update_patient(patient)
        assert success is True

        # 4. Verify update
        updated = temp_db.get_patient(sample_patient_data.id)
        assert updated.phone == "8888888888"
        assert updated.address == "New Address, Delhi"


class TestVisitWorkflow:
    """Integration tests for visit management workflow."""

    def test_complete_visit_workflow(self, temp_db, temp_rag, sample_patient_data):
        """Test complete workflow of patient visit."""
        # 1. Create visit
        visit = Visit(
            patient_id=sample_patient_data.id,
            visit_date=date(2024, 1, 20),
            chief_complaint="Headache and fever for 2 days",
            clinical_notes="Temp 101F, BP 130/80. Viral fever suspected.",
            diagnosis="Viral Fever"
        )

        # 2. Add visit to database
        added_visit = temp_db.add_visit(visit)
        assert added_visit.id is not None

        # 3. Get all visits for patient
        visits = temp_db.get_patient_visits(sample_patient_data.id)
        assert len(visits) == 1
        assert visits[0].diagnosis == "Viral Fever"

        # 4. Index visit for RAG
        documents = temp_db.get_patient_documents_for_rag(sample_patient_data.id)
        temp_rag.index_patient_documents(sample_patient_data.id, documents)

        # 5. Verify indexing
        doc_count = temp_rag.get_patient_document_count(sample_patient_data.id)
        assert doc_count > 0

    def test_visit_with_prescription_workflow(self, temp_db, sample_patient_data):
        """Test visit with prescription JSON."""
        # 1. Create prescription JSON
        prescription_data = {
            "diagnosis": ["Viral Fever"],
            "medications": [
                {
                    "drug_name": "Paracetamol",
                    "strength": "500mg",
                    "dose": "1",
                    "frequency": "TDS",
                    "duration": "3 days"
                }
            ],
            "advice": ["Rest", "Plenty of fluids"],
            "follow_up": "3 days if fever persists"
        }

        # 2. Create visit with prescription
        visit = Visit(
            patient_id=sample_patient_data.id,
            chief_complaint="Fever",
            prescription_json=json.dumps(prescription_data)
        )

        # 3. Add to database
        added_visit = temp_db.add_visit(visit)
        assert added_visit.prescription_json is not None

        # 4. Retrieve and verify
        visits = temp_db.get_patient_visits(sample_patient_data.id)
        retrieved_prescription = json.loads(visits[0].prescription_json)
        assert retrieved_prescription["diagnosis"] == ["Viral Fever"]
        assert len(retrieved_prescription["medications"]) == 1


class TestPrescriptionWorkflow:
    """Integration tests for prescription generation workflow."""

    def test_complete_prescription_workflow_with_mocks(
        self, temp_db, temp_pdf, sample_patient_data, mock_prescription_response
    ):
        """Test complete prescription workflow with mocked LLM."""
        # 1. Create clinical notes
        clinical_notes = """
        Patient presents with fever, vomiting and loose stools for 2 days.
        Dehydrated. No blood in stools.
        Diagnosis: Acute gastroenteritis
        """

        # 2. Mock LLM to generate prescription
        with patch('psutil.virtual_memory') as mock_mem, \
             patch('requests.get') as mock_get, \
             patch('requests.post') as mock_post:

            mock_mem.return_value = Mock(total=8 * 1024**3)
            mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})

            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "response": json.dumps(mock_prescription_response)
            }
            mock_post.return_value = mock_post_response

            llm = LLMService()
            success, prescription, raw_json = llm.generate_prescription(clinical_notes)

            assert success is True
            assert prescription is not None

        # 3. Create visit with prescription
        visit = Visit(
            patient_id=sample_patient_data.id,
            chief_complaint="Fever, vomiting, loose stools",
            clinical_notes=clinical_notes,
            diagnosis="Acute Gastroenteritis",
            prescription_json=raw_json
        )

        # 4. Save visit
        added_visit = temp_db.add_visit(visit)
        assert added_visit.id is not None

        # 5. Generate PDF
        patient = temp_db.get_patient(sample_patient_data.id)
        pdf_path = temp_pdf.generate_prescription_pdf(
            patient=patient,
            prescription=prescription,
            chief_complaint=visit.chief_complaint
        )

        assert pdf_path is not None
        assert Path(pdf_path).exists()

    def test_prescription_update_workflow(self, temp_db, sample_patient_data):
        """Test updating a visit with new prescription."""
        # 1. Create initial visit
        visit = Visit(
            patient_id=sample_patient_data.id,
            chief_complaint="Cough",
            diagnosis="URTI"
        )
        added_visit = temp_db.add_visit(visit)

        # 2. Update with prescription
        prescription_data = {
            "diagnosis": ["Upper Respiratory Tract Infection"],
            "medications": [
                {
                    "drug_name": "Azithromycin",
                    "strength": "500mg",
                    "dose": "1",
                    "frequency": "OD",
                    "duration": "3 days"
                }
            ]
        }

        added_visit.prescription_json = json.dumps(prescription_data)
        success = temp_db.update_visit(added_visit)
        assert success is True

        # 3. Verify update
        visits = temp_db.get_patient_visits(sample_patient_data.id)
        assert visits[0].prescription_json is not None


class TestInvestigationWorkflow:
    """Integration tests for investigation management."""

    def test_complete_investigation_workflow(self, temp_db, temp_rag, sample_patient_data):
        """Test complete workflow of adding investigations."""
        # 1. Add multiple investigations
        investigations = [
            Investigation(
                patient_id=sample_patient_data.id,
                test_name="Hemoglobin",
                result="10.5",
                unit="g/dL",
                reference_range="12-16",
                test_date=date(2024, 1, 15),
                is_abnormal=True
            ),
            Investigation(
                patient_id=sample_patient_data.id,
                test_name="Blood Sugar (F)",
                result="125",
                unit="mg/dL",
                reference_range="70-110",
                test_date=date(2024, 1, 15),
                is_abnormal=True
            ),
        ]

        for inv in investigations:
            temp_db.add_investigation(inv)

        # 2. Retrieve investigations
        patient_investigations = temp_db.get_patient_investigations(sample_patient_data.id)
        assert len(patient_investigations) == 2

        # 3. Index for RAG
        documents = temp_db.get_patient_documents_for_rag(sample_patient_data.id)
        temp_rag.index_patient_documents(sample_patient_data.id, documents)

        # 4. Query for abnormal results
        context = temp_rag.query_patient_context(
            sample_patient_data.id,
            "What abnormal lab results does the patient have?",
            n_results=5
        )

        assert "Hemoglobin" in context or "Blood Sugar" in context


class TestRAGWorkflow:
    """Integration tests for RAG queries."""

    def test_complete_rag_workflow_with_mocked_llm(
        self, temp_db, temp_rag, sample_patient_data
    ):
        """Test complete RAG workflow with patient data."""
        # 1. Add patient data
        visit = Visit(
            patient_id=sample_patient_data.id,
            visit_date=date(2024, 1, 10),
            chief_complaint="Routine checkup",
            clinical_notes="Patient doing well, BP controlled",
            diagnosis="Hypertension - controlled"
        )
        temp_db.add_visit(visit)

        investigation = Investigation(
            patient_id=sample_patient_data.id,
            test_name="Creatinine",
            result="1.4",
            unit="mg/dL",
            reference_range="0.7-1.3",
            test_date=date(2024, 1, 10),
            is_abnormal=True
        )
        temp_db.add_investigation(investigation)

        # 2. Index patient data
        summary = temp_db.get_patient_summary(sample_patient_data.id)
        documents = temp_db.get_patient_documents_for_rag(sample_patient_data.id)

        temp_rag.index_patient_summary(sample_patient_data.id, summary)
        temp_rag.index_patient_documents(sample_patient_data.id, documents)

        # 3. Query for context
        context = temp_rag.query_patient_context(
            sample_patient_data.id,
            "What was the creatinine level?",
            n_results=3
        )

        assert "Creatinine" in context or "creatinine" in context.lower()
        assert "1.4" in context

        # 4. Mock LLM to answer query
        with patch('psutil.virtual_memory') as mock_mem, \
             patch('requests.get') as mock_get, \
             patch('requests.post') as mock_post:

            mock_mem.return_value = Mock(total=8 * 1024**3)
            mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})

            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "response": "The last creatinine level was 1.4 mg/dL on 2024-01-10, which is slightly elevated above the normal range of 0.7-1.3 mg/dL."
            }
            mock_post.return_value = mock_post_response

            llm = LLMService()
            success, answer = llm.query_patient_records(
                context,
                "What was the creatinine level?"
            )

            assert success is True
            assert "1.4" in answer


class TestFullPatientLifecycle:
    """Integration test for complete patient lifecycle."""

    def test_full_patient_lifecycle(self, temp_db, temp_rag, temp_pdf):
        """Test complete patient lifecycle from registration to prescription."""
        # 1. Register new patient
        patient = Patient(
            name="Sita Devi",
            age=60,
            gender="F",
            phone="9876543210",
            address="Bangalore"
        )
        patient = temp_db.add_patient(patient)
        assert patient.id is not None

        # 2. Index patient for search
        summary = temp_db.get_patient_summary(patient.id)
        temp_rag.index_patient_summary(patient.id, summary)

        # 3. Add first visit
        visit1 = Visit(
            patient_id=patient.id,
            visit_date=date(2024, 1, 1),
            chief_complaint="Fatigue, increased thirst",
            clinical_notes="Random blood sugar 250 mg/dL",
            diagnosis="Type 2 Diabetes Mellitus - newly diagnosed"
        )
        temp_db.add_visit(visit1)

        # 4. Add investigations
        temp_db.add_investigation(Investigation(
            patient_id=patient.id,
            test_name="HbA1c",
            result="8.5",
            unit="%",
            reference_range="4-6",
            test_date=date(2024, 1, 1),
            is_abnormal=True
        ))

        # 5. Add procedure (counseling)
        temp_db.add_procedure(Procedure(
            patient_id=patient.id,
            procedure_name="Diabetes counseling",
            details="Diet and lifestyle modification discussed",
            procedure_date=date(2024, 1, 1)
        ))

        # 6. Index all data for RAG
        documents = temp_db.get_patient_documents_for_rag(patient.id)
        temp_rag.index_patient_documents(patient.id, documents)

        # 7. Add follow-up visit
        visit2 = Visit(
            patient_id=patient.id,
            visit_date=date(2024, 2, 1),
            chief_complaint="Follow-up",
            clinical_notes="Patient compliant with medications",
            diagnosis="Type 2 Diabetes - controlled"
        )
        temp_db.add_visit(visit2)

        # 8. Verify complete patient history
        all_visits = temp_db.get_patient_visits(patient.id)
        assert len(all_visits) == 2

        all_investigations = temp_db.get_patient_investigations(patient.id)
        assert len(all_investigations) == 1

        all_procedures = temp_db.get_patient_procedures(patient.id)
        assert len(all_procedures) == 1

        # 9. Verify RAG can answer questions
        context = temp_rag.query_patient_context(
            patient.id,
            "What was the HbA1c level?",
            n_results=5
        )
        assert "8.5" in context or "HbA1c" in context


class TestMultiPatientWorkflow:
    """Integration tests with multiple patients."""

    def test_multiple_patients_isolation(self, temp_db, temp_rag):
        """Test that multiple patients' data is properly isolated."""
        # Create patient 1
        patient1 = temp_db.add_patient(Patient(name="Patient One", age=50))
        temp_db.add_visit(Visit(
            patient_id=patient1.id,
            diagnosis="Diabetes"
        ))

        # Create patient 2
        patient2 = temp_db.add_patient(Patient(name="Patient Two", age=60))
        temp_db.add_visit(Visit(
            patient_id=patient2.id,
            diagnosis="Hypertension"
        ))

        # Index both patients
        for patient in [patient1, patient2]:
            summary = temp_db.get_patient_summary(patient.id)
            documents = temp_db.get_patient_documents_for_rag(patient.id)
            temp_rag.reindex_patient(patient.id, summary, documents)

        # Verify isolation - patient 1's context shouldn't include patient 2's data
        context1 = temp_rag.query_patient_context(
            patient1.id,
            "medical conditions",
            n_results=5
        )
        assert "Diabetes" in context1 or "diabetes" in context1.lower()
        assert "Hypertension" not in context1

        context2 = temp_rag.query_patient_context(
            patient2.id,
            "medical conditions",
            n_results=5
        )
        assert "Hypertension" in context2 or "hypertension" in context2.lower()
        assert "Diabetes" not in context2

    def test_search_across_multiple_patients(self, temp_db, temp_rag):
        """Test searching across multiple patients."""
        # Create multiple patients with different conditions
        patients = [
            ("Ram Lal", "Diabetes"),
            ("Shyam Kumar", "Diabetes and Hypertension"),
            ("Mohan Singh", "Hypertension only"),
            ("Geeta Devi", "No chronic illness"),
        ]

        for name, diagnosis in patients:
            patient = temp_db.add_patient(Patient(name=name))
            if diagnosis != "No chronic illness":
                temp_db.add_visit(Visit(
                    patient_id=patient.id,
                    diagnosis=diagnosis
                ))
            summary = temp_db.get_patient_summary(patient.id)
            temp_rag.index_patient_summary(patient.id, summary)

        # Search for diabetic patients
        results = temp_rag.search_patients("patients with diabetes", n_results=10)

        assert len(results) >= 2
        # Top results should be patients with diabetes
        patient_ids = [r[0] for r in results[:2]]

        # Verify they are the diabetic patients
        for patient_id in patient_ids:
            patient = temp_db.get_patient(patient_id)
            assert patient.name in ["Ram Lal", "Shyam Kumar"]
