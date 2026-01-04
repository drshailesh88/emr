"""Tests for RAGService."""

import pytest
import os
import shutil
import tempfile

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.rag import RAGService


class TestRAGServiceInitialization:
    """Tests for RAGService initialization."""

    def test_service_creates_directory(self, temp_chroma_dir):
        """Test that ChromaDB directory is created."""
        service = RAGService(persist_directory=temp_chroma_dir)
        assert os.path.exists(temp_chroma_dir)

    def test_collections_created(self, rag_service):
        """Test that both collections are created."""
        assert rag_service.patient_summaries is not None
        assert rag_service.patient_documents is not None

    def test_default_directory_from_env(self, temp_dir, monkeypatch):
        """Test default directory from environment variable."""
        test_path = os.path.join(temp_dir, "env_chroma")
        monkeypatch.setenv("DOCASSIST_CHROMA_DIR", test_path)

        service = RAGService(persist_directory=None)
        # Should use env variable (but we'll check it doesn't fail)
        assert service.persist_dir is not None


class TestPatientSummaryOperations:
    """Tests for patient summary indexing and search."""

    def test_index_patient_summary(self, rag_service):
        """Test indexing a patient summary."""
        rag_service.index_patient_summary(
            patient_id=1,
            summary="Patient: Ram Lal. UHID: EMR-2024-0001. Age: 65. Gender: M. Diagnoses: CAD, HTN"
        )

        # Verify by searching
        results = rag_service.search_patients("Ram Lal")
        assert len(results) >= 1

    def test_index_patient_summary_update(self, rag_service):
        """Test updating an existing patient summary."""
        # Index initial summary
        rag_service.index_patient_summary(
            patient_id=1,
            summary="Patient: Ram Lal. Age: 65"
        )

        # Update summary
        rag_service.index_patient_summary(
            patient_id=1,
            summary="Patient: Ram Lal. Age: 66. Diagnosis: CAD"
        )

        # Should find updated summary
        results = rag_service.search_patients("CAD")
        assert len(results) >= 1
        assert any("CAD" in result[2] for result in results)

    def test_search_patients_by_name(self, rag_service):
        """Test searching patients by name."""
        rag_service.index_patient_summary(1, "Patient: Ram Lal. Age: 65")
        rag_service.index_patient_summary(2, "Patient: Shyam Kumar. Age: 45")
        rag_service.index_patient_summary(3, "Patient: Ram Singh. Age: 50")

        results = rag_service.search_patients("Ram")

        assert len(results) >= 2
        summaries = [r[2] for r in results]
        assert any("Ram Lal" in s for s in summaries)
        assert any("Ram Singh" in s for s in summaries)

    def test_search_patients_by_diagnosis(self, rag_service):
        """Test searching patients by diagnosis."""
        rag_service.index_patient_summary(
            1, "Patient: Ram Lal. Diagnoses: CAD, HTN"
        )
        rag_service.index_patient_summary(
            2, "Patient: Shyam Kumar. Diagnoses: Diabetes"
        )

        results = rag_service.search_patients("patient with heart disease CAD")

        assert len(results) >= 1
        # Ram Lal should be more relevant
        top_patient_id = results[0][0]
        assert top_patient_id == 1

    def test_search_patients_by_procedure(self, rag_service):
        """Test searching patients by procedure."""
        rag_service.index_patient_summary(
            1, "Patient: Ram Lal. Procedures: PCI to LAD, CABG"
        )
        rag_service.index_patient_summary(
            2, "Patient: Shyam Kumar. Procedures: Colonoscopy"
        )

        results = rag_service.search_patients("who had PCI")

        assert len(results) >= 1
        top_result = results[0]
        assert top_result[0] == 1

    def test_search_patients_returns_similarity_score(self, rag_service):
        """Test that search returns similarity scores."""
        rag_service.index_patient_summary(1, "Patient: Ram Lal")

        results = rag_service.search_patients("Ram Lal")

        assert len(results) >= 1
        patient_id, similarity, summary = results[0]
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1

    def test_search_patients_n_results(self, rag_service):
        """Test limiting number of search results."""
        for i in range(10):
            rag_service.index_patient_summary(i, f"Patient: Test{i}")

        results = rag_service.search_patients("Test", n_results=3)

        assert len(results) == 3

    def test_search_patients_empty_collection(self, rag_service):
        """Test searching when no patients indexed."""
        results = rag_service.search_patients("Ram Lal")
        assert results == []


