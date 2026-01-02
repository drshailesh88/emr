"""Unit tests for RAG service."""

import pytest
from pathlib import Path

from src.services.rag import RAGService


class TestRAGInitialization:
    """Tests for RAG service initialization."""

    def test_rag_initialization(self, temp_rag):
        """Test RAG service initializes correctly."""
        assert temp_rag.client is not None
        assert temp_rag.patient_summaries is not None
        assert temp_rag.patient_documents is not None

    def test_persist_directory_created(self, temp_rag):
        """Test persistence directory is created."""
        assert Path(temp_rag.persist_dir).exists()

    def test_collections_created(self, temp_rag):
        """Test both collections are created."""
        collections = temp_rag.client.list_collections()
        collection_names = [c.name for c in collections]

        assert "patient_summaries" in collection_names
        assert "patient_documents" in collection_names


class TestPatientSummaryOperations:
    """Tests for patient summary indexing and search."""

    def test_index_patient_summary(self, temp_rag):
        """Test indexing a patient summary."""
        summary = "Patient: Ram Lal, Age: 65, Gender: M, UHID: EMR-2024-0001. Diagnoses: Hypertension, Diabetes."

        temp_rag.index_patient_summary(patient_id=1, summary=summary)

        # Verify it was indexed
        results = temp_rag.patient_summaries.get(ids=["patient_1"])
        assert len(results["ids"]) == 1
        assert results["documents"][0] == summary

    def test_index_patient_summary_update(self, temp_rag):
        """Test updating an existing patient summary."""
        summary1 = "Patient: John Doe, Age: 50"
        summary2 = "Patient: John Doe, Age: 51, New diagnosis: Hypertension"

        temp_rag.index_patient_summary(patient_id=1, summary=summary1)
        temp_rag.index_patient_summary(patient_id=1, summary=summary2)

        # Should have only one entry with updated content
        results = temp_rag.patient_summaries.get(ids=["patient_1"])
        assert len(results["ids"]) == 1
        assert "51" in results["documents"][0]
        assert "Hypertension" in results["documents"][0]

    def test_search_patients_single_result(self, temp_rag):
        """Test searching for patients returns correct result."""
        temp_rag.index_patient_summary(
            patient_id=1,
            summary="Patient: Ram Lal, Age: 65, M, UHID: EMR-2024-0001. Procedures: PCI to LAD."
        )
        temp_rag.index_patient_summary(
            patient_id=2,
            summary="Patient: Shyam Kumar, Age: 45, M, UHID: EMR-2024-0002. Diagnoses: Diabetes."
        )

        results = temp_rag.search_patients("patient who had PCI", n_results=5)

        assert len(results) > 0
        # First result should be Ram Lal (has PCI)
        assert results[0][0] == 1  # patient_id
        assert results[0][1] > 0  # similarity score

    def test_search_patients_multiple_results(self, temp_rag):
        """Test searching returns multiple relevant results."""
        temp_rag.index_patient_summary(
            patient_id=1,
            summary="Patient: Ram Lal, M, 65. Diabetes, Hypertension."
        )
        temp_rag.index_patient_summary(
            patient_id=2,
            summary="Patient: Sita Devi, F, 60. Diabetes, Chronic Kidney Disease."
        )
        temp_rag.index_patient_summary(
            patient_id=3,
            summary="Patient: Mohan Singh, M, 55. Hypertension only."
        )

        results = temp_rag.search_patients("diabetic patients", n_results=5)

        assert len(results) >= 2
        # Both patients with diabetes should be in results
        patient_ids = [r[0] for r in results]
        assert 1 in patient_ids
        assert 2 in patient_ids

    def test_search_patients_no_results(self, temp_rag):
        """Test searching with no matches."""
        temp_rag.index_patient_summary(
            patient_id=1,
            summary="Patient: Ram Lal, Diabetes."
        )

        results = temp_rag.search_patients("patient with cancer treatment", n_results=5)

        # Should still return results (semantic search), but with lower scores
        # Or could be empty if nothing remotely matches
        assert isinstance(results, list)

    def test_search_patients_limit_results(self, temp_rag):
        """Test limiting search results."""
        # Index 5 patients
        for i in range(5):
            temp_rag.index_patient_summary(
                patient_id=i + 1,
                summary=f"Patient: Patient {i}, Diabetes."
            )

        results = temp_rag.search_patients("diabetes", n_results=3)

        assert len(results) <= 3

    def test_search_patients_empty_collection(self, temp_rag):
        """Test searching empty collection."""
        results = temp_rag.search_patients("any query", n_results=5)
        assert results == []


