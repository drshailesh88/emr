"""App mode detection and configuration.

This module determines whether to run in Full or Lite mode based on
system resources and user preferences.

Modes:
- LITE: Core EMR only, no AI features (works on 2-4GB RAM)
- STANDARD: Core EMR + LLM for prescriptions (works on 4-8GB RAM)
- FULL: All features including vector RAG (8GB+ RAM)
"""

import os
import psutil
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class AppMode(Enum):
    """Application modes based on system capabilities."""
    LITE = "lite"           # No AI, 2GB RAM
    STANDARD = "standard"   # LLM only, 4GB RAM
    FULL = "full"           # LLM + Vector RAG, 8GB+ RAM


@dataclass
class ModeCapabilities:
    """Capabilities available in each mode."""
    mode: AppMode

    # Core features (always available)
    patient_management: bool = True
    visit_tracking: bool = True
    investigation_tracking: bool = True
    procedure_tracking: bool = True
    pdf_generation: bool = True
    fts_search: bool = True
    phonetic_search: bool = True
    patient_snapshot: bool = True
    consultations: bool = True
    audit_logging: bool = True

    # AI features (mode-dependent)
    llm_prescription: bool = False
    llm_query_answering: bool = False
    vector_rag: bool = False
    semantic_search: bool = False

    # Resource info
    recommended_ram_gb: float = 2.0
    max_context_length: int = 0


# Mode definitions
MODE_CAPABILITIES = {
    AppMode.LITE: ModeCapabilities(
        mode=AppMode.LITE,
        llm_prescription=False,
        llm_query_answering=False,
        vector_rag=False,
        semantic_search=False,
        recommended_ram_gb=2.0,
        max_context_length=0,
    ),
    AppMode.STANDARD: ModeCapabilities(
        mode=AppMode.STANDARD,
        llm_prescription=True,
        llm_query_answering=True,
        vector_rag=False,
        semantic_search=False,
        recommended_ram_gb=4.0,
        max_context_length=2048,
    ),
    AppMode.FULL: ModeCapabilities(
        mode=AppMode.FULL,
        llm_prescription=True,
        llm_query_answering=True,
        vector_rag=True,
        semantic_search=True,
        recommended_ram_gb=8.0,
        max_context_length=8192,
    ),
}


class AppModeManager:
    """Manages application mode detection and configuration."""

    # RAM thresholds for mode selection (in GB)
    RAM_THRESHOLDS = {
        AppMode.LITE: 4.0,      # Use lite if available RAM < 4GB
        AppMode.STANDARD: 8.0,   # Use standard if available RAM < 8GB
        AppMode.FULL: float("inf"),  # Use full if 8GB+ available
    }

    def __init__(self, mode_override: Optional[str] = None):
        """
        Initialize mode manager.

        Args:
            mode_override: Force specific mode (from env or config)
        """
        self.mode_override = mode_override or os.getenv("EMR_APP_MODE")
        self._detected_mode: Optional[AppMode] = None
        self._capabilities: Optional[ModeCapabilities] = None

    @property
    def mode(self) -> AppMode:
        """Get current app mode."""
        if self._detected_mode is None:
            self._detected_mode = self._detect_mode()
        return self._detected_mode

    @property
    def capabilities(self) -> ModeCapabilities:
        """Get capabilities for current mode."""
        if self._capabilities is None:
            self._capabilities = MODE_CAPABILITIES[self.mode]
        return self._capabilities

    def _detect_mode(self) -> AppMode:
        """Detect appropriate mode based on system resources."""
        # Honor override if set
        if self.mode_override:
            try:
                mode = AppMode(self.mode_override.lower())
                print(f"Using mode override: {mode.value}")
                return mode
            except ValueError:
                print(f"Invalid mode override: {self.mode_override}")

        # Detect based on available RAM
        available_ram = self._get_available_ram_gb()
        total_ram = self._get_total_ram_gb()

        print(f"System RAM: {available_ram:.1f}GB available / {total_ram:.1f}GB total")

        for mode, threshold in self.RAM_THRESHOLDS.items():
            if available_ram < threshold:
                print(f"Selected mode: {mode.value}")
                return mode

        return AppMode.FULL

    def _get_available_ram_gb(self) -> float:
        """Get available RAM in GB."""
        return psutil.virtual_memory().available / (1024 ** 3)

    def _get_total_ram_gb(self) -> float:
        """Get total RAM in GB."""
        return psutil.virtual_memory().total / (1024 ** 3)

    def get_status(self) -> Dict[str, Any]:
        """Get mode status for display."""
        caps = self.capabilities
        return {
            "mode": self.mode.value,
            "mode_display": self._get_mode_display_name(),
            "ram_available_gb": round(self._get_available_ram_gb(), 1),
            "ram_total_gb": round(self._get_total_ram_gb(), 1),
            "features": {
                "AI Prescriptions": caps.llm_prescription,
                "AI Query Answering": caps.llm_query_answering,
                "Semantic Search": caps.semantic_search,
                "FTS Search": caps.fts_search,
                "Phonetic Search": caps.phonetic_search,
            },
            "override_active": self.mode_override is not None,
        }

    def _get_mode_display_name(self) -> str:
        """Get human-readable mode name."""
        names = {
            AppMode.LITE: "Lite Mode (No AI)",
            AppMode.STANDARD: "Standard Mode (LLM Only)",
            AppMode.FULL: "Full Mode (LLM + RAG)",
        }
        return names.get(self.mode, "Unknown")

    def can_use_feature(self, feature: str) -> bool:
        """Check if a specific feature is available in current mode."""
        return getattr(self.capabilities, feature, False)

    def get_upgrade_message(self) -> Optional[str]:
        """Get message about upgrading to a better mode."""
        if self.mode == AppMode.LITE:
            return (
                "💡 Upgrade to Standard mode for AI-powered prescriptions. "
                "Requires 4GB+ RAM available."
            )
        elif self.mode == AppMode.STANDARD:
            return (
                "💡 Upgrade to Full mode for semantic search and advanced RAG. "
                "Requires 8GB+ RAM available."
            )
        return None

    def force_mode(self, mode: AppMode):
        """Force a specific mode (use with caution)."""
        self._detected_mode = mode
        self._capabilities = MODE_CAPABILITIES[mode]
        print(f"Mode forced to: {mode.value}")


# Global mode manager instance
_mode_manager: Optional[AppModeManager] = None


def get_mode_manager() -> AppModeManager:
    """Get the global mode manager instance."""
    global _mode_manager
    if _mode_manager is None:
        _mode_manager = AppModeManager()
    return _mode_manager


def get_current_mode() -> AppMode:
    """Get the current app mode."""
    return get_mode_manager().mode


def get_capabilities() -> ModeCapabilities:
    """Get capabilities for current mode."""
    return get_mode_manager().capabilities


def can_use_llm() -> bool:
    """Check if LLM features are available."""
    return get_capabilities().llm_prescription


def can_use_rag() -> bool:
    """Check if vector RAG is available."""
    return get_capabilities().vector_rag