class TestPatientDocumentOperations:
    """Tests for patient document indexing and querying."""

    def test_index_patient_documents(self, rag_service):
        """Test indexing patient documents."""
        documents = [
            ("visit_1", "Visit on 2024-01-15: Fever, Headache", {"type": "visit", "date": "2024-01-15"}),
            ("investigation_1", "CBC: Normal", {"type": "investigation", "date": "2024-01-15"}),
        ]

        rag_service.index_patient_documents(patient_id=1, documents=documents)

        count = rag_service.get_patient_document_count(1)
        assert count == 2

    def test_index_patient_documents_empty(self, rag_service):
        """Test indexing empty document list."""
        rag_service.index_patient_documents(patient_id=1, documents=[])

        count = rag_service.get_patient_document_count(1)
        assert count == 0

    def test_index_patient_documents_replaces_existing(self, rag_service):
        """Test that indexing replaces existing documents."""
        # Index initial documents
        rag_service.index_patient_documents(
            patient_id=1,
            documents=[("doc_1", "First visit", {"type": "visit"})]
        )

        # Re-index with new documents
        rag_service.index_patient_documents(
            patient_id=1,
            documents=[
                ("doc_2", "Second visit", {"type": "visit"}),
                ("doc_3", "Third visit", {"type": "visit"})
            ]
        )

        count = rag_service.get_patient_document_count(1)
        assert count == 2

    def test_clear_patient_documents(self, rag_service):
        """Test clearing patient documents."""
        rag_service.index_patient_documents(
            patient_id=1,
            documents=[("doc_1", "Test doc", {"type": "visit"})]
        )

        rag_service.clear_patient_documents(patient_id=1)

        count = rag_service.get_patient_document_count(1)
        assert count == 0

    def test_query_patient_context(self, rag_service):
        """Test querying patient context."""
        documents = [
            ("visit_1", "Visit: Patient has diabetes, taking Metformin", {"type": "visit", "date": "2024-01-15"}),
            ("investigation_1", "Creatinine = 1.4 mg/dL", {"type": "investigation", "date": "2024-01-15"}),
            ("investigation_2", "HbA1c = 7.2%", {"type": "investigation", "date": "2024-01-15"}),
        ]
        rag_service.index_patient_documents(patient_id=1, documents=documents)

        context = rag_service.query_patient_context(
            patient_id=1,
            query="What is the creatinine level?"
        )

        assert "Creatinine" in context or "creatinine" in context
        assert "1.4" in context

    def test_query_patient_context_returns_type_and_date(self, rag_service):
        """Test that context includes document type and date."""
        documents = [
            ("inv_1", "Creatinine = 1.4 mg/dL", {"type": "investigation", "date": "2024-01-15"}),
        ]
        rag_service.index_patient_documents(patient_id=1, documents=documents)

        context = rag_service.query_patient_context(
            patient_id=1,
            query="creatinine"
        )

        assert "INVESTIGATION" in context
        assert "2024-01-15" in context

    def test_query_patient_context_n_results(self, rag_service):
        """Test limiting number of context results."""
        documents = [
            (f"doc_{i}", f"Document {i} content", {"type": "visit", "date": f"2024-01-{i:02d}"})
            for i in range(1, 11)
        ]
        rag_service.index_patient_documents(patient_id=1, documents=documents)

        context = rag_service.query_patient_context(
            patient_id=1,
            query="document",
            n_results=3
        )

        # Should only include up to 3 documents
        assert context.count("[VISIT -") <= 3

    def test_query_patient_context_no_documents(self, rag_service):
        """Test querying patient with no documents."""
        context = rag_service.query_patient_context(
            patient_id=999,
            query="anything"
        )

        assert "no relevant records" in context.lower() or context == ""

    def test_query_patient_context_filters_by_patient(self, rag_service):
        """Test that query only returns documents for specified patient."""
        rag_service.index_patient_documents(
            patient_id=1,
            documents=[("doc_1", "Patient 1 has diabetes", {"type": "visit"})]
        )
        rag_service.index_patient_documents(
            patient_id=2,
            documents=[("doc_2", "Patient 2 has CAD", {"type": "visit"})]
        )

        context = rag_service.query_patient_context(
            patient_id=1,
            query="diabetes"
        )

        assert "diabetes" in context.lower()
        assert "CAD" not in context