class TestPatientDocumentOperations:
    """Tests for patient document indexing and querying."""

    def test_index_patient_documents(self, temp_rag):
        """Test indexing patient documents."""
        documents = [
            ("visit_1", "Visit on 2024-01-10: Chief complaint: Fever. Diagnosis: Viral fever.",
             {"type": "visit", "date": "2024-01-10"}),
            ("investigation_1", "Investigation on 2024-01-10: CBC - Normal",
             {"type": "investigation", "date": "2024-01-10"}),
        ]

        temp_rag.index_patient_documents(patient_id=1, documents=documents)

        # Verify documents were indexed
        count = temp_rag.get_patient_document_count(patient_id=1)
        assert count == 2

    def test_index_documents_replaces_existing(self, temp_rag):
        """Test that reindexing replaces existing documents."""
        docs1 = [
            ("visit_1", "Old visit", {"type": "visit", "date": "2024-01-01"}),
        ]
        docs2 = [
            ("visit_2", "New visit", {"type": "visit", "date": "2024-01-15"}),
        ]

        temp_rag.index_patient_documents(patient_id=1, documents=docs1)
        temp_rag.index_patient_documents(patient_id=1, documents=docs2)

        # Should only have documents from docs2
        count = temp_rag.get_patient_document_count(patient_id=1)
        assert count == 1

    def test_clear_patient_documents(self, temp_rag):
        """Test clearing all documents for a patient."""
        documents = [
            ("visit_1", "Visit 1", {"type": "visit", "date": "2024-01-01"}),
            ("visit_2", "Visit 2", {"type": "visit", "date": "2024-01-02"}),
        ]

        temp_rag.index_patient_documents(patient_id=1, documents=documents)
        assert temp_rag.get_patient_document_count(patient_id=1) == 2

        temp_rag.clear_patient_documents(patient_id=1)
        assert temp_rag.get_patient_document_count(patient_id=1) == 0

    def test_query_patient_context(self, temp_rag):
        """Test querying patient documents for context."""
        documents = [
            ("visit_1", "Visit on 2024-01-10: Chief complaint: Chest pain. Diagnosis: Angina.",
             {"type": "visit", "date": "2024-01-10"}),
            ("investigation_1", "Investigation on 2024-01-10: Troponin = Negative",
             {"type": "investigation", "date": "2024-01-10", "test_name": "Troponin"}),
            ("visit_2", "Visit on 2024-01-05: Routine checkup. BP normal.",
             {"type": "visit", "date": "2024-01-05"}),
        ]

        temp_rag.index_patient_documents(patient_id=1, documents=documents)

        context = temp_rag.query_patient_context(
            patient_id=1,
            query="What was the troponin result?",
            n_results=3
        )

        assert context != ""
        assert "Troponin" in context or "troponin" in context.lower()

    def test_query_patient_context_formats_with_metadata(self, temp_rag):
        """Test that query context includes metadata formatting."""
        documents = [
            ("visit_1", "Visit notes here",
             {"type": "visit", "date": "2024-01-10"}),
        ]

        temp_rag.index_patient_documents(patient_id=1, documents=documents)

        context = temp_rag.query_patient_context(
            patient_id=1,
            query="visit notes",
            n_results=1
        )

        # Should include type and date in formatting
        assert "VISIT" in context.upper()
        assert "2024-01-10" in context

    def test_query_patient_context_no_results(self, temp_rag):
        """Test querying with no indexed documents."""
        context = temp_rag.query_patient_context(
            patient_id=999,
            query="any question",
            n_results=5
        )

        assert "No relevant records" in context

    def test_query_patient_context_filters_by_patient(self, temp_rag):
        """Test that query only returns documents for the specified patient."""
        # Index documents for patient 1
        docs1 = [
            ("visit_1", "Patient 1 has diabetes", {"type": "visit", "date": "2024-01-10"}),
        ]
        # Index documents for patient 2
        docs2 = [
            ("visit_1", "Patient 2 has hypertension", {"type": "visit", "date": "2024-01-10"}),
        ]

        temp_rag.index_patient_documents(patient_id=1, documents=docs1)
        temp_rag.index_patient_documents(patient_id=2, documents=docs2)

        # Query patient 1
        context = temp_rag.query_patient_context(
            patient_id=1,
            query="medical conditions",
            n_results=5
        )

        # Should only include patient 1's documents
        assert "diabetes" in context.lower()
        assert "hypertension" not in context.lower()

    def test_get_patient_document_count(self, temp_rag):
        """Test getting document count for a patient."""
        documents = [
            ("visit_1", "Visit 1", {"type": "visit", "date": "2024-01-01"}),
            ("visit_2", "Visit 2", {"type": "visit", "date": "2024-01-02"}),
            ("inv_1", "Investigation 1", {"type": "investigation", "date": "2024-01-01"}),
        ]

        temp_rag.index_patient_documents(patient_id=1, documents=documents)

        count = temp_rag.get_patient_document_count(patient_id=1)
        assert count == 3

    def test_get_patient_document_count_zero(self, temp_rag):
        """Test document count for patient with no documents."""
        count = temp_rag.get_patient_document_count(patient_id=999)
        assert count == 0


