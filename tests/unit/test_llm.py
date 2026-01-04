"""Unit tests for LLM service."""

import pytest
import json
from unittest.mock import Mock, patch

from src.services.llm import LLMService
from src.models.schemas import Prescription


class TestModelSelection:
    """Tests for RAM-based model selection."""

    def test_model_selection_low_ram(self):
        """Test model selection with < 6GB RAM."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=4 * 1024**3)  # 4GB

            with patch('requests.get') as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                llm = LLMService()

            assert llm.model == "qwen2.5:1.5b"

    def test_model_selection_medium_ram(self):
        """Test model selection with 6-10GB RAM."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)  # 8GB

            with patch('requests.get') as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                llm = LLMService()

            assert llm.model == "qwen2.5:3b"

    def test_model_selection_high_ram(self):
        """Test model selection with > 10GB RAM."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=16 * 1024**3)  # 16GB

            with patch('requests.get') as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                llm = LLMService()

            assert llm.model == "qwen2.5:7b"

    def test_get_available_ram_gb(self):
        """Test RAM calculation."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                llm = LLMService()

            ram_gb = llm._get_available_ram_gb()
            assert 7.9 < ram_gb < 8.1  # Allow small floating point variance


class TestOllamaAvailability:
    """Tests for checking Ollama availability."""

    def test_is_available_success(self):
        """Test Ollama is detected as available."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"models": []}
                mock_get.return_value = mock_response

                llm = LLMService()
                assert llm.is_available() is True

    def test_is_available_failure(self):
        """Test Ollama is detected as unavailable."""
        import requests

        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                llm = LLMService()

                # Now make it unavailable
                mock_get.side_effect = requests.RequestException("Connection refused")
                assert llm.is_available() is False

    def test_is_available_timeout(self):
        """Test Ollama check with timeout."""
        import requests

        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                llm = LLMService()

                mock_get.side_effect = requests.Timeout("Timeout")
                assert llm.is_available() is False


class TestModelPulling:
    """Tests for ensuring model is pulled."""

    def test_ensure_model_pulled_already_exists(self):
        """Test when model already exists."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "models": [{"name": "qwen2.5:3b"}]
                }
                mock_get.return_value = mock_response

                llm = LLMService()
                success, message = llm.ensure_model_pulled()

                assert success is True
                assert "ready" in message.lower()

    def test_ensure_model_pulled_needs_download(self):
        """Test when model needs to be downloaded."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get, \
                 patch('requests.post') as mock_post:

                # First call - no models
                mock_get_response = Mock()
                mock_get_response.status_code = 200
                mock_get_response.json.return_value = {"models": []}
                mock_get.return_value = mock_get_response

                # Pull successful
                mock_post_response = Mock()
                mock_post_response.status_code = 200
                mock_post.return_value = mock_post_response

                llm = LLMService()
                success, message = llm.ensure_model_pulled()

                assert success is True
                assert "downloaded" in message.lower() or "ready" in message.lower()

    def test_ensure_model_pulled_ollama_not_running(self):
        """Test when Ollama is not running."""
        import requests

        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                llm = LLMService()

                # Make Ollama unavailable
                mock_get.side_effect = requests.RequestException("Connection refused")

                success, message = llm.ensure_model_pulled()
                assert success is False
                assert "not running" in message.lower()


class TestGeneration:
    """Tests for text generation."""

    def test_generate_success(self):
        """Test successful generation."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get, \
                 patch('requests.post') as mock_post:

                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})

                mock_post_response = Mock()
                mock_post_response.status_code = 200
                mock_post_response.json.return_value = {
                    "response": "This is a test response."
                }
                mock_post.return_value = mock_post_response

                llm = LLMService()
                success, response = llm.generate("Test prompt")

                assert success is True
                assert response == "This is a test response."

    def test_generate_json_mode(self):
        """Test generation with JSON mode."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get, \
                 patch('requests.post') as mock_post:

                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})

                mock_post_response = Mock()
                mock_post_response.status_code = 200
                mock_post_response.json.return_value = {
                    "response": '{"key": "value"}'
                }
                mock_post.return_value = mock_post_response

                llm = LLMService()
                success, response = llm.generate("Test prompt", json_mode=True)

                assert success is True
                # Check that json_mode was passed
                assert mock_post.called
                call_args = mock_post.call_args
                assert call_args[1]['json']['format'] == 'json'

    def test_generate_ollama_not_available(self):
        """Test generation when Ollama is not available."""
        import requests

        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get:
                mock_get.side_effect = requests.RequestException("Connection refused")
                llm = LLMService()

                success, response = llm.generate("Test prompt")
                assert success is False
                assert "not running" in response.lower()

    def test_generate_timeout(self):
        """Test generation with timeout."""
        import requests

        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get, \
                 patch('requests.post') as mock_post:

                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                mock_post.side_effect = requests.Timeout("Request timed out")

                llm = LLMService()
                success, response = llm.generate("Test prompt")

                assert success is False
                assert "timed out" in response.lower()


class TestPrescriptionGeneration:
    """Tests for prescription generation."""

    def test_generate_prescription_success(self, mock_prescription_response):
        """Test successful prescription generation."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get, \
                 patch('requests.post') as mock_post:

                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})

                mock_post_response = Mock()
                mock_post_response.status_code = 200
                mock_post_response.json.return_value = {
                    "response": json.dumps(mock_prescription_response)
                }
                mock_post.return_value = mock_post_response

                llm = LLMService()
                success, prescription, raw_json = llm.generate_prescription(
                    "Patient with fever and loose stools"
                )

                assert success is True
                assert prescription is not None
                assert isinstance(prescription, Prescription)
                assert len(prescription.medications) == 2
                assert prescription.diagnosis == ["Acute Gastroenteritis"]

    def test_generate_prescription_with_markdown(self, mock_prescription_response):
        """Test prescription generation with markdown code blocks."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get, \
                 patch('requests.post') as mock_post:

                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})

                # Response wrapped in markdown
                markdown_json = f"```json\n{json.dumps(mock_prescription_response)}\n```"

                mock_post_response = Mock()
                mock_post_response.status_code = 200
                mock_post_response.json.return_value = {
                    "response": markdown_json
                }
                mock_post.return_value = mock_post_response

                llm = LLMService()
                success, prescription, raw_json = llm.generate_prescription("Test notes")

                assert success is True
                assert prescription is not None
                assert len(prescription.medications) == 2

    def test_generate_prescription_invalid_json(self):
        """Test prescription generation with invalid JSON."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get, \
                 patch('requests.post') as mock_post:

                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})

                mock_post_response = Mock()
                mock_post_response.status_code = 200
                mock_post_response.json.return_value = {
                    "response": "This is not valid JSON"
                }
                mock_post.return_value = mock_post_response

                llm = LLMService()
                success, prescription, error = llm.generate_prescription("Test notes")

                assert success is False
                assert prescription is None
                assert "Invalid JSON" in error

    def test_generate_prescription_ollama_error(self):
        """Test prescription generation when Ollama returns error."""
        import requests

        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get, \
                 patch('requests.post') as mock_post:

                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                mock_post.side_effect = requests.RequestException("Connection error")

                llm = LLMService()
                success, prescription, error = llm.generate_prescription("Test notes")

                assert success is False
                assert prescription is None


