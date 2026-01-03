"""Local LLM service via Ollama with RAM-based model selection."""

import logging
import json
import os
import requests
import psutil
from typing import Optional, Tuple
from pathlib import Path

from ..models.schemas import Prescription

logger = logging.getLogger(__name__)


class LLMService:
    """Handles all LLM operations via Ollama."""

    # RAM thresholds for model selection (in GB)
    MODEL_TIERS = [
        (6, "qwen2.5:1.5b"),   # < 6GB RAM
        (10, "qwen2.5:3b"),    # 6-10GB RAM
        (float("inf"), "qwen2.5:7b"),  # > 10GB RAM
    ]

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        """Initialize LLM service.

        Args:
            base_url: Ollama API base URL (defaults to env var or localhost:11434)
            model: Model name to use (if None, auto-selects based on RAM)
        """
        if base_url is None:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.base_url = base_url

        # Allow model override for testing
        if model is not None:
            self.model = model
        else:
            self.model = self._select_model()

        self._load_prompts()

    @classmethod
    def for_testing(cls, model: str = "qwen2.5:1.5b", base_url: str = "http://localhost:11434"):
        """Create an LLM service instance for testing.

        Args:
            model: Model name to use (defaults to smallest model)
            base_url: Ollama API base URL

        Returns:
            LLMService instance configured for testing
        """
        return cls(base_url=base_url, model=model)

    def _get_available_ram_gb(self) -> float:
        """Get available system RAM in GB.

        This method is extracted for easy mocking in tests.
        """
        mem = psutil.virtual_memory()
        return mem.total / (1024 ** 3)

    def _select_model(self) -> str:
        """Select appropriate model based on available RAM."""
        ram_gb = self._get_available_ram_gb()
        for threshold, model in self.MODEL_TIERS:
            if ram_gb < threshold:
                logger.info(f"System RAM: {ram_gb:.1f}GB - Selected model: {model}")
                return model
        return self.MODEL_TIERS[-1][1]

    def _load_prompts(self):
        """Load prompt templates."""
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"

        # Prescription prompt
        rx_prompt_path = prompts_dir / "prescription.txt"
        if rx_prompt_path.exists():
            self.prescription_prompt = rx_prompt_path.read_text()
        else:
            self.prescription_prompt = self._default_prescription_prompt()

        # RAG query prompt
        rag_prompt_path = prompts_dir / "rag_query.txt"
        if rag_prompt_path.exists():
            self.rag_prompt = rag_prompt_path.read_text()
        else:
            self.rag_prompt = self._default_rag_prompt()

    def _default_prescription_prompt(self) -> str:
        return """You are a medical prescription assistant for Indian doctors.

Your ONLY job is to convert clinical notes into a structured JSON prescription.

RULES:
1. Output ONLY valid JSON. No explanations. No markdown. No code blocks.
2. Use generic drug names when possible, but Indian brand names are acceptable.
3. Include standard Indian dosing conventions.
4. If information is missing, make reasonable clinical assumptions.
5. Always include red flags for the condition.

The JSON must follow this EXACT schema:
{
  "diagnosis": ["string"],
  "medications": [
    {
      "drug_name": "string",
      "strength": "string with unit",
      "form": "tablet|capsule|syrup|injection|cream|drops",
      "dose": "string",
      "frequency": "OD|BD|TDS|QID|HS|SOS|stat",
      "duration": "string",
      "instructions": "string"
    }
  ],
  "investigations": ["string"],
  "advice": ["string"],
  "follow_up": "string",
  "red_flags": ["string"]
}

If the clinical notes are in Hinglish, translate to English for the prescription.

Clinical Notes:
"""

    def _default_rag_prompt(self) -> str:
        return """You are a medical assistant helping a doctor query patient records.

Based on the following patient records, answer the doctor's question accurately and concisely.
If the information is not available in the records, say so clearly.
Always mention the date when providing clinical information.

PATIENT RECORDS:
{context}

DOCTOR'S QUESTION: {question}

ANSWER (be concise and clinical):"""

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def ensure_model_pulled(self) -> Tuple[bool, str]:
        """Ensure the selected model is available locally."""
        if not self.is_available():
            return False, "Ollama is not running. Please start Ollama first."

        try:
            # Check if model exists
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if self.model in model_names or any(self.model in n for n in model_names):
                    return True, f"Model {self.model} is ready."

            # Pull the model if not exists
            logger.info(f"Pulling model {self.model}... This may take a few minutes.")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                timeout=600  # 10 minutes for download
            )
            if response.status_code == 200:
                return True, f"Model {self.model} downloaded successfully."
            return False, f"Failed to pull model: {response.text}"

        except requests.RequestException as e:
            return False, f"Error checking/pulling model: {str(e)}"

    def generate(self, prompt: str, json_mode: bool = False) -> Tuple[bool, str]:
        """Generate response from LLM.

        Args:
            prompt: The prompt to send
            json_mode: If True, expect JSON output

        Returns:
            (success, response_or_error)
        """
        if not self.is_available():
            return False, "Ollama is not running. Please start Ollama."

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
            if json_mode:
                payload["format"] = "json"

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # 2 minutes
            )

            if response.status_code == 200:
                result = response.json()
                return True, result.get("response", "")
            return False, f"API error: {response.status_code}"

        except requests.Timeout:
            return False, "Request timed out. Try again."
        except requests.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def generate_prescription(self, clinical_notes: str) -> Tuple[bool, Optional[Prescription], str]:
        """Generate structured prescription from clinical notes.

        Returns:
            (success, prescription_object, raw_json_or_error)
        """
        full_prompt = self.prescription_prompt + clinical_notes

        success, response = self.generate(full_prompt, json_mode=True)
        if not success:
            return False, None, response

        try:
            # Clean the response (remove any markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()

            # Parse JSON
            data = json.loads(cleaned)
            prescription = Prescription(**data)
            return True, prescription, cleaned

        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON from LLM: {str(e)}\nRaw: {response[:500]}"
        except Exception as e:
            return False, None, f"Failed to parse prescription: {str(e)}"

    def query_patient_records(self, context: str, question: str) -> Tuple[bool, str]:
        """Answer a question about patient records using RAG context.

        Args:
            context: Retrieved documents about the patient
            question: Doctor's question

        Returns:
            (success, answer_or_error)
        """
        full_prompt = self.rag_prompt.format(context=context, question=question)
        return self.generate(full_prompt, json_mode=False)

    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model": self.model,
            "ram_gb": self._get_available_ram_gb(),
            "ollama_available": self.is_available()
        }
