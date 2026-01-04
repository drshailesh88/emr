"""Tests for LLMService."""

import pytest
from unittest.mock import patch, MagicMock
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.llm import LLMService
from src.models.schemas import Prescription


class TestLLMServiceInitialization:
    """Tests for LLMService initialization."""

    @patch('src.services.llm.psutil')
    def test_model_selection_low_ram(self, mock_psutil):
        """Test model selection for < 6GB RAM."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=4 * 1024 ** 3  # 4GB
        )
        llm = LLMService()
        assert llm.model == "qwen2.5:1.5b"

    @patch('src.services.llm.psutil')
    def test_model_selection_medium_ram(self, mock_psutil):
        """Test model selection for 6-10GB RAM."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3  # 8GB
        )
        llm = LLMService()
        assert llm.model == "qwen2.5:3b"

    @patch('src.services.llm.psutil')
    def test_model_selection_high_ram(self, mock_psutil):
        """Test model selection for > 10GB RAM."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=16 * 1024 ** 3  # 16GB
        )
        llm = LLMService()
        assert llm.model == "qwen2.5:7b"

    @patch('src.services.llm.psutil')
    def test_custom_base_url(self, mock_psutil):
        """Test custom Ollama base URL."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )
        llm = LLMService(base_url="http://custom:8080")
        assert llm.base_url == "http://custom:8080"

    @patch('src.services.llm.psutil')
    def test_prompts_loaded(self, mock_psutil):
        """Test that prompts are loaded."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )
        llm = LLMService()
        assert llm.prescription_prompt is not None
        assert llm.rag_prompt is not None
        assert len(llm.prescription_prompt) > 0
        assert len(llm.rag_prompt) > 0


class TestOllamaAvailability:
    """Tests for Ollama availability checking."""

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_is_available_true(self, mock_requests, mock_psutil):
        """Test is_available returns True when Ollama is running."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        llm = LLMService()
        assert llm.is_available() is True

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_is_available_false_connection_error(self, mock_requests, mock_psutil):
        """Test is_available returns False on connection error."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )
        import requests
        mock_requests.get.side_effect = requests.RequestException("Connection refused")
        mock_requests.RequestException = requests.RequestException

        llm = LLMService()
        assert llm.is_available() is False

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_is_available_false_bad_status(self, mock_requests, mock_psutil):
        """Test is_available returns False on non-200 status."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests.get.return_value = mock_response

        llm = LLMService()
        assert llm.is_available() is False


class TestModelPulling:
    """Tests for model pulling functionality."""

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_ensure_model_pulled_ollama_not_running(self, mock_requests, mock_psutil):
        """Test ensure_model_pulled when Ollama not running."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )
        import requests
        mock_requests.get.side_effect = requests.RequestException("Connection refused")
        mock_requests.RequestException = requests.RequestException

        llm = LLMService()
        success, message = llm.ensure_model_pulled()

        assert success is False
        assert "not running" in message.lower()

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_ensure_model_pulled_model_exists(self, mock_requests, mock_psutil):
        """Test ensure_model_pulled when model already exists."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "qwen2.5:3b"}]
        }
        mock_requests.get.return_value = mock_response

        llm = LLMService()
        success, message = llm.ensure_model_pulled()

        assert success is True
        assert "ready" in message.lower()


class TestGenerate:
    """Tests for generate method."""

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_generate_ollama_not_running(self, mock_requests, mock_psutil):
        """Test generate when Ollama not running."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )
        import requests
        mock_requests.get.side_effect = requests.RequestException("Connection refused")
        mock_requests.RequestException = requests.RequestException

        llm = LLMService()
        success, response = llm.generate("Test prompt")

        assert success is False
        assert "not running" in response.lower()

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_generate_success(self, mock_requests, mock_psutil):
        """Test successful generation."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )

        # Mock is_available check
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_requests.get.return_value = mock_get_response

        # Mock generation
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"response": "Test response"}
        mock_requests.post.return_value = mock_post_response

        llm = LLMService()
        success, response = llm.generate("Test prompt")

        assert success is True
        assert response == "Test response"

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_generate_json_mode(self, mock_requests, mock_psutil):
        """Test generation with JSON mode."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_requests.get.return_value = mock_get_response

        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"response": '{"test": true}'}
        mock_requests.post.return_value = mock_post_response

        llm = LLMService()
        success, response = llm.generate("Test prompt", json_mode=True)

        assert success is True
        # Verify JSON mode was set in request
        call_args = mock_requests.post.call_args
        assert call_args[1]["json"]["format"] == "json"

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_generate_timeout(self, mock_requests, mock_psutil):
        """Test generation timeout handling."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_requests.get.return_value = mock_get_response

        import requests
        mock_requests.post.side_effect = requests.Timeout("Timed out")
        mock_requests.Timeout = requests.Timeout
        mock_requests.RequestException = requests.RequestException

        llm = LLMService()
        success, response = llm.generate("Test prompt")

        assert success is False
        assert "timed out" in response.lower()