class TestRAGQueries:
    """Tests for RAG query answering."""

    def test_query_patient_records_success(self, mock_rag_context):
        """Test successful RAG query."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get, \
                 patch('requests.post') as mock_post:

                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})

                mock_post_response = Mock()
                mock_post_response.status_code = 200
                mock_post_response.json.return_value = {
                    "response": "The last creatinine level was 1.4 mg/dL on 2024-01-10, which is slightly elevated."
                }
                mock_post.return_value = mock_post_response

                llm = LLMService()
                success, answer = llm.query_patient_records(
                    mock_rag_context,
                    "What was the last creatinine level?"
                )

                assert success is True
                assert "1.4" in answer
                assert "2024-01-10" in answer

    def test_query_patient_records_formats_prompt(self, mock_rag_context):
        """Test that RAG query formats the prompt correctly."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get, \
                 patch('requests.post') as mock_post:

                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})

                mock_post_response = Mock()
                mock_post_response.status_code = 200
                mock_post_response.json.return_value = {"response": "Answer"}
                mock_post.return_value = mock_post_response

                llm = LLMService()
                llm.query_patient_records(mock_rag_context, "Test question")

                # Check that the prompt was formatted with context and question
                call_args = mock_post.call_args
                prompt = call_args[1]['json']['prompt']
                assert "Test question" in prompt
                assert mock_rag_context in prompt


class TestModelInfo:
    """Tests for model information."""

    def test_get_model_info(self):
        """Test getting model information."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                llm = LLMService()

                info = llm.get_model_info()

                assert "model" in info
                assert "ram_gb" in info
                assert "ollama_available" in info
                assert info["model"] == "qwen2.5:3b"
                assert info["ram_gb"] > 0


class TestPromptLoading:
    """Tests for prompt template loading."""

    def test_default_prescription_prompt(self):
        """Test default prescription prompt is loaded."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                llm = LLMService()

                assert llm.prescription_prompt is not None
                assert "prescription" in llm.prescription_prompt.lower()
                assert "json" in llm.prescription_prompt.lower()

    def test_default_rag_prompt(self):
        """Test default RAG prompt is loaded."""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(total=8 * 1024**3)

            with patch('requests.get') as mock_get:
                mock_get.return_value = Mock(status_code=200, json=lambda: {"models": []})
                llm = LLMService()

                assert llm.rag_prompt is not None
                assert "{context}" in llm.rag_prompt
                assert "{question}" in llm.rag_prompt
