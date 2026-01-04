"""Unit tests for database service."""

import pytest
from datetime import date, datetime
from pathlib import Path

from src.services.database import DatabaseService
from src.models.schemas import Patient, Visit, Investigation, Procedure


class TestDatabaseInitialization:
    """Tests for database initialization."""

    def test_database_creation(self, temp_db):
        """Test that database file is created."""
        assert Path(temp_db.db_path).exists()

    def test_tables_created(self, temp_db):
        """Test that all tables are created."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            assert 'patients' in tables
            assert 'visits' in tables
            assert 'investigations' in tables
            assert 'procedures' in tables

    def test_indexes_created(self, temp_db):
        """Test that indexes are created."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index'
            """)
            indexes = [row[0] for row in cursor.fetchall()]

            assert 'idx_patients_name' in indexes
            assert 'idx_visits_patient' in indexes


class TestPatientOperations:
    """Tests for patient CRUD operations."""

    def test_add_patient(self, temp_db, sample_patient):
        """Test adding a new patient."""
        patient = temp_db.add_patient(sample_patient)

        assert patient.id is not None
        assert patient.uhid is not None
        assert patient.uhid.startswith("EMR-")
        assert patient.name == sample_patient.name
        assert patient.age == sample_patient.age

    def test_uhid_generation(self, temp_db, sample_patient):
        """Test UHID generation is sequential."""
        patient1 = temp_db.add_patient(sample_patient)
        patient2 = temp_db.add_patient(Patient(name="Test Patient 2"))

        # Extract numbers from UHID
        uhid1_num = int(patient1.uhid.split("-")[-1])
        uhid2_num = int(patient2.uhid.split("-")[-1])

        assert uhid2_num == uhid1_num + 1

    def test_get_patient(self, temp_db, sample_patient_data):
        """Test retrieving a patient by ID."""
        patient = temp_db.get_patient(sample_patient_data.id)

        assert patient is not None
        assert patient.id == sample_patient_data.id
        assert patient.name == sample_patient_data.name

    def test_get_patient_not_found(self, temp_db):
        """Test getting non-existent patient returns None."""
        patient = temp_db.get_patient(99999)
        assert patient is None

    def test_get_all_patients(self, temp_db):
        """Test retrieving all patients."""
        # Add multiple patients
        temp_db.add_patient(Patient(name="Alice"))
        temp_db.add_patient(Patient(name="Bob"))
        temp_db.add_patient(Patient(name="Charlie"))

        patients = temp_db.get_all_patients()
        assert len(patients) == 3
        # Should be sorted by name
        assert patients[0].name == "Alice"
        assert patients[1].name == "Bob"

    def test_search_patients_by_name(self, temp_db):
        """Test searching patients by name."""
        temp_db.add_patient(Patient(name="Ram Lal"))
        temp_db.add_patient(Patient(name="Shyam Kumar"))
        temp_db.add_patient(Patient(name="Ram Singh"))

        results = temp_db.search_patients_basic("Ram")
        assert len(results) == 2
        assert all("Ram" in p.name for p in results)

    def test_search_patients_by_uhid(self, temp_db):
        """Test searching patients by UHID."""
        patient = temp_db.add_patient(Patient(name="Test Patient"))
        uhid_part = patient.uhid[-4:]  # Last 4 digits

        results = temp_db.search_patients_basic(uhid_part)
        assert len(results) >= 1
        assert any(p.id == patient.id for p in results)

    def test_search_patients_case_insensitive(self, temp_db):
        """Test search is case insensitive."""
        temp_db.add_patient(Patient(name="John Doe"))

        results = temp_db.search_patients_basic("john")
        assert len(results) == 1
        assert results[0].name == "John Doe"

    def test_update_patient(self, temp_db, sample_patient_data):
        """Test updating patient details."""
        sample_patient_data.age = 66
        sample_patient_data.phone = "9999999999"

        success = temp_db.update_patient(sample_patient_data)
        assert success is True

        updated = temp_db.get_patient(sample_patient_data.id)
        assert updated.age == 66
        assert updated.phone == "9999999999"

    def test_update_nonexistent_patient(self, temp_db):
        """Test updating non-existent patient returns False."""
        fake_patient = Patient(id=99999, name="Ghost")
        success = temp_db.update_patient(fake_patient)
        assert success is False


class TestVisitOperations:
    """Tests for visit CRUD operations."""

    def test_add_visit(self, temp_db, sample_patient_data):
        """Test adding a visit."""
        visit = Visit(
            patient_id=sample_patient_data.id,
            chief_complaint="Headache",
            clinical_notes="Migraine, no aura"
        )

        added_visit = temp_db.add_visit(visit)
        assert added_visit.id is not None
        assert added_visit.patient_id == sample_patient_data.id

    def test_add_visit_with_date(self, temp_db, sample_patient_data):
        """Test adding visit with specific date."""
        visit = Visit(
            patient_id=sample_patient_data.id,
            visit_date=date(2024, 1, 15),
            chief_complaint="Fever"
        )

        added_visit = temp_db.add_visit(visit)
        assert added_visit.visit_date == date(2024, 1, 15)

    def test_get_patient_visits(self, temp_db, sample_patient_data):
        """Test retrieving all visits for a patient."""
        # Add multiple visits
        for i in range(3):
            temp_db.add_visit(Visit(
                patient_id=sample_patient_data.id,
                visit_date=date(2024, 1, i + 1),
                chief_complaint=f"Complaint {i}"
            ))

        visits = temp_db.get_patient_visits(sample_patient_data.id)
        assert len(visits) == 3
        # Should be sorted by date descending
        assert visits[0].visit_date > visits[-1].visit_date

    def test_get_visits_empty(self, temp_db, sample_patient_data):
        """Test getting visits for patient with no visits."""
        visits = temp_db.get_patient_visits(sample_patient_data.id)
        assert visits == []

    def test_update_visit(self, temp_db, sample_visit_data):
        """Test updating a visit."""
        sample_visit_data.diagnosis = "NSTEMI"
        sample_visit_data.prescription_json = '{"medications": []}'

        success = temp_db.update_visit(sample_visit_data)
        assert success is True

        visits = temp_db.get_patient_visits(sample_visit_data.patient_id)
        updated_visit = next(v for v in visits if v.id == sample_visit_data.id)
        assert updated_visit.diagnosis == "NSTEMI"


class TestInvestigationOperations:
    """Tests for investigation operations."""

    def test_add_investigation(self, temp_db, sample_patient_data):
        """Test adding an investigation."""
        inv = Investigation(
            patient_id=sample_patient_data.id,
            test_name="CBC",
            result="Normal",
            test_date=date(2024, 1, 10)
        )

        added_inv = temp_db.add_investigation(inv)
        assert added_inv.id is not None
        assert added_inv.test_name == "CBC"

    def test_add_abnormal_investigation(self, temp_db, sample_investigation):
        """Test adding abnormal investigation."""
        added_inv = temp_db.add_investigation(sample_investigation)

        assert added_inv.is_abnormal is True
        assert added_inv.result == "1.4"

    def test_get_patient_investigations(self, temp_db, sample_patient_data):
        """Test retrieving all investigations for a patient."""
        # Add multiple investigations
        tests = ["CBC", "LFT", "RFT"]
        for test in tests:
            temp_db.add_investigation(Investigation(
                patient_id=sample_patient_data.id,
                test_name=test,
                test_date=date(2024, 1, 15)
            ))

        investigations = temp_db.get_patient_investigations(sample_patient_data.id)
        assert len(investigations) == 3
        test_names = [inv.test_name for inv in investigations]
        assert set(test_names) == set(tests)

    def test_investigations_sorted_by_date(self, temp_db, sample_patient_data):
        """Test investigations are sorted by date descending."""
        temp_db.add_investigation(Investigation(
            patient_id=sample_patient_data.id,
            test_name="Test1",
            test_date=date(2024, 1, 1)
        ))
        temp_db.add_investigation(Investigation(
            patient_id=sample_patient_data.id,
            test_name="Test2",
            test_date=date(2024, 1, 15)
        ))

        investigations = temp_db.get_patient_investigations(sample_patient_data.id)
        assert investigations[0].test_date > investigations[1].test_date


class TestProcedureOperations:
    """Tests for procedure operations."""

    def test_add_procedure(self, temp_db, sample_patient_data):
        """Test adding a procedure."""
        proc = Procedure(
            patient_id=sample_patient_data.id,
            procedure_name="ECG",
            details="12-lead ECG done",
            procedure_date=date(2024, 1, 10)
        )

        added_proc = temp_db.add_procedure(proc)
        assert added_proc.id is not None
        assert added_proc.procedure_name == "ECG"

    def test_get_patient_procedures(self, temp_db, sample_patient_data, sample_procedure):
        """Test retrieving all procedures for a patient."""
        temp_db.add_procedure(sample_procedure)
        temp_db.add_procedure(Procedure(
            patient_id=sample_patient_data.id,
            procedure_name="Angiography",
            procedure_date=date(2024, 1, 5)
        ))

        procedures = temp_db.get_patient_procedures(sample_patient_data.id)
        assert len(procedures) == 2

    def test_procedures_sorted_by_date(self, temp_db, sample_patient_data):
        """Test procedures are sorted by date descending."""
        temp_db.add_procedure(Procedure(
            patient_id=sample_patient_data.id,
            procedure_name="Procedure1",
            procedure_date=date(2024, 1, 1)
        ))
        temp_db.add_procedure(Procedure(
            patient_id=sample_patient_data.id,
            procedure_name="Procedure2",
            procedure_date=date(2024, 1, 15)
        ))

        procedures = temp_db.get_patient_procedures(sample_patient_data.id)
        assert procedures[0].procedure_date > procedures[1].procedure_date


class TestRAGHelperMethods:
    """Tests for RAG helper methods."""

    def test_get_patient_summary(self, temp_db, sample_patient_data):
        """Test generating patient summary."""
        summary = temp_db.get_patient_summary(sample_patient_data.id)

        assert "Ram Lal" in summary
        assert str(sample_patient_data.age) in summary
        assert sample_patient_data.gender in summary

    def test_patient_summary_with_diagnosis(self, temp_db, sample_patient_data):
        """Test summary includes diagnoses from visits."""
        temp_db.add_visit(Visit(
            patient_id=sample_patient_data.id,
            diagnosis="Diabetes"
        ))
        temp_db.add_visit(Visit(
            patient_id=sample_patient_data.id,
            diagnosis="Hypertension"
        ))

        summary = temp_db.get_patient_summary(sample_patient_data.id)
        assert "Diabetes" in summary or "Hypertension" in summary

    def test_patient_summary_with_procedures(self, temp_db, sample_patient_data, sample_procedure):
        """Test summary includes procedures."""
        temp_db.add_procedure(sample_procedure)

        summary = temp_db.get_patient_summary(sample_patient_data.id)
        assert "PCI to LAD" in summary

    def test_get_patient_documents_for_rag(self, temp_db, sample_patient_data, sample_visit_data):
        """Test getting documents for RAG indexing."""
        # Add investigation and procedure
        temp_db.add_investigation(Investigation(
            patient_id=sample_patient_data.id,
            test_name="CBC",
            result="Normal",
            test_date=date(2024, 1, 10)
        ))
        temp_db.add_procedure(Procedure(
            patient_id=sample_patient_data.id,
            procedure_name="ECG",
            procedure_date=date(2024, 1, 10)
        ))

        documents = temp_db.get_patient_documents_for_rag(sample_patient_data.id)

        # Should have 1 visit, 1 investigation, 1 procedure
        assert len(documents) == 3

        doc_types = [doc[2]["type"] for doc in documents]
        assert "visit" in doc_types
        assert "investigation" in doc_types
        assert "procedure" in doc_types

    def test_documents_contain_patient_id(self, temp_db, sample_patient_data, sample_visit_data):
        """Test documents metadata includes patient_id."""
        documents = temp_db.get_patient_documents_for_rag(sample_patient_data.id)

        for doc_id, content, metadata in documents:
            assert metadata["patient_id"] == sample_patient_data.id

    def test_visit_document_includes_prescription(self, temp_db, sample_patient_data):
        """Test visit document includes medications from prescription."""
        import json
        rx_json = json.dumps({
            "medications": [
                {"drug_name": "Aspirin"},
                {"drug_name": "Atorvastatin"}
            ]
        })

        temp_db.add_visit(Visit(
            patient_id=sample_patient_data.id,
            chief_complaint="Chest pain",
            prescription_json=rx_json
        ))

        documents = temp_db.get_patient_documents_for_rag(sample_patient_data.id)
        visit_docs = [doc for doc in documents if doc[2]["type"] == "visit"]

        assert len(visit_docs) > 0
        assert "Aspirin" in visit_docs[0][1] or "Atorvastatin" in visit_docs[0][1]
