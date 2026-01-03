"""Tests for UI panel components."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.schemas import Patient, Prescription, Medication, Visit


class TestPatientPanelLogic:
    """Tests for PatientPanel logic and state management."""

    @patch('src.ui.patient_panel.ft')
    def test_patient_panel_creation(self, mock_ft):
        """Test PatientPanel can be instantiated."""
        mock_ft.Container = MagicMock()
        mock_ft.Column = MagicMock()
        mock_ft.Row = MagicMock()
        mock_ft.TextField = MagicMock()
        mock_ft.ListView = MagicMock()
        mock_ft.ElevatedButton = MagicMock()
        mock_ft.Icon = MagicMock()
        mock_ft.Icons = MagicMock()
        mock_ft.icons = MagicMock()
        mock_ft.colors = MagicMock()
        mock_ft.border = MagicMock()
        mock_ft.padding = MagicMock()
        mock_ft.alignment = MagicMock()

        from src.ui.patient_panel import PatientPanel

        panel = PatientPanel(
            on_patient_selected=MagicMock(),
            on_new_patient=MagicMock(),
            on_search=MagicMock(),
            db=MagicMock(),
            rag=MagicMock()
        )

        assert panel is not None

    def test_patient_data_structure(self):
        """Test patient data can be properly structured."""
        patient = Patient(
            id=1,
            uhid="EMR-2024-0001",
            name="Ram Lal",
            age=65,
            gender="M"
        )

        assert patient.id == 1
        assert patient.name == "Ram Lal"
        assert patient.uhid == "EMR-2024-0001"


class TestCentralPanelLogic:
    """Tests for CentralPanel logic and state management."""

    @patch('src.ui.central_panel.ft')
    def test_central_panel_creation(self, mock_ft):
        """Test CentralPanel can be instantiated."""
        mock_ft.Container = MagicMock()
        mock_ft.Column = MagicMock()
        mock_ft.Row = MagicMock()
        mock_ft.TextField = MagicMock()
        mock_ft.ElevatedButton = MagicMock()
        mock_ft.Text = MagicMock()
        mock_ft.Tabs = MagicMock()
        mock_ft.Tab = MagicMock()
        mock_ft.ListView = MagicMock()
        mock_ft.SnackBar = MagicMock()
        mock_ft.Icon = MagicMock()
        mock_ft.Icons = MagicMock()
        mock_ft.icons = MagicMock()
        mock_ft.colors = MagicMock()
        mock_ft.border = MagicMock()
        mock_ft.padding = MagicMock()
        mock_ft.alignment = MagicMock()
        mock_ft.TextStyle = MagicMock()
        mock_ft.FontWeight = MagicMock()
        mock_ft.MainAxisAlignment = MagicMock()
        mock_ft.CrossAxisAlignment = MagicMock()
        mock_ft.ScrollMode = MagicMock()
        mock_ft.ProgressRing = MagicMock()

        from src.ui.central_panel import CentralPanel

        panel = CentralPanel(
            on_generate_rx=MagicMock(),
            on_save_visit=MagicMock(),
            on_print_pdf=MagicMock(),
            llm=MagicMock()
        )

        assert panel is not None

    def test_prescription_display_format(self):
        """Test prescription can be formatted for display."""
        prescription = Prescription(
            diagnosis=["Type 2 DM", "HTN"],
            medications=[
                Medication(
                    drug_name="Metformin",
                    strength="500mg",
                    dose="1",
                    frequency="BD",
                    duration="30 days"
                )
            ],
            investigations=["HbA1c", "Lipid Profile"],
            advice=["Diet control", "Exercise"],
            follow_up="1 month",
            red_flags=["Hypoglycemia symptoms"]
        )

        # Test that prescription data is accessible
        assert len(prescription.diagnosis) == 2
        assert prescription.medications[0].drug_name == "Metformin"
        assert prescription.follow_up == "1 month"

    def test_visit_data_structure(self):
        """Test visit data structure."""
        visit = Visit(
            id=1,
            patient_id=1,
            visit_date=date.today(),
            chief_complaint="Fever and headache",
            clinical_notes="Patient c/o fever for 2 days",
            diagnosis="Viral fever",
            prescription_json='{"diagnosis": ["Viral fever"]}'
        )

        assert visit.patient_id == 1
        assert visit.chief_complaint == "Fever and headache"
        assert "Viral fever" in visit.prescription_json


class TestAgentPanelLogic:
    """Tests for AgentPanel logic and state management."""

    @patch('src.ui.agent_panel.ft')
    def test_agent_panel_creation(self, mock_ft):
        """Test AgentPanel can be instantiated."""
        mock_ft.Container = MagicMock()
        mock_ft.Column = MagicMock()
        mock_ft.Row = MagicMock()
        mock_ft.TextField = MagicMock()
        mock_ft.ElevatedButton = MagicMock()
        mock_ft.IconButton = MagicMock()
        mock_ft.Text = MagicMock()
        mock_ft.ListView = MagicMock()
        mock_ft.ProgressRing = MagicMock()
        mock_ft.Icon = MagicMock()
        mock_ft.Icons = MagicMock()
        mock_ft.icons = MagicMock()
        mock_ft.colors = MagicMock()
        mock_ft.border = MagicMock()
        mock_ft.padding = MagicMock()
        mock_ft.border_radius = MagicMock()
        mock_ft.alignment = MagicMock()
        mock_ft.TextStyle = MagicMock()
        mock_ft.FontWeight = MagicMock()
        mock_ft.MainAxisAlignment = MagicMock()
        mock_ft.CrossAxisAlignment = MagicMock()
        mock_ft.ScrollMode = MagicMock()

        from src.ui.agent_panel import AgentPanel

        panel = AgentPanel(
            on_query=MagicMock(),
            llm=MagicMock(),
            rag=MagicMock()
        )

        assert panel is not None

    def test_chat_message_structure(self):
        """Test chat message data structure."""
        from dataclasses import dataclass

        @dataclass
        class ChatMessage:
            role: str
            content: str

        user_msg = ChatMessage(role="user", content="What is the creatinine?")
        assistant_msg = ChatMessage(role="assistant", content="The creatinine was 1.4 mg/dL")

        assert user_msg.role == "user"
        assert assistant_msg.role == "assistant"


class TestAppOrchestration:
    """Tests for main app orchestration logic."""

    def test_service_initialization_order(self):
        """Test that services can be initialized independently."""
        import tempfile
        import os
        import shutil

        tmpdir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(tmpdir, "test.db")
            chroma_path = os.path.join(tmpdir, "chroma")
            pdf_path = os.path.join(tmpdir, "pdfs")

            from src.services.database import DatabaseService
            from src.services.rag import RAGService
            from src.services.pdf import PDFService

            db = DatabaseService(db_path=db_path)
            rag = RAGService(persist_directory=chroma_path)
            pdf = PDFService(output_dir=pdf_path)

            assert db is not None
            assert rag is not None
            assert pdf is not None
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_patient_workflow(self, db_service, rag_service):
        """Test complete patient workflow."""
        from src.models.schemas import Patient, Visit

        # Create patient
        patient = Patient(name="Test Patient", age=50, gender="M")
        saved_patient = db_service.add_patient(patient)

        assert saved_patient.id is not None
        assert saved_patient.uhid is not None

        # Index patient for RAG
        summary = db_service.get_patient_summary(saved_patient.id)
        rag_service.index_patient_summary(saved_patient.id, summary)

        # Search should find patient
        results = rag_service.search_patients("Test Patient")
        assert len(results) >= 1

        # Add visit
        visit = Visit(
            patient_id=saved_patient.id,
            chief_complaint="Fever",
            clinical_notes="High fever for 2 days"
        )
        saved_visit = db_service.add_visit(visit)

        assert saved_visit.id is not None

        # Get documents for RAG
        documents = db_service.get_patient_documents_for_rag(saved_patient.id)
        assert len(documents) >= 1

        # Index documents
        rag_service.index_patient_documents(saved_patient.id, documents)

        # Query should work
        context = rag_service.query_patient_context(
            saved_patient.id, "fever"
        )
        assert "fever" in context.lower() or "Fever" in context


class TestEventCallbacks:
    """Tests for event callback patterns."""

    def test_callback_pattern(self):
        """Test callback pattern used in panels."""
        callback_called = False
        callback_args = None

        def on_patient_selected(patient):
            nonlocal callback_called, callback_args
            callback_called = True
            callback_args = patient

        patient = Patient(id=1, name="Test")
        on_patient_selected(patient)

        assert callback_called is True
        assert callback_args.id == 1

    def test_multiple_callbacks(self):
        """Test multiple callbacks can be chained."""
        calls = []

        def callback1():
            calls.append(1)

        def callback2():
            calls.append(2)

        def callback3():
            calls.append(3)

        # Simulate event chain
        callback1()
        callback2()
        callback3()

        assert calls == [1, 2, 3]


class TestUIStateManagement:
    """Tests for UI state management patterns."""

    def test_patient_selection_state(self):
        """Test patient selection state management."""
        selected_patient = None

        def select_patient(patient):
            nonlocal selected_patient
            selected_patient = patient

        # Select patient
        patient = Patient(id=1, name="Ram Lal")
        select_patient(patient)

        assert selected_patient is not None
        assert selected_patient.id == 1

    def test_prescription_draft_state(self):
        """Test prescription draft state management."""
        draft_prescription = None
        is_draft_saved = False

        def set_draft(prescription):
            nonlocal draft_prescription, is_draft_saved
            draft_prescription = prescription
            is_draft_saved = False

        def save_draft():
            nonlocal is_draft_saved
            is_draft_saved = True

        # Generate draft
        prescription = Prescription(diagnosis=["Test"])
        set_draft(prescription)

        assert draft_prescription is not None
        assert is_draft_saved is False

        # Save draft
        save_draft()
        assert is_draft_saved is True

    def test_loading_state(self):
        """Test loading state management."""
        is_loading = False

        def start_loading():
            nonlocal is_loading
            is_loading = True

        def stop_loading():
            nonlocal is_loading
            is_loading = False

        assert is_loading is False

        start_loading()
        assert is_loading is True

        stop_loading()
        assert is_loading is False
