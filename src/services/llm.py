"""Local LLM service via Ollama with RAM-based model selection.

Key improvements from original:
1. Uses AVAILABLE RAM, not total RAM for model selection
2. Includes smaller model tiers for low-RAM systems
3. Implements fallback ladder if preferred model unavailable
4. Adds context length limits to prevent OOM
5. Supports model override via environment variable
"""

import json
import os
import gc
import requests
import psutil
from typing import Optional, Tuple, List
from pathlib import Path
from datetime import datetime

from ..models.schemas import Prescription


class LLMService:
    """Handles all LLM operations via Ollama with intelligent RAM management."""

    # RAM thresholds for model selection (based on AVAILABLE RAM, not total)
    # Format: (available_ram_threshold_gb, model_name, context_length)
    MODEL_TIERS = [
        # Minimal mode - for systems with <2GB available
        (2, "qwen2.5:0.5b", 1024),     # ~400MB model
        # Low RAM mode - 2-4GB available
        (4, "qwen2.5:1.5b", 2048),     # ~1.2GB model
        # Standard mode - 4-8GB available
        (8, "qwen2.5:3b", 4096),       # ~2.5GB model
        # Full mode - 8GB+ available
        (float("inf"), "qwen2.5:7b", 8192),  # ~5GB model
    ]

    # Fallback chain - if primary model fails, try these in order
    FALLBACK_MODELS = [
        "qwen2.5:1.5b",
        "qwen2.5:0.5b",
        "tinyllama:latest",
        "phi:latest",
    ]

    # Minimum RAM reserve (don't use if less than this available)
    MIN_RAM_RESERVE_GB = 1.0

    def __init__(self, base_url: Optional[str] = None, model_override: Optional[str] = None):
        """
        Initialize LLM service.

        Args:
            base_url: Ollama API URL (default: http://localhost:11434)
            model_override: Force specific model (ignores RAM-based selection)
        """
        if base_url is None:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.base_url = base_url

        # Check for model override from env or parameter
        self.model_override = model_override or os.getenv("EMR_LLM_MODEL")
        self.model, self.context_length = self._select_model()

        # Track model load status
        self._model_loaded = False
        self._last_used = None

        self._load_prompts()

    def _get_available_ram_gb(self) -> float:
        """Get AVAILABLE (not total) system RAM in GB."""
        mem = psutil.virtual_memory()
        # Use available, not total - this is the key fix
        return mem.available / (1024 ** 3)

    def _get_total_ram_gb(self) -> float:
        """Get total system RAM in GB."""
        mem = psutil.virtual_memory()
        return mem.total / (1024 ** 3)

    def _select_model(self) -> Tuple[str, int]:
        """
        Select appropriate model based on AVAILABLE RAM.

        Returns:
            (model_name, context_length)
        """
        # Honor override if set
        if self.model_override:
            print(f"Using model override: {self.model_override}")
            return self.model_override, 4096  # Default context for overrides

        available_ram = self._get_available_ram_gb()
        total_ram = self._get_total_ram_gb()

        # Check if we have minimum RAM
        if available_ram < self.MIN_RAM_RESERVE_GB:
            print(f"⚠️ Warning: Only {available_ram:.1f}GB RAM available. LLM may not work reliably.")

        # Select model based on available RAM
        for threshold, model, context in self.MODEL_TIERS:
            if available_ram < threshold:
                print(f"RAM: {available_ram:.1f}GB available (of {total_ram:.1f}GB total)")
                print(f"Selected model: {model} (context: {context})")
                return model, context

        # Default to largest if plenty of RAM
        return self.MODEL_TIERS[-1][1], self.MODEL_TIERS[-1][2]

    def _get_conservative_context_length(self) -> int:
        """Get conservative context length based on current RAM state."""
        available_ram = self._get_available_ram_gb()

        if available_ram < 2:
            return 512
        elif available_ram < 4:
            return 1024
        elif available_ram < 8:
            return 2048
        else:
            return self.context_length

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
            print(f"Pulling model {self.model}... This may take a few minutes.")
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

    def generate(
        self,
        prompt: str,
        json_mode: bool = False,
        timeout: int = 120,
        max_tokens: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Generate response from LLM with memory-aware settings.

        Args:
            prompt: The prompt to send
            json_mode: If True, expect JSON output
            timeout: Request timeout in seconds
            max_tokens: Maximum tokens to generate (default: auto based on RAM)

        Returns:
            (success, response_or_error)
        """
        if not self.is_available():
            return False, "Ollama is not running. Please start Ollama."

        # Check RAM before generation
        available_ram = self._get_available_ram_gb()
        if available_ram < self.MIN_RAM_RESERVE_GB:
            # Try to free memory
            gc.collect()
            available_ram = self._get_available_ram_gb()
            if available_ram < self.MIN_RAM_RESERVE_GB:
                return False, f"Insufficient RAM ({available_ram:.1f}GB). Close other applications."

        # Get conservative context length based on current RAM
        context_len = self._get_conservative_context_length()

        # Truncate prompt if too long (rough estimate: 4 chars per token)
        max_prompt_chars = context_len * 3  # Leave room for response
        if len(prompt) > max_prompt_chars:
            prompt = prompt[:max_prompt_chars] + "\n[TRUNCATED - Context too long]"
            print(f"Warning: Prompt truncated to {max_prompt_chars} chars")

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_ctx": context_len,
                    "num_predict": max_tokens or 1024,
                }
            }
            if json_mode:
                payload["format"] = "json"

            self._last_used = datetime.now()

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout
            )

            if response.status_code == 200:
                result = response.json()
                return True, result.get("response", "")

            # Handle specific error codes
            if response.status_code == 500:
                error_text = response.text.lower()
                if "out of memory" in error_text or "oom" in error_text:
                    return False, "Out of memory. Try closing other applications or using a smaller model."
                if "model not found" in error_text:
                    # Try fallback model
                    return self._generate_with_fallback(prompt, json_mode, timeout)

            return False, f"API error: {response.status_code} - {response.text[:200]}"

        except requests.Timeout:
            return False, "Request timed out. The model may be too large for your system."
        except requests.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def _generate_with_fallback(
        self,
        prompt: str,
        json_mode: bool,
        timeout: int
    ) -> Tuple[bool, str]:
        """Try generation with fallback models."""
        for fallback in self.FALLBACK_MODELS:
            if fallback == self.model:
                continue  # Skip current model

            print(f"Trying fallback model: {fallback}")
            try:
                payload = {
                    "model": fallback,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": 1024,  # Conservative for fallbacks
                        "num_predict": 512,
                    }
                }
                if json_mode:
                    payload["format"] = "json"

                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=timeout
                )

                if response.status_code == 200:
                    self.model = fallback  # Switch to working model
                    result = response.json()
                    return True, result.get("response", "")

            except Exception:
                continue

        return False, "All models failed. Please check Ollama installation."

    def unload_model(self) -> bool:
        """Attempt to unload model from memory (if supported by Ollama)."""
        try:
            # Ollama doesn't have explicit unload, but we can try
            # to minimize memory by calling garbage collection
            gc.collect()

            # Some Ollama versions support keep_alive: 0 to unload
            requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "",
                    "keep_alive": 0  # Unload immediately
                },
                timeout=5
            )
            self._model_loaded = False
            return True
        except Exception:
            return False

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
        """Get detailed information about the current model and system."""
        return {
            "model": self.model,
            "context_length": self.context_length,
            "ram_available_gb": round(self._get_available_ram_gb(), 2),
            "ram_total_gb": round(self._get_total_ram_gb(), 2),
            "ram_percent_used": round(psutil.virtual_memory().percent, 1),
            "ollama_available": self.is_available(),
            "model_override": self.model_override,
            "last_used": self._last_used.isoformat() if self._last_used else None,
        }

    def get_health_status(self) -> dict:
        """Get health status for monitoring."""
        available_ram = self._get_available_ram_gb()

        status = "healthy"
        warnings = []

        if available_ram < 1.5:
            status = "critical"
            warnings.append("Very low RAM available")
        elif available_ram < 3:
            status = "warning"
            warnings.append("Low RAM available")

        if not self.is_available():
            status = "unavailable"
            warnings.append("Ollama not running")

        return {
            "status": status,
            "warnings": warnings,
            "model": self.model,
            "ram_available_gb": round(available_ram, 2),
        }
