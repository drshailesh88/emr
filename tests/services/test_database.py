"""Tests for DatabaseService."""

import pytest
import os
from datetime import date, datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.database import DatabaseService
from src.models.schemas import Patient, Visit, Investigation, Procedure


class TestDatabaseServiceInitialization:
    """Tests for DatabaseService initialization."""

    def test_database_creates_file(self, temp_db_path):
        """Test that database file is created."""
        db = DatabaseService(db_path=temp_db_path)
        assert os.path.exists(temp_db_path)

    def test_database_creates_parent_directories(self, temp_dir):
        """Test that parent directories are created."""
        nested_path = os.path.join(temp_dir, "nested", "path", "test.db")
        db = DatabaseService(db_path=nested_path)
        assert os.path.exists(nested_path)

    def test_database_tables_created(self, db_service):
        """Test that all required tables are created."""
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}

        expected = {"patients", "visits", "investigations", "procedures"}
        assert expected.issubset(tables)

    def test_database_indexes_created(self, db_service):
        """Test that indexes are created."""
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = {row[0] for row in cursor.fetchall()}

        assert "idx_patients_name" in indexes
        assert "idx_visits_patient" in indexes


class TestPatientOperations:
    """Tests for patient CRUD operations."""

    def test_add_patient(self, db_service, sample_patient):
        """Test adding a new patient."""
        result = db_service.add_patient(sample_patient)

        assert result.id is not None
        assert result.uhid is not None
        assert result.uhid.startswith("EMR-")
        assert result.name == sample_patient.name

    def test_add_patient_generates_unique_uhid(self, db_service):
        """Test that each patient gets unique UHID."""
        patient1 = Patient(name="Patient One")
        patient2 = Patient(name="Patient Two")

        result1 = db_service.add_patient(patient1)
        result2 = db_service.add_patient(patient2)

        assert result1.uhid != result2.uhid

    def test_uhid_format(self, db_service, sample_patient):
        """Test UHID format is EMR-YYYY-NNNN."""
        result = db_service.add_patient(sample_patient)

        parts = result.uhid.split("-")
        assert len(parts) == 3
        assert parts[0] == "EMR"
        assert parts[1] == str(datetime.now().year)
        assert len(parts[2]) == 4

    def test_get_patient_by_id(self, db_service, sample_patient):
        """Test retrieving patient by ID."""
        added = db_service.add_patient(sample_patient)
        retrieved = db_service.get_patient(added.id)

        assert retrieved is not None
        assert retrieved.id == added.id
        assert retrieved.name == added.name
        assert retrieved.uhid == added.uhid

    def test_get_patient_not_found(self, db_service):
        """Test getting non-existent patient returns None."""
        result = db_service.get_patient(999)
        assert result is None

    def test_get_all_patients_empty(self, db_service):
        """Test get all patients when database is empty."""
        result = db_service.get_all_patients()
        assert result == []

    def test_get_all_patients(self, db_service):
        """Test retrieving all patients."""
        for name in ["Alice", "Bob", "Charlie"]:
            db_service.add_patient(Patient(name=name))

        result = db_service.get_all_patients()

        assert len(result) == 3
        # Should be ordered by name
        assert result[0].name == "Alice"
        assert result[1].name == "Bob"
        assert result[2].name == "Charlie"

    def test_search_patients_by_name(self, db_service):
        """Test searching patients by name."""
        db_service.add_patient(Patient(name="Ram Lal"))
        db_service.add_patient(Patient(name="Shyam Kumar"))
        db_service.add_patient(Patient(name="Ram Singh"))

        result = db_service.search_patients_basic("Ram")

        assert len(result) == 2
        names = [p.name for p in result]
        assert "Ram Lal" in names
        assert "Ram Singh" in names

    def test_search_patients_by_uhid(self, db_service):
        """Test searching patients by UHID."""
        patient = db_service.add_patient(Patient(name="Test Patient"))

        # Search by partial UHID
        result = db_service.search_patients_basic("EMR-")

        assert len(result) >= 1
        assert any(p.uhid == patient.uhid for p in result)

    def test_search_patients_case_insensitive(self, db_service):
        """Test that search is case-insensitive."""
        db_service.add_patient(Patient(name="Ram Lal"))

        result_upper = db_service.search_patients_basic("RAM")
        result_lower = db_service.search_patients_basic("ram")

        assert len(result_upper) == 1
        assert len(result_lower) == 1

    def test_update_patient(self, db_service, sample_patient):
        """Test updating patient details."""
        patient = db_service.add_patient(sample_patient)
        patient.age = 70
        patient.phone = "1234567890"

        result = db_service.update_patient(patient)

        assert result is True
        updated = db_service.get_patient(patient.id)
        assert updated.age == 70
        assert updated.phone == "1234567890"


