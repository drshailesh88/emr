"""EMR Services - Core business logic and data access."""

# Database
from .database import DatabaseService
<<<<<<< HEAD

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

# Backup and Cloud Sync
try:
    from .backup import BackupService, BackupInfo
    from .crypto import CryptoService, EncryptedData, DecryptionError, is_crypto_available
    from .sync import (
        SyncService, SyncStatus, SyncProgress,
        StorageBackend, LocalStorageBackend, S3StorageBackend, DocAssistCloudBackend,
        get_or_create_device_id
    )
    from .settings import SettingsService, BackupSettings, DoctorSettings, AppSettings
    from .scheduler import BackupScheduler
except ImportError:
    BackupService = None
    BackupInfo = None
    CryptoService = None
    EncryptedData = None
    DecryptionError = None
    is_crypto_available = None
    SyncService = None
    SyncStatus = None
    SyncProgress = None
    StorageBackend = None
    LocalStorageBackend = None
    S3StorageBackend = None
    DocAssistCloudBackend = None
    get_or_create_device_id = None
    SettingsService = None
    BackupSettings = None
    DoctorSettings = None
    AppSettings = None
    BackupScheduler = None

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
    # Backup
    "BackupService",
    "BackupInfo",
    "CryptoService",
    "EncryptedData",
    "DecryptionError",
    "is_crypto_available",
    "SyncService",
    "SyncStatus",
    "SyncProgress",
    "StorageBackend",
    "LocalStorageBackend",
    "S3StorageBackend",
    "DocAssistCloudBackend",
    "get_or_create_device_id",
    "SettingsService",
    "BackupSettings",
    "DoctorSettings",
    "AppSettings",
    "BackupScheduler",
]
