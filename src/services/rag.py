"""RAG service using ChromaDB for local vector storage."""

import logging
import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Tuple, Optional
import hashlib
import os

logger = logging.getLogger(__name__)


class RAGService:
    """Handles vector storage and retrieval for patient records."""

    def __init__(self, persist_directory: Optional[str] = None):
        if persist_directory is None:
            persist_directory = os.getenv("DOCASSIST_CHROMA_DIR", "data/chroma")
        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with local persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Two collections: patient summaries (for search) and patient documents (for RAG)
        self.patient_summaries = self.client.get_or_create_collection(
            name="patient_summaries",
            metadata={"description": "Patient summaries for search"}
        )

        self.patient_documents = self.client.get_or_create_collection(
            name="patient_documents",
            metadata={"description": "Patient records for RAG queries"}
        )

    def _generate_doc_id(self, patient_id: int, doc_type: str, content: str) -> str:
        """Generate unique document ID."""
        hash_input = f"{patient_id}_{doc_type}_{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    # ============== PATIENT SUMMARY OPERATIONS ==============

    def index_patient_summary(self, patient_id: int, summary: str):
        """Index or update a patient's summary for natural language search.

        Args:
            patient_id: The patient's database ID
            summary: Text summary including name, UHID, diagnoses, procedures
        """
        doc_id = f"patient_{patient_id}"

        # Check if exists and delete first (ChromaDB doesn't have upsert)
        try:
            existing = self.patient_summaries.get(ids=[doc_id])
            if existing and existing["ids"]:
                self.patient_summaries.delete(ids=[doc_id])
        except Exception as e:
            logger.warning(f"Could not check/delete existing patient summary for patient {patient_id}: {e}")

        self.patient_summaries.add(
            documents=[summary],
            ids=[doc_id],
            metadatas=[{"patient_id": patient_id}]
        )

    def search_patients(self, query: str, n_results: int = 10) -> List[Tuple[int, float, str]]:
        """Search patients using natural language.

        Args:
            query: Natural language query like "Ram Lal who had PCI to LAD"
            n_results: Maximum number of results

        Returns:
            List of (patient_id, relevance_score, summary) tuples
        """
        try:
            results = self.patient_summaries.query(
                query_texts=[query],
                n_results=n_results
            )

            output = []
            if results and results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    patient_id = results["metadatas"][0][i]["patient_id"]
                    distance = results["distances"][0][i] if results.get("distances") else 0
                    # Convert distance to similarity score (lower distance = higher similarity)
                    similarity = 1 / (1 + distance)
                    summary = results["documents"][0][i]
                    output.append((patient_id, similarity, summary))

            return output

        except Exception as e:
            logger.error(f"Patient search error: {e}")
            return []

    # ============== PATIENT DOCUMENT OPERATIONS ==============

    def index_patient_documents(self, patient_id: int, documents: List[Tuple[str, str, dict]]):
        """Index all documents for a patient.

        Args:
            patient_id: Patient's database ID
            documents: List of (doc_id, content, metadata) tuples
        """
        if not documents:
            return

        # First, remove all existing documents for this patient
        self.clear_patient_documents(patient_id)

        # Add new documents
        ids = []
        contents = []
        metadatas = []

        for doc_id, content, metadata in documents:
            ids.append(f"p{patient_id}_{doc_id}")
            contents.append(content)
            metadata["patient_id"] = patient_id
            metadatas.append(metadata)

        if ids:
            self.patient_documents.add(
                documents=contents,
                ids=ids,
                metadatas=metadatas
            )

    def clear_patient_documents(self, patient_id: int):
        """Remove all indexed documents for a patient."""
        try:
            # Get all documents for this patient
            results = self.patient_documents.get(
                where={"patient_id": patient_id}
            )
            if results and results["ids"]:
                self.patient_documents.delete(ids=results["ids"])
        except Exception as e:
            logger.error(f"Error clearing patient documents for patient {patient_id}: {e}")

    def query_patient_context(
        self,
        patient_id: int,
        query: str,
        n_results: int = 5
    ) -> str:
        """Query documents for a specific patient.

        Args:
            patient_id: Patient to query
            query: Natural language question
            n_results: Number of relevant documents to retrieve

        Returns:
            Combined context string from relevant documents
        """
        try:
            results = self.patient_documents.query(
                query_texts=[query],
                n_results=n_results,
                where={"patient_id": patient_id}
            )

            if results and results["documents"] and results["documents"][0]:
                # Combine retrieved documents into context
                context_parts = []
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    doc_type = metadata.get("type", "record")
                    date = metadata.get("date", "unknown date")
                    context_parts.append(f"[{doc_type.upper()} - {date}]\n{doc}")

                return "\n\n".join(context_parts)

            return "No relevant records found for this patient."

        except Exception as e:
            logger.error(f"RAG query error for patient {patient_id}: {e}")
            return f"Error searching records: {str(e)}"

    def get_patient_document_count(self, patient_id: int) -> int:
        """Get number of indexed documents for a patient."""
        try:
            results = self.patient_documents.get(
                where={"patient_id": patient_id}
            )
            return len(results["ids"]) if results and results["ids"] else 0
        except Exception as e:
            logger.warning(f"Could not get document count for patient {patient_id}: {e}")
            return 0

    def get_all_patient_ids(self) -> List[int]:
        """Get all patient IDs with indexed summaries."""
        try:
            results = self.patient_summaries.get()
            if results and results["metadatas"]:
                return [m["patient_id"] for m in results["metadatas"]]
            return []
        except Exception as e:
            logger.warning(f"Could not retrieve patient IDs from summaries: {e}")
            return []

    def reindex_patient(self, patient_id: int, summary: str, documents: List[Tuple[str, str, dict]]):
        """Reindex both summary and documents for a patient."""
        self.index_patient_summary(patient_id, summary)
        self.index_patient_documents(patient_id, documents)