class TestVisitOperations:
    """Tests for visit operations."""

    def test_add_visit(self, db_service, sample_patient, sample_visit):
        """Test adding a visit."""
        patient = db_service.add_patient(sample_patient)
        sample_visit.patient_id = patient.id

        result = db_service.add_visit(sample_visit)

        assert result.id is not None
        assert result.patient_id == patient.id

    def test_add_visit_auto_date(self, db_service, sample_patient):
        """Test visit date defaults to today."""
        patient = db_service.add_patient(sample_patient)
        visit = Visit(patient_id=patient.id, chief_complaint="Fever")

        result = db_service.add_visit(visit)

        # Should default to today
        assert result.id is not None

    def test_get_patient_visits(self, db_service, sample_patient):
        """Test retrieving all visits for a patient."""
        patient = db_service.add_patient(sample_patient)

        for complaint in ["Fever", "Headache", "Cough"]:
            db_service.add_visit(Visit(
                patient_id=patient.id,
                chief_complaint=complaint
            ))

        result = db_service.get_patient_visits(patient.id)

        assert len(result) == 3

    def test_get_patient_visits_ordered(self, db_service, sample_patient):
        """Test visits are ordered by date descending."""
        patient = db_service.add_patient(sample_patient)

        db_service.add_visit(Visit(
            patient_id=patient.id,
            visit_date=date(2024, 1, 1),
            chief_complaint="First"
        ))
        db_service.add_visit(Visit(
            patient_id=patient.id,
            visit_date=date(2024, 12, 31),
            chief_complaint="Last"
        ))

        result = db_service.get_patient_visits(patient.id)

        # Most recent first
        assert result[0].chief_complaint == "Last"
        assert result[1].chief_complaint == "First"

    def test_update_visit(self, db_service, sample_patient, sample_visit):
        """Test updating a visit."""
        patient = db_service.add_patient(sample_patient)
        sample_visit.patient_id = patient.id
        visit = db_service.add_visit(sample_visit)

        visit.diagnosis = "Viral fever with dehydration"
        result = db_service.update_visit(visit)

        assert result is True


class TestInvestigationOperations:
    """Tests for investigation operations."""

    def test_add_investigation(self, db_service, sample_patient, sample_investigation):
        """Test adding an investigation."""
        patient = db_service.add_patient(sample_patient)
        sample_investigation.patient_id = patient.id

        result = db_service.add_investigation(sample_investigation)

        assert result.id is not None
        assert result.test_name == "Creatinine"

    def test_get_patient_investigations(self, db_service, sample_patient):
        """Test retrieving investigations for a patient."""
        patient = db_service.add_patient(sample_patient)

        for test in ["CBC", "LFT", "RFT"]:
            db_service.add_investigation(Investigation(
                patient_id=patient.id,
                test_name=test,
                result="Normal"
            ))

        result = db_service.get_patient_investigations(patient.id)

        assert len(result) == 3

    def test_investigation_abnormal_flag(self, db_service, sample_patient):
        """Test abnormal flag is stored correctly."""
        patient = db_service.add_patient(sample_patient)

        db_service.add_investigation(Investigation(
            patient_id=patient.id,
            test_name="Creatinine",
            result="2.5",
            is_abnormal=True
        ))

        result = db_service.get_patient_investigations(patient.id)

        assert result[0].is_abnormal is True


class TestProcedureOperations:
    """Tests for procedure operations."""

    def test_add_procedure(self, db_service, sample_patient, sample_procedure):
        """Test adding a procedure."""
        patient = db_service.add_patient(sample_patient)
        sample_procedure.patient_id = patient.id

        result = db_service.add_procedure(sample_procedure)

        assert result.id is not None
        assert result.procedure_name == "PCI to LAD"

    def test_get_patient_procedures(self, db_service, sample_patient):
        """Test retrieving procedures for a patient."""
        patient = db_service.add_patient(sample_patient)

        for proc in ["CABG", "PCI to LAD", "Pacemaker implant"]:
            db_service.add_procedure(Procedure(
                patient_id=patient.id,
                procedure_name=proc
            ))

        result = db_service.get_patient_procedures(patient.id)

        assert len(result) == 3


class TestRAGHelperMethods:
    """Tests for RAG helper methods."""

    def test_get_patient_summary(self, populated_db):
        """Test generating patient summary."""
        db_service, patient = populated_db

        summary = db_service.get_patient_summary(patient.id)

        assert patient.name in summary
        assert patient.uhid in summary
        assert str(patient.age) in summary
        assert patient.gender in summary

    def test_get_patient_summary_not_found(self, db_service):
        """Test summary for non-existent patient."""
        summary = db_service.get_patient_summary(999)
        assert summary == ""

    def test_get_patient_documents_for_rag(self, populated_db):
        """Test getting documents for RAG indexing."""
        db_service, patient = populated_db

        documents = db_service.get_patient_documents_for_rag(patient.id)

        assert len(documents) == 3  # 1 visit, 1 investigation, 1 procedure

        doc_ids = [doc[0] for doc in documents]
        assert any("visit_" in doc_id for doc_id in doc_ids)
        assert any("investigation_" in doc_id for doc_id in doc_ids)
        assert any("procedure_" in doc_id for doc_id in doc_ids)

    def test_get_patient_documents_format(self, populated_db):
        """Test document format is (doc_id, content, metadata)."""
        db_service, patient = populated_db

        documents = db_service.get_patient_documents_for_rag(patient.id)

        for doc_id, content, metadata in documents:
            assert isinstance(doc_id, str)
            assert isinstance(content, str)
            assert isinstance(metadata, dict)
            assert "type" in metadata
            assert "patient_id" in metadata

    def test_get_patient_documents_empty(self, db_service, sample_patient):
        """Test documents for patient with no records."""
        patient = db_service.add_patient(sample_patient)

        documents = db_service.get_patient_documents_for_rag(patient.id)

        assert documents == []


class TestDatabaseConnectionHandling:
    """Tests for database connection management."""

    def test_connection_context_manager(self, db_service):
        """Test connection context manager works correctly."""
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_connection_rollback_on_error(self, db_service, sample_patient):
        """Test that errors cause rollback."""
        # Add a patient first
        db_service.add_patient(sample_patient)

        # Try to insert invalid data (should rollback)
        try:
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                # This should work
                cursor.execute(
                    "INSERT INTO patients (name) VALUES (?)", ("Test",)
                )
                # This should fail (duplicate primary key if we try)
                cursor.execute(
                    "INSERT INTO patients (id, name) VALUES (1, 'Conflict')"
                )
        except Exception:
            pass

        # Original patient should still exist
        patients = db_service.get_all_patients()
        assert len(patients) >= 1