class TestDocumentCount:
    """Tests for document count functionality."""

    def test_get_patient_document_count(self, rag_service):
        """Test counting patient documents."""
        documents = [
            ("doc_1", "Content 1", {"type": "visit"}),
            ("doc_2", "Content 2", {"type": "investigation"}),
            ("doc_3", "Content 3", {"type": "procedure"}),
        ]
        rag_service.index_patient_documents(patient_id=1, documents=documents)

        count = rag_service.get_patient_document_count(1)
        assert count == 3

    def test_get_patient_document_count_zero(self, rag_service):
        """Test counting documents for patient with none."""
        count = rag_service.get_patient_document_count(999)
        assert count == 0


class TestPatientIDRetrieval:
    """Tests for getting all patient IDs."""

    def test_get_all_patient_ids(self, rag_service):
        """Test getting all indexed patient IDs."""
        rag_service.index_patient_summary(1, "Patient 1")
        rag_service.index_patient_summary(2, "Patient 2")
        rag_service.index_patient_summary(3, "Patient 3")

        patient_ids = rag_service.get_all_patient_ids()

        assert len(patient_ids) == 3
        assert set(patient_ids) == {1, 2, 3}

    def test_get_all_patient_ids_empty(self, rag_service):
        """Test getting patient IDs when none indexed."""
        patient_ids = rag_service.get_all_patient_ids()
        assert patient_ids == []


class TestReindexPatient:
    """Tests for patient reindexing."""

    def test_reindex_patient(self, rag_service):
        """Test reindexing both summary and documents."""
        # Initial index
        rag_service.index_patient_summary(1, "Patient: Ram Lal")
        rag_service.index_patient_documents(
            1, [("doc_1", "Old visit", {"type": "visit"})]
        )

        # Reindex
        rag_service.reindex_patient(
            patient_id=1,
            summary="Patient: Ram Lal. Diagnoses: CAD",
            documents=[
                ("doc_2", "New visit 1", {"type": "visit"}),
                ("doc_3", "New visit 2", {"type": "visit"})
            ]
        )

        # Check summary updated
        results = rag_service.search_patients("CAD")
        assert len(results) >= 1

        # Check documents updated
        count = rag_service.get_patient_document_count(1)
        assert count == 2


class TestDocumentIDGeneration:
    """Tests for document ID generation."""

    def test_generate_doc_id_deterministic(self, rag_service):
        """Test that doc ID is deterministic."""
        id1 = rag_service._generate_doc_id(1, "visit", "Test content")
        id2 = rag_service._generate_doc_id(1, "visit", "Test content")

        assert id1 == id2

    def test_generate_doc_id_unique_for_different_content(self, rag_service):
        """Test that different content produces different IDs."""
        id1 = rag_service._generate_doc_id(1, "visit", "Content A")
        id2 = rag_service._generate_doc_id(1, "visit", "Content B")

        assert id1 != id2

    def test_generate_doc_id_unique_for_different_patient(self, rag_service):
        """Test that different patient IDs produce different doc IDs."""
        id1 = rag_service._generate_doc_id(1, "visit", "Same content")
        id2 = rag_service._generate_doc_id(2, "visit", "Same content")

        assert id1 != id2
