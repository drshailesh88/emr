"""EMR Services - Core business logic and data access."""

# Database
from .database import DatabaseService

# LLM (optional - requires Ollama)
try:
    from .llm import LLMService
except ImportError:
    LLMService = None

# RAG (Vector-based - optional, for 8GB+ systems, requires chromadb)
try:
    from .rag import RAGService
except ImportError:
    RAGService = None

# PDF Generation (optional - requires fpdf2)
try:
    from .pdf import PDFService
except ImportError:
    PDFService = None

# Export Service
try:
    from .export import ExportService
except ImportError:
    ExportService = None

# Phonetic Search (for Indian names)
from .phonetic import IndianPhoneticSearch, MultiStrategySearch, get_phonetic_code

# Safety Framework
from .safety import (
    PrescriptionSafetyChecker,
    CriticalInfoBanner,
    DRUG_DATABASE,
    ALLERGY_CROSS_REACTIVITY,
)

# SQL-based Context Builder (alternative to vector RAG)
from .context_builder import ContextBuilder, QueryParser

# App Mode Detection
from .app_mode import (
    AppMode,
    AppModeManager,
    ModeCapabilities,
    get_mode_manager,
    get_current_mode,
    get_capabilities,
    can_use_llm,
    can_use_rag,
)

__all__ = [
    # Database
    "DatabaseService",
    # LLM
    "LLMService",
    # RAG
    "RAGService",
    # PDF
    "PDFService",
    # Export
    "ExportService",
    # Phonetic
    "IndianPhoneticSearch",
    "MultiStrategySearch",
    "get_phonetic_code",
    # Safety
    "PrescriptionSafetyChecker",
    "CriticalInfoBanner",
    "DRUG_DATABASE",
    "ALLERGY_CROSS_REACTIVITY",
    # Context Builder
    "ContextBuilder",
    "QueryParser",
    # App Mode
    "AppMode",
    "AppModeManager",
    "ModeCapabilities",
    "get_mode_manager",
    "get_current_mode",
    "get_capabilities",
    "can_use_llm",
    "can_use_rag",
]