class TestRAGHelperMethods:
    """Tests for RAG helper methods."""

    def test_get_all_patient_ids(self, temp_rag):
        """Test getting all indexed patient IDs."""
        temp_rag.index_patient_summary(1, "Patient 1")
        temp_rag.index_patient_summary(2, "Patient 2")
        temp_rag.index_patient_summary(3, "Patient 3")

        patient_ids = temp_rag.get_all_patient_ids()

        assert len(patient_ids) == 3
        assert set(patient_ids) == {1, 2, 3}

    def test_get_all_patient_ids_empty(self, temp_rag):
        """Test getting patient IDs from empty collection."""
        patient_ids = temp_rag.get_all_patient_ids()
        assert patient_ids == []

    def test_reindex_patient(self, temp_rag):
        """Test reindexing both summary and documents."""
        summary = "Patient: Ram Lal, 65, M. Diabetes."
        documents = [
            ("visit_1", "Visit 1", {"type": "visit", "date": "2024-01-01"}),
            ("visit_2", "Visit 2", {"type": "visit", "date": "2024-01-02"}),
        ]

        temp_rag.reindex_patient(patient_id=1, summary=summary, documents=documents)

        # Check summary was indexed
        summary_results = temp_rag.search_patients("Ram Lal", n_results=1)
        assert len(summary_results) > 0
        assert summary_results[0][0] == 1

        # Check documents were indexed
        doc_count = temp_rag.get_patient_document_count(patient_id=1)
        assert doc_count == 2

    def test_reindex_patient_updates_existing(self, temp_rag):
        """Test that reindexing updates existing data."""
        # First index
        temp_rag.reindex_patient(
            patient_id=1,
            summary="Old summary",
            documents=[("visit_1", "Old visit", {"type": "visit", "date": "2024-01-01"})]
        )

        # Reindex with new data
        temp_rag.reindex_patient(
            patient_id=1,
            summary="New summary with updated info",
            documents=[
                ("visit_2", "New visit", {"type": "visit", "date": "2024-01-15"}),
                ("visit_3", "Another visit", {"type": "visit", "date": "2024-01-16"}),
            ]
        )

        # Check updated summary
        summary_results = temp_rag.patient_summaries.get(ids=["patient_1"])
        assert "updated info" in summary_results["documents"][0]

        # Check updated documents
        doc_count = temp_rag.get_patient_document_count(patient_id=1)
        assert doc_count == 2