class TestGeneratePrescription:
    """Tests for prescription generation."""

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_generate_prescription_success(self, mock_requests, mock_psutil):
        """Test successful prescription generation."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_requests.get.return_value = mock_get_response

        prescription_json = json.dumps({
            "diagnosis": ["Viral fever"],
            "medications": [{
                "drug_name": "Paracetamol",
                "strength": "500mg",
                "form": "tablet",
                "dose": "1",
                "frequency": "TDS",
                "duration": "3 days",
                "instructions": "after meals"
            }],
            "investigations": ["CBC"],
            "advice": ["Rest", "Fluids"],
            "follow_up": "3 days",
            "red_flags": ["High fever", "Rash"]
        })

        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"response": prescription_json}
        mock_requests.post.return_value = mock_post_response

        llm = LLMService()
        success, prescription, raw = llm.generate_prescription("Fever for 2 days")

        assert success is True
        assert prescription is not None
        assert isinstance(prescription, Prescription)
        assert "Viral fever" in prescription.diagnosis
        assert prescription.medications[0].drug_name == "Paracetamol"

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_generate_prescription_cleans_markdown(self, mock_requests, mock_psutil):
        """Test prescription cleans markdown code blocks."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_requests.get.return_value = mock_get_response

        prescription_json = """```json
{
    "diagnosis": ["Fever"],
    "medications": [],
    "investigations": [],
    "advice": [],
    "follow_up": "",
    "red_flags": []
}
```"""

        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"response": prescription_json}
        mock_requests.post.return_value = mock_post_response

        llm = LLMService()
        success, prescription, raw = llm.generate_prescription("Fever")

        assert success is True
        assert prescription is not None
        assert "Fever" in prescription.diagnosis

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_generate_prescription_invalid_json(self, mock_requests, mock_psutil):
        """Test handling of invalid JSON from LLM."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_requests.get.return_value = mock_get_response

        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"response": "Not valid JSON"}
        mock_requests.post.return_value = mock_post_response

        llm = LLMService()
        success, prescription, error = llm.generate_prescription("Fever")

        assert success is False
        assert prescription is None
        assert "invalid json" in error.lower()


class TestQueryPatientRecords:
    """Tests for RAG query functionality."""

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_query_patient_records_success(self, mock_requests, mock_psutil):
        """Test successful patient record query."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_requests.get.return_value = mock_get_response

        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "response": "The last creatinine was 1.4 mg/dL on 15-Dec-2024"
        }
        mock_requests.post.return_value = mock_post_response

        llm = LLMService()
        success, answer = llm.query_patient_records(
            context="Investigation on 15-Dec-2024: Creatinine = 1.4 mg/dL",
            question="What was the last creatinine?"
        )

        assert success is True
        assert "1.4" in answer

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_query_uses_rag_prompt(self, mock_requests, mock_psutil):
        """Test that query uses RAG prompt template."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_requests.get.return_value = mock_get_response

        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"response": "Answer"}
        mock_requests.post.return_value = mock_post_response

        llm = LLMService()
        llm.query_patient_records(
            context="Test context",
            question="Test question"
        )

        # Verify prompt contains context and question placeholders filled
        call_args = mock_requests.post.call_args
        prompt = call_args[1]["json"]["prompt"]
        assert "Test context" in prompt
        assert "Test question" in prompt


class TestGetModelInfo:
    """Tests for get_model_info method."""

    @patch('src.services.llm.psutil')
    @patch('src.services.llm.requests')
    def test_get_model_info(self, mock_requests, mock_psutil):
        """Test get_model_info returns correct info."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024 ** 3
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        llm = LLMService()
        info = llm.get_model_info()

        assert "model" in info
        assert "ram_gb" in info
        assert "ollama_available" in info
        assert info["model"] == "qwen2.5:3b"
        assert info["ollama_available"] is True