class TestDocumentIDGeneration:
    """Tests for document ID generation."""

    def test_generate_doc_id(self, temp_rag):
        """Test document ID generation."""
        doc_id = temp_rag._generate_doc_id(
            patient_id=1,
            doc_type="visit",
            content="Test content"
        )

        assert doc_id is not None
        assert len(doc_id) == 16  # MD5 hash truncated to 16 chars
        assert isinstance(doc_id, str)

    def test_generate_doc_id_consistent(self, temp_rag):
        """Test that same input generates same ID."""
        doc_id1 = temp_rag._generate_doc_id(1, "visit", "Test content")
        doc_id2 = temp_rag._generate_doc_id(1, "visit", "Test content")

        assert doc_id1 == doc_id2

    def test_generate_doc_id_different_inputs(self, temp_rag):
        """Test that different inputs generate different IDs."""
        doc_id1 = temp_rag._generate_doc_id(1, "visit", "Content 1")
        doc_id2 = temp_rag._generate_doc_id(1, "visit", "Content 2")
        doc_id3 = temp_rag._generate_doc_id(2, "visit", "Content 1")

        assert doc_id1 != doc_id2
        assert doc_id1 != doc_id3
        assert doc_id2 != doc_id3


class TestRAGIntegrationWithRealData:
    """Integration-style tests with realistic data."""

    def test_full_patient_workflow(self, temp_rag):
        """Test complete workflow of indexing and querying patient data."""
        # Index patient summary
        summary = """Patient: Ram Lal, Age: 65, Gender: M, UHID: EMR-2024-0001.
        Diagnoses: Type 2 Diabetes Mellitus, Hypertension, Chronic Kidney Disease.
        Procedures: PCI to LAD (2023-12-15)."""

        temp_rag.index_patient_summary(patient_id=1, summary=summary)

        # Index patient documents
        documents = [
            ("visit_1",
             "Visit on 2024-01-15: Chief complaint: Chest pain. Diagnosis: Stable angina. Medications: Aspirin, Atorvastatin.",
             {"type": "visit", "date": "2024-01-15"}),
            ("investigation_1",
             "Investigation on 2024-01-10: Creatinine = 1.8 mg/dL (ABNORMAL)",
             {"type": "investigation", "date": "2024-01-10", "test_name": "Creatinine"}),
            ("investigation_2",
             "Investigation on 2024-01-10: HbA1c = 7.2 %",
             {"type": "investigation", "date": "2024-01-10", "test_name": "HbA1c"}),
            ("procedure_1",
             "Procedure on 2023-12-15: PCI to LAD. Details: Drug-eluting stent placed successfully.",
             {"type": "procedure", "date": "2023-12-15"}),
        ]

        temp_rag.index_patient_documents(patient_id=1, documents=documents)

        # Test search
        search_results = temp_rag.search_patients("patient with PCI and diabetes", n_results=5)
        assert len(search_results) > 0
        assert search_results[0][0] == 1

        # Test query
        context = temp_rag.query_patient_context(
            patient_id=1,
            query="What was the HbA1c level?",
            n_results=3
        )
        assert "HbA1c" in context or "hba1c" in context.lower()
        assert "7.2" in context

        # Test document count
        count = temp_rag.get_patient_document_count(patient_id=1)
        assert count == 4
